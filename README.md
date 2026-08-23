# NeuroDetect — Memory Recall (Milestone 1)

> **This is a prototype behavioural assessment system. Synthetic development
> data is not clinical ground truth and the Memory Recall game does not
> diagnose HC, MCI, or Dementia.**

NeuroDetect is a multimodal cognitive assessment prototype. This milestone
implements exactly one component, end-to-end, as the **reference
architecture** for the four cognitive games that will follow it:

**Memory Recall** — a 12-item learning / immediate recall / delayed recall /
recognition task that produces 13 locked behavioural features per completed
assessment.

Nothing else (other games, PHQ-9/GAD-7, PROCESS-2 speech, fusion/ML,
diagnosis) is implemented here. See "Out of scope" below.

---

## Architecture

```
Patient
   ↓
Memory Recall UI (React)
   ↓
Game State / Logic  (reducer-based state machine, timestamps as source of truth)
   ↓
Raw Interaction Telemetry (append-only event log, UI-agnostic)
   ↓
Feature Extraction  (pure functions, backend only)
   ↓
FastAPI  (validation → service → repository)
   ↓
Supabase (Postgres)
   ↓
13 Memory Features (persisted, one row per assessment)
```

The frontend **never** computes features and **never** talks to Supabase
directly — it only sends raw telemetry to FastAPI, which is the sole owner
of the Supabase service-role key.

---

## Folder structure

```
neurodetect/
├── frontend/            React + Vite + TypeScript
│   └── src/games/memory/  Memory Recall UI, state, telemetry, config
├── backend/              FastAPI + Pydantic
│   └── app/games/memory/  router, service, features, validators, schemas
├── database/              schema.sql + setup notes
├── .env.example
└── README.md (this file)
```

---

## Frontend setup

```bash
cd frontend
npm install
cp ../.env.example .env   # then set VITE_API_BASE_URL
npm run dev
```

Runs on `http://localhost:5173`. In this milestone there is no
assessment-creation UI — pass an existing assessment id via the URL:
`http://localhost:5173/?assessment_id=<uuid>`.

Type-check / production build:

```bash
npm run build
```

---

## Backend setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # then set SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health` → `{"status": "ok"}`

---

## Environment variables

| Variable | Where | Notes |
|---|---|---|
| `SUPABASE_URL` | backend only | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | backend only | **Never** ship this to the browser |
| `ENVIRONMENT` | backend only | `development` / `production` |
| `VITE_API_BASE_URL` | frontend only | Where the browser reaches FastAPI |

---

## Supabase setup

1. Create a Supabase project.
2. Run `database/schema.sql` in the SQL editor — creates `patients`,
   `assessments`, `memory_results`.
3. Seed at least one `patients` row and one `assessments` row so you have a
   real `assessment_id` to pass to the frontend/API (this milestone's game
   never creates an assessment itself — see `database/README.md`).
4. Put the project URL + service-role key into `backend/.env`.

---

## API endpoint

```
POST /api/assessments/{assessment_id}/games/memory/complete
```

**Request**

```json
{
  "events": [
    {
      "event_id": "evt_00001",
      "assessment_id": "11111111-1111-1111-1111-111111111111",
      "game": "memory",
      "phase": "LEARNING",
      "event_type": "item_presented",
      "timestamp": "2026-01-01T12:00:01Z",
      "item_id": "item_001",
      "trial_id": null,
      "value": null,
      "metadata": { "label": "apple", "position": 0 }
    }
  ],
  "confidence": {
    "immediate_recall": 4,
    "delayed_recall": 3,
    "recognition": 5
  }
}
```

**Response**

```json
{
  "assessment_id": "11111111-1111-1111-1111-111111111111",
  "game": "memory",
  "status": "completed",
  "features": {
    "immediate_recall_accuracy": 0.75,
    "delayed_recall_accuracy": 0.5833333333333334,
    "recognition_accuracy": 1.0,
    "recall_decay_rate": 0.2222222222222222,
    "recall_latency": 3.0,
    "omission_errors": 5,
    "intrusion_errors": 1,
    "sequence_recall_accuracy": 1.0,
    "hesitation_duration": 0.0,
    "retry_frequency": 0,
    "confidence_variability": 1.0,
    "completion_time": 151.0,
    "memory_consistency_trend": 0.7777777777777778
  }
}
```

