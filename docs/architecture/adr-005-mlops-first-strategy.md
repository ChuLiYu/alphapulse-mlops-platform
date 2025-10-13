# ADR-005: MLOps-First Strategy - Leveraging Libraries for Technical Indicators

## Status

**Accepted** | Date: 2026-01-10

## Context

As an **MLOps Engineer** (not a quantitative analyst or financial engineer), we need to clarify where to invest development effort. The original plan included implementing technical indicators (RSI, MACD, Bollinger Bands) from scratch, which conflicts with our core professional positioning.

### Key Questions

1. **Should we reimplement well-established technical indicators?**
2. **Where does an MLOps engineer create differentiated value?**
3. **How do we demonstrate the right skill set for MLOps roles?**

### Professional Context

- **Target Role**: MLOps Engineer at HFT/FinTech firms
- **Core Competencies Expected**: Pipeline orchestration, experiment tracking, feature versioning, model deployment, drift monitoring
- **Not Expected**: Reimplementing standard financial indicators (that's a quant's job)

## Decision

We adopt a **three-layer strategy** that clearly separates commodity functionality from differentiated value:

### Layer 1: Technical Indicators → Use `pandas-ta` Library ✅

**Scope**: All standard technical analysis indicators

- Trend: SMA, EMA, WMA, VWAP
- Momentum: RSI, MACD, Stochastic, CCI
- Volatility: Bollinger Bands, ATR, Keltner Channels
- Volume: OBV, Volume SMA, Force Index
- Support/Resistance: Pivot Points, Fibonacci Retracements

**Implementation**:

```python
import pandas_ta as ta

# Single line replaces 50+ lines of custom code
df.ta.rsi(length=14, append=True)
df.ta.macd(fast=12, slow=26, signal=9, append=True)
df.ta.bbands(length=20, std=2, append=True)
```

**Rationale**:

- **Commoditized Functionality**: Technical indicators are well-defined mathematical formulas
- **Battle-Tested Library**: `pandas-ta` has 11,000+ GitHub stars, used in production systems
- **Time Efficiency**: 30 lines of code vs 300+ lines of custom implementation
- **Maintenance Burden**: Let the community maintain and optimize these calculations
- **Interview Perception**: Shows engineering judgment, not "reinventing the wheel"

### Layer 2: Feature Engineering → Custom Development ✨

**Scope**: All proprietary features that create differentiated value

- **Time-Series Features**:
  - Price velocity (rate of change over multiple timeframes)
  - Price acceleration (second derivative)
  - Momentum regime changes (trend direction shifts)
- **Cross-Domain Features**:
  - `sentiment × volatility` (news impact during high volatility)
  - `sentiment × RSI` (contrarian signals)
  - `news_frequency × price_change` (information flow correlation)
- **Statistical Features**:
  - Rolling z-scores (normalized price deviations)
  - Percentile ranks (relative strength over windows)
  - Entropy measures (market uncertainty quantification)
- **Custom Signals**:
  - Fear & Greed Index (composite sentiment measure)
  - News velocity (publishing rate acceleration)
  - Sentiment divergence (news vs price direction mismatch)

**Implementation Location**: [`docs/features/FEATURE_ENGINEERING.md`](../features/FEATURE_ENGINEERING.md)

**Rationale**:

- **This is Where We Add Value**: Creative feature design demonstrates domain knowledge
- **Interview Differentiator**: Shows ability to extract signal from noise
- **Portfolio Centerpiece**: Highlights problem-solving and modeling skills
- **Not Commoditized**: These features are unique to our use case

### Layer 3: MLOps Infrastructure → Core Competency 🚀

**Scope**: End-to-end ML lifecycle management

- **Orchestration**: Mage.ai pipeline design and scheduling
- **Tracking**: MLflow experiment logging and model registry
- **Feature Store**: PostgreSQL-based feature versioning
- **Monitoring**: Evidently AI drift detection
- **Deployment**: FastAPI model serving with Docker
- **Multi-Cloud**: Terraform managing Hetzner + AWS infrastructure

**Rationale**:

- **Job Requirements**: This is what MLOps roles actually require
- **System Design**: Demonstrates architectural thinking
- **Production Experience**: Shows real-world deployment skills
- **Scalability**: Proves understanding of operational concerns

## Consequences

### Positive

1. **Clear Professional Identity**:

   - ✅ "I'm an MLOps engineer who uses industry-standard tools"
   - ❌ "I'm a quant who reimplements RSI from scratch"

2. **Time Reallocation**:

   - **Saved**: 8-10 hours on technical indicator implementation
   - **Invested**: 8-10 hours on advanced feature engineering
   - **Net Benefit**: More impressive portfolio features

