# SENTINEL — MASTER BUILD SPECIFICATION v2

## AI-Powered Coordinated Refund Abuse Detection

**Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager**

**Document purpose:** This is the authoritative implementation specification for an AI coding agent.  
**Primary builder environment:** Google Antigravity  
**Primary model:** Claude Opus 4.6 (Thinking)  
**Repository:** `sentinel/`

---

# 0. Executive Directive

You are the lead software engineer, ML engineer, data engineer, and QA engineer responsible for building **Sentinel**, a working hackathon-grade but experimentally defensible prototype for detecting **coordinated refund abuse**.

Do not treat this as a request to make a visually impressive fraud dashboard.

The core scientific/product question is:

> **Does adding relationship and temporal intelligence materially improve detection of coordinated refund abuse compared with a strong individual-level behavioral baseline, on a genuinely held-out test set with no entity/ring leakage?**

The project succeeds only if the answer is measured honestly.

## Non-negotiable rules

1. **Never fabricate metrics.**
2. **Never claim graph intelligence works unless the experiment demonstrates it.**
3. **Never use transaction-level random splitting when it can leak customer/ring information.**
4. **Never generate labels from a feature that is then exposed directly to the model.**
5. **Never allow the LLM investigator to invent evidence.**
6. **Never use real personal data. All prototype identifiers must be synthetic/pseudonymous.**
7. **Do not deploy a GNN simply because it sounds sophisticated.**
8. **The behavioral baseline is mandatory.**
9. **The final held-out test set must remain untouched until model selection and threshold selection are complete.**
10. **If the Sentinel model does not materially outperform the baseline, report the result and simplify or pivot rather than tuning until it wins.**
11. **Every phase must have tests and acceptance criteria.**
12. **Do not proceed to expensive UI polish until the ML/evaluation core works.**
13. **Keep all generated data, labels, experiments, metrics, seeds, and configurations reproducible.**
14. **Do not build offensive capabilities. This is strictly defensive risk detection.**

---

# 1. Problem Definition

## 1.1 Target loss class

Sentinel targets:

> **Coordinated abuse of a merchant's refund workflow by multiple linked or behaviorally coordinated entities.**

This is intentionally narrower than generic fraud.

Out of scope as primary targets:

- chargeback prediction
- account takeover
- card theft
- generic transaction fraud
- RTO prediction
- counterfeit-return verification
- promotion farming
- phishing/BEC

Those may be represented as background patterns only if they help construct realistic data, but the target label remains coordinated refund abuse.

## 1.2 Product promise

A refund request that looks normal in isolation can become suspicious when considered alongside:

- related customers/accounts
- shared devices
- shared addresses
- shared payment tokens
- correlated transaction behavior
- synchronized refund activity
- abnormal cluster-level refund behavior

Sentinel should convert these signals into:

1. a risk score,
2. a case,
3. evidence,
4. estimated financial exposure,
5. a recommended action.

## 1.3 Product positioning

Sentinel is a **merchant risk layer** around a refund workflow.

Conceptual flow:

```text
Merchant refund request
        |
        v
   Sentinel risk layer
        |
        +---- Low ------> Approve
        |
        +---- Medium ---> Verify
        |
        +---- High -----> Manual review
        |
        +---- Critical -> Hold pending verification
```

The system does not claim that Razorpay itself automatically denies every merchant refund.

---

# 2. Success Criteria

The project must satisfy all of the following before being considered complete.

## 2.1 Functional

- Synthetic dataset can be generated from a fixed seed.
- Dataset contains legitimate and coordinated-abuse populations.
- Baseline model can be trained.
- Sentinel model can be trained.
- Held-out evaluation runs reproducibly.
- Risk scoring API works.
- Case-generation API works.
- Dashboard displays risk cases and evidence.
- Network graph can be explored.
- Demo scenario can be reset and replayed.
- Tests pass.

## 2.2 Scientific

