# Historical k3s deployment notes

The manifests in `base/` are legacy examples. They do not contain plaintext
credentials or keys and do not create Secret objects. Create the following Secrets in
the `alphapulse` namespace through your secret manager or another protected
workflow before applying the manifests:

- `alphapulse-db-credentials`: `postgres-username`, `postgres-password`,
  `api-database-url`, `trainer-database-url`, `mlflow-database-url`, and
  `airflow-database-url`.
- `alphapulse-app-secrets`: `secret-key` and `airflow-fernet-key`.

The database URL values must point to the matching database (`alphapulse` for
the API and trainer, `mlflow` for MLflow, and `airflow` for Airflow) and use
the same PostgreSQL role and password supplied in the first two keys. URL
encode reserved characters in the username or password. The Airflow URL is
documented for the legacy workload, but its Deployment currently has no pod
container definition; wiring and validating that workload remains manual.

The legacy Airflow configuration requires a stable Fernet key from
`alphapulse-app-secrets/airflow-fernet-key`. Wire it into the actual Airflow
container as `AIRFLOW__CORE__FERNET_KEY` when completing that workload. The
current incomplete Deployment intentionally has no generated or fallback key
and remains manual/disabled until the container and Secret reference are
configured. Keep the same key available to all Airflow components and preserve
it across rollouts. If Airflow data was encrypted with the formerly committed
key, plan a coordinated key rotation/re-encryption before replacing it.

Any credentials or keys ever deployed from earlier versions of these manifests
must be rotated before reuse, including PostgreSQL credentials, database URLs,
API signing keys, Airflow Fernet keys, and Grafana/admin credentials. Updating
these manifests or Secret values does not rotate credentials in an existing
database or re-encrypt stored data. Check the deployed state and backups, then
rotate each credential in its owning service before updating the corresponding
Secret. Existing Airflow encrypted values may require the old Fernet key during
a controlled migration.

All Secret references in the API, trainer, MLflow, and PostgreSQL pods are
required. Kubernetes leaves those containers in `CreateContainerConfigError`
when the named Secret or key is missing, so the workloads cannot silently use
the old committed `postgres` password. The API also requires `SECRET_KEY` from
`alphapulse-app-secrets`. Use one randomly generated key of at least 32
characters for every API replica and every rollout that must continue to
validate existing tokens. Changing it invalidates tokens signed by the old
key. Do not put the Secret values in this repository or a checked-in
Kubernetes manifest.

For an existing Postgres PVC, `POSTGRES_USER` and `POSTGRES_PASSWORD` only
initialize an empty data directory. Set the Secret to the credentials already
configured in the database, or rotate the database role separately before
changing the Secret. Do not assume changing the Secret rotates credentials in
an existing database.

## Refresh token table initialization

The legacy startup `init_db()` does not import `models_user.RefreshToken`, and
the PostgreSQL init scripts do not create `refresh_tokens`. Before enabling
refresh-token endpoints, connect to the `alphapulse` database and run this SQL
after the `users` table exists:

```sql
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    jti_digest VARCHAR(64) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

This is a manual schema prerequisite for the historical deployment; the
manifests do not run migrations. Back up the database and verify the table and
foreign key before enabling refresh-token use.

These notes document configuration only. No cluster was contacted or
deployed as part of this change.
