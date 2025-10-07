# Kyle Versluis, 10/05/2025, Assignment 9
# Title: Web Crawler & Scraper
# Purpose: Process a target website and extract key information and suspicious content.

# Notes:
# The script only follows http(s) links that resolve to the same host (and port) as the starting URL.
# The script only downloads images that are also hosted on the same approved host.
# If the page includes external resources, such as 3rd party links, they are skipped.

# Requires Python 3.6+
# 3rd party dependencies: requests, beautifulsoup4
# pip install requests beautifulsoup4

# Usage: python3 web_crawler_scraper.py https://approved-website.edu/ --depth 2 --output IMAGES

# Standard Libraries
import argparse                                             # for command-line parsing
import hashlib                                              # for image/content hashing
import os                                                   # for filesystem operations
import sys                                                  # for exit codes
import time                                                 # for throttling
import random                                               # for random delay
from pathlib import Path                                    # for path manipulations
from typing import Set, Tuple                               # for type hints

# for URL manipulation
from urllib.parse import urljoin, urlparse, urldefrag, urlunparse, parse_qsl, urlencode

# 3rd Party Libraries
import requests                                             # for HTTP requests
from bs4 import BeautifulSoup                               # for HTML parsing

# ---------- Configuration Defaults ----------------
COMMON_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
REQUEST_TIMEOUT = 15                                        # seconds
URL_PROTOCOLS = {"http", "https"}                           # allowed URL protocols

# Request pacing
SLEEP_MIN = 0.5                                             # jittered sleep lower bound (seconds)
SLEEP_MAX = 2.0                                             # jittered sleep upper bound (seconds)
SLEEP_BETWEEN_PAGES = 1.0                                   # base delay between page requests (seconds)

# Tracking params to strip from all URLs we resolve
TRACKING_PREFIXES = tuple(p.lower() for p in [
    "utm_", "gclid", "fbclid", "sessionid", "jsessionid"
])
# --------------------------------------------------

# sleeps for a random duration in [min_s, max_s]
def sleep_jitter(min_s: float = SLEEP_MIN, max_s: float = SLEEP_MAX):
    time.sleep(random.uniform(min_s, max_s))

# Strips tracking parameters from a URL
def strip_tracking(u: str):
    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
    p = urlparse(u)
    q = [(k, v) for (k, v) in parse_qsl(p.query, keep_blank_values=False)
         if not any(k.lower().startswith(pref) for pref in TRACKING_PREFIXES)]
    return urlunparse(p._replace(query=urlencode(q, doseq=True)))

# resolves link relative to current_url and strips any URL fragments
def url_cleanup(current_url: str, link: str):
    absolute = urljoin(current_url, link)
    absolute, fragment = urldefrag(absolute)
    return strip_tracking(absolute)

# Ensures that the URL resolves to the same host as the approved_netloc
def stay_on_site(url: str, approved_netloc: str):
    p = urlparse(url)
    if p.scheme not in URL_PROTOCOLS:
        return False
    host_port = p.netloc.lower()
    approved = approved_netloc.lower()
    # Cleanse common 'www.' prefix but treat ports explicitly
    def strip_www(site: str):
        return site[4:] if site.startswith("www.") else site
    return strip_www(host_port) == strip_www(approved)

# skips common crawler traps (hidden/nofollow)
def is_trap_link(a):
    rel = [r.lower() for r in (a.get("rel") or [])]
    if "nofollow" in rel:
        return True
    style = (a.get("style") or "").lower()
    if "display:none" in style or "visibility:hidden" in style:
        return True
    if a.get("aria-hidden") == "true":
        return True
    return False

# Generates a safe filename for an image URL
def safe_image_filename(img_url: str):
    pr = urlparse(img_url)
    name = os.path.basename(pr.path) or "image"
    if not os.path.splitext(name)[1]:
        # Try to guess the extension from a path. If none, it falls back to hash.jpg
        ext = ".jpg" if ".jpg" in pr.path.lower() else ".png" if ".png" in pr.path.lower() else ""
        if not ext:
            name = name + "-" + hashlib.sha256(img_url.encode("utf-8")).hexdigest()[:10] + ".jpg"
        else:
            name = name + ext
    return name

# fetches a URL and parses it with BeautifulSoup
def fetch(url: str) -> Tuple[requests.Response, BeautifulSoup]:
    headers = {"User-Agent": COMMON_UA}
    fetch_response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    fetch_response.raise_for_status()
    # Quick content-type guard for HTML pages
    content_type = fetch_response.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise ValueError(f"Non-HTML content type for page: {content_type!r}")
    soup = BeautifulSoup(fetch_response.text, "html.parser")
    return fetch_response, soup

