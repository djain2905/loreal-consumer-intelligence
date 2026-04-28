with reviews as (
    select * from {{ ref('stg_sephora_reviews') }}
),

products as (
    select
        product_id,
        brand_name,
        lower(brand_name) in ('lancôme', 'lancome') as is_lancome
    from {{ ref('stg_sephora_products') }}
)

select
    r.review_id,
    r.product_id,
    r.author_id,
    r.rating,
    r.review_date,
    r.is_recommended,
    r.review_title,
    r.review_text,
    r.skin_tone,
    r.skin_type,
    p.is_lancome,

    -- Sentiment bucket based on star rating
    case
        when r.rating >= 4 then 'positive'
        when r.rating = 3  then 'neutral'
        else                    'negative'
    end                                                             as sentiment_bucket,

    -- Complaint flag: low rating or explicit dissatisfaction language
    case
        when r.rating <= 2 then true
        when lower(r.review_text) regexp
            '.*(broke me out|breakout|irritat|reaction|burn|sting|rash|allerg|doesn.t work|did not work|waste of money|return|returned|disappointed|awful|terrible|horrible|worst).*'
        then true
        else false
    end                                                             as complaint_flag,

    -- Desire flag: consumer expresses an unmet want
    case
        when lower(r.review_text) regexp
            '.*(wish|want|need|hope|would love|if only|should have|missing|lacks|lack|doesn.t have|doesn.t include|no spf|needs spf).*'
        then true
        else false
    end                                                             as desire_flag,

    -- Desire category: what type of whitespace does the consumer signal?
    case
        when lower(r.review_text) regexp
            '.*(spf|sun protection|sunscreen|uv protection|no spf|needs spf|add spf).*'
            then 'SPF & Sun Protection'
        when lower(r.review_text) regexp
            '.*(more shade|shade range|shade match|skin tone|darker shade|lighter shade|deeper shade|fairer|more inclusive|no shade|my shade|my color).*'
            then 'Shade Range & Inclusivity'
        when lower(r.review_text) regexp
            '.*(retinol|hyaluronic|vitamin c|niacinamide|peptide|collagen|aha|bha|glycolic|salicylic|ceramide|squalane|bakuchiol).*'
            then 'Key Ingredients'
        when lower(r.review_text) regexp
            '.*(fragrance.free|unscented|no scent|no fragrance|sensitive to fragrance|fragrance sensitive|smells|strong smell|overwhelming scent).*'
            then 'Fragrance & Scent'
        when lower(r.review_text) regexp
            '.*(sensitive skin|broke me out|breakout|clog|non.comedogenic|irritat|reaction|burn|sting|rash|allerg|gentle formula|hypoallergenic).*'
            then 'Sensitive Skin Formula'
        when lower(r.review_text) regexp
            '.*(last longer|longer lasting|stay all day|wear longer|better wear|waterproof|transfer.proof|budge|fade|smudge|smear).*'
            then 'Longevity & Wear'
        when lower(r.review_text) regexp
            '.*(texture|formula|consistency|too thick|too thin|lighter formula|heavier|silky|smooth|greasy|oily|dry down|settl).*'
            then 'Texture & Formula'
        when lower(r.review_text) regexp
            '.*(packaging|pump|dropper|tube|bottle|applicator|cap|lid|dispenser|travel size|mini|refill|sustainable|recycle).*'
            then 'Packaging & Format'
        when lower(r.review_text) regexp
            '.*(price|expensive|pricey|affordable|cheaper|cost|worth the|value|budget|splurge|too much|not worth).*'
            then 'Price & Value'
        else null
    end                                                             as desire_category,

    -- Full review text when desire is present (for dashboard display)
    case
        when lower(r.review_text) regexp
            '.*(wish|want|need|hope|would love|if only|should have|missing|lacks|lack|doesn.t have|doesn.t include|no spf|needs spf).*'
        then r.review_text
        else null
    end                                                             as desire_text

from reviews r
inner join products p on r.product_id = p.product_id