- No customer/ring leakage between train, validation, and test.
- Label-generation logic is documented.
- Hard legitimate negatives exist.
- Multiple abuse-ring structures exist.
- Test includes unseen ring structures.
- Baseline and Sentinel are evaluated on exactly the same final test set.
- Threshold is selected using validation data only.
- Metrics include precision and recall.
- PR-AUC is reported because the task is imbalanced.
- False-positive cost is reported.
- Expected financial loss is reported.
- Results are stored as machine-readable artifacts.

## 2.3 Product

- Alert explains why it was flagged.
- Explanation is grounded in structured evidence.
- Merchant can see affected entities and estimated exposure.
- Recommended action is proportional to risk.
- System is defense-only.

---

# 3. Architecture

Use a simple modular architecture. Do not over-engineer.

```text
                         SENTINEL
                            |
          +-----------------+-----------------+
          |                 |                 |
       Frontend          Backend           ML Service
        React           FastAPI             Python
          |                 |                 |
          +-----------------+-----------------+
                            |
                         Database
                        PostgreSQL
                            |
                 +----------+----------+
                 |                     |
            Event tables          Case tables
                 |
        Feature / graph pipeline
                 |
          Model artifacts
```

## Recommended stack

| Area | Choice |
|---|---|
| Frontend | React + Vite |
| UI | Tailwind CSS or clean CSS |
| Graph visualization | React Flow, Cytoscape.js, or D3 |
| Backend | FastAPI |
| ML | Python, scikit-learn, LightGBM or XGBoost |
| Graph computation | NetworkX initially |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Testing | pytest + frontend test framework |
| Packaging | Docker Compose |
| Model artifacts | local `artifacts/` directory |
| LLM investigator | structured-output capable LLM, optional for first ML milestone |

If LightGBM is difficult to install in the environment, use XGBoost. If both are problematic, use sklearn HistGradientBoostingClassifier.

---

# 4. Repository Structure

Create:

```text
sentinel/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
│
├── docs/
│   ├── problem.md
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── evaluation.md
│   ├── threat_model.md
│   └── demo_script.md
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── splits/
│   └── demo/
│
├── ml/
│   ├── config/
│   ├── data_generation/
│   ├── features/
│   ├── graph/
│   ├── temporal/
│   ├── models/
│   ├── evaluation/
│   ├── adversarial/
│   ├── training/
│   └── scripts/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── main.py
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   ├── hooks/
│   │   └── types/
│   └── tests/
│
├── artifacts/
│   ├── models/
│   ├── metrics/
│   ├── plots/
│   └── reports/
│
└── scripts/
    ├── setup.sh
    ├── generate_data.sh
    ├── train.sh
    ├── evaluate.sh
    └── demo.sh
```

The repository itself is the source of truth.

---

# 5. Data Model

All identifiers are synthetic.

## 5.1 Core entities

### Customer

```text
customer_id
account_created_at
merchant_id
segment
```

### Device

```text
device_id
device_type
```

### Address

```text
address_id
region
household_group_id
```

### Payment token

```text
payment_token_id
payment_type
```

### Order

```text
order_id
customer_id
merchant_id
timestamp
amount
product_category
device_id
address_id
payment_token_id
```

### Refund

```text
refund_id
order_id
customer_id
timestamp
amount
reason_category
status
```

### Ring

Synthetic ground-truth metadata only:

```text
ring_id
ring_type
is_abuse
structure_class
```

Do not expose ring_id or the true abuse mechanism as a model feature.

---

# 6. Event Schema

Representative order/refund event:

```json
{
  "event_id": "EVT_000001",
  "event_type": "refund_request",
  "merchant_id": "MER_17",
  "customer_id": "CUS_2841",
  "order_id": "ORD_9182",
  "timestamp": "2026-08-31T14:32:00Z",
  "amount": 2499.0,
  "device_id": "DEV_912",
  "address_id": "ADDR_771",
  "payment_token_id": "PM_551",
  "account_age_days": 143,
  "previous_orders": 18,
  "previous_refunds": 7
}
```

