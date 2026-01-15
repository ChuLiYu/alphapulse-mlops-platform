# AlphaPulse Production Deployment Checklist (v2.0 - Oracle Cloud Edition)

## Overview

This checklist ensures all components are ready for production deployment to the **Oracle Cloud Always Free** infrastructure (ARM64 + K3s).

**Core Goal**: Zero Cost Operation ($0.00/month)
**Architecture**: Single Node K3s on VM.Standard.A1.Flex (4 OCPU, 24GB RAM)

## Pre-Deployment Verification

### ✅ 1. Local Environment & Artifacts

- [x] Local environment migrated to OrbStack (macOS)
- [x] Docker images built for `linux/arm64` architecture
- [x] **Base Images optimized**:
  - [x] MLflow: `python:3.12-slim` (Locked version)
  - [x] Trainer: Multi-stage build (No build tools in runtime)
  - [x] Frontend: Nginx Alpine
  - [x] FastAPI: `python:3.12-slim` (Code imports fixed)
- [x] Local K3s cluster operational with all services running
- [x] API Health Check passed (`/health` returns 200 OK)

### 🟡 2. Infrastructure as Code (Terraform)

- [x] **Provider Switch**: Replaced `hcloud`/`aws` with `oci` provider
- [x] **Networking**: VCN, Public Subnet, Security Lists (Port 80/443/22/6443) defined
- [x] **Compute**: `VM.Standard.A1.Flex` resource defined with Cloud-init
- [x] **Storage**: OCI Object Storage bucket defined (replacing S3)
- [ ] `terraform validate` passed on `infra/terraform/environments/prod`
- [ ] OCI Credentials (`tfvars`) prepared

### 🟡 3. Kubernetes Manifests (K3s)

- [x] Base Kustomization structure created (`infra/k3s/base`)
- [x] Services defined: Frontend, FastAPI, MLflow, Trainer, Airflow, Postgres
- [x] Ingress Route defined (Traefik)
- [ ] **Resource Limits**: Memory requests/limits tuned for 24GB RAM capacity
- [ ] **Secrets Management**: Database passwords and API keys converted to K8s Secrets

### 🟡 4. CI/CD Pipeline (GitHub Actions)

- [ ] **Build Workflow**: Update to build/push `linux/arm64` images to GHCR/OCIR
- [ ] **Deploy Workflow**: SSH action to execute `helm upgrade` or `kubectl apply` on Oracle VM
- [ ] **Secret Injection**: GitHub Secrets configured for OCI keys

## Deployment Steps

### Phase 1: Infrastructure Provisioning (Terraform)

1. **Initialize Terraform**
   ```bash
   cd infra/terraform/environments/prod
   terraform init
   ```

2. **Apply Infrastructure**
   ```bash
   terraform apply -var-file="prod.tfvars"
   ```

3. **Verify Connectivity**
   - [ ] SSH into Oracle instance: `ssh opc@<public-ip>`
   - [ ] Check K3s status: `kubectl get nodes`

### Phase 2: Cluster Setup (On Oracle VM)

1. **K3s Installation (Automated via Cloud-init)**
   - [ ] Verify K3s service is running
   - [ ] Verify `iptables` rules allow traffic

2. **Namespace & Registry Secret**
   ```bash
   kubectl create namespace alphapulse
   # If using GHCR/Private Registry
   kubectl create secret docker-registry regcred ...
   ```

### Phase 3: Service Deployment (GitOps/Manual)

1. **Deploy Stack**
   ```bash
   kubectl apply -k infra/k3s/base
   ```

2. **Verify Pod Status**
   ```bash
   kubectl get pods -n alphapulse -w
   ```
   - [ ] All pods `Running` or `Completed`

### Phase 4: Data & State Initialization

1. **Database Migration**
   - [ ] Airflow DB initialized (Auto)
   - [ ] MLflow DB initialized (Auto)
   - [ ] Application DB migration (alembic upgrade head)

2. **Ingress Verification**
   - [ ] Public IP accessible via HTTP/HTTPS
   - [ ] SSL Certificates provisioned (Cert-Manager)

## Post-Deployment Verification

### Service Health Checks

- [ ] **Frontend**: `http://<public-ip>` (Loads UI)
- [ ] **FastAPI**: `http://<public-ip>/api/health`
- [ ] **MLflow**: `http://<public-ip>/mlflow`
- [ ] **Trainer**: `http://<public-ip>/trainer/health` (Internal only?)

### Security Validation

- [ ] **Firewall**: Only ports 80/443/22 open to public (6443 restricted to Admin IP)
- [ ] **Database**: Port 5432 **NOT** accessible publicly
- [ ] **HTTPS**: Valid TLS certificate active

## Cost Monitoring (Zero Cost)

- [ ] **Compute**: 4 OCPUs, 24GB RAM (Always Free Eligible)
- [ ] **Storage**: Block Volume < 200GB, Object Storage < 20GB
- [ ] **Network**: Outbound traffic < 10TB/month

---

**Last Updated**: 2026-01-14
**Version**: 2.0 (Oracle Cloud Migration)
**Owner**: AlphaPulse DevOps Team