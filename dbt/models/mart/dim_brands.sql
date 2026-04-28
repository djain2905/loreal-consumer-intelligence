with brands as (
    select distinct
        brand_name
    from {{ ref('stg_sephora_products') }}
)

select
    md5(brand_name)                                     as brand_id,
    brand_name,
    case
        when lower(brand_name) in ('lancôme', 'lancome', 'ysl beauty',
                                   'yves saint laurent', 'giorgio armani beauty',
                                   'valentino beauty', 'urban decay', 'it cosmetics')
                                                        then 'Luxe'
        when lower(brand_name) in ('l\'oréal paris', 'loreal paris',
                                   'maybelline', 'nyx professional makeup',
                                   'essie', 'garnier')
                                                        then 'Consumer Products'
        when lower(brand_name) in ('la roche-posay', 'cerave', 'vichy',
                                   'skinceuticals', 'dermalogica')
                                                        then 'Dermatological'
        when lower(brand_name) in ('kérastase', 'redken', 'matrix',
                                   'pureology', 'l\'oréal professionnel')
                                                        then 'Professional'
        else                                                'Consumer Products'
    end                                                 as division
from brands
