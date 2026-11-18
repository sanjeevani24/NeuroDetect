"""
Configuration and thresholds for NeuroDetect Multimodal Fusion Engine.

All thresholds are configurable via environment variables with statistically defensible defaults
derived from the 47-feature Model 1 XGBoost regressor (500 trees, 16,000 training samples)
and PROCESS-2 Model 3 multimodal speech classifier.
"""
from __future__ import annotations

import os

# --- Model 1 Cognitive Performance Thresholds ---
# Direction: Higher score indicates better cognitive performance.
# Basis: Derived from empirical tree splits on 47 cognitive-game features.
# - MMSE 24 (clinical cutoff for impairment) predicts ~75-78 on Model 1.
# - MMSE 20 (moderate impairment boundary) predicts ~65 on Model 1.
# - MMSE 27-30 (healthy intact cognition) predicts >85 on Model 1.
MODEL1_NORMAL_THRESHOLD: float = float(os.getenv("MODEL1_NORMAL_THRESHOLD", "75.0"))
MODEL1_BORDERLINE_THRESHOLD: float = float(os.getenv("MODEL1_BORDERLINE_THRESHOLD", "65.0"))

# --- Model 3 Speech Assessment Thresholds ---
# Margin between the top probability and second-highest probability required for decisive categorization.
# If margin < SPEECH_UNCERTAINTY_MARGIN or top probability < SPEECH_MIN_DOMINANT_PROB, speech is deemed UNCERTAIN.
SPEECH_UNCERTAINTY_MARGIN: float = float(os.getenv("SPEECH_UNCERTAINTY_MARGIN", "0.08"))
SPEECH_MIN_DOMINANT_PROB: float = float(os.getenv("SPEECH_MIN_DOMINANT_PROB", "0.40"))

# Tolerance for probability distribution sum check (sum must be ~1.0)
PROBABILITY_SUM_TOLERANCE: float = float(os.getenv("PROBABILITY_SUM_TOLERANCE", "0.02"))

# --- Model 2 Mental Health Screening Cutoffs (Clinical Standards) ---
PHQ9_ELEVATED_THRESHOLD: int = int(os.getenv("PHQ9_ELEVATED_THRESHOLD", "10"))  # Moderate depression cutoff
GAD7_ELEVATED_THRESHOLD: int = int(os.getenv("GAD7_ELEVATED_THRESHOLD", "10"))  # Moderate anxiety cutoff

# Weight distribution (documented primary cognitive indicators)
MODEL1_WEIGHT_PERCENT: int = 50
MODEL3_WEIGHT_PERCENT: int = 50

# Disclaimers & Notices
FUSION_DISCLAIMER: str = (
    "NeuroDetect is an experimental research screening prototype, not a diagnostic tool. "
    "Multimodal fusion results reflect algorithmic risk stratification across standardized research stimuli "
    "and must not be interpreted as a medical diagnosis. Clinical evaluation by a qualified specialist is required."
)

PROVISIONAL_ASR_WARNING: str = (
    "PROVISIONAL RESULT: Speech classification was performed on an automated speech recognition (ASR) transcript "
    "awaiting clinical verification. Model 3 was trained on human clinical transcripts; automated transcription "
    "may introduce shifts in acoustic-linguistic alignment or disfluency representation."
)
