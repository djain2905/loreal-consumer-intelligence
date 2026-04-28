with source as (
    select * from {{ source('raw', 'sephora_reviews') }}
),

deduped as (
    select *,
        row_number() over (
            partition by author_id, product_id, submission_time, review_text
            order by submission_time
        ) as rn
    from source
)

select
    md5(concat(coalesce(author_id, ''), coalesce(product_id, ''), coalesce(cast(submission_time as varchar), ''), coalesce(review_text, ''))) as review_id,
    product_id,
    author_id,
    cast(rating as integer)                         as rating,
    try_cast(submission_time as date)               as review_date,
    case
        when upper(is_recommended) = 'TRUE'  then true
        when upper(is_recommended) = '1'     then true
        else false
    end                                             as is_recommended,
    review_title,
    review_text,
    skin_tone,
    skin_type
from deduped
where rn = 1
