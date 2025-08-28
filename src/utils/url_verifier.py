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
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        # urlparse(url) succeeds
        parsed = urlparse(url)
        if not parsed:
            raise ValueError("URL parsing failed")

        # Netloc (domain part) is non-empty
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain")

        # Domain name validation
        domain = parsed.netloc.split(":")[0]  # Remove port if present
        if not is_valid_domain(domain):
            raise ValueError("Invalid domain name")

        # Port validation if specified
        if ":" in parsed.netloc:
            port_str = parsed.netloc.split(":")[1]
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
    domain_pattern = (
        r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
        r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
    )
    if not re.match(domain_pattern, domain):
        return False

    # Check individual label lengths
    labels = domain.split(".")
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
    dangerous_chars = [
        "<",
        ">",
        '"',
        "'",
        "\\",
        "\x00",
        "\x01",
        "\x02",
        "\x03",
        "\x04",
        "\x05",
        "\x06",
        "\x07",
    ]

    for char in dangerous_chars:
        if char in path or char in query:
            return False

    return True


def semantic_checks(url: str) -> bool:
    """Perform semantic validation checks."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.split(":")[0]  # Remove port if present

        # DNS resolution
        try:
            socket.gethostbyname(domain)
        except socket.gaierror:
            print(f"Semantic check failed: DNS resolution failed for {domain}")
            return False

        # Reserved domain check
        reserved_domains = [".invalid", ".example", ".test", ".localhost"]
        for reserved in reserved_domains:
            if domain.endswith(reserved):
                print(f"Semantic check failed: Reserved domain {reserved}")
                return False

        # Private IP check
        if is_valid_ip(domain):
            try:
                ip = ipaddress.ip_address(domain)
                if ip.is_private:
                    print(f"Semantic check failed: Private IP address {domain}")
                    return False
            except ValueError:
                pass

        return True

    except Exception as e:
        print(f"Semantic check failed: {e}")
        return False


def protocol_checks(url: str) -> bool:
    """Perform protocol-level validation checks."""
    try:
        # Create request with timeout
        req = Request(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; MyCrawler/1.0)"}
        )

        with urlopen(req, timeout=10) as response:
            # Check status code
            if response.status < 200 or response.status >= 400:
                print(f"Protocol check failed: HTTP {response.status}")
                return False

            # Check content type
            content_type = response.headers.get("Content-Type", "").lower()
            if not any(
                ct in content_type
                for ct in ["text/html", "text/plain", "application/xhtml+xml"]
            ):
                print(f"Protocol check failed: Unsupported content type {content_type}")
                return False

            return True

    except HTTPError as e:
        print(f"Protocol check failed: HTTP error {e.code}")
        return False
    except URLError as e:
        print(f"Protocol check failed: URL error {e.reason}")
        return False
    except Exception as e:
        print(f"Protocol check failed: {e}")
        return False


def operational_checks(url: str) -> bool:
    """Perform operational checks (robots.txt, rate limiting, etc.)."""
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Check robots.txt
        robots_url = urljoin(base_url, "/robots.txt")
        try:
            req = Request(
                robots_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; MyCrawler/1.0)"},
            )
            with urlopen(req, timeout=5) as response:
                if response.status == 200:
                    print("Operational check: robots.txt found and accessible")
        except Exception:
            print("Operational check: robots.txt not accessible")

        # Check for rate limiting headers
        req = Request(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; MyCrawler/1.0)"}
        )
        with urlopen(req, timeout=10) as response:
            if "Retry-After" in response.headers:
                print(
                    f"Operational check: Rate limiting detected "
                    f"(Retry-After: {response.headers['Retry-After']})"
                )
                return False

            if response.status == 403:
                print("Operational check: Access forbidden (403)")
                return False

        return True

    except Exception as e:
        print(f"Operational check failed: {e}")
        return False


def security_checks(url: str) -> bool:
    """Perform security validation checks."""
    try:
        parsed = urlparse(url)

        # Check for dangerous schemes
        dangerous_schemes = ["javascript:", "data:", "file:", "ftp:", "mailto:", "tel:"]
        for scheme in dangerous_schemes:
            if url.lower().startswith(scheme):
                print(f"Security check failed: Dangerous scheme {scheme}")
                return False

        # Check for localhost patterns
        localhost_patterns = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]
        domain = parsed.netloc.split(":")[0].lower()
        for pattern in localhost_patterns:
            if pattern in domain:
                print(f"Security check failed: Localhost pattern {pattern}")
                return False

        # Check for private network patterns
        private_patterns = [
            "192.168.",
            "10.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31.",
        ]
        for pattern in private_patterns:
            if domain.startswith(pattern):
                print(f"Security check failed: Private network pattern {pattern}")
                return False

        return True

    except Exception as e:
        print(f"Security check failed: {e}")
        return False


def verify(url: str) -> bool:
    """
    Verify that the URL is valid, safe and suitable for crawling.

    This function performs comprehensive validation including:
    - Syntactic checks (format, structure)
    - Semantic checks (DNS resolution, reserved domains)
    - Protocol checks (HTTP response, content type)
    - Operational checks (robots.txt, rate limiting)
    - Security checks (dangerous schemes, localhost)

    Args:
        url: The URL to verify

    Returns:
        bool: True if URL is valid and safe, False otherwise
    """
    try:
        # Perform all validation checks
        if not syntactic_checks(url):
            return False

        if not semantic_checks(url):
            return False

        if not protocol_checks(url):
            return False

        if not operational_checks(url):
            return False

        if not security_checks(url):
            return False

        return True

    except Exception as e:
        print(f"Verification failed: {e}")
        return False
