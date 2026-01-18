# ADR-006: Backend-First Strategy - Pivot from MLOps to Infrastructure Engineering

## Status

**Accepted** | Date: 2026-01-10

## Context

### The Professional Positioning Problem

The project was initially positioned as an "MLOps Platform" targeting MLOps Engineer roles. However, this positioning creates several challenges:

1. **Competition Landscape**: MLOps roles attract PhDs and Data Scientists with deep ML expertise
2. **Value Proposition Mismatch**: The user's core strength is **DevOps/Infrastructure** (Terraform, AWS), not advanced ML algorithms
3. **Career Goal Misalignment**: Target is **Backend/Infrastructure Engineer at Fintech** companies, not ML-focused roles
4. **Certification Path**: Currently preparing for **Terraform Associate Certification**

### The Strategic Insight

**What Fintech Companies Actually Need**:

- Reliable, auditable infrastructure
- Type-safe financial APIs (Decimal precision, not Float)
- Cost-optimized cloud architecture
- Automated deployment pipelines
- NOT: Cutting-edge ML models or feature engineering research

**What DevOps→Backend Engineers Demonstrate Best**:

- Infrastructure as Code (IaC) proficiency
- Production-grade API design
- CI/CD automation
- System reliability engineering
- NOT: Advanced statistical modeling or algorithm development

## Decision

We pivot the project positioning from **"MLOps Platform"** to **"Backend Infrastructure for Algorithmic Trading Systems"**.

### Three Pillars of Differentiation

#### Pillar 1: Infrastructure as Code (IaC) Mastery 🏛️

**Goal**: Prove ability to manage cloud resources professionally using Terraform.

**Implementation**:

- **Terraform is P0 Priority**: Day 1 focus, not "nice to have"
- **Modular Structure**: `modules/networking`, `modules/compute`, `modules/database`
- **Pragmatic Architecture**: Docker Compose on EC2 (not K8s overengineering)

**Why This Works**:

- Aligns with Terraform certification preparation
- Demonstrates "Simple Architecture for Simple Scale" judgment
- Shows IaC skills that 80% of ML Engineers lack

**Interview Value**:

> "I can nuke and rebuild the entire environment in 10 minutes using Terraform."

#### Pillar 2: Fintech-Grade API Design 💳

**Goal**: Prove understanding of financial system constraints.

**Critical Implementation Details**:

```python
# ❌ WRONG: Float causes precision errors
price: float = 19.99

# ✅ CORRECT: Decimal for financial calculations
from decimal import Decimal
price: Decimal = Decimal("19.99")
```

**Why This Single Detail Matters**:

- Floating-point errors are **unacceptable in Fintech**
- This detail alone sets candidates apart in interviews
- Shows domain-specific engineering maturity

**Additional Requirements**:

- `/health` endpoint for Load Balancer integration
- Pydantic models with strict type validation
- Auto-generated Swagger/OpenAPI documentation (`/api/docs`)

**Interview Value**:

> "I enforce Decimal types for all monetary values because floating-point arithmetic can cause precision errors—critical in financial systems."

#### Pillar 3: DevOps Maturity & Automation ⚙️

**Goal**: Prove system is "Production Ready" and automated.

**Implementation**:

- **CI/CD is Mandatory**: GitHub Actions on every PR
- **Automated Checks**: pytest, black (linting), terraform fmt
- **Shift Left Mentality**: Quality checks before merge

**Terminology Correction**:

- ❌ "Feature Store" (implies Feast, overkill for solo project)
- ✅ "Reproducible Feature Pipeline" (accurate and impressive)

**Why This Works**:

- Demonstrates "Shift Left" quality mindset
- Shows automated testing culture
- Proves production-readiness beyond "works on my machine"

**Interview Value**:

> "Every PR runs automated tests and infrastructure validation—we catch issues before deployment."

## Consequences

### Positive

1. **Clear Competitive Positioning**:

   - Competing with **Backend Engineers**, not ML PhDs
   - Leveraging existing DevOps strengths
   - Targeting companies that need infrastructure, not research

2. **Terraform Certification Synergy**:

   - Project work directly supports certification prep
   - Real-world IaC portfolio piece
   - Interview talking point alignment

3. **Fintech Domain Credibility**:

   - Decimal vs Float detail shows domain understanding
   - Type-safe API design demonstrates production awareness
   - Cost optimization ($11/month) shows business acumen

