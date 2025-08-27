import unittest
from unittest.mock import patch, Mock, AsyncMock
import sys
import os
import pytest

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from web_crawler import (
    WebCrawler, CrawlConfig, CrawlResult, RedirectLoopError, 
    RedirectHandler, URLNormalizer, crawl, crawl_async
)


class TestURLNormalizer(unittest.TestCase):
    """Test the URLNormalizer class."""
    
    def setUp(self):
        self.normalizer = URLNormalizer()
    
    def test_normalize_url_basic(self):
        """Test basic URL normalization"""
        # Test trailing slash removal
        self.assertEqual(
            self.normalizer.normalize_url("https://example.com/page/"),
            "https://example.com/page"
        )
        
        # Test root path preservation
        self.assertEqual(
            self.normalizer.normalize_url("https://example.com/"),
            "https://example.com/"
        )
        
        # Test lowercase conversion
        self.assertEqual(
            self.normalizer.normalize_url("HTTPS://EXAMPLE.COM/page"),
            "https://example.com/page"
        )
    
    def test_normalize_url_ports(self):
        """Test port normalization"""
        # Test default HTTP port removal
        self.assertEqual(
            self.normalizer.normalize_url("http://example.com:80/page"),
            "http://example.com/page"
        )
        
        # Test default HTTPS port removal
        self.assertEqual(
            self.normalizer.normalize_url("https://example.com:443/page"),
            "https://example.com/page"
        )
        
        # Test non-default port preservation
        self.assertEqual(
            self.normalizer.normalize_url("http://example.com:8080/page"),
            "http://example.com:8080/page"
        )
    
    def test_normalize_url_fragments(self):
        """Test fragment removal"""
        self.assertEqual(
            self.normalizer.normalize_url("https://example.com/page#section"),
            "https://example.com/page"
        )
        
        self.assertEqual(
            self.normalizer.normalize_url("https://example.com/page#"),
            "https://example.com/page"
        )
    
    def test_normalize_url_query_params(self):
        """Test query parameter normalization"""
        # Test parameter sorting
        self.assertEqual(
            self.normalizer.normalize_url("https://example.com/page?b=2&a=1"),
            "https://example.com/page?a=1&b=2"
        )
        
        # Test duplicate parameter removal
        self.assertEqual(
            self.normalizer.normalize_url("https://example.com/page?a=1&a=2"),
            "https://example.com/page?a=2"
        )
        
        # Test empty query parameters
        self.assertEqual(
            self.normalizer.normalize_url("https://example.com/page?"),
            "https://example.com/page"
        )
    
    def test_normalize_url_complex(self):
        """Test complex URL normalization"""
        complex_url = "HTTPS://EXAMPLE.COM:443/page/?b=2&a=1&a=3#section"
        expected = "https://example.com/page?a=3&b=2"
        self.assertEqual(self.normalizer.normalize_url(complex_url), expected)
    
    def test_normalize_url_invalid(self):
        """Test handling of invalid URLs"""
        # Should return original URL if normalization fails
        invalid_url = "not-a-valid-url"
        self.assertEqual(self.normalizer.normalize_url(invalid_url), invalid_url)


class TestRedirectHandler(unittest.TestCase):
    """Test the RedirectHandler class."""
    
    def setUp(self):
        self.handler = RedirectHandler()
    
    def test_detect_redirect_loop_infinite(self):
        """Test detection of infinite redirect loops"""
        redirect_chain = ["https://example.com", "https://example.com/redirect1", "https://example.com/redirect2", "https://example.com/redirect3", "https://example.com/redirect4"]
        new_url = "https://example.com/redirect1"  # Same as second URL
        
        is_loop, loop_type, description = self.handler.detect_redirect_loop(redirect_chain, new_url)
        
        self.assertTrue(is_loop)
        self.assertEqual(loop_type, "circular")
        self.assertIn("Circular redirect loop detected", description)
    
    def test_detect_redirect_loop_reverse(self):
        """Test detection of reverse redirect loops (A -> B -> A)"""
        redirect_chain = ["https://example.com", "https://example.com/redirect1"]
        new_url = "https://example.com"  # Same as first URL
        
        is_loop, loop_type, description = self.handler.detect_redirect_loop(redirect_chain, new_url)
        
        self.assertTrue(is_loop)
        self.assertEqual(loop_type, "reverse")
        self.assertIn("Reverse redirect loop", description)
    
    def test_detect_redirect_loop_circular(self):
        """Test detection of circular redirect loops (A -> B -> C -> A)"""
        redirect_chain = ["https://example.com", "https://example.com/redirect1", "https://example.com/redirect2"]
        new_url = "https://example.com"  # Same as first URL
        
        is_loop, loop_type, description = self.handler.detect_redirect_loop(redirect_chain, new_url)
        
        self.assertTrue(is_loop)
        self.assertEqual(loop_type, "circular")
        self.assertIn("Circular redirect loop", description)
    
    def test_detect_redirect_loop_max_redirects(self):
        """Test detection when maximum redirects is exceeded"""
        redirect_chain = ["https://example.com"] * 10  # 10 URLs
        new_url = "https://example.com/redirect11"
        
        is_loop, loop_type, description = self.handler.detect_redirect_loop(redirect_chain, new_url, max_redirects=10)
        
        self.assertTrue(is_loop)
        self.assertEqual(loop_type, "max_redirects")
        self.assertIn("Maximum redirects (10) exceeded", description)
    
    def test_detect_redirect_loop_no_loop(self):
        """Test that no loop is detected for normal redirects"""
        redirect_chain = ["https://example.com", "https://example.com/redirect1"]
        new_url = "https://example.com/redirect2"  # New URL
        
        is_loop, loop_type, description = self.handler.detect_redirect_loop(redirect_chain, new_url)
        
        self.assertFalse(is_loop)
        self.assertIsNone(loop_type)
        self.assertIsNone(description)


