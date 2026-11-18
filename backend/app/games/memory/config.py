"""
Centralized constants for the Memory Recall game (backend side).

These must stay consistent with frontend/src/games/memory/config/memoryConfig.ts.
Duplication is intentional: the frontend needs these values at render time and
the backend needs them for feature extraction/validation independent of any
single request payload.
"""

TARGET_ITEM_COUNT = 12

HESITATION_THRESHOLD_SECONDS = 2.0

# Phases that must each report at least one `phase_completed` event before a
# completion request is accepted. DISTRACTOR is required to exist as a phase
# but produces no memory features itself.
REQUIRED_PHASES = [
    "LEARNING",
    "IMMEDIATE_RECALL",
    "DISTRACTOR",
    "DELAYED_RECALL",
    "RECOGNITION",
    "CONFIDENCE",
]

CONFIDENCE_PHASES = ["immediate_recall", "delayed_recall", "recognition"]