4. **Clearer Interview Narrative**:

   - **Before**: "I'm learning MLOps..." (defensive)
   - **After**: "I build reliable infrastructure for financial systems" (confident)

5. **Realistic Scope**:
   - Docker Compose on EC2 (not K8s overengineering)
   - Demonstrates pragmatic engineering judgment
   - Easier to explain and defend in interviews

### Negative

1. **Less "ML Hype"**:

   - Project may seem less "cutting-edge" to ML-focused companies
   - **Mitigation**: We're targeting **Backend/Infrastructure roles**, not ML roles

2. **De-emphasizing Model Accuracy**:

   - Less focus on feature engineering and model performance
   - **Mitigation**: We still have ML components, but they're not the hero

3. **Terraform Learning Curve**:
   - Requires mastering IaC concepts for certification
   - **Mitigation**: Aligns with career goals and certification prep

## Alternatives Considered

### Alternative 1: Keep MLOps Focus ❌

**Pros**:

- Trendy, buzzword-heavy positioning
- Attractive to ML-focused companies

**Cons**:

- Competing against PhDs with stronger ML backgrounds
- Mismatch with user's DevOps/Infrastructure core strength
- Doesn't align with Terraform certification path

**Verdict**: **Rejected** - Playing to weaknesses, not strengths

### Alternative 2: Full-Stack Engineer Positioning ❌

**Pros**:

- Broader job market appeal
- Could showcase React/Frontend skills

**Cons**:

- Dilutes infrastructure specialization
- Harder to compete without deep frontend expertise
- Doesn't leverage DevOps background

**Verdict**: **Rejected** - Too generic, loses specialization advantage

### Alternative 3: Data Engineer Positioning ❌

**Pros**:

- Related to data pipelines (Apache Airflow)
- Growing job market

**Cons**:

- Requires different skill emphasis (Spark, Kafka, etc.)
- Less aligned with Terraform/AWS strengths
- Overlaps with ML pipeline engineering

**Verdict**: **Rejected** - Not the primary target role

## Implementation Plan

### Phase 1: Documentation Refactor (Week 1)

1. **Update README.md**:

   - Hero section: "Backend Infrastructure for Algorithmic Trading Systems"
   - Reorder tech stack: Terraform > FastAPI > Docker > GitHub Actions
   - Highlight: IaC, Type-Safe API, Cost Optimization

2. **Create ADR-006**: This document

3. **Update PLAN.md**: New Week 1-4 roadmap with Terraform-first approach

4. **Create Interview Talking Points**: `docs/interview/TALKING_POINTS.md`

### Phase 2: Infrastructure Foundation (Week 1 Implementation)

**Priority Tasks**:

1. Terraform module structure setup
2. AWS provider configuration
3. EC2 instance provisioning
4. Docker Compose deployment via Terraform
5. GitHub Actions CI/CD pipeline

**Success Criteria**:

- [ ] Can provision entire infrastructure with `terraform apply`
- [ ] Can destroy and recreate in < 10 minutes
- [ ] GitHub Actions runs on every PR

### Phase 3: Backend API Development (Week 2)

**Priority Tasks**:

1. FastAPI project setup with Pydantic models
2. **Decimal type enforcement** for all financial values
3. `/health` endpoint implementation
4. Auto-generated OpenAPI documentation
5. Unit tests with pytest

**Success Criteria**:

- [ ] All monetary values use Decimal (not Float)
- [ ] API passes type checking (mypy)
- [ ] 80%+ test coverage

### Phase 4: Data Pipeline Integration (Week 3)

**Priority Tasks**:

1. PostgreSQL schema with Terraform
2. Apache Airflow DAG for data ingestion
3. "Reproducible Feature Pipeline" (not "Feature Store")
4. Integration tests

**Success Criteria**:

- [ ] Data pipeline runs automatically
- [ ] Feature reproducibility validated
- [ ] End-to-end tests passing

### Phase 5: Documentation & Demo (Week 4)

**Priority Tasks**:

1. Architecture diagrams (infrastructure focus)
2. Interview talking points refinement
3. Demo video/screenshots
4. Cost analysis documentation

**Success Criteria**:

- [ ] Can demo system in < 5 minutes
- [ ] Clear infrastructure-first narrative
- [ ] Portfolio-ready documentation

## Updated Technology Stack Priority

### Tier 1: Core Infrastructure (P0)

