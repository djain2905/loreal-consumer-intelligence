with products as (
    select * from {{ ref('stg_sephora_products') }}
)

select
    product_id,
    product_name,
    brand_name                                          as brand,
    price_usd,
    price_tier,
    case
        when lower(brand_name) = 'lancôme'             then 'Luxe'
        when lower(brand_name) = 'lancome'             then 'Luxe'
        else                                                'Consumer Products'
    end                                                 as division
from products
