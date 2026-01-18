# Decimal Migration Strategy for Financial Data

## Overview

This document outlines the strategy for migrating from Float to Decimal types for all financial data in the AlphaPulse platform, as mandated by Fintech best practices and ADR-006.

## Why Decimal Over Float?

- **Financial Precision**: Floating-point errors are unacceptable in financial systems (e.g., 0.1 + 0.2 ≠ 0.3 in Float)
- **Exact Decimal Representation**: Decimal provides exact representation of decimal numbers
- **Regulatory Compliance**: Financial systems require precise calculations for audit trails
- **Domain Knowledge**: Demonstrates Fintech engineering maturity

## Current State Analysis

### Files Using Float Types

#### 1. Database Schema (`create_feature_table.py`)

- **Location**: `airflow/plugins/alphapulse_utils/feature_integrator.py`
- **Float Columns**: 67+ columns using `FLOAT` type
- **Impact**: High - affects all stored financial data

#### 2. Technical Indicators Calculation (`calculate_technical_indicators.py`)

- **Location**: `airflow/plugins/alphapulse_utils/indicators.py`
- **Float Usage**: pandas-ta returns float64 values
- **Impact**: Medium - calculation outputs need Decimal conversion

#### 3. Feature Pipeline Files

- `calculate_news_frequency_features.py`
- `calculate_sentiment_features.py`
- `calculate_interaction_features.py`
- All use float for intermediate calculations

## Migration Strategy

### Phase 1: Database Schema Migration

**Objective**: Update PostgreSQL schema from FLOAT to DECIMAL/NUMERIC

#### Steps:

1. **Create Migration Scripts**:

   - Use Alembic for database migrations
   - Create migration to change column types
   - Preserve existing data with type casting

2. **Column Type Mapping**:

   - `FLOAT` → `DECIMAL(20, 8)` for price data (supports up to 999,999,999.99999999)
   - `FLOAT` → `DECIMAL(10, 6)` for percentages and ratios
   - `FLOAT` → `DECIMAL(10, 4)` for sentiment scores (-1.0000 to 1.0000)

3. **Backward Compatibility**:
   - Maintain API compatibility during transition
   - Use database views for legacy applications
   - Gradual rollout with feature flags

### Phase 2: Python Code Migration

**Objective**: Replace float usage with Decimal in Python code

#### Steps:

1. **Import Decimal Type**:

   ```python
   from decimal import Decimal, ROUND_HALF_UP
   ```

2. **Update Data Processing**:

   - Convert pandas DataFrames to use Decimal
   - Update pandas-ta integration to return Decimal
   - Modify feature calculations to use Decimal arithmetic

3. **Configuration**:
   - Set Decimal precision globally
   - Define rounding policies (ROUND_HALF_UP for financial)

### Phase 3: API Layer Migration

**Objective**: Update FastAPI models and responses

#### Steps:

1. **Pydantic Models**:

   - Use `condecimal` for Decimal validation
   - Define precision constraints in schemas

2. **Response Serialization**:
   - Ensure Decimal serialization to JSON strings
   - Maintain API contract compatibility

## Technical Implementation Details

### Database Migration Example

```python
# Before
from sqlalchemy.dialects.postgresql import FLOAT

Column('close', FLOAT)

# After
from sqlalchemy import DECIMAL

Column('close', DECIMAL(20, 8))
```

### Python Decimal Usage

```python
from decimal import Decimal, getcontext

# Set precision
getcontext().prec = 28  # Standard Decimal precision

# Decimal arithmetic
price = Decimal('40000.50')
change = Decimal('0.025')  # 2.5%
new_price = price * (Decimal('1') + change)
```

### Pandas Integration

```python
import pandas as pd
from decimal import Decimal

# Convert DataFrame columns to Decimal
df['close'] = df['close'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00000001')))
```

## Migration Timeline

### Week 1: Planning & Preparation

- [ ] Create detailed migration plan
- [ ] Set up test environment
- [ ] Create backup strategy

### Week 2: Database Migration

- [ ] Create Alembic migration scripts
- [ ] Test migration on staging
- [ ] Update database schema

### Week 3: Code Migration

- [ ] Update feature pipeline calculations
- [ ] Modify technical indicators to use Decimal
- [ ] Update API models

### Week 4: Testing & Validation

- [ ] Comprehensive testing
- [ ] Performance benchmarking
- [ ] Rollback testing

## Risk Mitigation

### Technical Risks

1. **Performance Impact**: Decimal operations are slower than float

   - Mitigation: Benchmark and optimize critical paths
   - Consider caching strategies

2. **Data Loss During Migration**:

   - Mitigation: Comprehensive backups
   - Dry-run migrations on test data

3. **API Breaking Changes**:
   - Mitigation: Versioned APIs
   - Gradual rollout with feature flags

### Business Risks

1. **Downtime During Migration**:
   - Mitigation: Schedule during low-traffic periods
   - Use blue-green deployment

## Success Criteria

### Technical

- [ ] Zero Float types in financial code
- [ ] All database columns use DECIMAL/NUMERIC
- [ ] API responses use Decimal precision
- [ ] No regression in calculation accuracy

### Business

- [ ] No data loss during migration
- [ ] Acceptable performance impact (<10% slowdown)
- [ ] Backward compatibility maintained

## Testing Strategy

### Unit Tests

- Test Decimal arithmetic correctness
- Verify precision preservation
- Test edge cases (very large/small numbers)

### Integration Tests

- End-to-end pipeline with Decimal data
- Database migration and rollback
- API contract validation

### Performance Tests

- Benchmark before/after migration
- Load testing with Decimal operations
- Memory usage comparison

## Rollback Plan

If issues arise:

1. **Immediate Rollback**: Revert database migration
2. **Code Rollback**: Switch back to float-based code
3. **Data Recovery**: Restore from backups

## Documentation Updates Required

1. **API Documentation**: Update with Decimal precision
2. **Database Schema**: Document new column types
3. **Developer Guide**: Decimal usage patterns
4. **Migration Guide**: Step-by-step instructions

## Cost Considerations

- **Development Time**: 4 weeks for full migration
- **Testing Resources**: Additional QA cycles
- **Infrastructure**: No additional costs
- **Maintenance**: Slightly higher complexity

## Next Steps

1. **Immediate Action**: Create proof-of-concept for Decimal conversion
2. **Short-term**: Update `create_feature_table.py` with DECIMAL types
3. **Medium-term**: Migrate technical indicators calculation
4. **Long-term**: Full system migration

---

**Last Updated**: 2026-01-10  
**Owner**: Backend Infrastructure Team  
**Status**: Planning Phase  
**Priority**: P1 (Week 2 per current_task.md)