---

# 7. Synthetic Data Generator

This is a critical component.

Do not create a trivial dataset where fraud is obvious from one field.

## 7.1 Initial scale

Target approximately:

- 50,000 customers
- 100,000–200,000 orders
- 10,000–20,000 refund requests
- 100–300 coordinated abuse rings
- 10–20% of refund requests belonging to coordinated-abuse populations

These are starting targets, not sacred numbers. Optimize for reproducibility and reasonable runtime.

## 7.2 Legitimate populations

Generate:

### A. Independent customers

Normal independent behavior.

### B. Families

- shared address
- sometimes shared device
- occasionally shared payment instrument
- legitimate purchases/refunds

### C. Hostels/shared housing

- many customers
- shared address/network-like relationships
- different devices
- normal independent behavior

### D. Offices

- many accounts
- shared network-like relationship
- unrelated purchasing behavior

### E. Gift buyers

- one customer
- multiple shipping addresses
- legitimate behavior

### F. Legitimate heavy returners

- unusually high refund rate
- but no coordinated network behavior

### G. Seasonal buyers

- bursts of purchases around events
- legitimate synchronized timing

These are mandatory hard negatives.

---

# 8. Abuse-Ring Generator

Create multiple ring structures.

## Ring Type A — Dense infrastructure sharing

High overlap:

- shared devices
- shared addresses
- shared payment tokens
- synchronized purchases/refunds

This is the easy case.

## Ring Type B — Partial overlap

Only some entities are shared.

Example:

```text
20 accounts
6 devices
4 addresses
3 payment tokens
```

No single relationship proves abuse.

## Ring Type C — Sparse infrastructure

Minimal shared infrastructure.

Signal primarily comes from:

- temporal coordination
- behavioral similarity
- cluster-level refund patterns

## Ring Type D — Temporal coordination

Accounts have weak/static relationships but exhibit synchronized activity.

## Ring Type E — Mixed structure

Combine partial overlap, timing, behavior, and different ring shapes.

## Ring Type F — Adversarial / unseen structure

Generate patterns intentionally different from training structures.

The final test set must contain some structures not represented in training.

---

# 9. Ground Truth and Labeling

The generator may know the hidden ring membership.

The model may not.

Define:

```text
coordinated_refund_abuse = 1
```

only when an event belongs to a synthetic abuse ring and meets the defined abuse participation criteria.

Legitimate shared-infrastructure events remain label 0 even if they have graph relationships.

## Critical anti-leakage rule

Never create a feature such as:

```text
fraud_ring_score
ring_id
is_synthetic_abuse
generator_abuse_probability
```

and feed it to the model.

Never derive a feature directly from the label.

Document the exact generation mechanism in:

```text
docs/data_dictionary.md
docs/evaluation.md
```

---

# 10. Dataset Splitting

Do NOT perform a naive random row split.

Use group-aware splitting.

Preferred structure:

```text
TRAIN
- legitimate groups
- abuse rings A–N

VALIDATION
- separate legitimate groups
- abuse rings O–R

TEST
- separate legitimate groups
- unseen abuse rings S–V
- at least one structural distribution shift
```

No customer, ring, device/address grouping that causes leakage should cross the relevant split where feasible.

The test set must be immutable after model selection.

Save split manifests:

```text
data/splits/train_groups.json
data/splits/validation_groups.json
data/splits/test_groups.json
```

---

# 11. Feature Engineering

## 11.1 Behavioral features

Per customer:

- order_count
- refund_count
- refund_rate
- total_order_value
- total_refund_value
- mean_order_value
- mean_refund_value
- refund_amount_ratio
- account_age_days
- orders_last_24h
- refunds_last_24h
- refunds_last_7d
- median_time_between_orders
- median_time_between_refunds
- unique_device_count
- unique_address_count
- unique_payment_count

## 11.2 Transaction-level features

