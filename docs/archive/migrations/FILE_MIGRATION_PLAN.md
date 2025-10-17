# File Migration Plan

## Overview

This document outlines the step-by-step migration plan to reorganize AlphaPulse project files according to the structure defined in [`FILE_STRUCTURE.md`](FILE_STRUCTURE.md).

## Prerequisites

✅ Review [`FILE_STRUCTURE.md`](FILE_STRUCTURE.md)  
✅ Backup current work: `git commit -am "Checkpoint before file migration"`

## Phase 1: Create Directory Structure

### Action Required

Run the following command in the project root:

```bash
mkdir -p config/{dev,prod} \
  docs/{deployment,api} \
  infra/terraform/modules/{s3,ec2,networking} \
  infra/terraform/environments/{dev,prod} \
  infra/k3s/{base,overlays} \
  notebooks/{exploratory,experiments} \
  scripts/{deployment,data,monitoring} \
  src/alphapulse/{api,core,data,ml,monitoring,utils} \
  src/alphapulse/api/{routes,schemas} \
  src/alphapulse/data/{collectors,storage} \
  src/alphapulse/ml/{training,inference} \
  tests/{unit,integration,e2e}
```

### Why?

- **Separation of Concerns**: Clear boundaries between infrastructure, application code, and orchestration
- **Scalability**: Easy to add new modules without cluttering root directory
- **Testability**: Organized test structure supporting unit, integration, and e2e tests

## Phase 2: Move Test Files

### Current State (Problems)

```
.
├── test_reddit.py              # ❌ Root directory
├── test_rss_basic.py           # ❌ Root directory
├── test_rss_news.py            # ❌ Root directory
├── test_rss_pipeline_integration.py  # ❌ Root directory
├── test_rss_simple.py          # ❌ Root directory
└── test_sentiment.py           # ❌ Root directory
```

### Target State

```
tests/
├── unit/
│   └── test_sentiment.py       # Fast, isolated sentiment tests
├── integration/
│   ├── test_reddit.py          # Tests with Reddit API
│   ├── test_rss_basic.py
│   ├── test_rss_news.py
│   ├── test_rss_simple.py
│   └── test_rss_pipeline_integration.py
└── e2e/
    └── (future end-to-end tests)
```

### Commands

```bash
# Move unit tests
mv test_sentiment.py tests/unit/

# Move integration tests
mv test_reddit.py tests/integration/
mv test_rss_basic.py tests/integration/
mv test_rss_news.py tests/integration/
mv test_rss_simple.py tests/integration/
mv test_rss_pipeline_integration.py tests/integration/
```

### Update Test Imports

After moving, you may need to adjust Python import paths if tests reference local modules.

## Phase 3: Relocate Infrastructure Files

### Current State

```
.
└── docker-compose.yml          # ❌ Root directory
```

### Target State

```
infra/
├── docker-compose.yml          # ✅ Infrastructure directory
└── docker/
    ├── Dockerfile.mage
    └── Dockerfile.mlflow
```

### Command

```bash
mv docker-compose.yml infra/
```

### Update References

After moving, update:

- [`Makefile`](../Makefile): Change `docker-compose.yml` references to `infra/docker-compose.yml`
- CI/CD workflows (future): Update paths

## Phase 4: Create Python Package Structure

### Create Core Application Package

```bash
# Create __init__.py files
touch src/alphapulse/__init__.py
touch src/alphapulse/api/__init__.py
touch src/alphapulse/core/__init__.py
touch src/alphapulse/data/__init__.py
touch src/alphapulse/ml/__init__.py
touch src/alphapulse/monitoring/__init__.py
touch src/alphapulse/utils/__init__.py
```

### Create setup.py

Location: [`src/setup.py`](../src/setup.py)

This allows installing the package:

```bash
pip install -e src/
```

## Phase 5: Create README Files

### Directories Needing READMEs

- `config/README.md` - Configuration management guide
- `notebooks/README.md` - Jupyter notebook usage
- `src/README.md` - Application code overview
- `infra/terraform/README.md` - Terraform module documentation

### Purpose

Each README should explain:

1. **What** the directory contains
2. **Why** it's structured this way
3. **How** to use/modify files in it

## Phase 6: Update Root Documentation

### Files to Update

1. [`README.md`](../README.md) - Add "Project Structure" section
2. [`Makefile`](../Makefile) - Update paths (docker-compose, test commands)
3. [`.gitignore`](../.gitignore) - Add new directories to ignore patterns

## Phase 7: Verification

### Test Suite

```bash
# Run tests from new locations
python -m pytest tests/unit/
python -m pytest tests/integration/
```

### Docker Compose

```bash
# Verify Docker Compose still works
cd infra
docker-compose up -d
docker-compose ps
docker-compose down
```

### Structure Visualization

```bash
tree -L 3 -d
```

## Rollback Plan

If issues occur during migration:

```bash
# Revert to previous commit
git reset --hard HEAD~1

# Or restore specific files
git checkout HEAD~1 -- <file_path>
```

## Post-Migration Tasks

- [ ] Update all documentation links
- [ ] Run full test suite
- [ ] Update CI/CD configuration
- [ ] Review and update [`.rooignore`](../.rooignore)
- [ ] Team announcement about new structure

## Timeline

| Phase                        | Estimated Time | Risk Level |
| ---------------------------- | -------------- | ---------- |
| Phase 1: Create Directories  | 1 minute       | Low        |
| Phase 2: Move Tests          | 5 minutes      | Low        |
| Phase 3: Move Infrastructure | 2 minutes      | Medium     |
| Phase 4: Python Package      | 10 minutes     | Medium     |
| Phase 5: Documentation       | 30 minutes     | Low        |
| Phase 6: Update Root Docs    | 15 minutes     | Low        |
| Phase 7: Verification        | 10 minutes     | Low        |
| **Total**                    | **~1.5 hours** | -          |

## Questions?

**Q: Will this break existing Mage pipelines?**  
A: No. [`mage_pipeline/`](../mage_pipeline/) directory remains unchanged.

**Q: Do we need to update database connections?**  
A: No. Connection strings are environment-variable based.

**Q: When should we do this?**  
A: During a development phase, not right before production deployment.

## Next Steps

1. ✅ Review this plan with the team
2. 🔄 Switch to **Code mode** to execute the migration
3. 🔄 Run verification tests
4. ✅ Commit changes with clear message: `refactor: reorganize project structure`

---

**Last Updated**: 2026-01-10  
**Approved By**: Pending Review
