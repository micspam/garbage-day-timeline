"""Fetch public Garbage Day issues from the sitemap and extract their body text.

Raw HTML and parsed text stay in data/ (gitignored) -- only short quotes are published.
"""
import html as htmllib
import json
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

SITE = "https://www.garbageday.email"
UA = "garbage-day-timeline/0.1 (proof of concept; polite crawler, 1 req/sec)"
DATA = Path("data")


def http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def sitemap_posts() -> list[str]:
    xml = http_get(f"{SITE}/sitemap.xml")
    return re.findall(r"<loc>(https://www\.garbageday\.email/p/[^<]+)</loc>", xml)


class PostParser(HTMLParser):
    """Collects text from <p class="dream-post-content-paragraph ..."> elements."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[str] = []
        self._depth = 0  # >0 while inside a body paragraph
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        if self._depth:
            if tag == "p":
                self._depth += 1
            elif tag == "br":
                self._buf.append(" ")
            return
        if tag == "p" and "dream-post-content-paragraph" in (dict(attrs).get("class") or ""):
            self._depth = 1
            self._buf = []

    def handle_endtag(self, tag):
        if self._depth and tag == "p":
            self._depth -= 1
            if not self._depth:
                text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
                if text:
                    self.paragraphs.append(text)

    def handle_data(self, data):
        if self._depth:
            self._buf.append(data)


def parse_post(url: str, html: str) -> dict:
    p = PostParser()
    p.feed(html)
    title = re.search(r'<meta property="og:title" content="([^"]*)"', html)
    date = re.search(r'"datePublished":"([^"]+)"', html)
    return {
        "url": url,
        "slug": url.rsplit("/", 1)[-1],
        "title": htmllib.unescape(title.group(1)) if title else "",
        "published": date.group(1)[:10] if date else "",
        "paragraphs": p.paragraphs,
    }


def run(limit: int | None, delay: float = 1.0):
    raw_dir, issue_dir = DATA / "raw", DATA / "issues"
    raw_dir.mkdir(parents=True, exist_ok=True)
    issue_dir.mkdir(parents=True, exist_ok=True)

    urls = sitemap_posts()
    print(f"sitemap: {len(urls)} posts")

    # --limit counts readable issues, so keep going past paywalled ones until we have enough.
    free = paywalled = 0
    for i, url in enumerate(urls, 1):
        if limit and free >= limit:
            break
        slug = url.rsplit("/", 1)[-1]
        raw = raw_dir / f"{slug}.html"
        if raw.exists():
            html = raw.read_text(encoding="utf-8")
        else:
            try:
                html = http_get(url)
            except Exception as e:
                print(f"  [{i}/{len(urls)}] {slug}: fetch failed ({e})")
                continue
            raw.write_text(html, encoding="utf-8")
            time.sleep(delay)
        post = parse_post(url, html)
        # Paid issues render only the headline publicly; short bodies are teasers, not issues.
        if sum(len(x) for x in post["paragraphs"]) < 1500:
            paywalled += 1
            continue
        free += 1
        (issue_dir / f"{slug}.json").write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  [{i}/{len(urls)}] {slug}: {len(post['paragraphs'])} paragraphs")
    print(f"done: {free} readable issues, {paywalled} paywalled/too short (skipped)")
