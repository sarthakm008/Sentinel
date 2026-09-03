# Demo Script

**Duration:** 2–4 minutes  
**Audience:** Hackathon judges, technical reviewers  
**Prerequisites:** Backend + Frontend running locally

---

## Demo Narrative

> "A refund request looks normal in isolation. But when you see it's connected to 12 other accounts sharing the same device, and those accounts have an 85% refund rate, and they're all requesting refunds within the same hour — that's coordinated abuse. Sentinel detects this automatically."

---

## Step-by-Step Flow

### 1. Setup (30 seconds)
**Terminal 1:**
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
*Wait for "Loaded production model: sentinel with 39 features" and "Built complete PIT state"*

**Terminal 2:**
```bash
cd frontend && npm run dev
```
*Open http://localhost:5173*

**Show:** Dashboard loads with KPI cards (all zeros initially)

---

### 2. Run Demo Scenario (15 seconds)
**Click:** "Run Demo Scenario" button (top right)

**Show:** Toast/notification "Demo completed: 5 cases created"

**Dashboard updates:**
- Total Analyzed: 5
- High Risk Cases: 2
- Review Queue: 2
- Auto-Approved: 3
- Est. Exposure: ₹XX,XXX

---

### 3. Case List (30 seconds)
**Click:** "Cases" in navigation or "View All" on dashboard

**Show:** Table with 5 cases:
| Refund ID | Customer | Score | Band | Action | Status |
|---|---|---|---|---|---|
| REF_0007580 | CUS_021764 | 0.660 | HIGH | REVIEW | pending |
| REF_0028520 | CUS_049320 | 0.445 | HIGH | REVIEW | pending |
| REF_0028458 | CUS_049306 | 0.171 | LOW | APPROVE | pending |
| REF_0025456 | CUS_048639 | 0.103 | LOW | APPROVE | pending |
| REF_0031741 | CUS_050039 | 0.009 | LOW | APPROVE | pending |

**Point out:** Real test-set refunds, real model scores, not hardcoded

---

### 4. Case Detail — High Risk (60 seconds)
**Click:** REF_0007580 (score 0.660, HIGH, REVIEW)

**Tabs shown:**

#### Evidence Tab
**Behavioral:**
- "Elevated refund rate: 100.0% (avg ~12%)"

**Graph:**
- "3 other customers share this device"
- "3 other customers at this address"
- "Connected cluster of 14 accounts"
- "Connected neighbors avg refund rate: 80.4%"
- "Device shared by unusually few customers (rare sharing)"

**Temporal:** (if any triggered)

#### Graph Tab
**Show:** Interactive network visualization
- Center: Target customer (red pulsing)
- 3 shared entities: Device (purple square), Address (green diamond), Payment (yellow hex)
- Legend explains node types
- Stats panel: 4 nodes, 3 edges, 1 device, 1 address, 1 payment

**Explain:** "This is the actual PIT-correct graph at the moment of refund request — no future leakage, no ground truth rings"

#### Decision Tab
**Show:** Recommended action: REVIEW
**Buttons:** APPROVE / VERIFY / REVIEW / HOLD

**Click:** REVIEW button
**Show:** Status changes to "Decided", decision recorded with timestamp

---

### 5. Case Detail — Low Risk (30 seconds)
**Click:** REF_0031741 (score 0.009, LOW, APPROVE)

**Show:** Minimal evidence, small graph, recommended APPROVE
**Click:** APPROVE button

---

### 6. Evaluation Page (45 seconds)
**Navigate to:** "Evaluation" in nav

**Show sections:**

#### PRODUCTION CANDIDATE
- Full Sentinel (39 features) — PR-AUC 0.4493
- Green badge "PRODUCTION"

#### ABLATION STUDY
- Baseline → Graph-Enhanced → Temporal-Enhanced → Sentinel
- Bar chart: PR-AUC and financial loss

#### OUT-OF-DISTRIBUTION: TYPE F
- All 6 models on unseen ring structure
- Sentinel generalizes best

#### TEMPORAL HOLDOUT: DAYS 120-180
- Future period performance

#### PHASE 5 EXPERIMENT — REJECTED
- Red badge "EXPERIMENTAL / REJECTED"
- ΔPR-AUC = +0.0004, 95% CI = [-0.0089, 0.0097]
- "CI includes zero → not statistically significant → not deployed"

**Key message:** "We don't ship features that don't prove their value."

---

### 7. Reset Demo (10 seconds)
**Click:** "Reset Demo" button
**Show:** All cases cleared, dashboard back to zeros
**Click:** "Run Demo Scenario" again — deterministic, same results

---

## Key Talking Points

| Topic | Script |
|---|---|
| **No leakage** | "Train/val/test split by customer groups — no shared devices, addresses, or rings across splits" |
| **PIT correctness** | "Features computed strictly from events before refund timestamp — graph built from orders before t_ref" |
| **Production vs Experiment** | "Green = deployed. Red = tested and rejected. Phase 5 feature failed our pre-registered statistical gate." |
| **Financial impact** | "Graph-Enhanced avoids ₹64K vs baseline on held-out test. Temporal avoids ₹317K." |
| **Decision semantics** | "Threshold 0.41 frozen on validation cost model. Four actions proportional to risk." |
| **Explainability** | "Every evidence item maps to a real model feature. No LLM hallucination — structured evidence only." |

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Backend won't start | Check Python 3.11+, `pip install -r requirements.txt` |
| Frontend won't start | `cd frontend && npm install && npm run dev` |
| API 404 on graph | Ensure both backend and frontend running, check CORS |
| Demo creates 0 cases | Backend needs restart after code changes (model reloads on startup) |
| Tests fail | `python -m pytest ml/tests/ backend/tests/ -v` |

---

## Deterministic Demo Data

The demo uses 5 real refund IDs from the locked test set:

| Refund ID | Label | Expected Band | Key Evidence |
|---|---|---|---|
| REF_0007580 | 0 (legit) | HIGH | 100% refund rate, shared device/address/payment, cluster of 14 |
| REF_0028520 | 1 (abuse) | HIGH | 600% refund rate, 6 refunds in 7 days |
| REF_0028458 | 1 (abuse) | LOW | 300% refund rate, 5 refunds in 7 days |
| REF_0025456 | 0 (legit) | LOW | 500% refund rate, shared device/address, cluster of 14, 80% neighbor rate |
| REF_0031741 | 1 (abuse) | LOW | 900% refund rate, 9 refunds in 7 days, cluster of 79 |

*Note: Model scores are probabilistic — bands may vary slightly but relative ordering is stable.*