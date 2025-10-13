# ADR-007: Cross-Cloud Abstraction Strategy - Low-Cost Implementation

## Status

**Proposed** | Date: 2026-01-10

## Context

### The Portfolio Requirement

To maximize appeal for Senior Backend and Infrastructure roles, the portfolio needs to demonstrate **"Cross-Cloud"** capabilities. However, the project has strict constraints:

1.  **Cost Minimization**: Cannot run parallel infrastructure on multiple clouds.
2.  **Complexity budget**: Cannot maintain two completely divergent codebases.

### The Problem

Current implementation targets AWS EC2 only. Simply duplicating the setup for GCP/Azure violates the "DRY" (Don't Repeat Yourself) principle and increases maintenance overhead.

## Decision

We will implement a **"Polymorphic Infrastructure"** pattern using Terraform Modules to achieve Cross-Cloud capability.

### 1. Unified Service Interface

We define a standard "Compute Module Interface" that both AWS and GCP implementations must satisfy:

```hcl
# Interface Contract
variable "instance_type" {}
variable "docker_image" {}
variable "environment" {}

output "public_ip" {}
output "instance_id" {}
```

### 2. Provider-Agnostic Abstraction

We will create a root-level `main.tf` that switches providers based on a variable, rather than separate directory trees for each cloud.

```hcl
# main.tf
module "compute" {
  source = var.cloud_provider == "aws" ? "./modules/compute/aws" : "./modules/compute/gcp"
  
  # ... shared variables
}
```

*Note: Terraform limitation requires specific handling for dynamic source, so we may use separate environment folders (`environments/aws-dev` vs `environments/gcp-dev`) that consume the shared modules.*

### 3. Implementation Scope

*   **Primary Cloud**: AWS (Production & Development)
*   **Secondary Cloud**: GCP (Skeleton Implementation)
    *   We will implement the *Terraform modules* for GCP (Compute Engine).
    *   We will **NOT** run the GCP stack permanently.
    *   **Verification**: We will verify the GCP stack *once* to prove it works, then destroy it.

## Consequences

### Positive

1.  **Portfolio Value**: Demonstrates "Cloud Agnostic Design" patterns, a senior-level skill.
2.  **Zero Recurring Cost**: We only pay for the cloud we are currently using (AWS).
3.  **Interview Narrative**: "I designed the system to be portable. I can deploy to GCP by changing one variable."

### Negative

1.  **Initial Effort**: Requires writing Terraform for Compute Engine and VPC on GCP.
2.  **Testing Overhead**: Needs manual verification on GCP to ensure the code actually works.

## Alternatives Considered

### Multi-Cloud Active-Active ❌
Running app on AWS and DB on GCP.
**Verdict**: Rejected. High latency, high egress costs, unnecessary complexity.

### Kubernetes Federation ❌
Using K8s to abstract the cloud.
**Verdict**: Rejected. Violates ADR-006 (Simple Architecture). $70+/mo cost.

## Compliance

*   **Cost**: Consistent with $12/mo budget (only one cloud active at a time).
*   **Backend-First**: Focuses on IaC abstraction, not application logic.