# downloads an image if it is on the approved host and looks like an image.
def download_image(img_url: str, out_dir: Path, approved_netloc: str):
    if not stay_on_site(img_url, approved_netloc):
        print(f"  [skip-img external] {img_url}")
        return False

    headers = {"User-Agent": COMMON_UA}
    try:
        with requests.get(img_url, headers=headers, timeout=REQUEST_TIMEOUT, stream=True) as download_response:
            download_response.raise_for_status()
            content_type = download_response.headers.get("Content-Type", "").lower()
            if not content_type.startswith("image/"):
                print(f"  [skip-img not image/*] {img_url} (Content-Type: {content_type or 'unknown'})")
                return False

            # Ensure the output directory exists and avoid overwriting existing files if already downloaded
            out_dir.mkdir(parents=True, exist_ok=True)
            safe_imgfile = safe_image_filename(img_url)
            dest = out_dir / safe_imgfile
            if dest.exists():
                print(f"  [image exists] {dest}")
                return True

            with open(dest, "wb") as image_data:
                for chunk in download_response.iter_content(chunk_size=8192):
                    if chunk:
                        image_data.write(chunk)
            print(f"  [image saved] {dest}")
            return True
    # image download error handling
    except Exception as e:
        print(f"  [image error] {img_url} -> {e}")
        return False

# extracts and prints info for a page and returns:
# (set_of_links_found, set_of_image_srcs_found) as absolute URLs.
def extract_and_print(page_url: str, soup: BeautifulSoup) -> Tuple[Set[str], Set[str]]:
    title = (soup.title.string.strip() if soup.title and soup.title.string else "(no title)")
    print(f"\n=== PAGE: {page_url}")
    print(f"TITLE: {title}")

    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag.get("href").strip()
        abs_url = url_cleanup(page_url, href)
        links.add(abs_url)
    if links:
        print("URLS FOUND:")
        for link in sorted(links):
            print(f" {link}")
    else:
        print("URLS FOUND: 0")

    images = set()
    for img in soup.find_all("img", src=True):
        src = img.get("src").strip()
        abs_src = url_cleanup(page_url, src)
        images.add(abs_src)
    if images:
        print("IMAGES FOUND:")
        for src in sorted(images):
            print(f" {src}")
    else:
        print("IMAGES FOUND: 0")

    return links, images

# Recursive page crawler that stays on the approved site
# Prints page info and downloads same-site images.
def crawl(url: str, approved_netloc: str, out_dir: Path, depth: int, visited: Set[str], seen_hashes: Set[str])-> None:
    if depth < 0:
        return
    if url in visited:
        return
    visited.add(url)

    # Enforce same-site at the entry to avoid accidental off-site recursion
    if not stay_on_site(url, approved_netloc):
        print(f"[skip external page] {url}")
        return

    try:
        resp, soup = fetch(url)
    except Exception as e:
        print(f"[error] {url} -> {e}")
        return

    text = soup.get_text(" ", strip=True)[:10000]
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if content_hash in seen_hashes:
        print("[dedup-alert] Skipping similar page")
        return
    seen_hashes.add(content_hash)

    links, images = extract_and_print(url, soup)

    # Download images from the same approved site only with a small pause between each
    for idx, img_url in enumerate(sorted(images)):
        if idx > 0:                                             # sleep only BETWEEN downloads
            time.sleep(random.uniform(0.5, 2.0))
        download_image(img_url, out_dir, approved_netloc)

    # Recurse into same-site links only
    if depth > 0:
        for link in sorted(links):
            if stay_on_site(link, approved_netloc):
                time.sleep(SLEEP_BETWEEN_PAGES)
                crawl(link, approved_netloc, out_dir, depth - 1, visited, seen_hashes)
            else:
                print(f"[skip external link] {link}")

def main(argv=None):
    parser = argparse.ArgumentParser(description="Recursive page extractor (title, URLs, images) for an approved host.")
    parser.add_argument("start_url", help="Starting URL on the approved host (http/https)")
    parser.add_argument("--depth", type=int, default=1, help="Recursion depth (default: 1)")
    parser.add_argument("--output", default="IMAGES", help="Folder for downloaded images (default: IMAGES)")
    args = parser.parse_args(argv)

    # Validate start_url
    parsed = urlparse(args.start_url)
    if parsed.scheme not in URL_PROTOCOLS or not parsed.netloc:
        print("Error: start_url must be an absolute http(s) URL, e.g. https://approved-website.edu/")
        return 2
    # stay on approved host
    approved_netloc = parsed.netloc
    out_dir = Path(args.output)
    visited: Set[str] = set()

    print(f"[start] {args.start_url} (approved host: {approved_netloc}, depth: {args.depth})")
    seen_hashes: Set[str] = set()
    crawl(args.start_url, approved_netloc, out_dir, args.depth, visited, seen_hashes)
    print(f"[done] Visited {len(visited)} page(s). Images saved under: {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())