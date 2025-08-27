# Web Crawler

A modern, asynchronous web crawler with comprehensive URL normalization, redirect handling, and detailed crawl reporting. This web crawler takes a base URL as input and recursively discovers all URLs within the same domain, with advanced features for robust and efficient crawling.

## Features

### Core Functionality
- **Asynchronous Crawling**: High-performance concurrent request handling
- **URL Normalization**: Comprehensive URL standardization to prevent duplicate crawling
- **Redirect Loop Detection**: Advanced protection against infinite, reverse, and circular redirect loops
- **Crawl Reports**: Automatic generation of detailed crawl reports with timestamps
- **Domain Restriction**: Only crawls URLs from the same domain as the base URL
- **Error Tracking**: Comprehensive tracking of error URLs and redirect URLs
- **Unlimited Depth**: Recursively discovers all URLs without depth limitations
- **Polite Crawling**: Configurable delays between requests to be respectful to servers

### URL Normalization
The crawler includes sophisticated URL normalization that:
- Removes trailing slashes from paths (except for root)
- Converts scheme and hostname to lowercase
- Removes default ports (80 for HTTP, 443 for HTTPS)
- Removes URL fragments (#section)
- Sorts query parameters alphabetically
- Removes duplicate query parameters (keeps last occurrence)

### Crawl Reports
Each crawl automatically generates a timestamped report folder containing:
- **`run_details.txt`**: Base URL, start/end times, total duration, URL counts, error counts, redirect counts
- **`all_found_urls.txt`**: Complete list of all discovered URLs
- **`all_error_urls.txt`**: URLs that encountered errors during crawling
- **`all_redirect_urls.txt`**: URLs that issued redirects during crawling

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

```bash
# Basic recursive crawl (unlimited depth)
./bin/web-crawler https://example.com

# Crawl with custom delay between requests
./bin/web-crawler https://example.com --delay 0.5

# Crawl with maximum redirect limit
./bin/web-crawler https://example.com --max-redirects 5

# Crawl with maximum concurrent requests
./bin/web-crawler https://example.com --max-concurrent 20

# Combine options
./bin/web-crawler https://example.com --delay 1.5 --max-redirects 8 --max-concurrent 15
```

#### CLI Options:
- `--delay`: Delay between requests in seconds (default: 0.1)
- `--max-redirects`: Maximum redirects to follow per URL (default: 10)
- `--max-concurrent`: Maximum concurrent requests (default: 10)
- `--help, -h`: Show help message

### Programmatic Usage

```python
from src.web_crawler import WebCrawler, CrawlConfig, crawl, crawl_async

# Using the WebCrawler class
config = CrawlConfig(
    delay=0.1,
    max_redirects=10,
    max_concurrent=10,
    timeout=10
)
crawler = WebCrawler(config)
result = await crawler.crawl("https://example.com")

# Using backward compatibility functions
crawl("https://example.com", delay=0.1, max_redirects=10, max_concurrent=10)
urls = await crawl_async("https://example.com", delay=0.1, max_redirects=10, max_concurrent=10)
```

## Architecture

### Class-Based Design
The crawler uses a modern, class-based architecture:

- **`WebCrawler`**: Main crawler class with comprehensive crawling logic
- **`CrawlConfig`**: Configuration dataclass for crawl settings
- **`CrawlResult`**: Result dataclass with detailed crawl statistics
- **`URLNormalizer`**: Utility class for URL normalization
- **`RedirectHandler`**: Utility class for redirect handling and loop detection

### Utility Modules
- **`src/utils/url_normalizer.py`**: URL normalization functionality
- **`src/utils/redirect_handler.py`**: Redirect handling and loop detection
- **`src/utils/verification_utils.py`**: URL verification system

## Testing

### Run All Tests
```bash
python3 -m pytest test/ -v
```

### Run Specific Test Suites
```bash
# All web crawler tests
python3 -m pytest test/test_web_crawler.py -v

# URL normalizer tests
python3 -m pytest test/test_web_crawler.py::TestURLNormalizer -v

# Redirect handler tests
python3 -m pytest test/test_web_crawler.py::TestRedirectHandler -v

# Verification utils tests
python3 -m pytest test/utils/test_verification_utils.py -v
```

### Test Coverage

#### Web Crawler Tests (23 tests)
- ✅ **URL Normalization**: Comprehensive URL standardization testing
- ✅ **Redirect Handling**: Loop detection and safe redirect following
- ✅ **Class Architecture**: WebCrawler, CrawlConfig, CrawlResult testing
- ✅ **Asynchronous Crawling**: Concurrent request handling
- ✅ **Error Handling**: Network errors, HTTP errors, parsing failures
- ✅ **Crawl Reports**: Report generation and file creation
- ✅ **Backward Compatibility**: Legacy function support

#### Verification Utils Tests (35 tests)
- ✅ **Syntactic Checks**: URL format validation, scheme validation
- ✅ **Domain Validation**: Valid/invalid domain names, IP addresses
- ✅ **Security Checks**: SSRF protection, dangerous protocols
- ✅ **Operational Checks**: robots.txt, rate limiting, crawler blocking

## Project Structure

```
web-crawler/
├── bin/
│   └── web-crawler              # CLI executable
├── src/
│   ├── web_crawler.py           # Main crawling logic
│   └── utils/
│       ├── url_normalizer.py    # URL normalization
│       ├── redirect_handler.py  # Redirect handling
│       └── verification_utils.py # URL verification
├── test/
│   ├── test_web_crawler.py      # Web crawler tests
│   └── utils/
│       └── test_verification_utils.py # Verification utils tests
├── crawling_runs/               # Generated crawl reports
│   └── YYYY-MM-DD_HH-MM-SS/     # Timestamped report folders
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Output Examples

### Console Output
```
INFO:web_crawler:Starting asynchronous recursive crawl of https://example.com
INFO:web_crawler:Domain: example.com
INFO:web_crawler:Delay between requests: 0.1s
INFO:web_crawler:Max redirects per URL: 10
INFO:web_crawler:Max concurrent requests: 10
INFO:web_crawler:--------------------------------------------------
INFO:web_crawler:Crawling: https://example.com
INFO:web_crawler:  Redirect 1: https://example.com -> https://example.com/home
INFO:web_crawler:--------------------------------------------------
INFO:web_crawler:Crawl completed!
INFO:web_crawler:Total URLs found: 4
INFO:web_crawler:Total URLs visited: 4
INFO:web_crawler:Errors encountered: 0
INFO:web_crawler:Redirects followed: 1
INFO:web_crawler:Crawl report created in: crawling_runs/2025-08-27_22-44-04
```

### Crawl Report Structure
```
crawling_runs/
└── 2025-08-27_22-44-04/
    ├── run_details.txt          # Crawl statistics and timing
    ├── all_found_urls.txt       # All discovered URLs
    ├── all_error_urls.txt       # Error URLs (empty if no errors)
    └── all_redirect_urls.txt    # Redirect URLs (empty if no redirects)
```

## Performance Features

- **Asynchronous Processing**: Concurrent HTTP requests for high performance
- **URL Normalization**: Prevents duplicate crawling of equivalent URLs
- **Efficient Parsing**: BeautifulSoup for fast HTML parsing
- **Domain Filtering**: Early filtering to reduce processing overhead
- **Concurrent Control**: Configurable semaphore limits
- **Redirect Protection**: Prevents infinite loops and wasted resources
- **Error Tracking**: Comprehensive error monitoring and reporting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.
