# Web Crawler

A command-line tool for crawling webpages and extracting URLs. This web crawler takes a base URL as input and outputs all URLs found on that webpage, filtered to the same domain.

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

The web crawler can be used as a CLI tool:

```bash
./bin/web-crawler <base_url>
```

Example:
```bash
./bin/web-crawler https://example.com
```

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

## Features

### Core Functionality
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

The tool outputs:
1. The base URL (first line)
2. All found URLs from the same domain (sorted alphabetically)

Example output:
```
https://example.com
https://example.com/about
https://example.com/contact
https://example.com/products
```

### Programmatic Usage

You can also use the crawler programmatically:

```python
from src.web_crawler import crawl

# The crawl function prints URLs to stdout
crawl("https://example.com")
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
- **URL Deduplication**: Uses sets to avoid duplicate processing
- **Timeout Handling**: Configurable timeouts to prevent hanging requests

## Future Enhancements

- **Asynchronous Crawling**: Concurrent request handling for improved performance
- **Recursive Crawling**: Multi-level crawling with depth limits
- **Rate Limiting**: Configurable delays between requests
- **URL Storage**: Persistent storage of crawled URLs
- **Robots.txt Compliance**: Full robots.txt parsing and compliance
- **Sitemap Support**: XML sitemap parsing for efficient discovery

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.
