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
    page_icon="🌹",
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
        s = st.secrets["snowflake"]
        return snowflake.connector.connect(
            account=s["account"], user=s["user"],
            password=s["password"], warehouse=s["warehouse"],
            database="LOREAL_DB",
        )
    except Exception:
        return snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database="LOREAL_DB",
        )

@st.cache_data(ttl=3600)
def q(sql: str) -> pd.DataFrame:
    cur = get_conn().cursor()
    cur.execute(sql)
    return cur.fetch_pandas_all()

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
st.title("🌹 Lancôme Consumer Intelligence")
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
            "OPPORTUNITY_SCORE": True,
            "DESIRE_CATEGORY": False,
        },
        title="Consumer Desire Gap Map — Lancôme Reviews",
        labels={
            "AVG_RATING":      "Average Rating (lower = more frustration)",
            "DESIRE_COUNT":    "Number of Desire Reviews (higher = stronger signal)",
            "UNIQUE_REVIEWERS":"Unique Reviewers",
            "OPPORTUNITY_SCORE": "Opportunity Score",
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
    top_opp = df_whitespace.sort_values("OPPORTUNITY_SCORE", ascending=False).iloc[0]
    m1, m2 = st.columns(2)
    m1.metric("Highest Volume Theme",      top_vol["DESIRE_CATEGORY"],
              f"{int(top_vol['DESIRE_COUNT'])} reviews")
    m2.metric("Highest Opportunity Theme", top_opp["DESIRE_CATEGORY"],
              f"Score {top_opp['OPPORTUNITY_SCORE']:.4f}")

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

    col1, col2 = st.columns(2)

    with col1:
        fig_avg = px.bar(
            df_comp.sort_values("AVG_RATING", ascending=True),
            x="AVG_RATING", y="BRAND_NAME", orientation="h",
            color="IS_LANCOME",
            color_discrete_map={True: ROSE, False: GRAY},
            title="Average Star Rating by Brand",
            labels={"AVG_RATING": "Avg Rating (★)", "BRAND_NAME": ""},
            text="AVG_RATING",
        )
        fig_avg.update_traces(texttemplate="%{text:.2f} ★", textposition="outside",
                              marker_line_width=0)
        fig_avg.update_layout(showlegend=False, xaxis_range=[0, 5.5])
        st.plotly_chart(style(fig_avg), use_container_width=True)

    with col2:
        fig_desire = px.bar(
            df_comp.sort_values("DESIRE_RATE", ascending=True),
            x="DESIRE_RATE", y="BRAND_NAME", orientation="h",
            color="IS_LANCOME",
            color_discrete_map={True: ROSE, False: GRAY},
            title="Unmet Need Rate (%) by Brand",
            labels={"DESIRE_RATE": "% Reviews Signaling an Unmet Need", "BRAND_NAME": ""},
            text="DESIRE_RATE",
        )
        fig_desire.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                                 marker_line_width=0)
        fig_desire.update_layout(showlegend=False)
        st.plotly_chart(style(fig_desire), use_container_width=True)

    st.caption(
        "**Unmet Need Rate** = % of a brand's reviews containing desire language "
        "(wish, want, need, would love, etc.). Higher = consumers are more actively "
        "signaling gaps in that brand's lineup."
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
with tab5:
    st.header("💡 Opportunity Brief")
    st.caption("Synthesized from 600K+ reviews, desire signal classification, and competitive benchmarks")

    top_opp  = df_whitespace.sort_values("OPPORTUNITY_SCORE", ascending=False).iloc[0]
    top_vol  = df_whitespace.iloc[0]
    lancome  = df_competitors[df_competitors["IS_LANCOME"] == True]
    others   = df_competitors[df_competitors["IS_LANCOME"] == False].head(5)
    lancome_rating    = float(lancome["AVG_RATING"].iloc[0])  if not lancome.empty else 0
    competitor_avg    = float(others["AVG_RATING"].mean())    if not others.empty  else 0
    lancome_desire    = float(lancome["DESIRE_RATE"].iloc[0]) if not lancome.empty else 0
    competitor_desire = float(others["DESIRE_RATE"].mean())   if not others.empty  else 0

    # ── Priority theme callout ─────────────────────────────────────────────────
    st.markdown(
        f"### Priority Whitespace: **{top_opp['DESIRE_CATEGORY']}**"
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Opportunity Score",  f"{top_opp['OPPORTUNITY_SCORE']:.4f}")
    m2.metric("Affected Reviewers", f"{int(top_opp['UNIQUE_REVIEWERS']):,}")
    m3.metric("Avg Rating on Theme", f"{top_opp['AVG_RATING']} ★")

    st.divider()

    # ── Competitor comparison charts ───────────────────────────────────────────
    st.subheader("Lancôme vs. Competitors — Where the Gap Lives")

    df_brief_comp = pd.concat([lancome, others], ignore_index=True)

    col1, col2 = st.columns(2)

    with col1:
        fig_c1 = px.bar(
            df_brief_comp.sort_values("DESIRE_RATE"),
            x="DESIRE_RATE", y="BRAND_NAME", orientation="h",
            color="IS_LANCOME",
            color_discrete_map={True: ROSE, False: GRAY},
            labels={"DESIRE_RATE": "Unmet Need Rate (%)", "BRAND_NAME": ""},
            title="Unmet Need Rate vs. Top Competitors",
            text="DESIRE_RATE",
        )
        fig_c1.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                             marker_line_width=0)
        fig_c1.update_layout(showlegend=False)
        st.plotly_chart(style(fig_c1), use_container_width=True)

    with col2:
        fig_c2 = px.bar(
            df_brief_comp.sort_values("COMPLAINT_RATE"),
            x="COMPLAINT_RATE", y="BRAND_NAME", orientation="h",
            color="IS_LANCOME",
            color_discrete_map={True: ROSE, False: GRAY},
            labels={"COMPLAINT_RATE": "Complaint Rate (%)", "BRAND_NAME": ""},
            title="Complaint Rate vs. Top Competitors",
            text="COMPLAINT_RATE",
        )
        fig_c2.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                             marker_line_width=0)
        fig_c2.update_layout(showlegend=False)
        st.plotly_chart(style(fig_c2), use_container_width=True)

    st.divider()

    # ── Narrative ─────────────────────────────────────────────────────────────
    st.subheader("What the Data Says")

    delta = round(lancome_rating - competitor_avg, 2)
    direction = "above" if delta >= 0 else "below"
    desire_comparison = (
        "more vocal about unmet needs than the average competitor"
        if lancome_desire > competitor_desire
        else "on par with peers in unmet need signaling — but specific categories stand out"
    )

    st.markdown(f"""
**Desire signal volume:**
{kpi['DESIRE_RATE']}% of Lancôme's {int(kpi['TOTAL_REVIEWS']):,} Sephora reviews contain
explicit desire language. The highest-volume theme is **{top_vol['DESIRE_CATEGORY']}**
({int(top_vol['DESIRE_COUNT'])} reviews).

**Where the gap is deepest:**
Adjusting for satisfaction, **{top_opp['DESIRE_CATEGORY']}** carries the highest opportunity
score ({top_opp['OPPORTUNITY_SCORE']:.4f}) — consumers not only want this, they are leaving
lower ratings ({top_opp['AVG_RATING']} ★) on products in this theme. That combination signals
a real product gap, not just a preference.

**Competitive position:**
Lancôme averages **{lancome_rating} ★** vs. a competitor average of **{competitor_avg:.2f} ★** —
{abs(delta)} stars {direction} the field. Its unmet need rate of **{lancome_desire:.1f}%**
means Lancôme consumers are {desire_comparison}.
""")

    st.divider()

    # ── Recommendation ────────────────────────────────────────────────────────
    st.subheader("Recommendation")

    st.success(f"""
**Action → Expected Outcome**

Launch a Lancôme product directly targeting **{top_opp['DESIRE_CATEGORY']}** —
the whitespace where consumer desire is most intense relative to current satisfaction.

With **{int(top_opp['UNIQUE_REVIEWERS']):,} unique reviewers** signaling this need and an average
rating of **{top_opp['AVG_RATING']} ★** on affected products, this gap is both wide and painful.
No top competitor has fully closed it.

→ **Expected outcome:** Capturing this whitespace converts high-intent, underserved consumers
into loyal Lancôme advocates — directly supporting L'Oréal Luxe growth targets and reinforcing
Lancôme's position as the innovating authority in premium beauty.
""")
