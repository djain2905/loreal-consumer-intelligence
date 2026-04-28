-- One row per brand. Benchmarks Lancôme against other brands in the dataset
-- across satisfaction, desire signals, and complaint rates.
-- Supports diagnostic analytics ("how does Lancôme compare?") in the dashboard.
with reviews as (
    select * from {{ ref('fct_reviews') }}
),

products as (
    select * from {{ ref('dim_products') }}
),

brands as (
    select * from {{ ref('dim_brands') }}
)

select
    p.brand                                                         as brand_name,
    b.division,
    lower(p.brand) in ('lancôme', 'lancome')                       as is_lancome,

    count(*)                                                        as review_count,
    round(avg(r.rating), 2)                                        as avg_rating,
    round(avg(case when r.is_recommended then 1.0 else 0.0 end) * 100, 1)
                                                                    as pct_recommended,
    round(sum(case when r.desire_flag    then 1.0 else 0.0 end) / count(*) * 100, 1)
                                                                    as desire_rate,
    round(sum(case when r.complaint_flag then 1.0 else 0.0 end) / count(*) * 100, 1)
                                                                    as complaint_rate,
    count(distinct r.product_id)                                   as product_count

from reviews r
inner join products p on r.product_id = p.product_id
inner join brands b   on lower(p.brand) = lower(b.brand_name)
group by p.brand, b.division, lower(p.brand) in ('lancôme', 'lancome')
having count(*) >= 50
order by review_count desc
