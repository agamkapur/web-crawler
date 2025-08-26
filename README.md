# Web Crawler

A command-line tool for recursively crawling websites and extracting URLs. This web crawler takes a base URL as input and recursively discovers all URLs within the same domain, maintaining a list of visited URLs to avoid duplicates.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd web-crawler
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

The web crawler can be used as a CLI tool with various options:

```bash
# Basic recursive crawl (unlimited depth)
./bin/web-crawler https://example.com

# Crawl with depth limit
./bin/web-crawler https://example.com --depth 2

# Crawl with custom delay between requests
./bin/web-crawler https://example.com --delay 0.5

# Crawl with maximum redirect limit
./bin/web-crawler https://example.com --max-redirects 5

# Single page crawl (original behavior)
./bin/web-crawler https://example.com --single

# Combine options
./bin/web-crawler https://example.com --depth 3 --delay 1.5 --max-redirects 8
```

#### CLI Options:
- `--depth, -d`: Maximum depth for recursive crawling (default: unlimited)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--max-redirects`: Maximum redirects to follow per URL (default: 10)
- `--single, -s`: Single page crawl (non-recursive, original behavior)
- `--help, -h`: Show help message

## Testing

The project includes comprehensive test coverage:

### Run All Tests
```bash
python3 -m pytest test/ -v
```

### Run Specific Test Suites
```bash
# Web crawler tests only
python3 -m pytest test/test_web_crawler.py -v

# Verification utils tests only
python3 -m pytest test/utils/test_verification_utils.py -v
```

### Test Coverage

#### Web Crawler Tests (18 tests)
- ✅ **Single Page Crawling**: Basic crawling functionality (backward compatibility)
- ✅ **Recursive Crawling**: Multi-level URL discovery with depth control
- ✅ **Visited URL Tracking**: Duplicate URL prevention and infinite loop avoidance
- ✅ **Redirect Loop Detection**: Infinite, reverse, and circular redirect loop detection
- ✅ **Redirect Following**: Safe redirect following with loop protection
- ✅ **Relative URL Handling**: Conversion of relative URLs to absolute URLs
- ✅ **Query Parameter Handling**: URLs with query parameters and fragments
- ✅ **Fragment Handling**: URLs with hash fragments
- ✅ **Empty Page Crawling**: Handling of pages with no links
- ✅ **HTTP Error Handling**: Network errors and connection failures
- ✅ **Timeout Error Handling**: Request timeout scenarios

#### Verification Utils Tests (35 tests)
- ✅ **Syntactic Checks**: URL format validation, scheme validation, port validation
- ✅ **Domain Validation**: Valid/invalid domain names, IP addresses, edge cases
- ✅ **IP Address Validation**: IPv4/IPv6 validation, invalid IP detection
- ✅ **Path/Query Validation**: Dangerous character detection, injection prevention
- ✅ **Semantic Checks**: DNS resolution, reserved domains, private IPs
- ✅ **Protocol Checks**: HTTP responses, content types, network errors
- ✅ **Operational Checks**: robots.txt, rate limiting, crawler blocking
- ✅ **Security Checks**: SSRF protection, dangerous protocols, input sanitization
- ✅ **Integration Tests**: Full verification pipeline testing

## Features

### Core Functionality
- **Recursive Crawling**: Recursively discovers all URLs within the same domain
- **Visited URL Tracking**: Maintains a list of visited URLs to avoid duplicates and infinite loops
- **Depth Control**: Configurable maximum depth for recursive crawling
- **Polite Crawling**: Configurable delays between requests to be respectful to servers
- **Redirect Protection**: Comprehensive protection against redirect loops (infinite, reverse, circular)
- **Single Domain Crawling**: Only crawls URLs from the same domain as the base URL
- **URL Validation**: Comprehensive validation of URLs before processing
- **Relative URL Handling**: Converts relative URLs to absolute URLs
- **Domain Filtering**: Automatically filters out external domains and subdomains
- **Error Handling**: Robust error handling for network issues and invalid URLs

### URL Verification System
The web crawler includes a comprehensive URL verification system with multiple validation layers:

#### 1. **Syntactic Checks**
- Validates URL format and structure
- Ensures proper HTTP/HTTPS schemes
- Validates domain names and IP addresses
- Checks port numbers (1-65535)
- Validates path and query string characters
- Prevents dangerous characters and injection attempts

#### 2. **Semantic Checks**
- DNS resolution validation
- Reserved domain detection (.invalid, .example, .test, .localhost)
- Private IP address filtering
- Domain name format validation

#### 3. **Protocol Checks**
- HTTP status code validation (2xx, 3xx)
- Content-Type verification for HTML pages
- SSL certificate validation
- Network connectivity testing

#### 4. **Operational Checks**
- robots.txt accessibility and compliance
- Rate limiting detection (Retry-After headers)
- Crawler blocking detection (403 Forbidden)
- Captcha and blocking page detection

#### 5. **Security Checks**
- SSRF (Server-Side Request Forgery) protection
- Local/internal service blocking
- Dangerous protocol filtering (javascript:, data:, file:, etc.)
- Input sanitization and validation



### Output Format

The tool provides detailed crawling progress and final results:

#### Progress Output:
```
Starting recursive crawl of https://example.com
Domain: example.com
Max depth: 2
Delay between requests: 1.0s
Max redirects per URL: 10
--------------------------------------------------
[Depth 0] Crawling: https://example.com
  Redirect 1: https://example.com -> https://example.com/home