3. **Interview Positioning**:

   - **Before**: "I implemented RSI" → Interviewer: "Why not use a library?"
   - **After**: "I used pandas-ta and focused on custom sentiment×price features" → Interviewer: "That shows good engineering judgment"

4. **Maintenance Reduction**:

   - No need to maintain/test/debug technical indicator calculations
   - Community-driven updates for `pandas-ta`
   - Focus maintenance on our unique features

5. **Portfolio Quality**:
   - Demonstrates **when to build vs buy** decision-making
   - Shows domain knowledge through custom features
   - Highlights MLOps skills (not quant skills)

### Negative

1. **Dependency Risk**: Relies on `pandas-ta` library maintenance
   - **Mitigation**: Pin version, library is mature (v0.3.14b) and widely adopted
2. **Less Code to Show**: Fewer lines of custom indicator code
   - **Mitigation**: More impressive custom feature engineering code instead
3. **Learning Opportunity**: Don't learn indicator implementation details
   - **Mitigation**: Focus learning on MLOps-specific skills instead

## Alternatives Considered

### Alternative 1: Implement All Indicators from Scratch ❌

**Pros**:

- Full control over calculations
- Deep understanding of indicator mathematics
- More lines of code to showcase

**Cons**:

- 10+ hours of development time for commodity functionality
- Ongoing maintenance burden (bug fixes, optimization)
- Reinventing the wheel (poor engineering judgment signal)
- Wrong skill set demonstration for MLOps roles
- Potential calculation errors vs battle-tested libraries

**Verdict**: **Rejected** - Poor time investment, wrong professional positioning

### Alternative 2: Use Multiple Libraries (TA-Lib, pandas-ta, etc.) ❌

**Pros**:

- Access to more indicators
- Flexibility in implementation

**Cons**:

- Dependency complexity (TA-Lib requires C compilation)
- Inconsistent APIs across libraries
- Maintenance burden tracking multiple dependencies

**Verdict**: **Rejected** - `pandas-ta` covers 130+ indicators, sufficient for our needs

### Alternative 3: Cloud-Based Indicator APIs (Alpha Vantage, etc.) ❌

**Pros**:

- Zero calculation overhead
- Professional-grade data

**Cons**:

- Monthly API costs ($50-200)
- Rate limiting
- Vendor lock-in
- Conflicts with "zero-cost development" goal

**Verdict**: **Rejected** - Violates cost optimization strategy

## Implementation Plan

### Week 2 Revised Tasks

1. **Replace Technical Indicator Block** (1 hour):

   ```python
   # File: mage_pipeline/pipelines/btc_price_pipeline/calculate_technical_indicators.py
   # Before: 300+ lines of custom implementation
   # After: 30 lines using pandas-ta

   import pandas_ta as ta
   df.ta.rsi(length=14, append=True)
   df.ta.macd(fast=12, slow=26, signal=9, append=True)
   df.ta.bbands(length=20, std=2, append=True)
   df.ta.atr(length=14, append=True)
   df.ta.sma(length=20, append=True)
   ```

2. **Develop Custom Feature Engineering** (6-8 hours):

   - Create [`docs/features/FEATURE_ENGINEERING.md`](../features/FEATURE_ENGINEERING.md) specification
   - Implement time-series features (velocity, acceleration)
   - Implement interaction features (sentiment × technical)
   - Implement statistical features (z-score, percentiles)
   - Unit tests for custom features

3. **Update Documentation** (2 hours):
   - Update [`README.md`](../../README.md) to emphasize MLOps focus
   - Update [`PLAN.md`](../../PLAN.md) with revised Week 2-3 timeline
   - Create this ADR to document decision

### Success Criteria

- [ ] `pandas-ta` integrated into technical indicator calculation
- [ ] At least 5 custom features implemented and documented
- [ ] Feature engineering specifications in [`docs/features/FEATURE_ENGINEERING.md`](../features/FEATURE_ENGINEERING.md)
- [ ] Documentation clearly positions project as MLOps (not quant) showcase

## References

- **pandas-ta Documentation**: https://github.com/twopirllc/pandas-ta
- **Technical Indicators Reference**: https://www.investopedia.com/trading/technical-analysis/
- **MLOps Principles**: https://ml-ops.org/content/mlops-principles
- **Feature Engineering Best Practices**: https://www.featurestore.org/

## Related ADRs

- [ADR-003: Training Hardware Evaluation](adr-003-training-hardware-evaluation.md)
- [ADR-004: Testing Framework Strategy](adr-004-testing-framework-strategy.md)

---

**Decision Owner**: MLOps Architect  
**Stakeholders**: Portfolio Reviewers, Interview Panel  
**Last Reviewed**: 2026-01-10  
**Next Review**: After Week 2 implementation
