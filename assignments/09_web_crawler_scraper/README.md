# 09 – Web Crawler & Scraper

Goals
- Crawl pages on an approved host to list titles, URLs, and images; download on-site images only.

Approach
- Use `requests` and `BeautifulSoup` to fetch and parse pages.
- Normalize links, strip tracking params, and enforce same-host navigation.
- Throttle requests and deduplicate similar pages via a content hash.

Results
- Prints page summaries, including discovered links and images.
- Saves images under the output folder (default: `IMAGES/`).

Dependencies
```bash
python3 -m pip install requests beautifulsoup4
```

Run
```bash
python3 assignments/09_web_crawler_scraper/09_web_crawler_scraper.py https://example.edu/ --depth 1 --output IMAGES
```
