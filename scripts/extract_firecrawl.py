import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()

app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

RAW_DIR = Path(__file__).parent.parent / "knowledge" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

today = date.today().isoformat()

SOURCES = [
    ("lancome-makeup-catalog", "https://www.lancome-usa.com/makeup"),
    ("lancome-skincare-catalog", "https://www.lancome-usa.com/skincare"),
    ("loreal-press-releases", "https://www.loreal.com/en/articles/"),
]


def scrape_to_file(slug: str, url: str) -> None:
    print(f"Scraping {url} ...")
    result = app.scrape(url, formats=["markdown"])
    content = result.markdown or ""
    filename = RAW_DIR / f"{slug}-{today}.md"
    filename.write_text(content, encoding="utf-8")
    print(f"  saved → {filename.relative_to(Path(__file__).parent.parent)}  ({len(content):,} chars)")


for slug, url in SOURCES:
    scrape_to_file(slug, url)

print("Done.")
