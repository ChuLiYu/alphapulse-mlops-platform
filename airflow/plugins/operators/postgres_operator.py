from airflow.models import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.decorators import apply_defaults
import pandas as pd
from sqlalchemy import create_engine


class PostgresUtils:
    @staticmethod
    def get_sqlalchemy_engine(conn_id="postgres_default"):
        hook = PostgresHook(postgres_conn_id=conn_id)
        return hook.get_sqlalchemy_engine()

    @staticmethod
    def save_df_to_postgres(
        df: pd.DataFrame,
        table_name: str,
        if_exists="append",
        conn_id="postgres_default",
    ):
        if df is None or df.empty:
            print("No data to save to Postgres")
            return

        engine = PostgresUtils.get_sqlalchemy_engine(conn_id)
        df.to_sql(table_name, engine, if_exists=if_exists, index=False)
        print(f"Saved {len(df)} rows to table {table_name}")

    @staticmethod
    def execute_sql(sql: str, conn_id="postgres_default"):
        hook = PostgresHook(postgres_conn_id=conn_id)
        hook.run(sql)


class CustomPostgresOperator(BaseOperator):
    """
    Custom wrapper to execute SQL or save DataFrames.
    """

    @apply_defaults
    def __init__(
        self,
        sql=None,
        postgres_conn_id="postgres_default",
        autocommit=False,
        parameters=None,
        database=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.sql = sql
        self.postgres_conn_id = postgres_conn_id
        self.autocommit = autocommit
        self.parameters = parameters
        self.database = database

    def execute(self, context):
        hook = PostgresHook(
            postgres_conn_id=self.postgres_conn_id, schema=self.database
        )
        if self.sql:
            hook.run(self.sql, self.autocommit, parameters=self.parameters)