- **Terraform**: IaC, certification preparation
- **AWS EC2 + VPC**: Cloud infrastructure
- **Docker Compose**: Container orchestration
- **GitHub Actions**: CI/CD automation

### Tier 2: Backend Services (P1)

- **FastAPI**: Type-safe API with Decimal support
- **PostgreSQL**: Relational database
- **Pydantic**: Data validation

### Tier 3: Data Pipeline (P2)

- **Apache Airflow**: Workflow orchestration
- **Python**: Data processing

### Tier 4: ML Components (P3 - Supporting Role)

- **MLflow**: Experiment tracking (optional)
- **Ollama**: Local LLM (optional)
- **pandas-ta**: Technical indicators

**Key Shift**: ML components are **supporting infrastructure**, not the hero.

## Interview Narrative Transformation

### Before (MLOps Focus)

**Question**: "What does your project do?"

> "I built an MLOps platform for cryptocurrency trading signals using sentiment analysis..."

**Interviewer Reaction**: 😐 "Why should we hire you over a PhD in ML?"

### After (Backend-First Focus)

**Question**: "What does your project do?"

> "I built a cost-optimized backend infrastructure for financial trading signals. The system uses Terraform for reproducible deployments, enforces Decimal precision for financial calculations, and includes automated CI/CD. Total production cost: $11/month—95% cheaper than traditional architectures."

**Interviewer Reaction**: 🤩 "Tell me about your Terraform setup and cost optimization strategy!"

## Risk Mitigation

### Risk 1: "Too Simple" Perception

**Risk**: Docker Compose might seem less impressive than Kubernetes.

**Mitigation**:

- Frame as **pragmatic engineering judgment**
- "Simple Architecture for Simple Scale"
- Demonstrate **when NOT to use K8s**

**Interview Response**:

> "I chose Docker Compose over Kubernetes because the system is batch-processing with daily jobs, not high-throughput microservices. K8s would add operational overhead without commensurate benefits. This shows engineering judgment—knowing when NOT to overengineer."

### Risk 2: Missing Advanced ML Features

**Risk**: Project may seem "basic" to ML-focused reviewers.

**Mitigation**:

- **Target audience is Backend/Infrastructure roles**, not ML roles
- ML components are present but not hero
- Focus on infrastructure reliability

**Interview Response**:

> "I'm applying for a Backend Engineer role, not ML Engineer. The ML components demonstrate I can integrate with data science teams, but my core value is building reliable infrastructure that ML models depend on."

### Risk 3: Terraform Certification Not Yet Completed

**Risk**: Project references certification in progress.

**Mitigation**:

- Frame as "In preparation for Terraform Associate Certification"
- Project serves as real-world study case
- Shows proactive learning

**Interview Response**:

> "I'm preparing for the Terraform Associate Certification, and this project serves as my real-world case study. I've implemented modular Terraform structures that follow HashiCorp best practices."

## Success Metrics

### Technical Metrics

- [ ] Terraform apply/destroy cycle < 10 minutes
- [ ] Zero Float types in financial calculations (100% Decimal)
- [ ] CI/CD pipeline passes on every PR
- [ ] API response time < 100ms (p95)

### Career Metrics

- [ ] Clear elevator pitch for Backend/Infrastructure roles
- [ ] Can explain Decimal vs Float in interviews
- [ ] Terraform knowledge validated through certification
- [ ] Portfolio positions for Fintech Backend roles

### Interview Metrics

- [ ] Can whiteboard infrastructure architecture in < 5 minutes
- [ ] Can discuss cost optimization decisions confidently
- [ ] Can explain trade-offs (Docker Compose vs K8s)
- [ ] Can demonstrate CI/CD pipeline live

## References

- **Terraform Best Practices**: https://www.terraform-best-practices.com/
- **FastAPI Production Practices**: https://fastapi.tiangolo.com/deployment/
- **Decimal Arithmetic in Python**: https://docs.python.org/3/library/decimal.html
- **GitHub Actions CI/CD**: https://docs.github.com/en/actions

## Related ADRs

- [ADR-005: MLOps-First Strategy](adr-005-mlops-first-strategy.md) - Superseded by this ADR

---

**Decision Owner**: Lead System Architect  
**Stakeholders**: Career Strategy Team, Portfolio Reviewers  
**Last Reviewed**: 2026-01-10  
**Next Review**: After Terraform Certification completion
