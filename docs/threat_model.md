# Threat Model

## Scope

Sentinel is **defense-only**. It detects coordinated refund abuse patterns.

## Not Implemented

- Credential theft
- Card testing
- Bypass techniques
- Fraud automation
- Attack generation against real systems
- Real-person profiling

## Data Safety

- All identifiers are synthetic/pseudonymous
- No real PII
- Secrets stored in `.env` (not committed)
- API inputs sanitized
- Database credentials not exposed to frontend
