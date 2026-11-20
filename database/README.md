# Database

NeuroDetect uses shared assessment tables plus per-game result storage:

- `patients`
- `assessments`
- `mmse_results`
- `memory_results`
- `nback_results`
- `boston_naming_results`
- `trail_making_results`
- `trail_making_events`
- `speech_assessments`
- `model3_results`
- `mri_assessments`

## Setup

1. Create a Supabase project.
2. Run `schema.sql`.
3. If your project was built incrementally, also run any missing per-game SQL files in this folder.
4. Copy your project URL and **service role key** into the backend `.env`.

## MRI Assessment & Model 4 Migration

To enable the MRI Assessment pathway in Supabase, run:

```bash
# Execute in Supabase SQL Editor:
database/mri_schema.sql
```

This migration:
- Adds `assessment_type` (`COGNITIVE` or `MRI_ONLY`) to `assessments`.
- Creates `mri_assessments` referencing `assessments(assessment_id)`.
- Enforces Row Level Security (RLS) with backend-only service-role access.
- Non-destructively preserves all existing patient and cognitive assessment data.

## Speech Assessment & Model 3 Migration

If you already have an existing `speech_assessments` table in Supabase, run:

```bash
# Execute in Supabase SQL Editor:
database/speech_and_model3_schema.sql
```

This migration:
- Preserves the existing `speech_assessments` table and all existing rows.
- Non-destructively adds telemetry columns (`duration_seconds`, `audio_format`, etc.) using `ADD COLUMN IF NOT EXISTS`.
- Creates `model3_results` referencing `speech_assessments(speech_id)` and `assessments(assessment_id)`.
- Enforces Row Level Security (RLS) and removes unrestricted public policies.
- Keeps service-role access backend-only.

## Notes

- Each `*_results.assessment_id` is intended to store one completed row per game per assessment.
- `trail_making_events` stores raw sampled telemetry keyed by both `assessment_id` and `game_session_id`.
- Assessment creation happens via the backend API and the frontend start flow, not inside individual game modules.
- No diagnostic or prediction tables are persisted here.
