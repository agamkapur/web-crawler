import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from utils.verification_utils import verify
from collections import deque
import time


class RedirectLoopError(Exception):
    """Exception raised when a redirect loop is detected."""
    pass


def detect_redirect_loop(redirect_chain, new_url, max_redirects=10):
    """
    Detect various types of redirect loops.
    
    Args:
        redirect_chain (list): List of URLs in the current redirect chain
        new_url (str): The new URL to check
        max_redirects (int): Maximum number of redirects allowed
        
    Returns:
        tuple: (is_loop, loop_type, loop_description)
    """
    if len(redirect_chain) >= max_redirects:
        return True, "max_redirects", f"Maximum redirects ({max_redirects}) exceeded"
    
    # Check for reverse loop (A -> B -> A pattern)
    if len(redirect_chain) >= 2:
        if new_url == redirect_chain[-2]:
            return True, "reverse", f"Reverse redirect loop: {redirect_chain[-1]} -> {new_url}"
    
    # Check for circular loop (A -> B -> C -> A pattern)
    if len(redirect_chain) >= 3:
        if new_url == redirect_chain[-3]:
            return True, "circular", f"Circular redirect loop: {redirect_chain[-2]} -> {redirect_chain[-1]} -> {new_url}"
    
    # Check for longer circular patterns (but not infinite)
    if len(redirect_chain) >= 4:
        for i in range(len(redirect_chain) - 3):
            if new_url == redirect_chain[i]:
                return True, "circular", f"Circular redirect loop detected at position {i}"
    
    # Check for infinite loop (same URL appears multiple times, but not in reverse/circular patterns)
    # This catches cases where a URL appears earlier in the chain but not in a reverse/circular pattern
    if new_url in redirect_chain:
        return True, "infinite", f"Infinite redirect loop detected: {new_url}"
    
    return False, None, None


def follow_redirects_safely(url, max_redirects=10, timeout=10):
    """
    Follow redirects safely with loop detection.
    
    Args:
        url (str): The URL to follow redirects for
        max_redirects (int): Maximum number of redirects allowed
        timeout (int): Request timeout in seconds
        
    Returns:
        tuple: (final_url, redirect_chain, response)
        
    Raises:
        RedirectLoopError: If a redirect loop is detected
    """
    redirect_chain = [url]
    current_url = url
    
    for redirect_count in range(max_redirects):
        try:
            # Make request with allow_redirects=False to manually handle redirects
            response = requests.get(current_url, timeout=timeout, allow_redirects=False)
            
            # Check if we got a redirect response
            if response.status_code in [301, 302, 303, 307, 308]:
                # Get the redirect location
                redirect_url = response.headers.get('Location')
                if not redirect_url:
                    # No Location header, return current response
                    return current_url, redirect_chain, response
                
                # Convert relative redirect URL to absolute
                redirect_url = urljoin(current_url, redirect_url)
                
                # Check for redirect loop
                is_loop, loop_type, loop_description = detect_redirect_loop(redirect_chain, redirect_url, max_redirects)
                if is_loop:
                    raise RedirectLoopError(f"Redirect loop detected: {loop_description}")
                
                # Add to redirect chain and continue
                redirect_chain.append(redirect_url)
                current_url = redirect_url
                
                print(f"  Redirect {redirect_count + 1}: {redirect_chain[-2]} -> {redirect_chain[-1]}")
                
            else:
                # No more redirects, return the final URL
                return current_url, redirect_chain, response
                
        except requests.RequestException as e:
            # If we can't follow redirects, return what we have
            return current_url, redirect_chain, None
    
    # If we've reached max redirects, raise an error
    raise RedirectLoopError(f"Maximum redirects ({max_redirects}) exceeded")


