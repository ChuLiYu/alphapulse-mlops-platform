import pandas as pd
from operators.postgres_operator import PostgresUtils


def export_indicators_to_postgres(df: pd.DataFrame):
    if df is None or df.empty:
        return

    schema_name = "public"
    table_name = "technical_indicators"

    if "symbol" not in df.columns:
        df["symbol"] = "BTC-USD"

    # 1. Export Prices
    prices_cols = ["symbol", "close", "volume", "timestamp"]
    df_prices = df[prices_cols].copy()
    df_prices.rename(columns={"close": "price"}, inplace=True)
    df_prices["source"] = "yahoo_finance"

    # Use to_sql or custom SQL execution.
    # PostgresUtils.save_df_to_postgres is available but we need conflicts handling.
    # So we will construct queries or use a smarter upsert function.
    # Since PostgresUtils is a wrapper I created, I should probably improve it or use raw SQL here.

    # We will use raw SQL construction for upsert behavior similar to Mage implementation
    from psycopg2.extras import execute_values

    engine = PostgresUtils.get_sqlalchemy_engine()
    # We need a raw connection for execute_values
    conn = engine.raw_connection()
    try:
        with conn.cursor() as cur:
            # Prices
            p_columns = ["symbol", "price", "volume", "timestamp", "source"]
            p_query = f"INSERT INTO {schema_name}.prices ({','.join(p_columns)}) VALUES %s ON CONFLICT (symbol, timestamp) DO NOTHING"
            p_data = [tuple(x) for x in df_prices[p_columns].to_numpy()]
            if p_data:
                execute_values(cur, p_query, p_data)

            # Indicators
            db_columns = [
                "symbol",
                "timestamp",
                "sma_7",
                "sma_25",
                "sma_99",
                "ema_12",
                "ema_26",
                "rsi_14",
                "macd",
                "macd_signal",
                "macd_histogram",
                "bb_upper",
                "bb_middle",
                "bb_lower",
                "atr_14",
                "obv",
                "adx_14",
            ]
            valid_cols = [c for c in db_columns if c in df.columns]
            ti_query = f"INSERT INTO {schema_name}.{table_name} ({','.join(valid_cols)}) VALUES %s ON CONFLICT DO NOTHING"
            ti_data = [tuple(x) for x in df[valid_cols].to_numpy()]
            if ti_data:
                execute_values(cur, ti_query, ti_data)

        conn.commit()
    finally:
        conn.close()
