-- Aggregates consumer desire signals on Lancôme products by theme.
-- Each row is one whitespace category. Powers the dashboard's recommendation view.
with lancome_desires as (
    select *
    from {{ ref('fct_reviews') }}
    where is_lancome = true
      and desire_flag = true
      and desire_category is not null
),

total_lancome_desires as (
    select count(*) as total from lancome_desires
)

select
    d.desire_category,
    count(*)                                                        as desire_count,
    round(count(*) * 100.0 / t.total, 1)                          as pct_of_all_desires,
    round(avg(d.rating), 2)                                        as avg_rating,
    count(case when d.sentiment_bucket = 'negative' then 1 end)    as negative_review_count,
    count(distinct d.product_id)                                   as product_count,
    count(distinct d.author_id)                                    as unique_reviewers,
    -- Opportunity score: high desire volume + low rating = biggest whitespace
    round(
        (count(*) * 1.0 / t.total) * (5.0 - avg(d.rating)),
        4
    )                                                               as opportunity_score
from lancome_desires d
cross join total_lancome_desires t
group by d.desire_category, t.total
order by opportunity_score desc