def crawl(base_url, max_depth=None, delay=1, max_redirects=10):
    """
    Recursively crawl a website starting from the base URL.
    
    Args:
        base_url (str): The URL of the webpage to start crawling from
        max_depth (int, optional): Maximum depth for recursive crawling. None for unlimited.
        delay (float): Delay between requests in seconds to be polite to the server
        max_redirects (int): Maximum number of redirects to follow per URL
        
    Returns:
        None: Prints all found URLs to stdout
    """
    try:
        # Validate the base URL before making the request
        if not verify(base_url):
            raise Exception(f"Invalid base URL: {base_url}")
        
        # Initialize tracking variables
        visited_urls = set()
        urls_to_visit = deque([(base_url, 0)])  # (url, depth)
        base_domain = urlparse(base_url).netloc
        all_found_urls = set()
        
        print(f"Starting recursive crawl of {base_url}")
        print(f"Domain: {base_domain}")
        print(f"Max depth: {max_depth if max_depth else 'unlimited'}")
        print(f"Delay between requests: {delay}s")
        print(f"Max redirects per URL: {max_redirects}")
        print("-" * 50)
        
        while urls_to_visit:
            current_url, current_depth = urls_to_visit.popleft()
            
            # Skip if already visited
            if current_url in visited_urls:
                continue
            
            # Check depth limit
            if max_depth is not None and current_depth > max_depth:
                continue
            
            # Skip if not same domain
            if urlparse(current_url).netloc != base_domain:
                continue
            
            
            try:
                print(f"[Depth {current_depth}] Crawling: {current_url}")
                
                # Follow redirects safely
                try:
                    final_url, redirect_chain, response = follow_redirects_safely(current_url, max_redirects)
                    
                    # If we ended up at a different URL, check if it's in the same domain
                    if final_url != current_url:
                        if urlparse(final_url).netloc != base_domain:
                            print(f"  Redirected to external domain: {final_url}")
                            continue
                        
                        # If the final URL is already visited, skip
                        if final_url in visited_urls:
                            print(f"  Final URL already visited: {final_url}")
                            continue
                        
                        # Update current_url to the final URL
                        current_url = final_url
                        print(f"  Final URL after redirects: {final_url}")
                    
                    # If no response (network error), skip
                    if response is None:
                        print(f"  Failed to get response for {current_url}")
                        continue
                    
                    # Check if response is successful
                    response.raise_for_status()
                    
                except RedirectLoopError as e:
                    print(f"  Redirect loop detected: {e}")
                    continue
                except requests.RequestException as e:
                    print(f"  Failed to follow redirects: {e}")
                    continue
                
                # Add to visited set
                visited_urls.add(current_url)
                all_found_urls.add(current_url)
                
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all anchor tags with href attributes
                links = soup.find_all('a', href=True)
                
                # Extract and process URLs
                for link in links:
                    href = link['href']
                    
                    # Convert relative URLs to absolute URLs
                    absolute_url = urljoin(current_url, href)
                    
                    # Validate the URL and only include URLs from the same domain
                    if (urlparse(absolute_url).netloc == base_domain and
                        absolute_url not in visited_urls):
                        
                        # Add to queue for future crawling
                        urls_to_visit.append((absolute_url, current_depth + 1))
                
                # Polite delay between requests
                if delay > 0:
                    time.sleep(delay)
                    
            except requests.RequestException as e:
                print(f"Failed to fetch {current_url}: {e}")
                continue
            except Exception as e:
                print(f"Error crawling {current_url}: {e}")
                continue
        
        # Print final results
        print("-" * 50)
        print(f"Crawl completed!")
        print(f"Total URLs found: {len(all_found_urls)}")
        print(f"Total URLs visited: {len(visited_urls)}")
        print("\nAll discovered URLs:")
        print("-" * 50)
        
        # Print all found URLs sorted
        for url in sorted(all_found_urls):
            print(url)
            
    except Exception as e:
        raise Exception(f"Error during recursive crawling: {e}")


def crawl_single_page(base_url, max_redirects=10):
    """
    Crawl a single webpage and extract all URLs found on it (non-recursive).
    This is the original functionality preserved for backward compatibility.
    
    Args:
        base_url (str): The URL of the webpage to crawl
        max_redirects (int): Maximum number of redirects to follow
        
    Returns:
        None: Prints all found URLs to stdout
    """
    try:
        # Validate the base URL before making the request
        if not verify(base_url):
            raise Exception(f"Invalid base URL: {base_url}")
        
        # Follow redirects safely
        try:
            final_url, redirect_chain, response = follow_redirects_safely(base_url, max_redirects)
            
            # If we ended up at a different URL, use that for crawling
            if final_url != base_url:
                print(f"Redirected from {base_url} to {final_url}")
                base_url = final_url
            
            # If no response (network error), raise exception
            if response is None:
                raise Exception(f"Failed to get response for {base_url}")
            
            # Check if response is successful
            response.raise_for_status()
            
        except RedirectLoopError as e:
            raise Exception(f"Redirect loop detected: {e}")
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch {base_url}: {e}")
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all anchor tags with href attributes
        links = soup.find_all('a', href=True)
        
        # Extract and normalize URLs
        urls = set()
        base_domain = urlparse(base_url).netloc
        
        for link in links:
            href = link['href']
            
            # Convert relative URLs to absolute URLs
            absolute_url = urljoin(base_url, href)
            
            if urlparse(absolute_url).netloc == base_domain:
                urls.add(absolute_url)
        
        # Print the base URL first
        print(base_url)
        
        # Print all found URLs
        for url in sorted(urls):
            print(url)
            
    except Exception as e:
        raise Exception(f"Error crawling {base_url}: {e}")

