import unittest
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from utils.url_normalizer import URLNormalizer


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


if __name__ == '__main__':
    unittest.main()
