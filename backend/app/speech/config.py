from __future__ import annotations

import os
from pathlib import Path

# Prevent macOS OpenMP conflict between ctranslate2 (faster-whisper) and PyTorch
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# If Hugging Face encoders are cached locally, enable offline mode to prevent redundant remote requests
_hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
if (_hf_cache / "models--facebook--wav2vec2-base").exists() and (
    (_hf_cache / "models--distilbert-base-uncased").exists()
    or (_hf_cache / "models--distilbert--distilbert-base-uncased").exists()
):
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

# Paths
DEFAULT_PACKAGE_DIR = Path(__file__).resolve().parents[2] / "models" / "model3" / "neurodetect_model3_process2_package"
FALLBACK_PACKAGE_DIR = Path(__file__).resolve().parents[3] / "neurodetect_model3_process2_package"

MODEL3_PACKAGE_DIR = Path(os.getenv("MODEL3_PACKAGE_DIR", str(DEFAULT_PACKAGE_DIR if DEFAULT_PACKAGE_DIR.exists() else FALLBACK_PACKAGE_DIR)))

# Audio constraints
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MIN_DURATION_SECONDS = 0.5
MAX_DURATION_SECONDS = 300.0  # 5 minutes

SUPPORTED_AUDIO_MIME_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/mpeg",
    "audio/m4a",
    "audio/aac",
    "audio/x-m4a",
}

# Transcription configuration
# Supported providers: "pluggable_local_asr", "whisper_local", "mock", "manual"
TRANSCRIPTION_ENGINE = os.getenv("TRANSCRIPTION_ENGINE", "pluggable_local_asr")

# Disclaimer
MODEL3_DISCLAIMER = (
    "NeuroDetect Model 3 is an experimental speech-based research screening model. "
    "Its predictions are not a medical diagnosis and must not be used as a substitute for professional clinical assessment."
)
ASR_VERIFICATION_NOTICE = (
    "Note: Model 3 was trained on human clinical transcripts. Predictions derived from automatic speech recognition (ASR) "
    "are flagged as awaiting ASR compatibility verification to account for potential disfluency/filler shifts."
)
