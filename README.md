# NeuroDetect

> **This is a prototype behavioural assessment system for research/demo use. It is not a medical diagnostic tool.**

NeuroDetect is a browser-based cognitive assessment prototype with five integrated games that all share one `assessment_id`:

1. MMSE
2. Memory Recall
3. N-Back
4. Boston Naming
5. Trail Making

Each game follows the same architecture:

```text
Raw interaction telemetry
  -> FastAPI validation
  -> backend feature extraction
  -> Supabase persistence
  -> feature aggregator / Model 1 compatibility
```

The frontend never computes authoritative features and never talks to Supabase directly.

## Project structure

```text
frontend/
  src/games/
    mmse/
    memory/
    nback/
    boston-naming/
    trail-making/

backend/
  app/games/
    mmse/
    memory/
    nback/
    boston_naming/
    trail_making/
  app/repositories/

database/
  schema.sql
  mmse_schema.sql
  nback_schema.sql
  boston_naming_schema.sql
  trail_making_schema.sql

docs/
  nback-feature-contract.md
  boston-naming-feature-contract.md
  trail-making-feature-contract.md
```

## Assessment flow

```text
Start Assessment
  -> MMSE
  -> Memory Recall
  -> N-Back
  -> Boston Naming
  -> Trail Making
```

All five games use the same `assessment_id`.

## Local setup

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend runs on `http://localhost:8000`.

Health check:

```text
GET http://localhost:8000/
```

## Environment variables

Backend:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ENVIRONMENT`

Frontend:

- `VITE_API_BASE_URL`

## Supabase setup

Run:

1. `database/schema.sql`
2. Any per-game SQL file you have not already applied:
   - `database/mmse_schema.sql`
   - `database/nback_schema.sql`
   - `database/boston_naming_schema.sql`
   - `database/trail_making_schema.sql`

Main game tables:

- `patients`
- `assessments`
- `mmse_results`
- `memory_results`
- `nback_results`
- `boston_naming_results`
- `trail_making_results`
- `trail_making_events`

## API endpoints

```text
POST /api/assessments
POST /api/assessments/{assessment_id}/games/mmse/complete
POST /api/assessments/{assessment_id}/games/memory/complete
POST /api/assessments/{assessment_id}/games/nback/complete
POST /api/assessments/{assessment_id}/games/boston-naming/complete
POST /api/assessments/{assessment_id}/games/trail-making/complete
```

## Trail Making summary

Trail Making is a Part-B-style alternating sequence:

```text
1 -> A -> 2 -> B -> 3 -> C -> ... -> 12 -> L -> 13
```

Trail Making persists:

- Summary features in `trail_making_results`
- Raw sampled pointer/click telemetry in `trail_making_events`
- Deterministic node layout in `trail_making_results.layout`

### Model 1-compatible Trail Making fields

- `path_efficiency`
- `sequence_accuracy`
- `switching_delay`
- `backtracking_frequency`
- `rule_violation_count`
- `cursor_movement_entropy`
- `trajectory_deviation`
- `tremor_jitter_frequency`

### Additional stored Trail Making fields

- `total_completion_time`
- `total_error_count`
- `correct_target_count`
- `mean_reaction_time`
- `median_reaction_time`
- `reaction_time_variance`
- `hesitation_duration`
- `error_recovery_time`
- `first_half_time`
- `second_half_time`
- `time_degradation_ratio`
- `switch_count`
- `correct_switch_count`
- `incorrect_switch_count`
- `backtracking_distance`
- `trajectory_length`
- `ideal_path_length`
- `correction_count`
- `idle_time`

### Key formulas

- `path_efficiency = ideal_path_length / actual_path_length`
- `sequence_accuracy = correct_target_count / total_targets`
- `switching_delay = mean(correct target reaction time after the first target)`
- `backtracking_frequency = backtracking_count / total_targets`
- `trajectory_deviation = mean((actual_segment_length - ideal_segment_length) / ideal_segment_length)`
- `tremor_jitter_frequency = (direction_reversals + micro_movements) / total_time_seconds`

## Verification SQL

Verify one Trail Making result:

```sql
select *
from trail_making_results
where assessment_id = 'YOUR_ASSESSMENT_ID';
```

Verify raw Trail Making telemetry:

```sql
select event_type, count(*) as row_count
from trail_making_events
where assessment_id = 'YOUR_ASSESSMENT_ID'
group by event_type
order by event_type;
```

Verify that all five games share the same assessment:

```sql
select 'assessments' as table_name, exists(select 1 from assessments where assessment_id = 'YOUR_ASSESSMENT_ID') as row_exists
union all
select 'mmse_results', exists(select 1 from mmse_results where assessment_id = 'YOUR_ASSESSMENT_ID')
union all
select 'memory_results', exists(select 1 from memory_results where assessment_id = 'YOUR_ASSESSMENT_ID')
union all
select 'nback_results', exists(select 1 from nback_results where assessment_id = 'YOUR_ASSESSMENT_ID')
union all
select 'boston_naming_results', exists(select 1 from boston_naming_results where assessment_id = 'YOUR_ASSESSMENT_ID')
union all
select 'trail_making_results', exists(select 1 from trail_making_results where assessment_id = 'YOUR_ASSESSMENT_ID')
union all
select 'trail_making_events', exists(select 1 from trail_making_events where assessment_id = 'YOUR_ASSESSMENT_ID');
```

## Testing

Backend:

```bash
cd backend
python -m pytest tests -q
```

Frontend:

```bash
cd frontend
npm run build
```

## Current verification status

- Backend tests pass locally
- Frontend production build passes locally
- Live Supabase verification must still be performed in your local environment after applying the SQL schema files

## Limitations

- No authentication
- No end-to-end browser automation yet
- Trail Making pointer telemetry is sampled rather than recorded at every single browser movement
- The system is a research/demo prototype, not a clinical instrument
