import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from utils.verification_utils import verify
from utils.url_normalizer import URLNormalizer
from utils.redirect_handler import RedirectHandler, RedirectLoopError
from collections import deque
from typing import Set, List, Optional, Dict, Any
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





@dataclass
class CrawlConfig:
    """Configuration for web crawling."""
    delay: float = 0.1
    max_redirects: int = 10
    max_concurrent: int = 10
    timeout: int = 10
    user_agent: str = "Mozilla/5.0 (compatible; MyCrawler/1.0; +https://example.com/bot)"


@dataclass
class CrawlResult:
    """Result of a crawl operation."""
    urls: Set[str]
    visited_count: int
    error_count: int
    redirect_count: int








class WebCrawler:
    """Async web crawler with comprehensive functionality."""
    
    def __init__(self, config: Optional[CrawlConfig] = None):
        """
        Initialize the web crawler.
        
        Args:
            config: Crawl configuration, uses defaults if None
        """
        self.config = config or CrawlConfig()
        self.redirect_handler = RedirectHandler()
        self.url_normalizer = URLNormalizer()
        self.visited_urls: Set[str] = set()
        self.all_found_urls: Set[str] = set()
        self.error_count = 0
        self.redirect_count = 0
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for HTTP requests."""
        return {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    async def _crawl_single_url(
        self, 
        session: aiohttp.ClientSession, 
        url: str, 
        base_domain: str
    ) -> List[str]:
        """
        Crawl a single URL and return discovered URLs.
        
        Args:
            session: aiohttp client session
            url: The URL to crawl
            base_domain: Base domain to restrict crawling to
            
        Returns:
            List of discovered URLs from the same domain
        """
        discovered_urls = []
        
        try:
            logger.info(f"Crawling: {url}")
            
            # Follow redirects safely
            try:
                final_url, redirect_chain, response_data = await self.redirect_handler.follow_redirects(
                    session, url, self.config
                )
                
                # Update redirect count
                if len(redirect_chain) > 1:
                    self.redirect_count += 1
                
                # If we ended up at a different URL, check if it's in the same domain
                if final_url != url:
                    if urlparse(final_url).netloc != base_domain:
                        logger.info(f"  Redirected to external domain: {final_url}")
                        return discovered_urls
                    
                    # If the final URL is already visited, skip
                    if final_url in self.visited_urls:
                        logger.info(f"  Final URL already visited: {final_url}")
                        return discovered_urls
                    
                    # Update url to the final URL
                    url = final_url
                    logger.info(f"  Final URL after redirects: {final_url}")
                
                # If no response (network error), skip
                if response_data is None:
                    logger.warning(f"  Failed to get response for {url}")
                    self.error_count += 1
                    return discovered_urls
                
                # Unpack response data
                response, html_content = response_data
                
                # Check if response is successful
                if response.status >= 400:
                    logger.warning(f"  HTTP {response.status} error for {url}")
                    self.error_count += 1
                    return discovered_urls
                
            except RedirectLoopError as e:
                logger.warning(f"  Redirect loop detected: {e}")
                self.error_count += 1
                return discovered_urls
            except Exception as e:
                logger.warning(f"  Failed to follow redirects: {e}")
                self.error_count += 1
                return discovered_urls
            
            # Parse the HTML content
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
            except Exception as e:
                logger.warning(f"  Failed to parse HTML for {url}: {e}")
                self.error_count += 1
                return discovered_urls
            
            # Find all anchor tags with href attributes
            links = soup.find_all('a', href=True)
            
            # Extract and process URLs
            for link in links:
                href = link['href']
                
                # Convert relative URLs to absolute URLs
                absolute_url = urljoin(url, href)
                
                # Normalize the discovered URL
                normalized_url = self.url_normalizer.normalize_url(absolute_url)
                
                # Only include URLs from the same domain and not already visited
                if (urlparse(normalized_url).netloc == base_domain and
                    normalized_url not in self.visited_urls):
                    discovered_urls.append(normalized_url)
            
            return discovered_urls
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            self.error_count += 1
            return discovered_urls

    async def crawl(self, base_url: str) -> CrawlResult:
        """
        Recursively crawl a website starting from the base URL.
        
        Args:
            base_url: The URL of the webpage to start crawling from
            
        Returns:
            CrawlResult containing all discovered URLs and statistics
            
        Raises:
            Exception: If the base URL is invalid or other errors occur
        """
        try:
            # Validate only the base URL
            if not verify(base_url):
                raise Exception(f"Invalid base URL: {base_url}")
            
            # Normalize the base URL
            normalized_base_url = self.url_normalizer.normalize_url(base_url)
            
            # Initialize tracking variables
            self.visited_urls.clear()
            self.all_found_urls.clear()
            self.error_count = 0
            self.redirect_count = 0
            
            urls_to_visit = deque([normalized_base_url])  # Just URLs, no depth tracking
            base_domain = urlparse(normalized_base_url).netloc
            
            logger.info(f"Starting asynchronous recursive crawl of {base_url}")
            logger.info(f"Domain: {base_domain}")
            logger.info(f"Delay between requests: {self.config.delay}s")
            logger.info(f"Max redirects per URL: {self.config.max_redirects}")
            logger.info(f"Max concurrent requests: {self.config.max_concurrent}")
            logger.info("-" * 50)
            
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.config.max_concurrent)
            
            headers = self._get_headers()

            async with aiohttp.ClientSession(headers=headers) as session:
                async def crawl_with_semaphore(url: str) -> List[str]:
                    async with semaphore:
                        if self.config.delay > 0:
                            await asyncio.sleep(self.config.delay)
                        return await self._crawl_single_url(session, url, base_domain)
                
                while urls_to_visit:
                    # Get current batch of URLs to process
                    current_batch = []
                    while urls_to_visit and len(current_batch) < self.config.max_concurrent:
                        current_url = urls_to_visit.popleft()
                        
                        # Skip if already visited
                        if current_url in self.visited_urls:
                            continue
                        
                        # Normalize the URL
                        normalized_url = self.url_normalizer.normalize_url(current_url)
                        
                        # Skip if not same domain
                        if urlparse(normalized_url).netloc != base_domain:
                            continue
                        
                        current_batch.append(normalized_url)
                    
                    if not current_batch:
                        break
                    
                    # Process current batch concurrently
                    tasks = [crawl_with_semaphore(url) for url in current_batch]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for i, url in enumerate(current_batch):
                        try:
                            # Add to visited set
                            self.visited_urls.add(url)
                            self.all_found_urls.add(url)
                            
                            # Process discovered URLs
                            if isinstance(results[i], list):
                                discovered_urls = results[i]
                                for discovered_url in discovered_urls:
                                    if discovered_url not in self.visited_urls:
                                        urls_to_visit.append(discovered_url)
                            else:
                                logger.error(f"Error processing {url}: {results[i]}")
                                self.error_count += 1
                                
                        except Exception as e:
                            logger.error(f"Error processing results for {url}: {e}")
                            self.error_count += 1
            
            # Print final results
            logger.info("-" * 50)
            logger.info(f"Crawl completed!")
            logger.info(f"Total URLs found: {len(self.all_found_urls)}")
            logger.info(f"Total URLs visited: {len(self.visited_urls)}")
            logger.info(f"Errors encountered: {self.error_count}")
            logger.info(f"Redirects followed: {self.redirect_count}")
            logger.info("\nAll discovered URLs:")
            logger.info("-" * 50)
            
            # Print all found URLs sorted
            for url in sorted(self.all_found_urls):
                print(url)
            
            return CrawlResult(
                urls=self.all_found_urls,
                visited_count=len(self.visited_urls),
                error_count=self.error_count,
                redirect_count=self.redirect_count
            )
                
        except Exception as e:
            raise Exception(f"Error during asynchronous recursive crawling: {e}")


# Backward compatibility functions
async def crawl_async(base_url: str, delay: float = 0.1, 
                     max_redirects: int = 10, max_concurrent: int = 10) -> Set[str]:
    """
    Backward compatibility function for async crawling.
    
    Args:
        base_url: The URL of the webpage to start crawling from
        delay: Delay between requests in seconds
        max_redirects: Maximum number of redirects to follow per URL
        max_concurrent: Maximum number of concurrent requests
        
    Returns:
        Set of all discovered URLs
    """
    config = CrawlConfig(
        delay=delay,
        max_redirects=max_redirects,
        max_concurrent=max_concurrent
    )
    
    crawler = WebCrawler(config)
    result = await crawler.crawl(base_url)
    return result.urls


def crawl(base_url: str, delay: float = 0.1, 
          max_redirects: int = 10, max_concurrent: int = 10) -> None:
    """
    Backward compatibility function for synchronous crawling.
    
    Args:
        base_url: The URL of the webpage to start crawling from
        delay: Delay between requests in seconds
        max_redirects: Maximum number of redirects to follow per URL
        max_concurrent: Maximum number of concurrent requests
        
    Returns:
        None: Prints all found URLs to stdout
    """
    try:
        asyncio.run(crawl_async(base_url, delay, max_redirects, max_concurrent))
    except Exception as e:
        raise Exception(f"Error during recursive crawling: {e}")


# Export the main classes and functions
__all__ = [
    'WebCrawler', 'CrawlConfig', 'CrawlResult', 'RedirectLoopError', 
    'crawl', 'crawl_async'
]