- amount_zscore_vs_customer
- amount_zscore_vs_merchant
- refund_delay_minutes
- order_to_refund_ratio
- category_refund_rate
- recent_activity_burst

## 11.3 Graph features

Construct an entity graph using:

```text
customer -> device
customer -> address
customer -> payment
customer -> order
customer -> refund
```

Calculate features such as:

- degree
- weighted degree
- number of shared devices
- number of shared addresses
- number of shared payments
- number of connected customers
- component size
- local clustering coefficient where meaningful
- neighbor refund rate
- neighbor average risk
- number of high-refund neighbors
- relationship diversity
- two-hop customer count

Do not use graph algorithms that are computationally excessive for the MVP.

## 11.4 Temporal features

- number of related events in 5m/15m/1h/24h windows
- related refund burst count
- synchronized refund ratio
- synchronized order ratio
- median time difference between connected customer events
- account creation burst
- cluster activity acceleration

---

# 12. Baseline Model

The baseline is mandatory.

Input:

```text
behavioral + transaction features
```

No graph-derived features.

Recommended model:

```text
LightGBMClassifier
```

or XGBoost/sklearn fallback.

Output:

```text
p_baseline
```

Store:

```text
artifacts/models/baseline.*
artifacts/metrics/baseline.json
```

---

# 13. Sentinel Model

Input:

```text
behavioral features
+
transaction features
+
graph features
+
temporal features
```

Recommended initial model:

```text
LightGBMClassifier
```

Output:

```text
p_sentinel
```

This is the MVP Sentinel model.

Do not introduce a GNN unless an experiment shows that graph features themselves are valuable and a GNN has a realistic chance of improving the operating point without excessive complexity.

---

# 14. Ablation Study

Run at least:

### Experiment A

Behavioral only.

### Experiment B

Behavioral + graph.

### Experiment C

Behavioral + graph + temporal.

Compare on the same held-out test set.

Report:

- Precision
- Recall
- F1
- PR-AUC
- False-positive rate
- Confusion matrix
- Expected financial loss

Also report validation and test results separately.

---

# 15. Threshold Selection

Do not select a threshold on the final test set.

Use validation data to select an operating threshold.

Possible strategy:

1. Generate validation probabilities.
2. Evaluate thresholds from 0.05 to 0.95.
3. Compute expected cost.
4. Choose threshold minimizing validation expected cost subject to a reasonable precision/recall constraint.
5. Freeze threshold.
6. Run exactly once on the final test set.

Store the selected threshold in:

```text
artifacts/metrics/threshold.json
```

---

# 16. Financial Cost Model

Use explicit configurable assumptions.

Default prototype assumptions:

```text
false_negative_cost = refund_amount
false_positive_cost = review_cost + customer_friction_cost
manual_review_cost = configurable fixed amount
```

Do not pretend these are real Razorpay economics.

Label them clearly as:

> Prototype economic assumptions.

Compute:

```text
expected_loss =
    sum(false_negative_costs)
  + sum(false_positive_costs)
  + sum(review_costs)
```

Also compute:

```text
loss_avoided_vs_baseline =
    baseline_expected_loss - sentinel_expected_loss
```

If the result is negative, report it.

---

# 17. Required Evaluation Outputs

Create:

```text
artifacts/metrics/
├── baseline.json
├── sentinel.json
├── ablation.json
├── threshold.json
├── financial_impact.json
└── adversarial.json
```

Create plots:

```text
artifacts/plots/
├── precision_recall.png
├── confusion_matrix.png
├── threshold_cost_curve.png
├── baseline_vs_sentinel.png
└── adversarial_results.png
```

Every result must include:

- dataset version
- seed
- model version
- feature set
- threshold
- split version
- timestamp

---

# 18. Adversarial Test Suite

Implement programmatic tests.

## Test 1 — Family

Expected:

- relationship signals present
- not automatically classified as abuse
- false positive should remain controlled

## Test 2 — Hostel

Expected:

- many shared relationships
- low coordinated-abuse probability if behavior is independent

