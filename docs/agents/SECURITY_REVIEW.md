# Security review and upgrade notes — 2026-10-18

A dedicated read-only security reviewer inspected the new agent plus related
existing authentication, API, Compose, and sentiment code. The implementation
was then revised and regression-tested. This is a scoped source review, not a
penetration test, dependency audit, Git history secret scan, or certification.

## Findings addressed in this branch

| Area | Prior behavior | Change |
| --- | --- | --- |
| Critical: API identity | Dependency constructed a superuser without a token | Require signed, unexpired access JWT and active persisted user; refresh tokens cannot authenticate API calls |
| Critical: credentials/bootstrap | Known JWT default and known admin password returned by initialize endpoint | Explicit signing secret required; initialize only creates role definitions for an authenticated admin; first admin created by local operator CLI |
| API keys | Raw keys stored in DB; keys accepted as query parameters; scopes ignored | SHA-256 digest of random ~190-bit keys; header transport; explicit dependency scopes constrained to current owner permissions and rechecked on use; legacy migration below |
| Market/trading data | Public price/signal/indicator reads and writes | Require data:read / data:write RBAC on every route in those routers |
| Refresh tokens | Token passed in URL query | Required JSON request body |
| Infrastructure defaults | Known service passwords/Fernet key; ports on all interfaces; anonymous artifact download | Required secret settings, loopback published ports, private bucket initialization |
| CORS/reports | Wildcard credentialed CORS; publicly mounted monitoring reports | Explicit origins (empty by default); report static mount removed |
| Agent networking | Arbitrary endpoint, proxy/redirect forwarding, unbounded JSON read | Host-only loopback allowlist; no redirects/proxies; 1 MiB response limit |
| Agent artifacts | Personal path in local evaluation runner; permissive overwriting | Reusable CLI with caller-selected new directory; atomic no-replace 0600 files and 0700 run directory; live stdout trace opt-in |
| News sentiment | Unvalidated output, raw provider errors in logs, failures saved as neutral | Untrusted JSON-string article context; strict finite numeric ranges/schema/label; rejected rows stay unscored; sanitized warnings; loopback or exact Docker `ollama` host, no proxies/redirects, streamed 1 MiB cap |

The model selects tools in live mode. Python allowlist dispatch intentionally
limits which functions it may execute. It is not a keyword router that fabricates
tool calls. Fixture symbols and thresholds are explicit demonstration scope.

## Upgrade existing API installations

The agent CLI does not need the API, database, or Compose stack. These steps apply
only to existing API installations; no deployment was performed by this change.

1. Stop the API and back up its database. Set `DATABASE_URL` explicitly. Generate
   a new random `SECRET_KEY` of at least 32 characters in a secret manager or a
   local ignored environment file, inject it into the API, and rotate any service
   passwords/keys previously using public defaults. JWT key rotation invalidates
   earlier access and refresh tokens. Do not commit the file or print secrets.
2. Before starting the new API, migrate legacy API keys offline:
   `PYTHONPATH=src python -m alphapulse.security.migrate_api_keys`.
   It hashes the prior generator's 32-character alphanumeric values in-place,
   commits once, and is idempotent. No plaintext fallback exists after upgrade.
   If any previous database copy was exposed, revoke/reissue keys instead.
   Existing bcrypt password hashes remain compatible; hashing now uses bcrypt
   directly rather than the deprecated Passlib compatibility layer.
3. If this is a new installation, initialize the DB schema first, then run
   `PYTHONPATH=src python -m alphapulse.security.bootstrap` on the trusted host.
   It prompts for an operator-chosen username/email/password without echoing the
   password. It refuses when a superuser already exists. Run only one bootstrap
   process at a time; it does not implement a distributed bootstrap lock.
4. Clients must authenticate with `Authorization: Bearer <access token>`.
   `/auth/refresh` now requires `{"refresh_token":"..."}` in its JSON body.
   API-key consumers must use `X-API-Key`, with scopes explicitly declared using
   FastAPI `Security` on each route. No existing route was newly opened to API keys.
   Price/signal/indicator clients now need data:read or data:write RBAC; API-key scopes cannot exceed the owner's current permissions.
   Key listing returns `***`; raw keys are shown only at creation.
5. Set `CORS_ORIGINS` to comma-separated exact browser origins. Wildcard is
   rejected. Public monitoring report URLs are removed; provide an authenticated
   report delivery path before restoring that feature.
6. Compose now requires `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD`,
   `AIRFLOW_FERNET_KEY`, `AIRFLOW_PASSWORD`, `GRAFANA_PASSWORD`, and `SECRET_KEY`.
   Generate Fernet keys using the cryptography library. Passwords embedded into
   connection URLs must be URL-safe (random hexadecimal is suitable). Changing
   environment values does not rotate credentials in existing volumes: rotate
   through each service's supported procedure first. The bucket initialization
   sets anonymous access to none when it runs; verify existing bucket policy.

## Verification and remaining scope

Eleven security tests exercise missing/forged/expired/refresh JWT rejection,
inactive users, permission boundaries, real password hashing/login, JSON refresh,
API-key header/scope checks and idempotent legacy migration, safe initialization,
sentiment validation, and parsed Compose policies. Agent tests cover networking,
artifacts, failure recording and the multi-turn protocol. Full API deployment,
Postgres migrations, Docker startup and the ML suite were not exercised here.

The application still contains demo endpoints/data and historical deployment
configuration. Do not treat these changes as making the whole platform ready for
public exposure. Review every mounted route, ingress/Kubernetes/Terraform setup,
rate limits, account lifecycle, logs, dependencies and secret history before any
future deployment. RSS prompt delimiters and validation reduce malformed output;
they cannot guarantee semantic resistance to prompt injection. No customer or
production data was used in the agent traces.

Refresh tokens still lack server-side single-use rotation/revocation (`jti` storage).
A stolen refresh token can be replayed until expiry; implement transactional
rotation/reuse detection before exposing authentication to untrusted networks.
This is an explicit remaining deployment blocker, not a completed security fix.
