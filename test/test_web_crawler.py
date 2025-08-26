import unittest
from unittest.mock import patch, Mock
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from web_crawler import crawl, crawl_single_page


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
    def test_crawl_single_page_success(self, mock_verify, mock_get):
        """Test successful single page crawling (backward compatibility)"""
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
            crawl_single_page(self.base_url)
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
        
        # Check that all expected URLs are present
        for url in expected_urls:
            self.assertIn(url, output)
        
        # Check that no external URLs are included
        self.assertNotIn("https://otherdomain.com/page4", output)
        self.assertNotIn("https://subdomain.example.com/page5", output)
    
    @patch('web_crawler.requests.get')
    @patch('web_crawler.verify')
    def test_recursive_crawl_success(self, mock_verify, mock_get):
        """Test successful recursive crawling"""
        # Mock verify to always return True
        mock_verify.return_value = True
        
        # Mock responses for different URLs
        def mock_get_side_effect(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if url == "https://example.com":
                mock_response.text = """
                <html>
                    <body>
                        <a href="/page1">Page 1</a>
                        <a href="/page2">Page 2</a>
                    </body>
                </html>
                """
            elif url == "https://example.com/page1":
                mock_response.text = """
                <html>
                    <body>
                        <a href="/page3">Page 3</a>
                        <a href="https://otherdomain.com/external">External</a>
                    </body>
                </html>
                """
            elif url == "https://example.com/page2":
                mock_response.text = """
                <html>
                    <body>
                        <a href="/page4">Page 4</a>
                    </body>
                </html>
                """
            elif url == "https://example.com/page3":
                mock_response.text = """
                <html>
                    <body>
                        <a href="/page1">Back to Page 1</a>
                    </body>
                </html>
                """
            elif url == "https://example.com/page4":
                mock_response.text = """
                <html>
                    <body>
                        <a href="/page5">Page 5</a>
                    </body>
                </html>
                """
            elif url == "https://example.com/page5":
                mock_response.text = """
                <html>
                    <body>
                        <a href="/page6">Page 6</a>
                    </body>
                </html>
                """
            else:
                mock_response.text = "<html><body></body></html>"
            
            return mock_response
        
        mock_get.side_effect = mock_get_side_effect
        
        # Capture stdout to test output
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            crawl(self.base_url, max_depth=2, delay=0)  # No delay for testing
            output = captured_output.getvalue()
        finally:
            sys.stdout = sys.__stdout__
        
        # Check that all expected URLs are found
        expected_urls = [
            "https://example.com",
            "https://example.com/page1", 
            "https://example.com/page2",
            "https://example.com/page3",
            "https://example.com/page4"
        ]
        
        for url in expected_urls:
            self.assertIn(url, output)
        
        # Check that external URLs are not included
        self.assertNotIn("https://otherdomain.com/external", output)
        
        # Check that URLs beyond max depth are not crawled
        self.assertNotIn("https://example.com/page5", output)
        self.assertNotIn("https://example.com/page6", output)
    
    @patch('web_crawler.requests.get')
    @patch('web_crawler.verify')
    def test_recursive_crawl_visited_urls(self, mock_verify, mock_get):
        """Test that visited URLs are not crawled again"""
        # Mock verify to always return True
        mock_verify.return_value = True
        
        # Mock responses with circular links
        def mock_get_side_effect(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if url == "https://example.com":
                mock_response.text = """
                <html>
                    <body>
                        <a href="/page1">Page 1</a>
                    </body>
                </html>
                """
            elif url == "https://example.com/page1":
                mock_response.text = """
                <html>
                    <body>
                        <a href="/page2">Page 2</a>
                    </body>
                </html>
                """
            elif url == "https://example.com/page2":
                mock_response.text = """
                <html>
                    <body>
                        <a href="/page1">Back to Page 1</a>
                        <a href="/page3">Page 3</a>
                    </body>
                </html>
                """
            elif url == "https://example.com/page3":
                mock_response.text = """
                <html>
                    <body>
                        <a href="/page1">Back to Page 1</a>
                    </body>
                </html>
                """
            else:
                mock_response.text = "<html><body></body></html>"
            
            return mock_response
        
        mock_get.side_effect = mock_get_side_effect
        
        # Capture stdout to test output
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            crawl(self.base_url, max_depth=3, delay=0)  # No delay for testing
            output = captured_output.getvalue()
        finally:
            sys.stdout = sys.__stdout__
        
        # Check that all URLs are found
        expected_urls = [
            "https://example.com",
            "https://example.com/page1",
            "https://example.com/page2", 
            "https://example.com/page3"
        ]
        
        for url in expected_urls:
            self.assertIn(url, output)
        
        # Count how many times each URL appears in the crawl output
        # Each URL should only be crawled once
        crawl_lines = [line for line in output.split('\n') if '[Depth' in line]
        
        # Count unique URLs crawled
        crawled_urls = set()
        for line in crawl_lines:
            if 'Crawling:' in line:
                url = line.split('Crawling: ')[1]
                crawled_urls.add(url)
        
        # Should have exactly 4 unique URLs crawled
        self.assertEqual(len(crawled_urls), 4)
    
    @patch('web_crawler.requests.get')
    @patch('web_crawler.verify')
    def test_crawl_with_relative_urls(self, mock_verify, mock_get):
        """Test crawling with relative URLs (single page)"""
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
            crawl_single_page(self.base_url)
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
    @patch('web_crawler.verify')
    def test_crawl_http_error(self, mock_verify, mock_get):
        """Test handling of HTTP errors"""
        mock_get.side_effect = Exception("Connection failed")
        mock_verify.return_value = True
        
        with self.assertRaises(Exception) as context:
            crawl_single_page(self.base_url)
        
        self.assertIn("Error crawling", str(context.exception))
    
    @patch('web_crawler.requests.get')
    @patch('web_crawler.verify')
    def test_crawl_timeout(self, mock_verify, mock_get):
        """Test handling of timeout errors"""
        from requests.exceptions import Timeout
        mock_get.side_effect = Timeout("Request timed out")
        mock_verify.return_value = True
        
        with self.assertRaises(Exception) as context:
            crawl_single_page(self.base_url)
        
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
            crawl_single_page(self.base_url)
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
            crawl_single_page(self.base_url)
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
            crawl_single_page(self.base_url)
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