## Test 3 — Office

Expected:

- shared network-like infrastructure
- independent transaction behavior

## Test 4 — Gift buyer

Expected:

- multiple addresses
- no abuse ring

## Test 5 — Legitimate heavy returner

Expected:

- high individual refund rate
- no coordinated network pattern

## Test 6 — Sparse abuse ring

Expected:

- detectable primarily through combined temporal/behavioral/network evidence

## Test 7 — Unseen ring structure

Expected:

- evaluate generalization rather than memorization

The exact pass/fail thresholds must be derived after a first benchmark run. Do not invent them beforehand.

---

# 19. Model Explainability

The numerical model must expose structured evidence.

Example:

```json
{
  "risk_score": 0.93,
  "risk_band": "critical",
  "evidence": [
    {
      "type": "network",
      "metric": "connected_customer_count",
      "value": 18
    },
    {
      "type": "network",
      "metric": "shared_devices",
      "value": 6
    },
    {
      "type": "behavior",
      "metric": "cluster_refund_rate",
      "value": 0.74
    },
    {
      "type": "temporal",
      "metric": "synchronized_refund_ratio",
      "value": 0.89
    }
  ]
}
```

Never ask the LLM to invent these values.

---

# 20. LLM Investigator

The LLM is NOT the fraud classifier.

It receives:

- risk score
- risk band
- structured evidence
- affected entity counts
- estimated exposure
- recommended action

It returns strict JSON:

```json
{
  "summary": "...",
  "key_findings": [
    "...",
    "..."
  ],
  "recommended_action": "hold_for_verification",
  "confidence_language": "high"
}
```

Rules:

- Never introduce facts absent from evidence.
- Never change the numerical risk score.
- Never invent customer behavior.
- Never claim real-world fraud certainty.
- Use language such as "high risk of coordinated abuse" rather than "proven fraud."
- If evidence is insufficient, say so.

For the first ML milestone, the LLM investigator may be stubbed with deterministic templates. Add the real LLM only after the risk pipeline works.

---

# 21. Risk Bands

Use configurable thresholds.

Example initial mapping:

```text
0.00–0.39  LOW
0.40–0.69  MEDIUM
0.70–0.89  HIGH
0.90–1.00  CRITICAL
```

These are presentation defaults, not claims of optimal thresholds.

The actual intervention threshold must be selected from validation economics.

---

# 22. Backend API

Implement REST endpoints.

## Health

```http
GET /api/health
```

## Metrics

```http
GET /api/metrics
```

Returns latest evaluation summary.

## Risk score

```http
POST /api/risk/score
```

Request:

```json
{
  "customer_id": "CUS_1",
  "order_id": "ORD_1",
  "refund_id": "REF_1"
}
```

Response:

```json
{
  "risk_score": 0.83,
  "risk_band": "high",
  "recommended_action": "manual_review",
  "evidence": []
}
```

## Case

```http
GET /api/cases/{case_id}
```

## Cases

```http
GET /api/cases
```

## Graph

```http
GET /api/cases/{case_id}/graph
```

## Decision

```http
POST /api/cases/{case_id}/decision
```

Request:

```json
{
  "decision": "hold"
}
```

Allowed:

```text
approve
verify
review
hold
```

Store decision history.

---

# 23. Database Tables

Minimum tables:

```text
customers
devices
addresses
payment_tokens
orders
refunds
risk_cases
case_entities
case_evidence
decisions
model_runs
evaluation_runs
```

Do not store raw real PII.

---

# 24. Frontend

Build three primary screens.

## Screen A — Risk Overview

Show:

- potential exposure
- active clusters
- number of high/critical cases
- precision
- recall
- expected loss
- recent alerts

Recent alert row:

```text
Severity | Case | Accounts | Exposure | Status
```

## Screen B — Cluster Investigation

Show:

- case ID
- risk score
- risk band
- estimated exposure
- graph
- accounts
- devices
- addresses
- payment instruments
- behavioral evidence
- temporal evidence
- AI summary

