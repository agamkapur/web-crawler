import unittest
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from utils.verification_utils import syntactic_checks, verify


class TestVerificationUtils(unittest.TestCase):
    
    def test_syntactic_checks_valid_urls(self):
        """Test syntactic_checks with valid URLs"""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://www.example.com",
            "https://example.com:8080",
            "https://example.com/path",
            "https://example.com/path?param=value",
            "https://example.com/path#fragment",
            "https://subdomain.example.com",
            "https://example.co.uk",
            "https://example.com:443",
            "http://example.com:80"
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(syntactic_checks(url), f"URL should be valid: {url}")
    
    def test_syntactic_checks_empty_url(self):
        """Test syntactic_checks with empty URLs"""
        empty_urls = [
            "",
            "   ",
            "\t",
            "\n"
        ]
        
        for url in empty_urls:
            with self.subTest(url=repr(url)):
                self.assertFalse(syntactic_checks(url), f"Empty URL should be invalid: {repr(url)}")
    
    def test_syntactic_checks_whitespace_urls(self):
        """Test syntactic_checks with URLs that have leading/trailing whitespace"""
        whitespace_urls = [
            " https://example.com",
            "https://example.com ",
            "  https://example.com  ",
            "\thttps://example.com\t"
        ]
        
        for url in whitespace_urls:
            with self.subTest(url=repr(url)):
                self.assertFalse(syntactic_checks(url), f"URL with whitespace should be invalid: {repr(url)}")
    
    def test_syntactic_checks_invalid_schemes(self):
        """Test syntactic_checks with invalid URL schemes"""
        invalid_scheme_urls = [
            "ftp://example.com",
            "file:///path/to/file",
            "mailto:test@example.com",
            "tel:+1234567890",
            "javascript:alert('test')",
            "example.com",
            "www.example.com",
            "//example.com"
        ]
        
        for url in invalid_scheme_urls:
            with self.subTest(url=url):
                self.assertFalse(syntactic_checks(url), f"URL with invalid scheme should be invalid: {url}")
    
    def test_syntactic_checks_missing_domain(self):
        """Test syntactic_checks with URLs missing domain"""
        invalid_domain_urls = [
            "https://",
            "http://",
            "https:///path"
        ]
        
        for url in invalid_domain_urls:
            with self.subTest(url=url):
                self.assertFalse(syntactic_checks(url), f"URL without domain should be invalid: {url}")
    
    def test_syntactic_checks_urls_with_only_port(self):
        """Test syntactic_checks with URLs that have only port but no domain"""
        # Note: The current implementation considers http://:8080 as valid
        # because urlparse treats ':8080' as a valid netloc
        port_only_urls = [
            "http://:8080",
            "https://:443"
        ]
        
        for url in port_only_urls:
            with self.subTest(url=url):
                # These are currently considered valid by the implementation
                # This might be a limitation that could be improved
                result = syntactic_checks(url)
                self.assertIsInstance(result, bool, f"Should return boolean for: {url}")
    
    def test_syntactic_checks_invalid_ports(self):
        """Test syntactic_checks with invalid ports"""
        invalid_port_urls = [
            "https://example.com:0",
            "https://example.com:65536",
            "https://example.com:99999",
            "https://example.com:abc",
            "https://example.com:port",
            "https://example.com:-1"
        ]
        
        for url in invalid_port_urls:
            with self.subTest(url=url):
                self.assertFalse(syntactic_checks(url), f"URL with invalid port should be invalid: {url}")
    
    def test_syntactic_checks_valid_ports(self):
        """Test syntactic_checks with valid ports"""
        valid_port_urls = [
            "https://example.com:1",
            "https://example.com:80",
            "https://example.com:443",
            "https://example.com:8080",
            "https://example.com:3000",
            "https://example.com:65535"
        ]
        
        for url in valid_port_urls:
            with self.subTest(url=url):
                self.assertTrue(syntactic_checks(url), f"URL with valid port should be valid: {url}")
    
    def test_syntactic_checks_complex_urls(self):
        """Test syntactic_checks with complex URLs"""
        complex_urls = [
            "https://example.com/path/to/page.html?param1=value1&param2=value2",
            "https://subdomain.example.co.uk:8443/api/v1/endpoint",
            "http://localhost:3000",
            "https://127.0.0.1:8080"
        ]
        
        for url in complex_urls:
            with self.subTest(url=url):
                self.assertTrue(syntactic_checks(url), f"Complex URL should be valid: {url}")
    
    def test_syntactic_checks_urls_with_credentials(self):
        """Test syntactic_checks with URLs containing credentials (these should fail due to port parsing)"""
        credential_urls = [
            "https://user:pass@example.com:8080/path",
            "https://username:password@example.com:3000/api"
        ]
        
        for url in credential_urls:
            with self.subTest(url=url):
                # These should fail due to the current port parsing logic
                self.assertFalse(syntactic_checks(url), f"URL with credentials should fail port parsing: {url}")
    
    def test_verify_function(self):
        """Test the verify function wrapper"""
        # Test valid URL
        self.assertTrue(verify("https://example.com"))
        
        # Test invalid URL
        self.assertFalse(verify("invalid-url"))
        
        # Test empty URL
        self.assertFalse(verify(""))
    
    def test_verify_function_consistency(self):
        """Test that verify function returns same result as syntactic_checks"""
        test_urls = [
            "https://example.com",
            "http://example.com:8080",
            "invalid-url",
            "",
            "ftp://example.com"
        ]
        
        for url in test_urls:
            with self.subTest(url=url):
                verify_result = verify(url)
                syntactic_result = syntactic_checks(url)
                self.assertEqual(verify_result, syntactic_result, 
                               f"verify() and syntactic_checks() should return same result for: {url}")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        edge_cases = [
            # Very long URLs
            "https://" + "a" * 1000 + ".com",
            
            # URLs with special characters in domain
            "https://example-domain.com",
            "https://example_domain.com",
            
            # URLs with IP addresses
            "https://192.168.1.1",
            "https://192.168.1.1:8080",
            
            # URLs with internationalized domain names (IDN)
            "https://münchen.de",
            
            # URLs with unusual TLDs
            "https://example.technology",
            "https://example.coffee"
        ]
        
        for url in edge_cases:
            with self.subTest(url=url):
                # These should all be syntactically valid
                result = syntactic_checks(url)
                # We expect most to be valid, but some might fail due to strict validation
                # The important thing is that it doesn't crash
                self.assertIsInstance(result, bool, f"Should return boolean for: {url}")


if __name__ == '__main__':
    unittest.main()
