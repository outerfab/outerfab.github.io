#!/usr/bin/env python3
"""Check a built release before upload; does not deploy or make network requests."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.robots = ""
        self.canonical = ""
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("name") == "robots":
            self.robots = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href", "")
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["preview", "production"])
    parser.add_argument("--dist", type=Path, default=Path(__file__).resolve().parents[1] / "dist")
    parser.add_argument("--host", default="outerfab.com")
    args = parser.parse_args()
    root = args.dist
    errors = []
    def require(condition, message):
        if not condition:
            errors.append(message)
    files = list(root.rglob("*.html"))
    require(bool(files), "No HTML pages built")
    expected_noindex = {"404.html", "contact/thanks/index.html", "resources/pack-requested/index.html",
                        "events/szoss/received/index.html", "events/szoss/error/index.html"}
    indexable = set()
    for f in files:
        rel = f.relative_to(root).as_posix()
        page = Page()
        page.feed(f.read_text())
        require(urlsplit(page.canonical).netloc == args.host and page.canonical.startswith("https://"), f"{rel}: wrong canonical")
        noindex = "noindex" in page.robots.split(",")
        require(noindex == (args.mode == "preview" or rel in expected_noindex), f"{rel}: wrong indexing policy")
        if not noindex:
            indexable.add(page.canonical)
        for src in page.scripts:
            if src.startswith("/assets/"):
                require((root / src.lstrip("/")).is_file(), f"{rel}: missing script {src}")
                require(src != "/assets/quote-form.js", f"{rel}: unversioned quote script")
    robots = (root / "robots.txt").read_text()
    headers = (root / "_headers").read_text()
    blocked = "Disallow: /" in robots.splitlines()
    require(blocked == (args.mode == "preview"), "Wrong robots.txt crawl policy")
    require(("x-robots-tag: noindex" in headers.lower()) == (args.mode == "preview"), "Wrong global indexing header")
    sitemap = root / "sitemap.xml"
    if args.mode == "production":
        require(sitemap.exists(), "Missing sitemap")
        if sitemap.exists():
            urls = [n.text for n in ET.parse(sitemap).findall(".//{*}loc")]
            require(len(urls) == len(set(urls)) and set(urls) == indexable, "Sitemap and indexable canonicals differ")
        require(f"Sitemap: https://{args.host}/sitemap.xml" in robots, "Wrong sitemap declaration")
        require((root / "llms.txt").exists(), "Missing llms.txt")
    else:
        require(not sitemap.exists() and not (root / "llms.txt").exists(), "Preview exposes search discovery files")
    print(json.dumps({"mode": args.mode, "pages": len(files), "indexable": len(indexable), "errors": errors}))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
