# Database

This milestone uses three tables in Supabase Postgres: `patients`,
`assessments`, `memory_results`.

## Setup

1. Create a Supabase project.
2. Open the SQL editor and run `schema.sql`.
3. Copy your project URL and **service role key** into the backend's `.env`
   (see `/backend/.env.example`, sourced from the repo-root `.env.example`).
   The service-role key must never be given to the frontend.

## Notes

- `memory_results.assessment_id` has a `UNIQUE` constraint — at most one
  completed Memory Recall result can exist per assessment. The backend also
  enforces this at the application layer before insert, so the constraint
  is a safety net, not the primary guard.
- The Memory Recall game never creates an `assessment` row — it expects an
  existing `assessment_id` to be supplied to it.
- No diagnostic or classification columns exist in this schema. That is
  intentional and out of scope for this milestone.
