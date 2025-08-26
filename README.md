# web-crawler
A CLI based tool for crawling webpages 

## Features

This web crawler will take a base URL as input and recursively crawl all URLs that have the same domain as the base URL. It is designed to be fast, efficient and resilient.

### Functional Requirements

- Single Domain : It should only crawl those URLs that have the same domain as the base URL
- Polite Crawling : It should provide sufficient delays between successive network requests so as to not get rate-limited by the target.
- Efficient Crawling : It should keep a track of the URLs that have been successfully processed so that it can skip them when re-visiting such URLs.

### Non-Functional Requirements

- Asynchronous Requests: Network I/O has significant latency overhead compared to local parsing, and so in order to optimise for time, the crawler should make concurrent asynchronous requests to the target for fetching the data for a URL.
- Resilient to Redirect Loops : A common problem encountered by web crawlers are the different kinds of re-direct loops they might encounter. This crawler should be resilient to these.
