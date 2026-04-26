import snowflake.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = snowflake.connector.connect(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE")
)

cursor = conn.cursor()

cursor.execute("CREATE DATABASE IF NOT EXISTS LOREAL_DB")
cursor.execute("USE DATABASE LOREAL_DB")
cursor.execute("CREATE SCHEMA IF NOT EXISTS RAW")

print("✅ Connected to Snowflake successfully!")
print("✅ LOREAL_DB database and RAW schema created!")

cursor.close()
conn.close()