## Screen C — Decision

Show:

- pending refunds
- recommendation
- evidence
- approve
- verify
- review
- hold

Include confirmation for destructive/financial actions.

---

# 25. Graph Visualization

The graph must communicate the product thesis quickly.

Example:

```text
              DEVICE
             /      \
        CUSTOMER   CUSTOMER
           |          |
        ADDRESS    PAYMENT
           |          |
        CUSTOMER---CUSTOMER
```

Visual requirements:

- distinguish entity types
- highlight suspicious cluster
- allow pan/zoom
- show relationship labels
- clicking a node reveals metadata
- clicking an edge reveals relationship
- do not overwhelm the screen with thousands of nodes

For the demo, default to the relevant case subgraph rather than the full dataset.

---

# 26. Demo Simulator

Create a deterministic demo dataset with a known scenario.

Demo sequence:

1. Start with normal traffic.
2. Introduce a coordinated abuse ring.
3. Process refund events.
4. Trigger Sentinel.
5. Show the cluster emerging.
6. Open the case.
7. Show graph and evidence.
8. Show estimated exposure.
9. Show recommended hold/review action.
10. Show baseline comparison.
11. Show held-out metrics.
12. Reset.

The demo must work offline after setup.

No dependency on a live external API is required.

---

# 27. Demo Data

Create a deterministic demo scenario:

```text
18 accounts
6 devices
4 addresses
3 payment instruments
multiple refund events
approximately ₹3–4L exposure
```

These numbers are for the demo narrative only.

Do not reuse them as evaluation metrics.

---

# 28. Security and Safety

This system is defense-only.

Do not implement:

- credential theft
- card testing
- bypass techniques
- fraud automation
- attack generation against real systems
- real-person profiling

Use synthetic IDs.

Sanitize all API inputs.

Do not expose database credentials to the frontend.

Use `.env` for secrets.

---

# 29. Testing Strategy

## Unit tests

Test:

- feature calculations
- graph construction
- temporal calculations
- risk banding
- cost calculations
- schema validation

## Integration tests

Test:

- event → feature → model → API
- case creation
- graph retrieval
- decision persistence

## ML tests

Test:

- reproducibility
- no forbidden columns
- train/test group disjointness
- feature matrix shape
- probability range
- threshold application

## Leakage tests

Programmatically assert:

```text
train_customers ∩ test_customers == empty
train_rings ∩ test_rings == empty
```

and equivalent constraints for any grouping entity that would create leakage.

---

# 30. ML Acceptance Tests

Before moving to product UI:

### Required

- Baseline trains successfully.
- Sentinel trains successfully.
- Test set is untouched until threshold is frozen.
- Precision and recall are computed.
- PR-AUC is computed.
- Financial cost is computed.
- Ablation results are available.
- Adversarial suite runs.

### Scientific kill condition

If:

```text
Sentinel ≈ Baseline
```

or Sentinel has worse expected loss at an acceptable operating point, do NOT claim graph intelligence as a differentiator.

Instead:

1. inspect feature leakage,
2. inspect graph usefulness,
3. inspect temporal features,
4. test whether the synthetic world is too easy,
5. simplify the product if required.

Do not tune solely to manufacture an improvement.

---

# 31. Product Acceptance Tests

The MVP is complete when:

- dashboard loads
- metrics load
- cases load
- graph loads
- evidence loads
- risk score loads
- recommendation loads
- decision can be recorded
- demo can be replayed
- backend tests pass
- frontend tests pass
- evaluation can be rerun from a clean environment

---

# 32. Phase-by-Phase Implementation Plan

## Phase 0 — Repository and environment

Tasks:

- initialize project
- create folders
- setup Python environment
- setup React
- setup FastAPI
- setup PostgreSQL/Docker
- create configuration
- create README
- create Makefile/scripts

Acceptance:

- clean setup works
- health endpoint works
- frontend loads

