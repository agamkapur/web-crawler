import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode
from bs4 import BeautifulSoup
from utils.verification_utils import verify
from collections import deque
from typing import Set, List, Optional, Dict, Any
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedirectLoopError(Exception):
    """Exception raised when a redirect loop is detected."""
    pass


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


class URLNormalizer:
    """Handles URL normalization to ensure consistent URL handling."""
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize a URL to ensure consistent handling.
        
        This function:
        - Removes trailing slashes from paths (except for root)
        - Converts to lowercase scheme and hostname
        - Removes default ports (80 for HTTP, 443 for HTTPS)
        - Removes fragments (#section)
        - Sorts query parameters
        - Removes duplicate query parameters
        
        Args:
            url: The URL to normalize
            
        Returns:
            Normalized URL string
        """
        try:
            # Parse the URL
            parsed = urlparse(url)
            
            # Normalize scheme and netloc (lowercase)
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            
            # Remove default ports
            if netloc.endswith(':80') and scheme == 'http':
                netloc = netloc[:-3]  # Remove ':80' from the end
            elif netloc.endswith(':443') and scheme == 'https':
                netloc = netloc[:-4]  # Remove ':443' from the end
            
            # Normalize path (remove trailing slash except for root)
            path = parsed.path
            if path != '/' and path.endswith('/'):
                path = path.rstrip('/')
            
            # Remove fragments
            fragment = ''
            
            # Normalize query parameters
            if parsed.query:
                # Parse query parameters
                query_params = parse_qs(parsed.query, keep_blank_values=True)
                
                # Remove duplicate parameters (keep last occurrence)
                normalized_params = {}
                for key, values in query_params.items():
                    if values:
                        # Keep the last value for each parameter
                        normalized_params[key] = [values[-1]]
                    else:
                        # Keep empty values as empty list
                        normalized_params[key] = []
                
                # Sort parameters and encode
                sorted_params = sorted(normalized_params.items())
                query = urlencode(sorted_params, doseq=True)
            else:
                query = ''
            
            # Reconstruct the URL
            normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
            
            return normalized
            
        except Exception as e:
            # If normalization fails, return the original URL
            logger.warning(f"Failed to normalize URL {url}: {e}")
            return url


class RedirectHandler:
    """Handles redirect logic and loop detection."""
    
    @staticmethod
    def detect_redirect_loop(redirect_chain: List[str], new_url: str, max_redirects: int = 10) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Detect various types of redirect loops.
        
        Args:
            redirect_chain: List of URLs in the current redirect chain
            new_url: The new URL to check
            max_redirects: Maximum number of redirects allowed
            
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
        
        # Check for longer circular patterns
        if len(redirect_chain) >= 4:
            for i in range(len(redirect_chain) - 3):
                if new_url == redirect_chain[i]:
                    return True, "circular", f"Circular redirect loop detected at position {i}"
        
        # Check for infinite loop (same URL appears multiple times)
        if new_url in redirect_chain:
            return True, "infinite", f"Infinite redirect loop detected: {new_url}"
        
        return False, None, None

    async def follow_redirects(
        self, 
        session: aiohttp.ClientSession, 
        url: str, 
        config: CrawlConfig
    ) -> tuple[str, List[str], Optional[tuple[aiohttp.ClientResponse, str]]]:
        """
        Follow redirects safely with loop detection.
        
        Args:
            session: aiohttp client session
            url: The URL to follow redirects for
            config: Crawl configuration
            
        Returns:
            tuple: (final_url, redirect_chain, response_data) where response_data is (response, content) or None
            
        Raises:
            RedirectLoopError: If a redirect loop is detected
        """
        redirect_chain = [url]
        current_url = url
        
        timeout_obj = aiohttp.ClientTimeout(total=config.timeout)
        
        for redirect_count in range(config.max_redirects):
            try:
                async with session.get(current_url, timeout=timeout_obj, allow_redirects=False) as response:
                    # Check if we got a redirect response
                    if response.status in [301, 302, 303, 307, 308]:
                        # Get the redirect location
                        redirect_url = response.headers.get('Location')
                        if not redirect_url:
                            # No Location header, read content and return current response
                            try:
                                content = await response.text()
                                return current_url, redirect_chain, (response, content)
                            except Exception as e:
                                logger.warning(f"  Failed to read response content: {e}")
                                return current_url, redirect_chain, None
                        
                        # Convert relative redirect URL to absolute
                        redirect_url = urljoin(current_url, redirect_url)
                        
                        # Check for redirect loop
                        is_loop, loop_type, loop_description = self.detect_redirect_loop(
                            redirect_chain, redirect_url, config.max_redirects
                        )
                        if is_loop:
                            raise RedirectLoopError(f"Redirect loop detected: {loop_description}")
                        
                        # Add to redirect chain and continue
                        redirect_chain.append(redirect_url)
                        current_url = redirect_url
                        
                        logger.info(f"  Redirect {redirect_count + 1}: {redirect_chain[-2]} -> {redirect_chain[-1]}")
                        
                    else:
                        # No more redirects, read content and return the final URL
                        try:
                            content = await response.text()
                            return current_url, redirect_chain, (response, content)
                        except Exception as e:
                            logger.warning(f"  Failed to read response content: {e}")
                            return current_url, redirect_chain, None
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # If we can't follow redirects, return what we have
                return current_url, redirect_chain, None
        
        # If we've reached max redirects, raise an error
        raise RedirectLoopError(f"Maximum redirects ({config.max_redirects}) exceeded")


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