Status codes: `404` unknown assessment · `409` already completed ·
`422` malformed/incomplete event data or feature validation failure ·
`500` unexpected server error (never leaks a stack trace).

---

## Memory Recall game flow

```
INTRO → LEARNING → IMMEDIATE_RECALL → DISTRACTOR → DELAYED_RECALL
      → RECOGNITION → CONFIDENCE → COMPLETE
```

12 target items are shown one at a time (learning), then the participant
selects remembered items from a target+distractor set (immediate recall),
performs a short counting-backwards task (distractor, no features of its
own), free-types remembered items (delayed recall), answers yes/no for a
target+distractor set (recognition), and rates confidence three times.
Every interaction is captured as a raw telemetry event; nothing is scored
in the browser.

---

## The 13 locked features

All formulas live in `backend/app/games/memory/features.py` (pure,
independently unit-tested). Ranges are enforced in
`backend/app/games/memory/validators.py` before insertion.

| # | Feature | Formula |
|---|---|---|
| 1 | `immediate_recall_accuracy` | correct targets selected during immediate recall ÷ 12 |
| 2 | `delayed_recall_accuracy` | correct targets recalled during delayed recall ÷ 12 |
| 3 | `recognition_accuracy` | correct recognition responses ÷ total recognition trials |
| 4 | `recall_decay_rate` | `(immediate − delayed) / immediate` if immediate > 0, else 0; clamped to [0,1] |
| 5 | `recall_latency` | seconds from delayed-recall phase start to first valid response |
| 6 | `omission_errors` | 12 − distinct targets correctly recalled in delayed recall |
| 7 | `intrusion_errors` | delayed-recall responses that are not target items |
| 8 | `sequence_recall_accuracy` | proportion of adjacent correctly-recalled-target pairs (in recall order) whose original learning order is preserved; 0 if fewer than 2 valid recalls |
| 9 | `hesitation_duration` | sum of `(gap − 2s)` over consecutive delayed-recall responses where gap > 2s |
| 10 | `retry_frequency` | count of explicit edit/retry events |
| 11 | `confidence_variability` | standard deviation of the 3 confidence ratings |
| 12 | `completion_time` | `game_completed` timestamp − `game_started` timestamp, seconds |
| 13 | `memory_consistency_trend` | targets recalled in **both** immediate and delayed ÷ targets recalled in immediate; 0 if immediate count is 0 |

No feature is hardcoded or randomly generated — every value is derived
from the raw event log for that specific completion.

---

## Testing

```bash
cd backend
python3 -m pytest -q
```

40 tests, all passing: the worked example from the spec (9/12 immediate
recall, 7/12 delayed recall, 5 omissions, 1 intrusion), every individual
feature calculator, edge cases (zero recall, perfect recall, duplicate
target responses, intrusions, long/no hesitation, missing responses,
incomplete games), feature-range validation, and service-layer rules
(unknown assessment, duplicate completion, missing required phases,
cross-assessment event mismatch) using a fake in-memory repository — no
network calls, fully deterministic.

Frontend type-check / build:

```bash
cd frontend
npm run build
```

---

## Limitations

- No authentication — out of scope for this milestone per the brief.
- Item pool, recognition distractors, and shuffling are fixed/MVP-sized;
  production would need larger, localized item banks.
- Frontend confidence-scale UI is minimal; no accessibility audit performed
  beyond basic `aria-pressed`/`aria-label` usage.
- No end-to-end browser test automation (e.g. Playwright) — verified via
  backend pytest + manual/typecheck-level frontend build only.
- Distractor task accepts only the exact expected number at each step (no
  partial-credit counting-error detection); it produces no features by
  design.

## Future extension points

- The same UI → state → telemetry → feature-extraction → validation → API →
  repository → DB layering is intended to be copied for MMSE/Serial 7s,
  Boston Naming, N-Back, and Trail Making.
- `app/repositories/` and `app/games/<name>/` are structured so a new game
  adds a sibling package without touching this one.
- Fusion/scoring and the ML classification layer will consume
  `memory_results` (and its four siblings) once all five games exist —
  neither is wired in here.
