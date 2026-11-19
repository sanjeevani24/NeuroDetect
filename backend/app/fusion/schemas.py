"""
Pydantic schemas for the NeuroDetect Multimodal Fusion Engine.
"""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


FusionInterpretation = Literal[
    "NO_ELEVATED_INDICATORS",
    "FURTHER_ASSESSMENT",
    "ELEVATED_COGNITIVE_INDICATORS",
    "INSUFFICIENT_DATA",
]

CognitiveConclusion = Literal[
    "NO_ELEVATED_INDICATORS",
    "FURTHER_ASSESSMENT",
    "ELEVATED_COGNITIVE_INDICATORS",
]

Model1CognitiveCategory = Literal[
    "NORMAL",
    "BORDERLINE",
    "LOW",
    "UNKNOWN",
]

Model3SpeechCategory = Literal[
    "HC_DOMINANT",
    "MCI_INDICATIVE",
    "DEMENTIA_INDICATIVE",
    "UNCERTAIN",
    "UNKNOWN",
]

VerificationStatus = Literal[
    "COMPLETE",
    "PROVISIONAL",
    "UNVERIFIED",
]


class MentalHealthContext(BaseModel):
    phq9_score: int | None = None
    phq9_severity: str | None = None
    gad7_score: int | None = None
    gad7_severity: str | None = None
    depression_elevated: bool = False
    anxiety_elevated: bool = False
    contextual_flags: list[str] = Field(default_factory=list)


class KeyFinding(BaseModel):
    title: str
    status_label: str
    summary: str
    badge_variant: str = "default"  # "success", "warning", "error", "neutral"


class FusionKeyFindings(BaseModel):
    cognitive_games: KeyFinding
    speech_analysis: KeyFinding
    mental_health: KeyFinding


class FusionResultSummary(BaseModel):
    available: bool = True
    status: Literal["completed", "provisional", "insufficient_data", "pending"] = "completed"
    title: str = "Final Assessment Conclusion"
    interpretation: FusionInterpretation
    interpretation_label: str
    conclusion: str
    verification_status: VerificationStatus = "COMPLETE"
    provisional_warning: str | None = None
    recommended_next_step: str = ""
    recommended_steps: list[str] = Field(default_factory=list)
    key_findings: FusionKeyFindings | None = None

    # Primary Cognitive Components (50% / 50%)
    model1_score: float | None = None
    model1_category: Model1CognitiveCategory = "UNKNOWN"
    model1_weight_percent: int = 50

    model3_predicted_class: str | None = None
    model3_category: Model3SpeechCategory = "UNKNOWN"
    model3_weight_percent: int = 50
    model3_probabilities: dict[str, float] | None = None

    # Contextual Component (Model 2)
    mental_health_context: MentalHealthContext = Field(default_factory=MentalHealthContext)
    contextual_flags: list[str] = Field(default_factory=list)

    # Explanation and Transparency
    rules_triggered: list[str] = Field(default_factory=list)
    explanation: str
    disclaimer: str
