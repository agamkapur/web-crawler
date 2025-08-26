from urllib.parse import urlparse


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
        
        # Port validation if specified
        if ':' in parsed.netloc:
            port_str = parsed.netloc.split(':')[1]
            try:
                port = int(port_str)
                if not (1 <= port <= 65535):
                    raise ValueError("Port must be between 1 and 65535")
            except ValueError:
                raise ValueError("Port must be numeric")
        
        return True
        
    except ValueError as e:
        print(f"Syntactic check failed: {e}")
        return False
    

def verify(url: str) -> bool:
    """Verify the URL is valid."""
    return syntactic_checks(url)