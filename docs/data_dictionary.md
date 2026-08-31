# Data Dictionary

*To be populated in Phase 1 — Synthetic World.*

## Core Entities

- Customer
- Device
- Address
- Payment Token
- Order
- Refund
- Ring (ground-truth metadata only — never exposed to model)

## Label Definition

```
coordinated_refund_abuse = 1
```

Only when an event belongs to a synthetic abuse ring AND meets defined abuse participation criteria.
