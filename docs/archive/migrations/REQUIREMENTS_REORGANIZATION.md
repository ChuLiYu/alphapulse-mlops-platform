# Requirements File Reorganization

## ✅ Completed Optimizations

In accordance with best practices, dependency configuration files have been reorganized into their respective directories, using the standard `requirements.txt` filename.

### File Structure Changes

#### Before ❌

```
alphapulse-mlops-platform/
├── requirements-training.txt         # At root directory
└── mage_pipeline/
    ├── requirements.txt              # Mixed dependencies (Old)
    └── requirements-mage.txt         # ETL specific (New)
```

#### After ✅

```
alphapulse-mlops-platform/
├── training/
│   └── requirements.txt             # Training specific dependencies
└── mage_pipeline/
    └── requirements.txt             # ETL specific dependencies
```

### Advantages

1. **Standardization**: Uses the standard `requirements.txt` filename.
2. **Modularity**: Each module has its own dependency file.
3. **Clarity**: File locations are intuitive and easy to understand.
4. **Docker Friendly**: Aligns with Docker build conventions.

### Dockerfile References

#### Mage Container

```dockerfile
COPY mage_pipeline/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
```

#### Training Container

```dockerfile
COPY training/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
```

### Dependency Contents

#### training/requirements.txt (Training Specific)

- torch, xgboost, lightgbm
- mlflow, optuna, evidently
- fastapi, uvicorn (API Server)
- scikit-learn, pandas, numpy

#### mage_pipeline/requirements.txt (ETL Specific)

- yfinance, feedparser (Data collection)
- transformers, torch (Sentiment analysis)
- pandas, sqlalchemy (Data processing)
- boto3, minio (Storage)

### Documentation Updates

All relevant documentation has been automatically updated, including:

- ✅ docs/CONTAINER_SEPARATION_GUIDE.md
- ✅ docs/REFACTOR_SUMMARY.md
- ✅ docs/REFACTOR_COMPLETE_REPORT.md
- ✅ docs/VALIDATION_CHECKLIST.md
- ✅ CONTAINER_QUICKSTART.md
- ✅ CHANGELOG_CONTAINER_SEPARATION.md

### Verification

```bash
# Verify file existence
ls -l training/requirements.txt
ls -l mage_pipeline/requirements.txt

# Verify Dockerfile references
grep "requirements" infra/docker/Dockerfile.trainer
grep "requirements" infra/docker/Dockerfile.mage
```

### Backward Compatibility

- ✅ Legacy backup files have been cleaned up.
- ✅ Dockerfiles have been updated.
- ✅ Documentation has been synchronized.
- ✅ No additional migration steps required.

---

**Last Updated**: 2026-01-11  
**Impact**: File path changes, functionality remains unchanged.  
**Action**: Rebuild containers to apply changes.