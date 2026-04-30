import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Lancôme Consumer Intelligence",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Brand palette ──────────────────────────────────────────────────────────────
ROSE  = "#C5817A"
GOLD  = "#C9A96E"
GRAY  = "#CCCCCC"
FONT  = "Inter, sans-serif"

st.markdown("""
<style>
  h1, h2, h3 { color: #1A1A1A; font-family: Inter, sans-serif; }
  .block-container { padding-top: 2rem; }
  .stMetric label { font-size: 0.72rem; color: #888; text-transform: uppercase;
                    letter-spacing: 0.05em; }
</style>
""", unsafe_allow_html=True)

# ── Shared chart style ─────────────────────────────────────────────────────────
def style(fig, height: int = 420):
    fig.update_layout(
        height=height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family=FONT, color="#1A1A1A", size=12),
        title_font=dict(size=14, color="#1A1A1A", family=FONT),
        margin=dict(t=50, b=40, l=10, r=20),
        legend=dict(font=dict(size=11, family=FONT)),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#F0F0F0", zeroline=False,
                     tickfont=dict(family=FONT, size=11))
    fig.update_yaxes(showgrid=True, gridcolor="#F0F0F0", zeroline=False,
                     tickfont=dict(family=FONT, size=11))
    return fig

# ── Connection ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    try:
        account   = st.secrets["snowflake"]["account"]
        user      = st.secrets["snowflake"]["user"]
        password  = st.secrets["snowflake"]["password"]
        warehouse = st.secrets["snowflake"]["warehouse"]
    except Exception:
        account   = os.getenv("SNOWFLAKE_ACCOUNT")
        user      = os.getenv("SNOWFLAKE_USER")
        password  = os.getenv("SNOWFLAKE_PASSWORD")
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")

    if not account:
        st.error("Snowflake credentials not found. Add them under App Settings → Secrets.")
        st.stop()

    return snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        warehouse=warehouse,
        database="LOREAL_DB",
        client_session_keep_alive=True,
        login_timeout=60,
        network_timeout=60,
    )

@st.cache_data(ttl=3600)
def q(sql: str) -> pd.DataFrame:
    import time
    for attempt in range(3):
        try:
            conn = get_conn()
            cur  = conn.cursor()
            # Resume warehouse explicitly before querying
            cur.execute(f"ALTER WAREHOUSE COMPUTE_WH RESUME IF SUSPENDED")
            cur.execute(sql)
            return cur.fetch_pandas_all()
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
            else:
                raise e

# ── Data ───────────────────────────────────────────────────────────────────────
df_kpis = q("""
    select
        count(*)                                                           as total_reviews,
        round(avg(rating), 2)                                             as avg_rating,
        round(sum(case when desire_flag then 1.0 else 0 end)
              / count(*) * 100, 1)                                        as desire_rate,
        sum(case when desire_flag then 1 else 0 end)                      as desire_count
    from loreal_db.dev_mart.fct_reviews
    where is_lancome = true
""")

df_ratings = q("""
    select rating, count(*) as cnt
    from loreal_db.dev_mart.fct_reviews
    where is_lancome = true
    group by rating order by rating
""")

df_time = q("""
    select * from loreal_db.dev_mart.mart_sentiment_over_time
    order by review_month
""")

df_whitespace = q("""
    select * from loreal_db.dev_mart.mart_whitespace_summary
    order by desire_count desc
""")

df_desires = q("""
    select f.review_text, f.rating, f.desire_category, f.sentiment_bucket,
           p.product_name
    from loreal_db.dev_mart.fct_reviews f
    join loreal_db.dev_mart.dim_products p on f.product_id = p.product_id
    where f.is_lancome = true and f.desire_flag = true
      and f.review_text is not null
    limit 2000
""")

df_competitors = q("""
    select * from loreal_db.dev_mart.mart_competitor_benchmarks
    order by review_count desc
""")

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Lancôme Consumer Intelligence")
st.caption("Identifying product whitespace from 600K+ verified Sephora reviews — built for L'Oréal USA")
st.divider()

kpi = df_kpis.iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Lancôme Reviews Analyzed", f"{int(kpi['TOTAL_REVIEWS']):,}")
c2.metric("Average Star Rating",       f"{kpi['AVG_RATING']} / 5.0")
c3.metric("Desire Signal Rate",        f"{kpi['DESIRE_RATE']}%",
          help="% of reviews containing wish / want / need language")
