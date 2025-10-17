# Architecture Decision Records (ADR)

## Purpose

This directory contains Architecture Decision Records (ADRs) documenting significant architectural decisions made during the AlphaPulse project.

## ADR Index

| ADR                                                | Title                                      | Status     | Date       |
| -------------------------------------------------- | ------------------------------------------ | ---------- | ---------- |
| [ADR-003](adr-003-training-hardware-evaluation.md) | Training Hardware Evaluation               | Accepted   | 2026-01-XX |
| [ADR-004](adr-004-testing-framework-strategy.md)   | Testing Framework Strategy                 | Accepted   | 2026-01-XX |
| [ADR-005](adr-005-mlops-first-strategy.md)         | MLOps-First Strategy (pandas-ta vs Custom) | Superseded | 2026-01-10 |
| [ADR-006](adr-006-backend-first-strategy.md)       | Backend-First Strategy (Pivot from MLOps)  | Accepted   | 2026-01-10 |
| [ADR-007](adr-007-cross-cloud-strategy.md)         | Cross-Cloud Strategy (Abstractions)        | Proposed   | 2026-01-10 |

**Note**: ADR-005 was superseded by ADR-006 due to strategic pivot from MLOps to Backend Infrastructure focus.

## ADR Format

Each ADR should follow this structure:

```markdown
# ADR-XXX: [Title]

## Status

[Proposed | Accepted | Deprecated | Superseded]

## Context

What is the issue that we're seeing that is motivating this decision?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

## Alternatives Considered

What other options were evaluated?

## References

- Link to related documentation
- External resources
```

## How to Create a New ADR

1. Copy the template above
2. Assign the next sequential number
3. Use descriptive kebab-case filename: `adr-XXX-short-title.md`
4. Update this index after creation

## Naming Convention

- `adr-003-training-hardware-evaluation.md`
- `adr-004-testing-framework-strategy.md`
- `adr-005-mlops-first-strategy.md`

## Related Documentation

- [File Structure](../FILE_STRUCTURE.md)
- [Deployment Guides](../deployment/)
- [Runbooks](../runbooks/)
