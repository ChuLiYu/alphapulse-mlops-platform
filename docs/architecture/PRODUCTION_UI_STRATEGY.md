# Production Web UI & Access Strategy

## 1. Overview

This document defines the strategy for exposing and securing the Web User Interfaces (UIs) and API endpoints for the AlphaPulse MLOps platform in the production environment (Oracle Cloud + K3s).

**Core Principle**: Minimize resource usage and attack surface by using a **Single Ingress Controller (Traefik)** with **Path-Based Routing** under a single domain.

## 2. Infrastructure & Networking

- **Domain**: `alphapulse.luichu.dev`
- **Ingress Controller**: Traefik (K3s default)
- **Public Ports**: 80 (HTTP), 443 (HTTPS) only.
- **Internal Ports**: All service ports (8080, 5000, 8000) remain closed to the public internet.

## 3. Service Routing Table

| Service | Public URL | Access Level | Description | Ingress Middleware |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | `https://domain.com/` | Public | Main Dashboard for end-users | None |
| **FastAPI** | `https://domain.com/api` | Public* | Backend API (Swagger at `/api/docs`) | None (App handles Auth) |
| **Airflow** | `https://domain.com/airflow` | Admin | Workflow Management DAGs | `admin-auth` (Basic Auth) |
| **MLflow** | `https://domain.com/mlflow` | Admin | Experiment Tracking UI | `admin-auth` (Basic Auth) |

*> Note: specific API endpoints are secured via JWT within the application logic.*

## 4. Implementation Details

### 4.1. Global Security (Middleware)
We utilize Traefik Middleware to enforce authentication at the gateway level for administrative tools.

- **Resource**: `admin-auth` (defined in `infra/k3s/base/auth-middleware.yaml`)
- **Mechanism**: Basic Authentication (username/password stored in Kubernetes Secret `admin-credentials`).
- **Applied to**: Airflow, MLflow.

### 4.2. Service Configuration Requirements

To support path-based routing (Sub-path support), specific configurations are required for each service to prevent "404 Not Found" errors on static assets (CSS/JS).

#### A. Airflow
- **Config**: `airflow.cfg` or Environment Variable.
- **Setting**: `AIRFLOW__WEBSERVER__BASE_URL = https://alphapulse.luichu.dev/airflow`
- **Status**: ✅ Already configured in `infra/k3s/base/airflow.yaml`.

#### B. FastAPI
- **Config**: Application Initialization (`src/main.py`).
- **Setting**: `app = FastAPI(root_path="/api")`
- **Action Required**: Update `src/alphapulse/app.py` or `main.py` to read `ROOT_PATH` env var.

#### C. MLflow
- **Config**: Environment Variable / Command Args.
- **Issue**: MLflow UI is notoriously difficult to host under a subpath without extensive reverse-proxy rewriting.
- **Strategy**:
    1. Attempt to set `MLFLOW_TRACKING_URI` and relative static paths.
    2. **Fallback**: If UI breaks, switch MLflow to a subdomain (`mlflow.alphapulse.luichu.dev`) while keeping `admin-auth`.

#### D. Frontend (React/Vite)
- **Config**: Nginx (`nginx.conf`) + Vite Base (`vite.config.ts`).
- **Setting**: Hosted at root `/`, so standard configuration applies.
- **Routing**: Ensure Nginx `try_files $uri /index.html` handles client-side routing correctly.

## 5. Deployment Checklist

1.  [ ] **DNS**: Point `alphapulse.luichu.dev` (A Record) to Oracle VM Public IP.
2.  [ ] **Secrets**: Create `admin-credentials` secret in K3s.
    ```bash
    htpasswd -nb admin <PASSWORD> | base64
    # Create Secret YAML
    ```
3.  [ ] **FastAPI Update**: Modify code to accept `root_path`.
4.  [ ] **Ingress Resources**:
    - Apply `frontend-ingress` (Root).
    - Apply `airflow-ingress` (Path: `/airflow`, Middleware: `admin-auth`).
    - Create/Apply `mlflow-ingress` (Path: `/mlflow`, Middleware: `admin-auth`).
    - Create/Apply `api-ingress` (Path: `/api`, RewriteTarget might be needed via Middleware `StripPrefix` if app doesn't handle `root_path`).

## 6. Maintenance

- **Certificate Management**: Use `cert-manager` (if installed) or manually manage TLS secrets for HTTPS.
- **Logs**: Monitor Traefik access logs to audit access to Admin endpoints.
