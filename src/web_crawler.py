import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from utils.verification_utils import verify
from collections import deque
import time


def crawl(base_url, max_depth=None, delay=1):
    """
    Recursively crawl a website starting from the base URL.
    
    Args:
        base_url (str): The URL of the webpage to start crawling from
        max_depth (int, optional): Maximum depth for recursive crawling. None for unlimited.
        delay (float): Delay between requests in seconds to be polite to the server
        
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
            
            # Skip if URL is invalid
            if not verify(current_url):
                continue
            
            try:
                print(f"[Depth {current_depth}] Crawling: {current_url}")
                
                # Add to visited set
                visited_urls.add(current_url)
                all_found_urls.add(current_url)
                
                # Send HTTP request
                response = requests.get(current_url, timeout=10)
                response.raise_for_status()
                
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
                    if (verify(absolute_url) and 
                        urlparse(absolute_url).netloc == base_domain and
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


def crawl_single_page(base_url):
    """
    Crawl a single webpage and extract all URLs found on it (non-recursive).
    This is the original functionality preserved for backward compatibility.
    
    Args:
        base_url (str): The URL of the webpage to crawl
        
    Returns:
        None: Prints all found URLs to stdout
    """
    try:
        # Validate the base URL before making the request
        if not verify(base_url):
            raise Exception(f"Invalid base URL: {base_url}")
        
        # Send HTTP request to the base URL
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        
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
            
            # Validate the URL and only include URLs from the same domain
            if verify(absolute_url) and urlparse(absolute_url).netloc == base_domain:
                urls.add(absolute_url)
        
        # Print the base URL first
        print(base_url)
        
        # Print all found URLs
        for url in sorted(urls):
            print(url)
            
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch {base_url}: {e}")
    except Exception as e:
        raise Exception(f"Error crawling {base_url}: {e}")