c4.metric("Total Desire Reviews",      f"{int(kpi['DESIRE_COUNT']):,}")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Descriptive",
    "📈 Trends",
    "🔍 Whitespace & Clusters",
    "⚖️ Competitor Benchmarks",
    "💡 Opportunity Brief",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DESCRIPTIVE
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("The Lancôme Review Landscape")
    st.markdown(
        f"Lancôme is L'Oréal's flagship Luxe brand with a strong presence across skincare "
        f"and makeup on Sephora. Across **{int(kpi['TOTAL_REVIEWS']):,}** verified reviews, "
        f"consumers rate it an average of **{kpi['AVG_RATING']} stars**. "
        f"But **{kpi['DESIRE_RATE']}% of those reviews** contain explicit desire language — "
        "signals of unmet needs. That's the whitespace this analysis maps."
    )

    col1, col2 = st.columns(2)

    with col1:
        fig_bar = px.bar(
            df_ratings, x="RATING", y="CNT",
            title="Rating Distribution — Lancôme Reviews",
            labels={"RATING": "Star Rating", "CNT": "Review Count"},
            color_discrete_sequence=[ROSE],
            text="CNT",
        )
        fig_bar.update_traces(texttemplate="%{text:,}", textposition="outside",
                              marker_line_width=0)
        fig_bar.update_layout(showlegend=False, yaxis_title="Reviews")
        st.plotly_chart(style(fig_bar), use_container_width=True)

    with col2:
        sentiment = pd.DataFrame({
            "Sentiment": ["Positive (4–5★)", "Neutral (3★)", "Negative (1–2★)"],
            "Count": [
                int(df_ratings[df_ratings["RATING"] >= 4]["CNT"].sum()),
                int(df_ratings[df_ratings["RATING"] == 3]["CNT"].sum()),
                int(df_ratings[df_ratings["RATING"] <= 2]["CNT"].sum()),
            ],
        })
        fig_pie = px.pie(
            sentiment, names="Sentiment", values="Count",
            title="Sentiment Breakdown",
            color_discrete_sequence=[ROSE, GOLD, GRAY],
            hole=0.4,
        )
        st.plotly_chart(style(fig_pie), use_container_width=True)

    desire_1_in = round(100 / float(kpi["DESIRE_RATE"]))
    st.markdown(
        f"> **Takeaway:** Nearly 1 in {desire_1_in} Lancôme reviewers explicitly articulates "
        "something they wish the product offered — a persistent, measurable signal of whitespace."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TRENDS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("How Has Sentiment Evolved Over Time?")
    st.markdown(
        "Tracking average rating alongside the **unmet need rate** — the share of reviews "
        "containing desire language — reveals whether consumer expectations are outpacing "
        "Lancôme's product launches over time."
    )

    df_time["REVIEW_MONTH"] = pd.to_datetime(df_time["REVIEW_MONTH"])
    df_time = df_time[df_time["REVIEW_COUNT"] >= 10]
    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(
        go.Scatter(
            x=df_time["REVIEW_MONTH"], y=df_time["AVG_RATING"],
            name="Avg Rating", line=dict(color=ROSE, width=2.5),
        ),
        secondary_y=False,
    )
    fig_trend.add_trace(
        go.Scatter(
            x=df_time["REVIEW_MONTH"], y=df_time["DESIRE_RATE"],
            name="Unmet Need Rate (%)", line=dict(color=GOLD, width=2, dash="dot"),
        ),
        secondary_y=True,
    )
    fig_trend.add_annotation(
        x="2018-06-01", y=4.48,
        xref="x", yref="y",
        text="<b>Ratings hold above 4.0★ for 9+ consecutive years</b><br>A loyal, satisfied base — not a brand in decline",
        showarrow=True, arrowhead=2, arrowcolor=ROSE, arrowwidth=1.8,
        ax=0, ay=-70,
        font=dict(size=10, color="#1A1A1A", family=FONT),
        bgcolor="rgba(253,246,245,0.5)", bordercolor=ROSE,
        borderwidth=1.5, borderpad=8, align="center",
    )
    fig_trend.add_annotation(
        x="2021-01-01", y=28,
        xref="x", yref="y2",
        text="<b>Desire signals persist even at peak satisfaction</b><br>These consumers aren't leaving — they're asking for more.<br>That's the whitespace opportunity.",
        showarrow=True, arrowhead=2, arrowcolor=GOLD, arrowwidth=1.8,
        ax=0, ay=-110,
        font=dict(size=10, color="#1A1A1A", family=FONT),
        bgcolor="rgba(253,246,245,0.5)", bordercolor=GOLD,
        borderwidth=1.5, borderpad=8, align="center",
    )
    fig_trend.update_layout(
        title="Lancôme — Avg Rating vs. Unmet Need Rate Over Time",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1, font=dict(family=FONT, size=11)),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family=FONT, size=12, color="#1A1A1A"),
        title_font=dict(size=14, family=FONT),
        margin=dict(t=60, b=40, l=10, r=20),
        height=460,
    )
    fig_trend.update_xaxes(showgrid=True, gridcolor="#F0F0F0", zeroline=False,
                            tickfont=dict(family=FONT, size=11))
    fig_trend.update_yaxes(title_text="Avg Rating (★)", secondary_y=False,
                            range=[1, 5], showgrid=True, gridcolor="#F0F0F0",
                            tickfont=dict(family=FONT, size=11))
    fig_trend.update_yaxes(title_text="Unmet Need Rate (%)", secondary_y=True,
                            range=[0, 100], showgrid=False,
                            tickfont=dict(family=FONT, size=11))
    st.plotly_chart(fig_trend, use_container_width=True)

    st.caption(
        "**Note:** Months with fewer than 10 reviews are excluded. "
        "Early periods (pre-2013) had very low monthly review volume — sometimes 1–3 reviews — "
        "causing extreme swings in both avg rating and desire rate that reflect sampling noise, "
        "not real consumer sentiment. The 10-review threshold keeps only months where the "
        "monthly average is statistically meaningful."
    )

    st.markdown(
        "> **Takeaway:** When the unmet need rate rises while average rating holds steady, "
        "consumers are satisfied with current products but still signaling they want *more* — "
        "a prime condition for a new product launch."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — WHITESPACE & CLUSTERS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("What Are Consumers Wishing For?")

    st.subheader("Consumer Desire Gap Map")
    st.markdown(
        "Each bubble is one whitespace theme. "
        "**Higher on the Y-axis** = more reviews signal this need (stronger volume). "
        "**Further left on the X-axis** = lower average ratings on those products (more frustration). "
        "**Bubble size** = number of unique reviewers. "
        "Themes in the **top-left** represent the highest-priority whitespace."
    )

    fig_gap = px.scatter(
        df_whitespace,
        x="AVG_RATING",
        y="DESIRE_COUNT",
        size="UNIQUE_REVIEWERS",
        text="DESIRE_CATEGORY",
        color="DESIRE_CATEGORY",
        hover_data={
            "DESIRE_COUNT": True,
            "AVG_RATING": True,
            "UNIQUE_REVIEWERS": True,
            "DESIRE_CATEGORY": False,
        },
        title="Consumer Desire Gap Map — Lancôme Reviews",
        labels={
            "AVG_RATING":      "Average Rating (lower = more frustration)",
            "DESIRE_COUNT":    "Number of Desire Reviews (higher = stronger signal)",
            "UNIQUE_REVIEWERS":"Unique Reviewers",
        },
        size_max=80,
    )
    fig_gap.update_traces(
        textposition="top center",
        marker=dict(opacity=0.82, line=dict(width=1.5, color="white")),
    )
    fig_gap.update_layout(
        showlegend=False,
        xaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(style(fig_gap, height=560), use_container_width=True)

    top_vol = df_whitespace.iloc[0]
    top_frustration = df_whitespace.sort_values("AVG_RATING").iloc[0]
    m1, m2 = st.columns(2)
    m1.metric("Highest Volume Theme",      top_vol["DESIRE_CATEGORY"],
              f"{int(top_vol['DESIRE_COUNT'])} reviews")
    m2.metric("Most Frustrated Theme",     top_frustration["DESIRE_CATEGORY"],
              f"{top_frustration['AVG_RATING']} ★ avg rating")

    st.divider()

    st.subheader("Browse Desire Reviews by Theme")
    st.markdown("Select a whitespace theme to read the actual consumer reviews behind it.")

    categories = df_whitespace["DESIRE_CATEGORY"].tolist()
    selected_cat = st.selectbox("Select a theme", categories)

    browse = (
        df_desires[df_desires["DESIRE_CATEGORY"] == selected_cat][[
            "PRODUCT_NAME", "RATING", "REVIEW_TEXT"
        ]]
        .rename(columns={
            "PRODUCT_NAME": "Product",
            "RATING": "Rating",
            "REVIEW_TEXT": "Review",
        })
        .head(50)
    )
    st.dataframe(browse, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — COMPETITOR BENCHMARKS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("How Does Lancôme Compare?")

    # Top 5 competitors by review volume (excluding Lancôme).
    # Highest review count = most statistically comparable benchmarks —
    # these are the brands Sephora consumers engage with most in the same categories.
    top5 = (
        df_competitors[df_competitors["IS_LANCOME"] == False]
        .sort_values("REVIEW_COUNT", ascending=False)
        .head(5)
    )
    lancome_row = df_competitors[df_competitors["IS_LANCOME"] == True]
    df_comp = pd.concat([lancome_row, top5], ignore_index=True)

    st.markdown(
        "Benchmarked against the **5 most-reviewed beauty brands on Sephora** in this dataset — "
        "the brands consumers engage with most in the same product categories as Lancôme. "
        "Lancôme is highlighted in rose."
    )

    df_grouped = df_comp.sort_values("AVG_RATING", ascending=True).copy()
    fig_grouped = go.Figure()
    fig_grouped.add_trace(go.Bar(
        y=df_grouped["BRAND_NAME"],
        x=df_grouped["AVG_RATING"],
        name="Avg Rating (★)",
        orientation="h",
        marker_color=[ROSE if v else GRAY for v in df_grouped["IS_LANCOME"]],
        text=df_grouped["AVG_RATING"].apply(lambda v: f"{v:.2f} ★"),
        textposition="outside",
        marker_line_width=0,
        offsetgroup=0,
    ))
    fig_grouped.add_trace(go.Bar(
        y=df_grouped["BRAND_NAME"],
        x=df_grouped["DESIRE_RATE"],
        name="Unmet Need Rate (%)",
        orientation="h",
        marker_color=[ROSE if v else "#E8E8E8" for v in df_grouped["IS_LANCOME"]],
        opacity=0.55,
        text=df_grouped["DESIRE_RATE"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        marker_line_width=0,
        offsetgroup=1,
    ))
    fig_grouped.update_layout(
        barmode="group",
        title="Avg Rating & Unmet Need Rate by Brand",
        legend=dict(orientation="h", y=1.08),
        xaxis_title="",
        yaxis_title="",
    )
    st.plotly_chart(style(fig_grouped), use_container_width=True)
    st.caption(
        "**Unmet Need Rate** = % of reviews containing desire language (wish, want, need, etc.). "
        "Higher = more consumers signaling gaps in that brand's lineup. "
        "Lancôme is highlighted in rose."
    )

    st.divider()

    fig_complaint = px.bar(
        df_comp.sort_values("COMPLAINT_RATE", ascending=True),
        x="COMPLAINT_RATE", y="BRAND_NAME", orientation="h",
        color="IS_LANCOME",
        color_discrete_map={True: ROSE, False: GRAY},
        title="Complaint Rate (%) by Brand — Lower Is Better",
        labels={"COMPLAINT_RATE": "% Reviews with Complaints", "BRAND_NAME": ""},
        text="COMPLAINT_RATE",
    )
    fig_complaint.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                                marker_line_width=0)
    fig_complaint.update_layout(showlegend=False)
    st.caption(
        "**Complaint Rate** = % of reviews with a 1–2★ rating or explicit dissatisfaction "
        "language (e.g. broke me out, doesn't work, returned, disappointed)."
    )
    st.plotly_chart(style(fig_complaint), use_container_width=True)

    st.dataframe(
        df_comp[[
            "BRAND_NAME", "DIVISION", "REVIEW_COUNT", "AVG_RATING",
            "DESIRE_RATE", "COMPLAINT_RATE",
        ]].rename(columns={
            "BRAND_NAME": "Brand", "DIVISION": "Division",
            "REVIEW_COUNT": "Reviews", "AVG_RATING": "Avg Rating",
            "DESIRE_RATE": "Unmet Need Rate (%)", "COMPLAINT_RATE": "Complaint Rate (%)",
        }),
        use_container_width=True, hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — OPPORTUNITY BRIEF
# ══════════════════════════════════════════════════════════════════════════════

# Pre-written product concepts per whitespace theme
HARDCODED_QUOTES = {
    "Key Ingredients": (
        "I wish I had paid attention to the ingredients prior to purchasing this serum. "
        "I have over 55 skin which is normal leaning a bit towards oily on hot, humid days. "
        "Everything was fine until I went on a trip to the desert. My skin became very dry. "
        "So, I added additional moisturizers and serum but it only worsened. It turns out that "
        "the high amount of glycerin was the culprit. Glycerin draws/attracts moisture. When "
        "there's low or no moisture in the environment it draws it from your skin. Never in my "
        "life have I had leathery skin. I mentioned my skin issues to a couple of people on our "
        "group trip and was advised to watch out for skin care with glycerin. I tried another "
        "member's serum and within a day my skin returned to normal."
    ),
    "Texture & Formula": (
        "I have been using this product for about a month now and it's alright. The pros are "
        "that it is dewy, lightweight and doesn't make me oily. The cons tho are that it is "
        "not all that hydrating on my dry/combo skin, SUPER scented, leaves my skin almost "
        "tacky/sticky and when I apply foundation over the top the shine that it provides my "
        "skin can no longer be seen (and I like to wear light coverage foundations). Overall "
        "it was not a good fit for me. I also find I have to use quite a few pumps to get the "
        "amount of product I want out to feel hydrated."
    ),
    "Packaging & Format": (
        "The toner itself is so-so. It does make my face feel soft, which is nice, but it "
        "doesn't do much more than that. The reason for me writing this review is the packaging. "
        "The product is slightly thicker than a typical liquid toner, which is fine. However, "
        "when you try to dispense this onto a cotton round I have found it incredibly difficult "
        "to get an amount that is anything but excessive. With any other liquid toner I would "
        "tilt the bottle upside down and let it saturate the cotton round. Since this product "
        "is a little thicker, that does not work. You must pour it onto a round which then "
        "results in a wastefully large amount of product coming out all at once. I wish there "
        "was a pump dispenser or a smaller hole at the top of the bottle."
    ),
    "Price & Value": (
        "This product is soooo expensive but it lasts a long time and does make my skin look "
        "radiant. As I am entering my 30s, I thought it would be a good product to try and it "
        "never disappoints. It's very hydrating and takes less than a minute to penetrate into "
        "the skin. Wish it was a little more affordable because there are other serums in the "
        "market at a lower cost that have similar ingredients and effects."
    ),
    "SPF & Sun Protection": (
        "I received this product for free through Influenster. Since I've gotten it, I've "
        "enjoyed it. Since it's winter my skin tends to be a slight bit more dry, so the "
        "hydration of this product does make a difference. But I don't know if it's just my "
        "skin, I feel like the product doesn't make my skin as smooth as it states. I also "
        "don't like that it doesn't have sunscreen. So I would have to add a small layer of "
        "sunscreen. Other than that the bottle is beautiful and smells great."
    ),
}

CONCEPTS = {
    "Sensitive Skin Formula": {
        "product_name":    "Génifique Sensitive",
        "positioning":     "The first Lancôme serum formulated fragrance-free and dermatologist-tested for reactive skin — microbiome science, zero compromise.",
        "consumer":        "Prestige skincare buyers with sensitive or reactive skin who want clinical efficacy without irritation.",
        "price_tier":      "$95 – $140",
        "gap":             "Lancôme has no fragrance-free or hypoallergenic product at any price tier. No prestige competitor owns this position.",
    },
    "Texture & Formula": {
        "product_name":    "Rénergie Featherlight",
        "positioning":     "Rénergie's full peptide complex in an ultra-lightweight water-gel — anti-aging results without the weight.",
        "consumer":        "Oily and combination skin consumers in warm climates who reject heavy creams but want premium anti-aging.",
        "price_tier":      "$85 – $120",
        "gap":             "The Rénergie franchise is cream-heavy with no lightweight or gel alternative in the lineup.",
    },
    "Fragrance & Scent": {
        "product_name":    "Génifique Pure",
        "positioning":     "The iconic Génifique serum, reformulated fragrance-free — same microbiome science, built for fragrance-sensitive skin.",
        "consumer":        "Existing Génifique loyalists bothered by the scent, plus new consumers who exclude fragrance from their routines.",
        "price_tier":      "$180 – $220",
        "gap":             "No fragrance-free variant of Lancôme's #1 bestselling serum exists.",
    },
    "Key Ingredients": {
        "product_name":    "Génifique Clarity",
        "positioning":     "A simplified, climate-adaptive Lancôme serum with full ingredient transparency — no hidden high-glycerin fillers, formulated to perform across all environments and skin types.",
        "consumer":        "Ingredient-literate prestige buyers who research formulations, read labels, and have been burned by hidden actives that behave differently across climates or skin conditions.",
        "price_tier":      "$130 – $175",
        "gap":             "Lancôme's current serums do not disclose ingredient rationale or flag climate/skin-type compatibility — consumers are discovering mismatches post-purchase and switching brands.",
    },
    "Packaging & Format": {
        "product_name":    "Absolue Refill System",
        "positioning":     "Refillable packaging extended across the Absolue and Rénergie lines — luxury skincare with a circular design commitment.",
        "consumer":        "Premium skincare consumers who want their luxury purchase to reflect their environmental values.",
        "price_tier":      "Refills at 20–30% discount vs. full price",
        "gap":             "Refillable packaging exists on only 2 SKUs. The rest of the catalog has no refill option.",
    },
    "SPF & Sun Protection": {
        "product_name":    "Génifique UV Defense SPF 50",
        "positioning":     "Daily SPF 50 serum-cream delivering Génifique's microbiome complex with broad-spectrum protection — one step, complete defense.",
        "consumer":        "Consumers who use Génifique daily and resent having to add a separate sunscreen step.",
        "price_tier":      "$110 – $150",
        "gap":             "Génifique ($220) and Absolue ($280) — Lancôme's top two SKUs — both lack SPF.",
    },
    "Price & Value": {
        "product_name":    "Génifique Discovery Set",
        "positioning":     "An entry-priced trial trio of Lancôme's top serums — the bridge from mass-market to Luxe.",
        "consumer":        "Aspiring prestige consumers who consider Lancôme but hesitate at full-price entry.",
        "price_tier":      "$45 – $65 (3-piece set)",
        "gap":             "No structured entry-price acquisition product in the Génifique franchise.",
    },
    "Shade Range & Inclusivity": {
        "product_name":    "Teint Idole Inclusive Edit",
        "positioning":     "20 new deeper and fairer shades for Teint Idole, developed from Lancôme's 22,000-skin-tone database.",
        "consumer":        "Prestige foundation buyers at the edges of the current shade range — deep tones underserved by luxury brands.",
        "price_tier":      "Same as existing Teint Idole ($53 – $63)",
        "gap":             "Despite 55 shades, consumers still signal shade mismatches at the extremes.",
    },
    "Longevity & Wear": {
        "product_name":    "Teint Idole 48H Ultra Wear",
        "positioning":     "A 48-hour transfer-proof foundation — Lancôme's most durable formula for consumers who can't touch up.",
        "consumer":        "Active, busy consumers who need makeup to last through sweat, heat, and long days.",
        "price_tier":      "$58 – $68",
        "gap":             "Teint Idole Ultra Wear claims 24H — no 48H or waterproof-first hero exists in the lineup.",
    },
}

THEME_KEYWORDS = {
    "Sensitive Skin Formula": [
        "broke me out", "breaking out", "broke out", "caused acne", "caused breakout",
        "skin reaction", "had a reaction", "allergic reaction", "hives", "rash",
        "irritated my skin", "burned my skin", "sensitive skin", "reactive skin",
        "clogged my pores", "clogged pores", "pimples", "inflammation",
    ],
    "Texture & Formula": [
        "too heavy", "too thick", "too greasy", "too oily", "pilling", "pills up",
        "balls up", "doesn't absorb", "won't absorb", "sits on top of",
        "clogs pores", "feels heavy", "so heavy", "very greasy",
    ],
    "Fragrance & Scent": [
        "the smell", "the scent", "too strong", "overpowering", "perfumey",
        "chemical smell", "fragrance is", "scent is", "smells like", "strong fragrance",
        "heavy scent", "fragrance free", "no fragrance",
    ],
    "Packaging & Format": [
        "pump broke", "pump doesn't work", "pump stopped", "hard to get out",
        "hard to open", "waste product", "dispenser broke", "bottle broke",
        "packaging is", "applicator", "messy", "leaks",
    ],
    "SPF & Sun Protection": [
        "wish it had spf", "needs spf", "no spf", "add spf", "without spf",
        "no sun protection", "wish it included sunscreen", "if only it had spf",
    ],
    "Key Ingredients": [
        "wish it had", "needs more", "vitamin c", "retinol", "hyaluronic acid",
        "niacinamide", "more antioxidant", "better ingredients", "if it had",
    ],
    "Price & Value": [
        "$", "hundred dollar", "dollars for", "not worth the price", "not worth",
        "overpriced", "too expensive", "cheaper", "half the price", "price tag",
        "for the price", "at this price", "paying this much",
    ],
    "Shade Range & Inclusivity": [
        "couldn't find my shade", "no shade for", "doesn't match my skin",
        "wrong shade", "runs pale", "runs yellow", "runs orange", "runs pink",
        "too yellow on", "too pink on", "too orange on", "oxidizes on me",
        "shade range", "more shades", "my undertone", "shade doesn't match",
    ],
    "Longevity & Wear": [
        "didn't last", "doesn't last", "wore off by", "faded by noon", "faded by lunch",
        "only lasted", "hours and it", "transferred", "creased", "wore off after",
    ],
}

def best_quote(df: pd.DataFrame, theme: str) -> str:
    if theme in HARDCODED_QUOTES:
        return HARDCODED_QUOTES[theme]
    keywords = THEME_KEYWORDS.get(theme, [])
    if not keywords:
        return df.sort_values("RATING").iloc[0]["REVIEW_TEXT"] if not df.empty else ""

    # Only look at negative reviews first; widen threshold only if needed
    for max_rating in (2, 3, 4):
        pool = df[df["RATING"] <= max_rating].copy()
        if pool.empty:
            continue
        text_lower = pool["REVIEW_TEXT"].str.lower()
        pool["_score"] = sum(text_lower.str.contains(kw, na=False).astype(int) for kw in keywords)
        relevant = pool[pool["_score"] > 0]
        if not relevant.empty:
            return relevant.sort_values(["_score", "RATING"], ascending=[False, True]).iloc[0]["REVIEW_TEXT"]

    return ""  # no negative, on-topic review found

with tab5:
    st.header("💡 Opportunity Brief")
    st.caption("A product launch brief built from 5,951 Lancôme reviews — synthesized for brand decision-making")

    top_vol  = df_whitespace.iloc[0]
    top_frus = df_whitespace.sort_values("AVG_RATING").iloc[0]
    lancome  = df_competitors[df_competitors["IS_LANCOME"] == True]
    others   = df_competitors[df_competitors["IS_LANCOME"] == False].head(5)
    lancome_rating = float(lancome["AVG_RATING"].iloc[0]) if not lancome.empty else 0
    competitor_avg = float(others["AVG_RATING"].mean())   if not others.empty  else 0
    delta          = round(lancome_rating - competitor_avg, 2)
    direction      = "above" if delta >= 0 else "below"

    # ── #1 Recommendation card ─────────────────────────────────────────────────
    top_concept = CONCEPTS[top_vol["DESIRE_CATEGORY"]]
    top_quote_df = df_desires[df_desires["DESIRE_CATEGORY"] == top_vol["DESIRE_CATEGORY"]]
    top_quote = best_quote(top_quote_df, top_vol["DESIRE_CATEGORY"])

    st.markdown(f"""
<div style="background:#FDF6F5;border-left:4px solid {ROSE};padding:1.5rem 2rem;border-radius:6px;margin-bottom:1rem;">
<p style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;color:{ROSE};margin:0 0 0.3rem 0;">
#1 PRODUCT OPPORTUNITY — HIGHEST CONSUMER SIGNAL</p>
<h2 style="margin:0 0 0.2rem 0;font-size:1.6rem;">{top_concept['product_name']}</h2>
<p style="color:#555;font-size:0.95rem;margin:0 0 1.2rem 0;font-style:italic;">{top_concept['positioning']}</p>
<table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">Target consumer</td>
<td style="padding:0.3rem 0;">{top_concept['consumer']}</td>
</tr>
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">Suggested price tier</td>
<td style="padding:0.3rem 0;">{top_concept['price_tier']}</td>
</tr>
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">The gap</td>
<td style="padding:0.3rem 0;">{top_concept['gap']}</td>
</tr>
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">Signal strength</td>
<td style="padding:0.3rem 0;"><strong>{int(top_vol['DESIRE_COUNT'])} desire reviews</strong> · {int(top_vol['UNIQUE_REVIEWERS'])} unique consumers · {top_vol['AVG_RATING']} ★ avg</td>
</tr>
</table>
{"<p style='margin:1rem 0 0 0;font-size:0.85rem;color:#555;border-top:1px solid #EEE;padding-top:0.8rem;'><em>&ldquo;" + top_quote + "&rdquo;</em></p>" if top_quote else ""}
</div>
""", unsafe_allow_html=True)

    frus_concept   = CONCEPTS[top_frus["DESIRE_CATEGORY"]]
    frus_quote_df  = df_desires[df_desires["DESIRE_CATEGORY"] == top_frus["DESIRE_CATEGORY"]]
    frus_quote     = best_quote(frus_quote_df, top_frus["DESIRE_CATEGORY"])

    st.markdown(f"""
<div style="background:#FDF6F5;border-left:4px solid #7A9CC5;padding:1.5rem 2rem;border-radius:6px;margin-bottom:1.5rem;">
<p style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;color:#7A9CC5;margin:0 0 0.3rem 0;">
HIGHEST FRUSTRATION — LOWEST AVG RATING</p>
<h2 style="margin:0 0 0.2rem 0;font-size:1.6rem;">{frus_concept['product_name']}</h2>
<p style="color:#555;font-size:0.95rem;margin:0 0 1.2rem 0;font-style:italic;">{frus_concept['positioning']}</p>
<table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">Target consumer</td>
<td style="padding:0.3rem 0;">{frus_concept['consumer']}</td>
</tr>
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">Suggested price tier</td>
<td style="padding:0.3rem 0;">{frus_concept['price_tier']}</td>
</tr>
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">The gap</td>
<td style="padding:0.3rem 0;">{frus_concept['gap']}</td>
</tr>
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">Signal strength</td>
<td style="padding:0.3rem 0;"><strong>{int(top_frus['DESIRE_COUNT'])} desire reviews</strong> · {int(top_frus['UNIQUE_REVIEWERS'])} unique consumers · <strong>{top_frus['AVG_RATING']} ★ avg</strong> (most dissatisfied segment)</td>
</tr>
</table>
{"<p style='margin:1rem 0 0 0;font-size:0.85rem;color:#555;border-top:1px solid #EEE;padding-top:0.8rem;'><em>&ldquo;" + frus_quote + "&rdquo;</em></p>" if frus_quote else ""}
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ── Product Concept Generator ──────────────────────────────────────────────
    st.subheader("Product Concept Generator")
    st.markdown(
        "Select any whitespace theme to generate a product brief — "
        "built from real consumer signal data and a proposed Lancôme product concept."
    )

    all_themes = df_whitespace["DESIRE_CATEGORY"].tolist()
    selected = st.selectbox("Choose a theme to explore", all_themes, key="brief_gen")

    row     = df_whitespace[df_whitespace["DESIRE_CATEGORY"] == selected].iloc[0]
    concept = CONCEPTS.get(selected, {})

    quote_df = df_desires[df_desires["DESIRE_CATEGORY"] == selected]
    quote = best_quote(quote_df, selected)

    pct_of_all = round(int(row["DESIRE_COUNT"]) / int(kpi["TOTAL_REVIEWS"]) * 100, 1)
    c1, c2, c3 = st.columns(3)
    c1.metric("Desire Reviews",          f"{int(row['DESIRE_COUNT']):,}")
    c2.metric("% of All Lancôme Reviews", f"{pct_of_all}%")
    c3.metric("Avg Rating",              f"{row['AVG_RATING']} ★")

    st.markdown(f"""
<div style="background:#FAFAFA;border:1px solid #E5E5E5;padding:1.5rem 2rem;border-radius:6px;margin-top:1rem;">
<p style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;color:#999;margin:0 0 0.5rem 0;">PROPOSED PRODUCT CONCEPT</p>
<h3 style="margin:0 0 0.3rem 0;">{concept.get('product_name', '—')}</h3>
<p style="color:#555;font-style:italic;margin:0 0 1rem 0;font-size:0.95rem;">{concept.get('positioning', '—')}</p>
<table style="width:100%;border-collapse:collapse;font-size:0.88rem;">
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">Target consumer</td>
<td>{concept.get('consumer', '—')}</td>
</tr>
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">Price tier</td>
<td>{concept.get('price_tier', '—')}</td>
</tr>
<tr>
<td style="padding:0.3rem 1rem 0.3rem 0;color:#888;white-space:nowrap;">Catalog gap</td>
<td>{concept.get('gap', '—')}</td>
</tr>
</table>
{"<p style='margin:1rem 0 0 0;font-size:0.85rem;color:#555;border-top:1px solid #EEE;padding-top:0.8rem;'><strong>What a consumer said:</strong><br><em>&ldquo;" + quote + "&rdquo;</em></p>" if quote else ""}
</div>
""", unsafe_allow_html=True)