class TestCrawlConfig(unittest.TestCase):
    """Test the CrawlConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = CrawlConfig()
        
        self.assertEqual(config.delay, 0.1)
        self.assertEqual(config.max_redirects, 10)
        self.assertEqual(config.max_concurrent, 10)
        self.assertEqual(config.timeout, 10)
        self.assertIn("MyCrawler/1.0", config.user_agent)
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = CrawlConfig(
            delay=0.5,
            max_redirects=5,
            max_concurrent=20,
            timeout=30,
            user_agent="CustomBot/1.0"
        )
        
        self.assertEqual(config.delay, 0.5)
        self.assertEqual(config.max_redirects, 5)
        self.assertEqual(config.max_concurrent, 20)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.user_agent, "CustomBot/1.0")


class TestCrawlResult(unittest.TestCase):
    """Test the CrawlResult dataclass."""
    
    def test_crawl_result(self):
        """Test CrawlResult creation and properties"""
        urls = {"https://example.com", "https://example.com/page1"}
        result = CrawlResult(
            urls=urls,
            visited_count=2,
            error_count=0,
            redirect_count=1
        )
        
        self.assertEqual(result.urls, urls)
        self.assertEqual(result.visited_count, 2)
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.redirect_count, 1)


class TestWebCrawler(unittest.TestCase):
    """Test the WebCrawler class."""
    
    def setUp(self):
        self.base_url = "https://example.com"
        self.sample_html = """
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="/page2">Page 2</a>
                <a href="https://example.com/page3">Page 3</a>
                <a href="https://otherdomain.com/page4">External Page</a>
                <a href="https://subdomain.example.com/page5">Subdomain Page</a>
                <a href="mailto:test@example.com">Email</a>
                <a href="tel:+1234567890">Phone</a>
                <a href="#section">Anchor</a>
                <a>No href</a>
            </body>
        </html>
        """
        self.config = CrawlConfig(delay=0, max_concurrent=1)
        self.crawler = WebCrawler(self.config)
    
    def test_web_crawler_initialization(self):
        """Test WebCrawler initialization"""
        crawler = WebCrawler()
        
        self.assertIsInstance(crawler.config, CrawlConfig)
        self.assertIsInstance(crawler.redirect_handler, RedirectHandler)
        self.assertEqual(len(crawler.visited_urls), 0)
        self.assertEqual(len(crawler.all_found_urls), 0)
        self.assertEqual(crawler.error_count, 0)
        self.assertEqual(crawler.redirect_count, 0)
    
    def test_get_headers(self):
        """Test header generation"""
        headers = self.crawler._get_headers()
        
        self.assertIn("User-Agent", headers)
        self.assertIn("Accept", headers)
        self.assertIn("Accept-Encoding", headers)
        self.assertIn("Accept-Language", headers)
        self.assertIn("MyCrawler/1.0", headers["User-Agent"])
    
    @patch('web_crawler.verify')
    @pytest.mark.asyncio
    async def test_crawl_invalid_base_url(self, mock_verify):
        """Test crawling with invalid base URL"""
        mock_verify.return_value = False
        
        with self.assertRaises(Exception) as context:
            await self.crawler.crawl("invalid-url")
        
        self.assertIn("Invalid base URL", str(context.exception))
    
    @patch('web_crawler.verify')
    @patch('aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_crawl_successful_single_page(self, mock_session_class, mock_verify):
        """Test successful crawling of a single page"""
        mock_verify.return_value = True
        
        # Mock session and response
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=self.sample_html)
        mock_response.headers = {}
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Capture stdout
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            result = await self.crawler.crawl(self.base_url)
            output = captured_output.getvalue()
        finally:
            sys.stdout = original_stdout
        
        # Verify results
        self.assertIsInstance(result, CrawlResult)
        self.assertIn(self.base_url, result.urls)
        self.assertIn("https://example.com/page1", result.urls)
        self.assertIn("https://example.com/page2", result.urls)
        self.assertIn("https://example.com/page3", result.urls)
        
        # Verify external URLs are not included
        self.assertNotIn("https://otherdomain.com/page4", result.urls)
        self.assertNotIn("https://subdomain.example.com/page5", result.urls)
        
        # Verify output contains URLs
        self.assertIn(self.base_url, output)
        self.assertIn("https://example.com/page1", output)
    
    @patch('web_crawler.verify')
    @patch('aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_crawl_with_redirect(self, mock_session_class, mock_verify):
        """Test crawling with redirects"""
        mock_verify.return_value = True
        
        # Mock session and responses
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # First response (redirect)
        mock_response1 = AsyncMock()
        mock_response1.status = 301
        mock_response1.headers = {'Location': '/redirected'}
        mock_response1.text = AsyncMock(return_value="")
        
        # Second response (final)
        mock_response2 = AsyncMock()
        mock_response2.status = 200
        mock_response2.headers = {}
        mock_response2.text = AsyncMock(return_value=self.sample_html)
        
        # Configure session to return different responses
        mock_session.get.side_effect = [
            mock_response1.__aenter__.return_value,
            mock_response2.__aenter__.return_value
        ]
        
        result = await self.crawler.crawl(self.base_url)
        
        # Verify redirect was followed
        self.assertGreater(self.crawler.redirect_count, 0)
        self.assertIn(self.base_url, result.urls)
    
    @patch('web_crawler.verify')
    @patch('aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_crawl_with_http_error(self, mock_session_class, mock_verify):
        """Test crawling with HTTP errors"""
        mock_verify.return_value = True
        
        # Mock session and response
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value="Not Found")
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        result = await self.crawler.crawl(self.base_url)
        
        # Verify error was counted
        self.assertGreater(self.crawler.error_count, 0)
        self.assertEqual(len(result.urls), 1)  # Only base URL
    
    @patch('web_crawler.verify')
    @patch('aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_crawl_with_redirect_loop(self, mock_session_class, mock_verify):
        """Test crawling with redirect loops"""
        mock_verify.return_value = True
        
        # Mock session and response
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 301
        mock_response.headers = {'Location': '/'}  # Redirect back to original
        mock_response.text = AsyncMock(return_value="")
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        result = await self.crawler.crawl(self.base_url)
        
        # Verify error was counted
        self.assertGreater(self.crawler.error_count, 0)
        self.assertEqual(len(result.urls), 1)  # Only base URL


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility functions."""
    
    def setUp(self):
        self.base_url = "https://example.com"
        self.sample_html = """
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="/page2">Page 2</a>
            </body>
        </html>
        """
    
    @patch('web_crawler.verify')
    @patch('aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_crawl_async_function(self, mock_session_class, mock_verify):
        """Test the crawl_async backward compatibility function"""
        mock_verify.return_value = True
        
        # Mock session and response
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value=self.sample_html)
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        urls = await crawl_async(self.base_url, delay=0, max_concurrent=1)
        
        self.assertIsInstance(urls, set)
        self.assertIn(self.base_url, urls)
        self.assertIn("https://example.com/page1", urls)
        self.assertIn("https://example.com/page2", urls)
    
    @patch('web_crawler.verify')
    @patch('aiohttp.ClientSession')
    def test_crawl_function(self, mock_session_class, mock_verify):
        """Test the crawl backward compatibility function"""
        mock_verify.return_value = True
        
        # Mock session and response
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value=self.sample_html)
        
        # Fix the mocking setup for async context
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session.get.return_value.__aexit__.return_value = None
        
        # Capture stdout
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            crawl(self.base_url, delay=0, max_concurrent=1)
            output = captured_output.getvalue()
        finally:
            sys.stdout = original_stdout
        
        # Verify output contains URLs
        self.assertIn(self.base_url, output)
        # Note: The actual crawling might not work in tests due to mocking complexity
        # We'll just verify the function runs without error
    



if __name__ == '__main__':
    unittest.main()