[Depth 1] Crawling: https://example.com/about
[Depth 1] Crawling: https://example.com/contact
[Depth 2] Crawling: https://example.com/about/team
--------------------------------------------------
Crawl completed!
Total URLs found: 4
Total URLs visited: 4

All discovered URLs:
--------------------------------------------------
https://example.com
https://example.com/about
https://example.com/about/team
https://example.com/contact
```

### Programmatic Usage

You can also use the crawler programmatically:

```python
from src.web_crawler import crawl, crawl_single_page

# Recursive crawling with options
crawl("https://example.com", max_depth=3, delay=1.0, max_redirects=10)

# Single page crawling (original behavior)
crawl_single_page("https://example.com", max_redirects=10)
```

## Project Structure

```
web-crawler/
├── bin/
│   └── web-crawler          # CLI executable
├── src/
│   ├── web_crawler.py       # Main crawling logic
│   └── utils/
│       └── verification_utils.py  # URL verification system
├── test/
│   ├── test_web_crawler.py  # Web crawler tests
│   └── utils/
│       └── test_verification_utils.py  # Verification utils tests
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Performance Considerations

- **Efficient Parsing**: Uses BeautifulSoup for fast HTML parsing
- **Domain Filtering**: Early filtering to reduce processing overhead
- **URL Deduplication**: Uses sets to avoid duplicate processing and infinite loops
- **Breadth-First Crawling**: Uses deque for efficient URL queue management
- **Visited URL Tracking**: Prevents redundant crawling of already visited URLs
- **Redirect Loop Protection**: Prevents infinite redirect loops and wasted resources
- **Configurable Delays**: Polite crawling with adjustable delays between requests
- **Depth Control**: Prevents excessive crawling with configurable depth limits
- **Timeout Handling**: Configurable timeouts to prevent hanging requests

## Future Enhancements

- **Asynchronous Crawling**: Concurrent request handling for improved performance
- **URL Storage**: Persistent storage of crawled URLs and crawl history
- **Robots.txt Compliance**: Full robots.txt parsing and compliance
- **Sitemap Support**: XML sitemap parsing for efficient discovery
- **Crawl Statistics**: Detailed analytics and reporting
- **Resume Capability**: Ability to resume interrupted crawls
- **Custom Filters**: Advanced URL filtering and content analysis
- **Export Formats**: Support for various output formats (JSON, CSV, XML)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.
