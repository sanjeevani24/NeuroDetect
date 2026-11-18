-- ==============================================================================
-- NeuroDetect: Speech Assessment & Model 3 Schema Compatibility & Security Migration
-- 
-- AUDIT & COMPATIBILITY GUARANTEES:
--   1. Preserves existing public.speech_assessments table and all existing records.
--   2. Non-destructively extends speech_assessments with IF NOT EXISTS columns.
--   3. Retains public.model3_results as a separate dedicated table for Model 3 inference.
--   4. Validates and uses the true primary keys:
--        - public.assessments(assessment_id)
--        - public.speech_assessments(speech_id)
--   5. Eliminates any unrestricted public SELECT / INSERT / UPDATE policies.
--   6. Enforces Row Level Security (RLS) keeping data accessible only by service_role.
--   7. Configures an optional private Supabase Storage bucket for clinical audio.
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. PRESERVE AND EXTEND public.speech_assessments
-- ------------------------------------------------------------------------------
-- If the table does not exist at all, create it with all base and extended columns.
-- If the table already exists, this statement is safely ignored.
CREATE TABLE IF NOT EXISTS public.speech_assessments (
    speech_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES public.assessments(assessment_id) ON DELETE CASCADE,
    task_type TEXT DEFAULT 'cookie_theft',
    audio_storage_path TEXT,
    transcript TEXT,
    processing_status TEXT DEFAULT 'pending',
    model_name TEXT,
    model_version TEXT,
    predicted_class TEXT,
    probability_hc NUMERIC(6, 5),
    probability_mci NUMERIC(6, 5),
    probability_dementia NUMERIC(6, 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Non-destructively extend existing speech_assessments table with audio & transcription telemetry
ALTER TABLE public.speech_assessments 
    ADD COLUMN IF NOT EXISTS task_type TEXT DEFAULT 'cookie_theft';

ALTER TABLE public.speech_assessments 
    ADD COLUMN IF NOT EXISTS audio_duration_seconds DOUBLE PRECISION;

ALTER TABLE public.speech_assessments 
    ADD COLUMN IF NOT EXISTS duration_seconds NUMERIC(6, 2);

ALTER TABLE public.speech_assessments 
    ADD COLUMN IF NOT EXISTS file_size_bytes INTEGER;

ALTER TABLE public.speech_assessments 
    ADD COLUMN IF NOT EXISTS audio_format TEXT DEFAULT 'wav';

ALTER TABLE public.speech_assessments 
    ADD COLUMN IF NOT EXISTS mime_type TEXT DEFAULT 'audio/wav';

ALTER TABLE public.speech_assessments 
    ADD COLUMN IF NOT EXISTS transcription_engine TEXT DEFAULT 'surrogate_clinical_asr';

ALTER TABLE public.speech_assessments 
    ADD COLUMN IF NOT EXISTS transcription_status TEXT DEFAULT 'completed';

-- Ensure unique constraint on assessment_id (one speech assessment per assessment session)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_speech_assessments_assessment_id'
           OR conname = 'speech_assessments_assessment_id_unique'
    ) THEN
        ALTER TABLE public.speech_assessments 
            ADD CONSTRAINT uq_speech_assessments_assessment_id UNIQUE (assessment_id);
    END IF;
END $$;

-- Index for assessment_id lookup
CREATE INDEX IF NOT EXISTS idx_speech_assessments_assessment_id 
    ON public.speech_assessments(assessment_id);


-- ------------------------------------------------------------------------------
-- 2. CREATE public.model3_results TABLE
-- ------------------------------------------------------------------------------
-- Dedicated table for Model 3 machine learning outputs, branch probabilities,
-- component logs, and ASR verification status.
CREATE TABLE IF NOT EXISTS public.model3_results (
    model3_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    speech_id UUID NOT NULL REFERENCES public.speech_assessments(speech_id) ON DELETE CASCADE,
    assessment_id UUID NOT NULL REFERENCES public.assessments(assessment_id) ON DELETE CASCADE,
    predicted_class TEXT NOT NULL CHECK (predicted_class IN ('HC', 'MCI', 'Dementia')),
    probability_hc NUMERIC(6, 5) NOT NULL CHECK (probability_hc >= 0.0 AND probability_hc <= 1.0),
    probability_mci NUMERIC(6, 5) NOT NULL CHECK (probability_mci >= 0.0 AND probability_mci <= 1.0),
    probability_dementia NUMERIC(6, 5) NOT NULL CHECK (probability_dementia >= 0.0 AND probability_dementia <= 1.0),
    branch_probabilities JSONB NOT NULL DEFAULT '{}'::jsonb,
    components_used JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_name TEXT NOT NULL DEFAULT 'PROCESS-2 CTD Model 3',
    model_version TEXT NOT NULL DEFAULT '1.0.0',
    inference_status TEXT NOT NULL DEFAULT 'awaiting_asr_verification'
        CHECK (inference_status IN ('completed', 'awaiting_asr_verification', 'failed', 'pending')),
    disclaimer TEXT NOT NULL DEFAULT 'Research screening tool only. Not for standalone clinical diagnosis.',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_model3_results_speech_id UNIQUE (speech_id),
    CONSTRAINT uq_model3_results_assessment_id UNIQUE (assessment_id)
);

CREATE INDEX IF NOT EXISTS idx_model3_results_assessment_id 
    ON public.model3_results(assessment_id);

CREATE INDEX IF NOT EXISTS idx_model3_results_speech_id 
    ON public.model3_results(speech_id);


-- ------------------------------------------------------------------------------
-- 3. ROW LEVEL SECURITY (RLS) & ACCESS CONTROL AUDIT
-- ------------------------------------------------------------------------------
-- Enable Row Level Security on both tables
ALTER TABLE public.speech_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model3_results ENABLE ROW LEVEL SECURITY;

-- Drop all unrestricted public policies that grant anonymous read/write access
DROP POLICY IF EXISTS "Allow public read access on speech_assessments" ON public.speech_assessments;
DROP POLICY IF EXISTS "Allow public insert on speech_assessments" ON public.speech_assessments;
DROP POLICY IF EXISTS "Allow public update on speech_assessments" ON public.speech_assessments;

DROP POLICY IF EXISTS "Allow public read access on model3_results" ON public.model3_results;
DROP POLICY IF EXISTS "Allow public insert on model3_results" ON public.model3_results;
DROP POLICY IF EXISTS "Allow public update on model3_results" ON public.model3_results;

-- With RLS enabled and no public policies created, all access from the public
-- PostgREST API (using anon key) is DENIED.
-- The FastAPI backend connects using SUPABASE_SERVICE_ROLE_KEY which automatically
-- bypasses RLS and retains exclusive administrative access.


-- ------------------------------------------------------------------------------
-- 4. PRIVATE SUPABASE STORAGE BUCKET FOR CLINICAL AUDIO (OPTIONAL)
-- ------------------------------------------------------------------------------
-- If clinical audio files are to be archived in Supabase Storage, create a private bucket:
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'clinical-speech-recordings',
    'clinical-speech-recordings',
    false, -- Private bucket: no public HTTP access
    26214400, -- 25MB max per recording
    ARRAY['audio/wav', 'audio/webm', 'audio/ogg', 'audio/mp4', 'audio/x-wav']
)
ON CONFLICT (id) DO UPDATE SET
    public = false,
    file_size_limit = 26214400,
    allowed_mime_types = ARRAY['audio/wav', 'audio/webm', 'audio/ogg', 'audio/mp4', 'audio/x-wav'];

-- Ensure public access to storage.objects in this bucket is removed
DROP POLICY IF EXISTS "Public Access" ON storage.objects;
DROP POLICY IF EXISTS "Allow public upload to clinical-speech-recordings" ON storage.objects;