Do not build UI polish.

---

## Phase 1 — Synthetic world

Tasks:

- implement entities
- implement legitimate populations
- implement abuse-ring generators
- implement ground truth
- generate dataset
- save metadata
- write data dictionary
- create group-aware splits

Acceptance:

- reproducible seed
- legitimate hard negatives exist
- multiple ring structures exist
- split leakage tests pass

---

## Phase 2 — Behavioral baseline

Tasks:

- implement features
- train baseline
- validation threshold selection
- final test evaluation
- metrics artifacts
- plots

Acceptance:

- reproducible model
- no leakage
- precision/recall/PR-AUC available
- financial loss available

---

## Phase 3 — Graph intelligence

Tasks:

- build entity graph
- calculate graph features
- train behavioral+graph model
- compare against baseline

Acceptance:

- ablation available
- no graph leakage
- graph features are explainable

---

## Phase 4 — Temporal intelligence

Tasks:

- implement temporal windows
- synchronization metrics
- temporal features
- train combined model
- compare A/B/C

Acceptance:

- temporal features independently tested
- final model selected on validation only

---

## Phase 5 — Adversarial evaluation

Tasks:

- family test
- hostel test
- office test
- gift buyer
- heavy returner
- sparse ring
- unseen ring structure

Acceptance:

- all tests execute
- failures are documented
- no hidden hard-coded behavior

---

## Phase 6 — Risk API

Tasks:

- model loading
- scoring endpoint
- evidence endpoint
- case generation
- decision endpoint
- persistence

Acceptance:

- end-to-end request works

---

## Phase 7 — Dashboard

Tasks:

- overview
- case list
- case detail
- graph
- evidence
- decisions

Acceptance:

- usable on laptop screen
- no broken states
- demo data works

---

## Phase 8 — Investigator

Tasks:

- structured evidence object
- deterministic fallback explanation
- optional LLM integration
- strict JSON output
- hallucination guardrails

Acceptance:

- every sentence can be traced to evidence

---

## Phase 9 — Demo mode

Tasks:

- deterministic scenario
- event playback
- alert trigger
- case view
- decision
- reset

Acceptance:

- demo runs end-to-end without manual database manipulation

---

## Phase 10 — Final audit

Tasks:

- rerun clean setup
- rerun evaluation
- verify metrics
- verify screenshots
- verify README
- verify architecture
- verify public-repo cleanliness
- verify no secrets
- verify defense-only scope

Acceptance:

- another developer can clone and run the project from README

---

# 33. What the README Must Contain

The README must explain:

1. Problem
2. Product
3. Architecture
4. Data generation
5. ML approach
6. Baseline
7. Evaluation protocol
8. Results
9. False-positive cost
10. How to run
11. Demo instructions
12. Limitations
13. Future work

Never claim the synthetic results are production performance.

---

# 34. Judge-Facing Narrative

The core pitch:

> **“A refund can look legitimate in isolation. Sentinel looks across the relationships and timing between accounts to detect coordinated refund abuse before the merchant loses more money.”**

Technical proof:

> **“We don't just show a model score. We compare a behavioral baseline against behavioral + relationship + temporal intelligence on a held-out set of unseen abuse rings, and measure precision, recall, and expected financial loss.”**

Product proof:

> **“When Sentinel finds a suspicious cluster, it shows the merchant the network, evidence, exposure, and a bounded action: approve, verify, review, or hold.”**

---

# 35. What Not To Say

Do not say:

- “This detects fraud with 99% accuracy.”
- “This is production-ready.”
- “Razorpay currently cannot detect this.”
- “Every shared device is suspicious.”
- “The LLM detects the fraud.”
- “Our synthetic dataset proves real-world performance.”

Prefer:

- “Our prototype detects coordinated refund-abuse patterns.”
- “On our held-out synthetic benchmark…”
- “The model was evaluated on unseen abuse-ring structures.”
- “Relationship signals add measurable value if the ablation supports that claim.”
- “The LLM explains structured model evidence; it is not the classifier.”

