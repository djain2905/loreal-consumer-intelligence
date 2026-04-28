-- Monthly trend of Lancôme review volume, average rating, and desire signals.
-- Supports descriptive analytics ("what happened over time?") in the dashboard.
with reviews as (
    select * from {{ ref('fct_reviews') }}
    where is_lancome = true
      and review_date is not null
)

select
    date_trunc('month', review_date)                               as review_month,
    count(*)                                                        as review_count,
    round(avg(rating), 2)                                          as avg_rating,
    sum(case when desire_flag   then 1 else 0 end)                 as desire_count,
    sum(case when complaint_flag then 1 else 0 end)                as complaint_count,
    round(sum(case when desire_flag   then 1.0 else 0.0 end) / count(*) * 100, 1)
                                                                    as desire_rate,
    round(sum(case when sentiment_bucket = 'positive' then 1.0 else 0.0 end) / count(*) * 100, 1)
                                                                    as positive_rate,
    round(sum(case when sentiment_bucket = 'negative' then 1.0 else 0.0 end) / count(*) * 100, 1)
                                                                    as negative_rate
from reviews
group by date_trunc('month', review_date)
order by review_month
