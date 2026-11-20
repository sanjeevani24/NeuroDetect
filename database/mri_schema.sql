-- ==============================================================================
-- NeuroDetect: MRI Assessment & Model 4 Schema Migration
-- 
-- ARCHITECTURE & INTEGRATION SPECIFICATION:
--   1. Non-destructive: preserves existing patient and cognitive assessment data.
--   2. Extends public.assessments with assessment_type ('COGNITIVE' | 'MRI_ONLY').
--      Defaults to 'COGNITIVE' so all existing historical sessions remain valid.
--   3. Creates dedicated public.mri_assessments table referencing public.assessments(assessment_id).
--   4. Enforces strict Row Level Security (RLS) ensuring access is restricted to service_role.
--   5. Eliminates any unrestricted public policies.
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. EXTEND public.assessments TABLE
-- ------------------------------------------------------------------------------
ALTER TABLE public.assessments 
ADD COLUMN IF NOT EXISTS assessment_type TEXT NOT NULL DEFAULT 'COGNITIVE';

DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_assessments_type'
    ) THEN 
        ALTER TABLE public.assessments 
        ADD CONSTRAINT check_assessments_type 
        CHECK (assessment_type IN ('COGNITIVE', 'MRI_ONLY')); 
    END IF; 
END $$;

CREATE INDEX IF NOT EXISTS idx_assessments_type ON public.assessments (assessment_type);

-- ------------------------------------------------------------------------------
-- 2. CREATE public.mri_assessments TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.mri_assessments (
    mri_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES public.assessments (assessment_id) ON DELETE CASCADE,
    image_filename TEXT,
    image_format TEXT,
    image_size_bytes INTEGER,
    processing_status TEXT NOT NULL DEFAULT 'completed',
    model_name TEXT NOT NULL DEFAULT 'NeuroDetect-MRI-EfficientNetB0',
    model_version TEXT NOT NULL DEFAULT '1.0.0',
    predicted_class TEXT NOT NULL,
    predicted_class_index INTEGER NOT NULL,
    probability_non_demented DOUBLE PRECISION NOT NULL,
    probability_very_mild DOUBLE PRECISION NOT NULL,
    probability_mild DOUBLE PRECISION NOT NULL,
    probability_moderate DOUBLE PRECISION NOT NULL,
    binary_prediction TEXT NOT NULL,
    binary_probability_dementia DOUBLE PRECISION NOT NULL,
    binary_probability_no_dementia DOUBLE PRECISION NOT NULL,
    disclaimer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT mri_assessments_assessment_id_unique UNIQUE (assessment_id)
);

CREATE INDEX IF NOT EXISTS idx_mri_assessments_assessment_id ON public.mri_assessments (assessment_id);

-- ------------------------------------------------------------------------------
-- 3. ROW LEVEL SECURITY (RLS) & ACCESS CONTROL
-- ------------------------------------------------------------------------------
-- Enable Row Level Security
ALTER TABLE public.mri_assessments ENABLE ROW LEVEL SECURITY;

-- Drop any permissive public policies that might have been inadvertently created
DROP POLICY IF EXISTS "Allow public read access on mri_assessments" ON public.mri_assessments;
DROP POLICY IF EXISTS "Allow public insert on mri_assessments" ON public.mri_assessments;
DROP POLICY IF EXISTS "Allow public update on mri_assessments" ON public.mri_assessments;

-- Ensure service_role policy is in place
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'mri_assessments' AND policyname = 'Service role full access on mri_assessments'
    ) THEN 
        CREATE POLICY "Service role full access on mri_assessments" 
        ON public.mri_assessments 
        FOR ALL 
        TO service_role 
        USING (true) 
        WITH CHECK (true); 
    END IF; 
END $$;