---

# 36. Engineering Behavior Required From the Coding Agent

When working on this repository:

### Before coding

- inspect repository
- read this specification
- identify contradictions
- identify missing dependencies
- propose a short plan
- do not start by generating hundreds of files

### During coding

- work phase-by-phase
- keep changes modular
- run tests after meaningful changes
- inspect actual command output
- never assume a command succeeded
- never claim a test passed without running it
- never fabricate metrics

### After each phase

Report:

```text
PHASE:
STATUS:
FILES CHANGED:
COMMANDS RUN:
TEST RESULTS:
METRICS:
KNOWN ISSUES:
NEXT STEP:
```

### When uncertain

Prefer:

1. ask for clarification only when genuinely blocking,
2. otherwise make the smallest reasonable implementation choice,
3. document the choice in `docs/architecture.md`.

### When an experiment fails

Do not hide it.

Report:

```text
Hypothesis:
Experiment:
Result:
Likely cause:
Next experiment:
```

---

# 37. Git Discipline

Create checkpoints after:

```text
phase-0
phase-1-data
phase-2-baseline
phase-3-graph
phase-4-temporal
phase-5-adversarial
phase-6-api
phase-7-ui
phase-8-investigator
phase-9-demo
final
```

Never commit secrets.

Use meaningful commit messages.

---

# 38. Performance Expectations

The MVP should prioritize correctness over scale.

Target:

- dataset generation in minutes, not hours
- training in minutes on a normal laptop
- API risk scoring under a few seconds for demo usage
- graph case loading under a few seconds
- frontend initial load under reasonable local-development time

Do not optimize prematurely.

---

# 39. Optional Enhancements

Only after the MVP is stable:

- GraphSAGE/GAT experiment
- online event streaming
- richer graph embeddings
- calibration
- SHAP explanations
- counterfactual explanations
- merchant-specific thresholds
- model drift simulation
- multi-merchant synthetic environment
- real Razorpay test-mode integration where appropriate

Optional enhancements must never compromise evaluation integrity.

---

# 40. Final Definition of Done

Sentinel is DONE only when all are true:

### Data

- realistic synthetic world
- difficult legitimate negatives
- multiple abuse-ring structures
- reproducible labels
- leakage-free splits

### ML

- baseline
- graph-enhanced model
- temporal-enhanced model
- ablation
- held-out precision
- held-out recall
- PR-AUC
- false-positive cost
- expected loss
- adversarial evaluation

### Product

- risk API
- case API
- decision workflow
- dashboard
- graph investigation
- evidence-backed explanation

### Demo

- deterministic abuse-ring scenario
- live-looking event flow
- alert
- investigation
- action
- metrics
- reset

### Engineering

- tests
- README
- setup scripts
- Docker Compose
- no secrets
- reproducible evaluation

---

# 41. First Instruction To The Agent

**Do not immediately build the entire system.**

Your first response after receiving this specification must:

1. Confirm you understand the product and scientific objective.
2. Inspect the current repository.
3. Identify the current environment and available runtimes.
4. Propose the Phase 0 implementation plan.
5. List any specification conflicts or blocking ambiguities.
6. Wait for approval before making large architectural changes.

Once Phase 0 is approved, implement only Phase 0 and run its acceptance tests.

Then proceed phase-by-phase.

**The repository, experiment artifacts, and this specification are the source of truth.**

---

# 42. Final Principle

Sentinel is not successful because it has:

- a graph,
- an LLM,
- a beautiful dashboard,
- or a high synthetic accuracy number.

It is successful if we can demonstrate, honestly:

> **“When coordinated refund abuse is hidden among realistic legitimate behavior, relationship and temporal intelligence can identify patterns that an individual-level behavioral model misses, with measured precision, recall, false-positive cost, and expected financial impact on a held-out test set.”**

That is the product.

That is the experiment.

That is the buildathon submission.
