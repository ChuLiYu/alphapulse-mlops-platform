{% snapshot dim_assets_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='symbol',
        strategy='check',
        check_cols=['risk_level', 'asset_class'],
        invalidate_hard_deletes=True
    )
}}

select
    symbol,
    asset_class,
    risk_level,
    first_seen_at,
    current_timestamp as snapshot_taken_at
from {{ ref('dim_assets') }}

{% endsnapshot %}
