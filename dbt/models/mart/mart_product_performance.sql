-- One row per Lancôme product. Summarizes review volume, satisfaction,
-- desire signals, and complaint signals to identify which products have
-- the most whitespace opportunity.
with reviews as (
    select * from {{ ref('fct_reviews') }}
    where is_lancome = true
),

products as (
    select * from {{ ref('dim_products') }}
)

select
    r.product_id,
    p.product_name,
    p.price_usd,
    p.price_tier,

    count(*)                                                        as review_count,
    round(avg(r.rating), 2)                                        as avg_rating,
    round(avg(case when r.is_recommended then 1.0 else 0.0 end) * 100, 1)
                                                                    as pct_recommended,

    sum(case when r.desire_flag   then 1 else 0 end)               as desire_count,
    sum(case when r.complaint_flag then 1 else 0 end)              as complaint_count,

    round(sum(case when r.desire_flag   then 1.0 else 0.0 end) / count(*) * 100, 1)
                                                                    as desire_rate,
    round(sum(case when r.complaint_flag then 1.0 else 0.0 end) / count(*) * 100, 1)
                                                                    as complaint_rate,

    -- Whitespace priority score: high desire + high complaint = biggest gap
    round(
        (sum(case when r.desire_flag   then 1.0 else 0.0 end) / count(*))
        * (sum(case when r.complaint_flag then 1.0 else 0.0 end) / count(*))
        * 100,
        4
    )                                                               as whitespace_score,

    -- Most common desire category for this product
    mode(r.desire_category)                                        as top_desire_category

from reviews r
inner join products p on r.product_id = p.product_id
group by r.product_id, p.product_name, p.price_usd, p.price_tier
having count(*) >= 5
order by whitespace_score desc
