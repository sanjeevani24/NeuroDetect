-- ==============================================================================
-- NeuroDetect: Speech Assessment & Model 3 Schema Compatibility & Security Migration
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. PRESERVE AND EXTEND public.speech_assessments
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

CREATE INDEX IF NOT EXISTS idx_speech_assessments_assessment_id 
    ON public.speech_assessments(assessment_id);


-- 2. CREATE public.model3_results TABLE
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


-- 3. ROW LEVEL SECURITY (RLS) & ACCESS CONTROL AUDIT
ALTER TABLE public.speech_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model3_results ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access on speech_assessments" ON public.speech_assessments;
DROP POLICY IF EXISTS "Allow public insert on speech_assessments" ON public.speech_assessments;
DROP POLICY IF EXISTS "Allow public update on speech_assessments" ON public.speech_assessments;

DROP POLICY IF EXISTS "Allow public read access on model3_results" ON public.model3_results;
DROP POLICY IF EXISTS "Allow public insert on model3_results" ON public.model3_results;
DROP POLICY IF EXISTS "Allow public update on model3_results" ON public.model3_results;
