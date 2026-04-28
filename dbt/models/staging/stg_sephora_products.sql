with source as (
    select * from {{ source('raw', 'sephora_reviews') }}
),

deduped as (
    select
        product_id,
        product_name,
        brand_name,
        cast(price_usd as float) as price_usd,
        row_number() over (partition by product_id order by submission_time desc) as rn
    from source
)

select
    product_id,
    product_name,
    brand_name,
    price_usd,
    case
        when price_usd < 25              then 'budget'
        when price_usd between 25 and 50 then 'mid'
        else                                  'premium'
    end as price_tier
from deduped
where rn = 1
