from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from minio import Minio
import pandas as pd
from io import BytesIO
import os

class MinIOUtils:
    """
    Helper class for MinIO interactions, intended to be used within PythonOperators
    or simplified Custom Operators.
    """
    @staticmethod
    def get_client():
        minio_endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
        # Handle protocol if present in endpoint
        if '://' in minio_endpoint:
            minio_endpoint = minio_endpoint.split('://')[1]
            
        access_key = os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('MINIO_ROOT_USER')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') or os.getenv('MINIO_ROOT_PASSWORD')
        
        # Validate that required credentials are present
        if not access_key or not secret_key:
            raise ValueError("MinIO credentials not found. Please set AWS_ACCESS_KEY_ID or MINIO_ROOT_USER and AWS_SECRET_ACCESS_KEY or MINIO_ROOT_PASSWORD environment variables.")
        
        return Minio(
            minio_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )

    @staticmethod
    def save_df_to_minio(df: pd.DataFrame, bucket_name: str, object_name: str):
        if df is None or df.empty:
            print(f"No data to export to {bucket_name}/{object_name}")
            return

        client = MinIOUtils.get_client()

        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

        csv_bytes = df.to_csv(index=False).encode('utf-8')
        csv_buffer = BytesIO(csv_bytes)

        client.put_object(
            bucket_name,
            object_name,
            csv_buffer,
            len(csv_bytes),
            content_type='application/csv'
        )
        print(f"Exported {len(df)} rows to MinIO: {bucket_name}/{object_name}")

    @staticmethod
    def load_df_from_minio(bucket_name: str, object_name: str) -> pd.DataFrame:
        client = MinIOUtils.get_client()
        
        try:
            response = client.get_object(bucket_name, object_name)
            df = pd.read_csv(response)
            return df
        except Exception as e:
            print(f"Error reading from MinIO {bucket_name}/{object_name}: {e}")
            raise

class MinIOUploadOperator(BaseOperator):
    """
    Custom Operator to upload DataFrame (passed via XCom or context) to MinIO.
    This is an example if one wants to use a dedicated Operator.
    """
    @apply_defaults
    def __init__(self, bucket_name, object_name, pandas_df=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.pandas_df = pandas_df

    def execute(self, context):
        df = self.pandas_df
        if df is None:
            # Try to get from XCom if not provided directly
            # This logic depends on how upstream passes data
            pass
        
        MinIOUtils.save_df_to_minio(df, self.bucket_name, self.object_name)
