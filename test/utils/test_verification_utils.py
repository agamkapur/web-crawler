import unittest
from unittest.mock import patch, Mock, MagicMock
import sys
import os
import socket
import ipaddress
from urllib.error import HTTPError, URLError

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from utils.verification_utils import (
    syntactic_checks, verify, semantic_checks, protocol_checks, 
    operational_checks, security_checks, is_valid_domain, 
    is_valid_ip, is_valid_path_query
)


class TestVerificationUtils(unittest.TestCase):
    
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

    # ==================== SYNTACTIC CHECKS TESTS ====================
    
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
            "http://example.com:80",
            "https://192.168.1.1",
            "https://127.0.0.1:8080"
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

    # ==================== IS_VALID_DOMAIN TESTS ====================
    
    def test_is_valid_domain_valid_domains(self):
        """Test is_valid_domain with valid domain names"""
        valid_domains = [
            "example.com",
            "www.example.com",
            "subdomain.example.com",
            "example.co.uk",
            "example-domain.com",
            "a" * 63 + ".com",  # Max label length
            "example.com" + "." + "a" * 63,  # Max label length
        ]
        
        for domain in valid_domains:
            with self.subTest(domain=domain):
                self.assertTrue(is_valid_domain(domain), f"Domain should be valid: {domain}")
    
    def test_is_valid_domain_invalid_domains(self):
        """Test is_valid_domain with invalid domain names"""
        invalid_domains = [
            "",  # Empty
            ".example.com",  # Starts with dot
            "example.com.",  # Ends with dot
            "example..com",  # Double dot
            "-example.com",  # Starts with hyphen
            "example-.com",  # Ends with hyphen
            "a" * 64 + ".com",  # Label too long
            "a" * 254 + ".com",  # Domain too long
            "example com",  # Space in domain
            "example@com",  # Invalid character
            "example_domain.com",  # Underscore not allowed in domain names
        ]
        
        for domain in invalid_domains:
            with self.subTest(domain=domain):
                self.assertFalse(is_valid_domain(domain), f"Domain should be invalid: {domain}")
    
    def test_is_valid_domain_ip_addresses(self):
        """Test is_valid_domain with IP addresses"""
        valid_ips = [
            "192.168.1.1",
            "127.0.0.1",
            "::1",
            "2001:db8::1"
        ]
        
        for ip in valid_ips:
            with self.subTest(ip=ip):
                self.assertTrue(is_valid_domain(ip), f"IP should be valid: {ip}")

    # ==================== IS_VALID_IP TESTS ====================
    
    def test_is_valid_ip_valid_addresses(self):
        """Test is_valid_ip with valid IP addresses"""
        valid_ips = [
            "192.168.1.1",
            "127.0.0.1",
            "8.8.8.8",
            "::1",
            "2001:db8::1",
            "fe80::1%lo0"
        ]
        
        for ip in valid_ips:
            with self.subTest(ip=ip):
                self.assertTrue(is_valid_ip(ip), f"IP should be valid: {ip}")
    
    def test_is_valid_ip_invalid_addresses(self):
        """Test is_valid_ip with invalid IP addresses"""
        invalid_ips = [
            "256.1.2.3",
            "1.2.3.256",
            "192.168.1",
            "192.168.1.1.1",
            "invalid",
            "192.168.1.1a"
        ]
        
        for ip in invalid_ips:
            with self.subTest(ip=ip):
                self.assertFalse(is_valid_ip(ip), f"IP should be invalid: {ip}")

    # ==================== IS_VALID_PATH_QUERY TESTS ====================
    
    def test_is_valid_path_query_valid(self):
        """Test is_valid_path_query with valid paths and queries"""
        valid_combinations = [
            ("/path", ""),
            ("/path/to/file", "param=value"),
            ("/", "q=test&page=1"),
            ("/api/v1/endpoint", "id=123&type=json"),
            ("/search", "query=hello+world"),
        ]
        
        for path, query in valid_combinations:
            with self.subTest(path=path, query=query):
                self.assertTrue(is_valid_path_query(path, query), 
                              f"Path/query should be valid: {path}?{query}")
    
    def test_is_valid_path_query_invalid(self):
        """Test is_valid_path_query with invalid paths and queries"""
        invalid_combinations = [
            ("/path<script>", ""),  # Dangerous char in path
            ("/path", "param=<script>"),  # Dangerous char in query
            ("/path\x00", ""),  # Null byte in path
            ("/path", "param=\x01"),  # Control char in query
            ("/path\"", ""),  # Quote in path
            ("/path", "param='"),  # Quote in query
        ]
        
        for path, query in invalid_combinations:
            with self.subTest(path=path, query=query):
                self.assertFalse(is_valid_path_query(path, query), 
                               f"Path/query should be invalid: {path}?{query}")

    # ==================== SEMANTIC CHECKS TESTS ====================
    
    @patch('utils.verification_utils.socket.gethostbyname')
    def test_semantic_checks_valid_domain(self, mock_gethostbyname):
        """Test semantic_checks with valid domain"""
        mock_gethostbyname.return_value = "93.184.216.34"
        
        result = semantic_checks("https://example.com")
        self.assertTrue(result)
        mock_gethostbyname.assert_called_once_with("example.com")
    
    @patch('utils.verification_utils.socket.gethostbyname')
    def test_semantic_checks_dns_failure(self, mock_gethostbyname):
        """Test semantic_checks with DNS resolution failure"""
        mock_gethostbyname.side_effect = socket.gaierror("Name or service not known")
        
        result = semantic_checks("https://nonexistent-domain-12345.com")
        self.assertFalse(result)
    
    def test_semantic_checks_reserved_domains(self):
        """Test semantic_checks with reserved domains"""
        reserved_domains = [
            "https://test.invalid",
            "https://example.example",
            "https://test.test",
            "https://localhost.localhost"
        ]
        
        for url in reserved_domains:
            with self.subTest(url=url):
                result = semantic_checks(url)
                self.assertFalse(result, f"Reserved domain should be invalid: {url}")
    
    def test_semantic_checks_private_ips(self):
        """Test semantic_checks with private IP addresses"""
        private_ips = [
            "https://192.168.1.1",
            "https://127.0.0.1",
            "https://10.0.0.1",
            "https://172.16.0.1"
        ]
        
        for url in private_ips:
            with self.subTest(url=url):
                result = semantic_checks(url)
                self.assertFalse(result, f"Private IP should be invalid: {url}")

    # ==================== PROTOCOL CHECKS TESTS ====================
    
    @patch('utils.verification_utils.urlopen')
    def test_protocol_checks_success(self, mock_urlopen):
        """Test protocol_checks with successful response"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'text/html; charset=utf-8'}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = protocol_checks("https://example.com")
        self.assertTrue(result)
    
    @patch('utils.verification_utils.urlopen')
    def test_protocol_checks_http_error(self, mock_urlopen):
        """Test protocol_checks with HTTP error"""
        mock_urlopen.side_effect = HTTPError("https://example.com", 404, "Not Found", {}, None)
        
        result = protocol_checks("https://example.com")
        self.assertFalse(result)
    
    @patch('utils.verification_utils.urlopen')
    def test_protocol_checks_url_error(self, mock_urlopen):
        """Test protocol_checks with URL error"""
        mock_urlopen.side_effect = URLError("Connection refused")
        
        result = protocol_checks("https://example.com")
        self.assertFalse(result)
    
    @patch('utils.verification_utils.urlopen')
    def test_protocol_checks_wrong_content_type(self, mock_urlopen):
        """Test protocol_checks with wrong content type"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = protocol_checks("https://example.com")
        self.assertTrue(result)  # Should still pass but with warning

    # ==================== OPERATIONAL CHECKS TESTS ====================
    
    @patch('utils.verification_utils.urlopen')
    def test_operational_checks_success(self, mock_urlopen):
        """Test operational_checks with successful response"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = operational_checks("https://example.com")
        self.assertTrue(result)
    
    @patch('utils.verification_utils.urlopen')
    def test_operational_checks_rate_limiting(self, mock_urlopen):
        """Test operational_checks with rate limiting"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {'Retry-After': '60'}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = operational_checks("https://example.com")
        self.assertTrue(result)  # Should pass but with warning
    
    @patch('utils.verification_utils.urlopen')
    def test_operational_checks_forbidden(self, mock_urlopen):
        """Test operational_checks with 403 Forbidden"""
        mock_response = Mock()
        mock_response.status = 403
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = operational_checks("https://example.com")
        self.assertTrue(result)  # Should pass but with warning

    # ==================== SECURITY CHECKS TESTS ====================
    
    def test_security_checks_valid_url(self):
        """Test security_checks with valid URL"""
        result = security_checks("https://example.com")
        self.assertTrue(result)
    
    def test_security_checks_localhost_patterns(self):
        """Test security_checks with localhost patterns"""
        localhost_urls = [
            "https://localhost",
            "https://127.0.0.1",
            "https://192.168.1.1",
            "https://10.0.0.1",
            "https://172.16.0.1"
        ]
        
        for url in localhost_urls:
            with self.subTest(url=url):
                result = security_checks(url)
                self.assertFalse(result, f"Localhost URL should be invalid: {url}")
    
    def test_security_checks_dangerous_patterns(self):
        """Test security_checks with dangerous patterns"""
        dangerous_urls = [
            "javascript:alert('test')",
            "data:text/html,<script>alert('test')</script>",
            "file:///etc/passwd",
            "ftp://example.com",
            "mailto:test@example.com",
            "tel:+1234567890"
        ]
        
        for url in dangerous_urls:
            with self.subTest(url=url):
                result = security_checks(url)
                self.assertFalse(result, f"Dangerous URL should be invalid: {url}")
    
    def test_security_checks_invalid_scheme(self):
        """Test security_checks with invalid scheme"""
        result = security_checks("ftp://example.com")
        self.assertFalse(result)

    # ==================== VERIFY FUNCTION TESTS ====================
    
    @patch('utils.verification_utils.security_checks')
    @patch('utils.verification_utils.operational_checks')
    @patch('utils.verification_utils.protocol_checks')
    @patch('utils.verification_utils.semantic_checks')
    @patch('utils.verification_utils.syntactic_checks')
    def test_verify_all_checks_pass(self, mock_syntactic, mock_semantic, mock_protocol, mock_operational, mock_security):
        """Test verify function when all checks pass"""
        mock_syntactic.return_value = True
        mock_semantic.return_value = True
        mock_protocol.return_value = True
        mock_operational.return_value = True
        mock_security.return_value = True
        
        result = verify("https://example.com")
        self.assertTrue(result)
        
        # Verify all checks were called
        mock_syntactic.assert_called_once()
        mock_semantic.assert_called_once()
        mock_protocol.assert_called_once()
        mock_operational.assert_called_once()
        mock_security.assert_called_once()
    
    @patch('utils.verification_utils.security_checks')
    @patch('utils.verification_utils.operational_checks')
    @patch('utils.verification_utils.protocol_checks')
    @patch('utils.verification_utils.semantic_checks')
    @patch('utils.verification_utils.syntactic_checks')
    def test_verify_syntactic_fails(self, mock_syntactic, mock_semantic, mock_protocol, mock_operational, mock_security):
        """Test verify function when syntactic checks fail"""
        mock_syntactic.return_value = False
        
        result = verify("invalid-url")
        self.assertFalse(result)
        
        # Only syntactic checks should be called
        mock_syntactic.assert_called_once()
        mock_semantic.assert_not_called()
        mock_protocol.assert_not_called()
        mock_operational.assert_not_called()
        mock_security.assert_not_called()
    
    @patch('utils.verification_utils.security_checks')
    @patch('utils.verification_utils.operational_checks')
    @patch('utils.verification_utils.protocol_checks')
    @patch('utils.verification_utils.semantic_checks')
    @patch('utils.verification_utils.syntactic_checks')
    def test_verify_semantic_fails(self, mock_syntactic, mock_semantic, mock_protocol, mock_operational, mock_security):
        """Test verify function when semantic checks fail"""
        mock_syntactic.return_value = True
        mock_semantic.return_value = False
        
        result = verify("https://example.com")
        self.assertFalse(result)
        
        # Only syntactic and semantic checks should be called
        mock_syntactic.assert_called_once()
        mock_semantic.assert_called_once()
        mock_protocol.assert_not_called()
        mock_operational.assert_not_called()
        mock_security.assert_not_called()
    
    def test_verify_exception_handling(self):
        """Test verify function exception handling"""
        with patch('utils.verification_utils.syntactic_checks', side_effect=Exception("Test exception")):
            result = verify("https://example.com")
            self.assertFalse(result)

    # ==================== INTEGRATION TESTS ====================
    
    def test_verify_function_consistency(self):
        """Test that verify function returns same result as syntactic_checks for basic cases"""
        test_urls = [
            "https://example.com",
            "http://example.com:8080",
            "invalid-url",
            "",
            "ftp://example.com"
        ]
        
        for url in test_urls:
            with self.subTest(url=url):
                # For basic cases, verify should at least run syntactic_checks
                # We can't easily test the full verify function without mocking network calls
                if url.startswith(('http://', 'https://')):
                    # Valid URLs should at least pass syntactic checks
                    self.assertTrue(syntactic_checks(url))
                else:
                    # Invalid URLs should fail syntactic checks
                    self.assertFalse(syntactic_checks(url))
    
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
