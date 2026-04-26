import os
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

# ── Set Kaggle credentials ──
os.environ["KAGGLE_USERNAME"] = os.getenv("KAGGLE_USERNAME")
os.environ["KAGGLE_KEY"] = os.getenv("KAGGLE_KEY")

import kaggle

# ── Download dataset from Kaggle ──
print("Downloading Sephora dataset from Kaggle...")
os.makedirs("data", exist_ok=True)

kaggle.api.authenticate()
kaggle.api.dataset_download_files(
    "nadyinky/sephora-products-and-skincare-reviews",
    path="data/",
    unzip=True
)

print("✅ Dataset downloaded!")

# ── Load reviews CSV ──
df = pd.read_csv("data/reviews_0-250.csv", low_memory=False)
df = df.where(pd.notnull(df), None)
print(f"Loaded {len(df)} reviews")

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
    CREATE OR REPLACE TABLE RAW.SEPHORA_REVIEWS (
        AUTHOR_ID VARCHAR,
        RATING NUMBER,
        IS_RECOMMENDED VARCHAR,
        REVIEW_TEXT VARCHAR,
        REVIEW_TITLE VARCHAR,
        SKIN_TONE VARCHAR,
        SKIN_TYPE VARCHAR,
        PRODUCT_ID VARCHAR,
        PRODUCT_NAME VARCHAR,
        BRAND_NAME VARCHAR,
        PRICE_USD FLOAT,
        SUBMISSION_TIME VARCHAR
    )
""")

print("✅ Table created in Snowflake!")

# ── Build rows ──
print("Loading data into Snowflake... (this may take a few minutes)")

rows = []
for _, row in df.iterrows():
    rows.append((
        str(row.get("author_id")) if row.get("author_id") else None,
        row.get("rating"),
        str(row.get("is_recommended")) if row.get("is_recommended") else None,
        str(row.get("review_text"))[:5000] if row.get("review_text") else None,
        str(row.get("review_title"))[:500] if row.get("review_title") else None,
        str(row.get("skin_tone")) if row.get("skin_tone") else None,
        str(row.get("skin_type")) if row.get("skin_type") else None,
        str(row.get("product_id")) if row.get("product_id") else None,
        str(row.get("product_name"))[:500] if row.get("product_name") else None,
        str(row.get("brand_name")) if row.get("brand_name") else None,
        row.get("price_usd"),
        str(row.get("submission_time")) if row.get("submission_time") else None,
    ))

# ── Insert in batches ──
BATCH_SIZE = 10000
total = len(rows)
for i in range(0, total, BATCH_SIZE):
    batch = rows[i:i + BATCH_SIZE]
    cursor.executemany("""
        INSERT INTO RAW.SEPHORA_REVIEWS (
            AUTHOR_ID, RATING, IS_RECOMMENDED, REVIEW_TEXT, REVIEW_TITLE,
            SKIN_TONE, SKIN_TYPE, PRODUCT_ID, PRODUCT_NAME, BRAND_NAME,
            PRICE_USD, SUBMISSION_TIME
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, batch)
    print(f"Inserted {min(i + BATCH_SIZE, total)}/{total} rows...")

print(f"✅ {total} rows loaded into Snowflake RAW.SEPHORA_REVIEWS!")

cursor.close()
conn.close()