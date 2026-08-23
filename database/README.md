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

## Setup

1. Create a Supabase project.
2. Run `schema.sql`.
3. If your project was built incrementally, also run any missing per-game SQL files in this folder.
4. Copy your project URL and **service role key** into the backend `.env`.

## Notes

- Each `*_results.assessment_id` is intended to store one completed row per game per assessment.
- `trail_making_events` stores raw sampled telemetry keyed by both `assessment_id` and `game_session_id`.
- Assessment creation happens via the backend API and the frontend start flow, not inside individual game modules.
- No diagnostic or prediction tables are persisted here.
