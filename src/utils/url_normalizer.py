from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import logging

logger = logging.getLogger(__name__)


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
