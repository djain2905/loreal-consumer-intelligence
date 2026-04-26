import os
import snowflake.connector
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()

# ── Initialize Firecrawl ──
app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

# ── Scrape Lancôme product catalog ──
print("Scraping Lancôme product catalog via Firecrawl...")

result = app.scrape(
    "https://www.lancome-usa.com/makeup",
    formats=["markdown"]
)

# Extract the markdown content
content = result.markdown or ""
print(f"✅ Scraped {len(content)} characters from Lancôme")

# ── Parse into rows ──
rows = []
for i, line in enumerate(content.split("\n")):
    line = line.strip()
    if line:
        rows.append((
            i,
            "lancome_makeup_catalog",
            "https://www.lancome-usa.com/makeup",
            line[:5000]
        ))

print(f"Parsed {len(rows)} content rows")

# ── Connect to Snowflake ──
conn = snowflake.connector.connect(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database="LOREAL_DB",
    schema="RAW"
)

cursor = conn.cursor()

# ── Create table ──
cursor.execute("""
    CREATE OR REPLACE TABLE RAW.LANCOME_CATALOG (
        LINE_NUMBER NUMBER,
        SOURCE VARCHAR,
        URL VARCHAR,
        CONTENT VARCHAR
    )
""")

print("✅ Table created in Snowflake!")

# ── Insert rows ──
cursor.executemany("""
    INSERT INTO RAW.LANCOME_CATALOG (LINE_NUMBER, SOURCE, URL, CONTENT)
    VALUES (%s, %s, %s, %s)
""", rows)

print(f"✅ {len(rows)} rows loaded into Snowflake RAW.LANCOME_CATALOG!")

cursor.close()
conn.close()