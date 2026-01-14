import pandas as pd
from sqlalchemy import create_engine, text
import sqlalchemy

engine = create_engine("postgresql://postgres:postgres@postgres:5432/alphapulse")
query = "SELECT count(*) FROM model_features"

print(f"Pandas version: {pd.__version__}")
print(f"SQLAlchemy version: {sqlalchemy.__version__}")

print("Attempt 1: read_sql with engine")
try:
    df = pd.read_sql(query, engine)
    print("Success 1")
except Exception as e:
    print(f"Fail 1: {e}")

print("Attempt 2: read_sql with connection")
try:
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    print("Success 2")
except Exception as e:
    print(f"Fail 2: {e}")

print("Attempt 3: read_sql_query with connection")
try:
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
    print("Success 3")
except Exception as e:
    print(f"Fail 3: {e}")

print("Attempt 4: read_sql with raw connection")
try:
    with engine.connect() as conn:
        df = pd.read_sql(query, conn.connection)
    print("Success 4")
except Exception as e:
    print(f"Fail 4: {e}")
