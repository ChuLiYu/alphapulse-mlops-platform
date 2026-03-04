select id, symbol, confidence_score, signal_timestamp,
    'confidence_score must be between 0 and 1' as failure_reason
from {{ ref('stg_trading_signals') }}
where confidence_score < 0 or confidence_score > 1
