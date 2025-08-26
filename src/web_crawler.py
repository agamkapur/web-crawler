import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from utils.verification_utils import verify


def crawl(base_url):
    """
    Crawl a webpage and extract all URLs found on it.
    
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

