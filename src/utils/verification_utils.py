import re
import socket
import ipaddress
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def syntactic_checks(url: str) -> bool:
    """Perform syntactic validation checks."""
    try:
        # Non-empty string
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        
        # No leading/trailing whitespace
        if url != url.strip():
            raise ValueError("URL cannot have leading or trailing whitespace")
        
        # Correct scheme: must be http:// or https://
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        # urlparse(url) succeeds
        parsed = urlparse(url)
        if not parsed:
            raise ValueError("URL parsing failed")
        
        # Netloc (domain part) is non-empty
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain")
        
        # Domain name validation
        domain = parsed.netloc.split(':')[0]  # Remove port if present
        if not is_valid_domain(domain):
            raise ValueError("Invalid domain name")
        
        # Port validation if specified
        if ':' in parsed.netloc:
            port_str = parsed.netloc.split(':')[1]
            try:
                port = int(port_str)
                if not (1 <= port <= 65535):
                    raise ValueError("Port must be between 1 and 65535")
            except ValueError:
                raise ValueError("Port must be numeric")
        
        # Path/query validation
        if not is_valid_path_query(parsed.path, parsed.query):
            raise ValueError("Invalid characters in path or query")
        
        return True
        
    except ValueError as e:
        print(f"Syntactic check failed: {e}")
        return False


def is_valid_domain(domain: str) -> bool:
    """Validate domain name format and length."""
    # Check for IP address
    if is_valid_ip(domain):
        return True
    
    # Domain name rules
    if len(domain) > 253:
        return False
    
    # Check for valid characters and structure
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    if not re.match(domain_pattern, domain):
        return False
    
    # Check individual label lengths
    labels = domain.split('.')
    for label in labels:
        if len(label) > 63:
            return False
    
    return True


def is_valid_ip(ip_str: str) -> bool:
    """Check if string is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def is_valid_path_query(path: str, query: str) -> bool:
    """Validate path and query string characters."""
    # Check for potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '\\', '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07']
    
    for char in dangerous_chars:
        if char in path or char in query:
            return False
    
    return True


def semantic_checks(base_url: str) -> bool:
    """Perform semantic validation checks."""
    try:
        parsed_url = urlparse(base_url)
        domain = parsed_url.netloc.split(':')[0]
        
        # Domain resolves via DNS
        try:
            socket.gethostbyname(domain)
        except socket.gaierror:
            raise ValueError("Domain does not resolve via DNS")
        
        # Check for reserved domains
        reserved_domains = ['.invalid', '.example', '.test', '.localhost']
        for reserved in reserved_domains:
            if domain.endswith(reserved):
                raise ValueError(f"Domain {domain} is reserved")
        
        # Check for private/reserved IP addresses
        if is_valid_ip(domain):
            ip = ipaddress.ip_address(domain)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise ValueError(f"IP address {domain} is private/reserved")
        
        return True
        
    except ValueError as e:
        print(f"Semantic check failed: {e}")
        return False


def protocol_checks(base_url: str) -> bool:
    """Perform protocol-level validation checks."""
    try:
        # Perform a HEAD request to the base URL
        req = Request(base_url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; WebCrawler/1.0)')
        
        try:
            with urlopen(req, timeout=10) as response:
                # Expect a 2xx or 3xx status code
                if not (200 <= response.status < 400):
                    raise ValueError(f"HTTP status code {response.status} not acceptable")
                
                # Verify correct Content-Type for websites
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                    print(f"Warning: Content-Type is {content_type}, expected HTML")
                
                # SSL certificate validation (handled automatically by urlopen)
                # Additional SSL checks could be added here
                
        except HTTPError as e:
            if e.code >= 400:
                raise ValueError(f"HTTP error {e.code}: {e.reason}")
            raise
        except URLError as e:
            raise ValueError(f"URL error: {e.reason}")
        
        return True
        
    except Exception as e:
        print(f"Protocol check failed: {e}")
        return False


def operational_checks(base_url: str) -> bool:
    """Perform operational validation checks."""
    try:
        # Check robots.txt
        robots_url = urljoin(base_url, '/robots.txt')
        try:
            req = Request(robots_url, method='HEAD')
            req.add_header('User-Agent', 'Mozilla/5.0 (compatible; WebCrawler/1.0)')
            with urlopen(req, timeout=5) as response:
                if response.status == 200:
                    print("robots.txt found and accessible")
                else:
                    print("robots.txt not found or not accessible")
        except:
            print("Could not access robots.txt")
        
        # Check for rate limiting headers
        req = Request(base_url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; WebCrawler/1.0)')
        
        with urlopen(req, timeout=10) as response:
            # Check for rate limiting
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                print(f"Rate limiting detected: Retry-After {retry_after}")
            
            # Check for crawler blocking
            if response.status == 403:
                print("Warning: Site may be blocking crawlers (403 Forbidden)")
            
            # Check for captcha or blocking indicators
            content_type = response.headers.get('Content-Type', '').lower()
            if 'captcha' in content_type or 'blocked' in content_type:
                print("Warning: Site may be showing captcha or blocking page")
        
        return True
        
    except Exception as e:
        print(f"Operational check failed: {e}")
        return False


def security_checks(base_url: str) -> bool:
    """Perform security validation checks."""
    try:
        parsed_url = urlparse(base_url)
        domain = parsed_url.netloc.split(':')[0]
        
        # Avoid SSRF: check for local/internal services
        localhost_patterns = [
            'localhost', '127.0.0.1', '::1', '0.0.0.0',
            '169.254.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
            '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
            '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
            '192.168.'
        ]
        
        for pattern in localhost_patterns:
            if domain.startswith(pattern):
                raise ValueError(f"URL points to local/internal service: {domain}")
        
        # Prevent protocol abuse
        allowed_schemes = ['http', 'https']
        if parsed_url.scheme not in allowed_schemes:
            raise ValueError(f"Protocol {parsed_url.scheme} not allowed")
        
        # Sanitize URL input (basic check)
        dangerous_patterns = [
            'javascript:', 'data:', 'file:', 'ftp:', 'mailto:', 'tel:',
            'vbscript:', 'onload=', 'onerror=', 'onclick='
        ]
        
        url_lower = base_url.lower()
        for pattern in dangerous_patterns:
            if pattern in url_lower:
                raise ValueError(f"URL contains dangerous pattern: {pattern}")
        
        return True
        
    except ValueError as e:
        print(f"Security check failed: {e}")
        return False


def verify(base_url: str) -> bool:
    """
    Verify that the URL is valid, safe and suitable for crawling.
    
    Args:
        base_url: The URL to verify
        
    Returns:
        bool: True if URL is valid and safe for crawling
    """
    try:
        # syntactic checks, no network calls
        if not syntactic_checks(base_url):
            return False
            
        # semantic checks, DNS & domain-level validation
        if not semantic_checks(base_url):
            return False
            
        # protocol checks, network connection level
        if not protocol_checks(base_url):
            return False
            
        # operational checks, application-level
        if not operational_checks(base_url):
            return False
            
        # security checks, safety before crawling
        if not security_checks(base_url):
            return False
            
        return True
        
    except Exception as e:
        print(f"Verification failed: {e}")
        return False