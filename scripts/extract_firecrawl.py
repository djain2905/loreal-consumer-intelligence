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
    # ── Lancôme USA (product catalog + brand) ─────────────────────────────────
    ("lancome-makeup-catalog",      "https://www.lancome-usa.com/makeup"),
    ("lancome-skincare-catalog",    "https://www.lancome-usa.com/skincare"),
    ("lancome-fragrance-catalog",   "https://www.lancome-usa.com/fragrance"),
    ("lancome-about",               "https://www.lancome-usa.com/about-lancome"),

    # ── L'Oréal Group (parent company, strategy, press) ───────────────────────
    ("loreal-press-releases",       "https://www.loreal.com/en/articles/"),
    ("loreal-group-about",          "https://www.loreal.com/en/group/about-loreal/"),
    ("loreal-luxe-division",        "https://www.loreal.com/en/group/loreal-luxe/"),
    ("loreal-innovation",           "https://www.loreal.com/en/innovation/"),
    ("loreal-sustainability",       "https://www.loreal.com/en/commitments-and-responsibilities/for-the-planet/"),

    # ── Beauty editorial (Byrdie, Allure, WWD) ────────────────────────────────
    ("byrdie-lancome-review",       "https://www.byrdie.com/best-lancome-products-5115880"),
    ("byrdie-luxury-skincare",      "https://www.byrdie.com/best-luxury-skincare-brands"),
    ("allure-best-lancome",         "https://www.allure.com/gallery/best-lancome-products"),
    ("allure-luxury-beauty-trends", "https://www.allure.com/story/luxury-beauty-trends"),
    ("wwd-loreal-strategy",         "https://wwd.com/tag/loreal/"),

    # ── Sephora (retail context) ───────────────────────────────────────────────
    ("sephora-lancome-brand",       "https://www.sephora.com/brand/lancome"),
]


def scrape_to_file(slug: str, url: str) -> None:
    print(f"Scraping {url} ...")
    try:
        result = app.scrape(url, formats=["markdown"])
        content = result.markdown or ""
        if len(content) < 100:
            print(f"  ⚠️  very short content ({len(content)} chars) — skipping")
            return
        filename = RAW_DIR / f"{slug}-{today}.md"
        filename.write_text(content, encoding="utf-8")
        print(f"  saved → {filename.relative_to(Path(__file__).parent.parent)}  ({len(content):,} chars)")
    except Exception as e:
        print(f"  ✗ failed: {e}")


for slug, url in SOURCES:
    scrape_to_file(slug, url)

print(f"\nDone. Raw files in {RAW_DIR}")
