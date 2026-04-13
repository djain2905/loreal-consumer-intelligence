**Name:** Dhwani Jain

**Project Name:** L'Oréal Consumer Intelligence

**GitHub Repo:** https://github.com/djain2905/loreal-consumer-intelligence

---

## Job Posting

**Role:** Commercial Management Trainee

**Company:** L'Oréal USA

**Link:** https://www.wayup.com/i-Consumer-Goods-j-2026-LOreal-USA-Commercial-Management-Trainee-Program-LOreal-191011435582500/

> Note: This posting is from the 2026 cycle of the Commercial Management Trainee Program; the 2027 cycle has not yet been posted and is expected to go live in summer 2026 — however, based on past trends, the program requirements remain consistent year over year, particularly for the data analysis and consumer insights responsibilities.

**SQL requirement (quote the posting):** "Generate insights and viable recommendations through data analysis across multiple sources" and "Work with internal data to generate accurate forecasting of sales volume and new client acquisitions." SQL is the foundational skill that makes these responsibilities executable — aggregating review data by product category, filtering by brand and price tier, joining product metadata to consumer sentiment, and computing demand signals from structured datasets are all SQL operations. The dbt + Snowflake layer in this project uses real SQL; the pandas layer functions as SQL for filtering and aggregation.

---

## Reflection

This posting is directly relevant to this course because the core job responsibilities — multi-source data analysis, sales pattern evaluation, and volume forecasting — are exactly what SQL, dimensional modeling, and a well-designed analytics pipeline enable. The role requires the same skills this class has developed: writing clean transformations in dbt, building a star schema that makes aggregation fast and reliable, and surfacing insights through an interactive dashboard. To prove I can do this work, I will build a consumer intelligence pipeline that pulls Sephora product and review data via the Kaggle API, loads it into Snowflake, transforms it through dbt staging and mart models, and surfaces product whitespace opportunities for Lancôme in a Streamlit dashboard — specifically by detecting desire language in consumer reviews, clustering those desires into product gap themes, and identifying which categories have the highest unmet demand. This project transfers directly to a consumer insights analyst role at any CPG or beauty company (Estée Lauder, Unilever, P&G), a BI analyst role at a retailer tracking product demand from review signals, or an analytics engineer role at any brand using unstructured consumer data to inform product strategy.
