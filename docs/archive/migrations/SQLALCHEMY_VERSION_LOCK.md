# SQLAlchemy Version Strategy

## Decision
We have locked the SQLAlchemy version to `< 2.0` or used `psycopg2-binary` compatible drivers to ensure stability across the MLOps platform.

## Rationale
1. **Airflow Compatibility**: The version of Apache Airflow currently in use has specific constraints on database driver versions.
2. **Backward Compatibility**: Existing data ingestion scripts were developed using the 1.x syntax.
3. **Stability**: Prevent breaking changes in DB session handling during production training.

## Migration Path
When upgrading to SQLAlchemy 2.0+, we must:
- Update all `engine.execute()` calls to use `conn.execute(text(...))`
- Standardize on `future=True` flag in engine creation.
- Verify session context managers in `FastAPI` routes.

---
**Last Updated**: 2026-01-12