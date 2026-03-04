select id, symbol, close_price, price_timestamp,
    'close_price must be > 0' as failure_reason
from {{ ref('stg_ohlcv') }}
where close_price <= 0

union all

select id, symbol, high_price, price_timestamp,
    'high_price must be >= low_price'
from {{ ref('stg_ohlcv') }}
where high_price < low_price
