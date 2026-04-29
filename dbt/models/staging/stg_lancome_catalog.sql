with source as (
    select * from {{ source('raw', 'lancome_catalog') }}
)

select
    line_number,
    source                          as source_name,
    url                             as source_url,
    content                         as content_text,
    length(content)                 as content_length
from source
where content is not null
  and trim(content) != ''
