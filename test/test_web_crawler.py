import unittest
from unittest.mock import patch, Mock
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from web_crawler import crawl


class TestWebCrawler(unittest.TestCase):
    
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
    
    @patch('web_crawler.requests.get')
    @patch('web_crawler.verify')
    def test_crawl_success(self, mock_verify, mock_get):
        """Test successful crawling of a webpage"""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.text = self.sample_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock verify to always return True
        mock_verify.return_value = True
        
        # Capture stdout to test output
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            crawl(self.base_url)
            output = captured_output.getvalue().strip().split('\n')
        finally:
            sys.stdout = sys.__stdout__
        
        # Verify the output
        expected_urls = [
            "https://example.com",
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ]
        
        # Check that all expected URLs are present (may have additional verification messages)
        for url in expected_urls:
            self.assertIn(url, output)
        
        # Check that no external URLs are included
        self.assertNotIn("https://otherdomain.com/page4", output)
        self.assertNotIn("https://subdomain.example.com/page5", output)
    

    
    @patch('web_crawler.requests.get')
    @patch('web_crawler.verify')
    def test_crawl_with_relative_urls(self, mock_verify, mock_get):
        """Test crawling with relative URLs"""
        html_with_relative = """
        <html>
            <body>
                <a href="about">About</a>
                <a href="./contact">Contact</a>
                <a href="../blog">Blog</a>
                <a href="https://example.com/products">Products</a>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = html_with_relative
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock verify to always return True
        mock_verify.return_value = True
        
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            crawl(self.base_url)
            output = captured_output.getvalue().strip().split('\n')
        finally:
            sys.stdout = sys.__stdout__
        
        expected_urls = [
            "https://example.com",
            "https://example.com/about",
            "https://example.com/contact",
            "https://example.com/products"
        ]
        
        # Check that all expected URLs are present (may have additional verification messages)
        for url in expected_urls:
            self.assertIn(url, output)
    
    @patch('web_crawler.requests.get')
    def test_crawl_http_error(self, mock_get):
        """Test handling of HTTP errors"""
        mock_get.side_effect = Exception("Connection failed")
        
        with self.assertRaises(Exception) as context:
            crawl(self.base_url)
        
        self.assertIn("Error crawling", str(context.exception))
    
    @patch('web_crawler.requests.get')
    def test_crawl_timeout(self, mock_get):
        """Test handling of timeout errors"""
        from requests.exceptions import Timeout
        mock_get.side_effect = Timeout("Request timed out")
        
        with self.assertRaises(Exception) as context:
            crawl(self.base_url)
        
        self.assertIn("Failed to fetch", str(context.exception))
    
    @patch('web_crawler.requests.get')
    @patch('web_crawler.verify')
    def test_crawl_empty_page(self, mock_verify, mock_get):
        """Test crawling an empty page"""
        mock_response = Mock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock verify to always return True
        mock_verify.return_value = True
        
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            crawl(self.base_url)
            output = captured_output.getvalue().strip().split('\n')
        finally:
            sys.stdout = sys.__stdout__
        
        # Should output the base URL (may have additional verification messages)
        self.assertIn(self.base_url, output)
    
    @patch('web_crawler.requests.get')
    @patch('web_crawler.verify')
    def test_crawl_with_query_params(self, mock_verify, mock_get):
        """Test crawling with URLs containing query parameters"""
        html_with_params = """
        <html>
            <body>
                <a href="/search?q=test">Search</a>
                <a href="/products?id=123&category=electronics">Product</a>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = html_with_params
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock verify to always return True
        mock_verify.return_value = True
        
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            crawl(self.base_url)
            output = captured_output.getvalue().strip().split('\n')
        finally:
            sys.stdout = sys.__stdout__
        
        expected_urls = [
            "https://example.com",
            "https://example.com/search?q=test",
            "https://example.com/products?id=123&category=electronics"
        ]
        
        # Check that all expected URLs are present (may have additional verification messages)
        for url in expected_urls:
            self.assertIn(url, output)
    
    @patch('web_crawler.requests.get')
    @patch('web_crawler.verify')
    def test_crawl_with_fragments(self, mock_verify, mock_get):
        """Test crawling with URLs containing fragments"""
        html_with_fragments = """
        <html>
            <body>
                <a href="/page#section1">Page with fragment</a>
                <a href="#section2">Just fragment</a>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = html_with_fragments
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock verify to always return True
        mock_verify.return_value = True
        
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            crawl(self.base_url)
            output = captured_output.getvalue().strip().split('\n')
        finally:
            sys.stdout = sys.__stdout__
        
        expected_urls = [
            "https://example.com",
            "https://example.com/page#section1"
        ]
        
        # Check that all expected URLs are present (may have additional verification messages)
        for url in expected_urls:
            self.assertIn(url, output)


if __name__ == '__main__':
    unittest.main()
