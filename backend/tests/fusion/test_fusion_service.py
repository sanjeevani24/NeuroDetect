"""
Comprehensive unit tests for the NeuroDetect Multimodal Fusion Engine.
Covers:
- All 9 matrix rule combinations
- Uncertain speech with Normal, Borderline, and Low cognitive performance
- Probability distribution validation (non-finite, negative, sum != 1, missing keys)
- Missing model outputs (missing Model 1, missing Model 3, missing both, failed speech)
- Provisional ASR status vs Complete status
- Non-causal mental health contextual flags (Model 2)
- Threshold configurability
- Results router fusion endpoint
"""
from __future__ import annotations

import math
import pytest

from app.fusion.config import (
    MODEL1_BORDERLINE_THRESHOLD,
    MODEL1_NORMAL_THRESHOLD,
    PROVISIONAL_ASR_WARNING,
)
from app.fusion.service import FusionService


@pytest.fixture
def service() -> FusionService:
    return FusionService()


def make_model1(score: float, available: bool = True) -> dict:
    return {
        "available": available,
        "cognitive_performance_score": score,
        "model_name": "NeuroDetect Model 1",
        "model_version": "1.0.0",
    }


def make_model3(
    predicted_class: str = "HC",
    p_hc: float = 0.80,
    p_mci: float = 0.15,
    p_dem: float = 0.05,
    status: str = "completed",
    available: bool = True,
) -> dict:
    return {
        "available": available,
        "status": status,
        "predicted_class": predicted_class,
        "hc_probability": p_hc,
        "mci_probability": p_mci,
        "dementia_probability": p_dem,
        "probabilities": {"HC": p_hc, "MCI": p_mci, "Dementia": p_dem},
    }


def make_mh(phq9_score: int = 2, phq9_sev: str = "Minimal", gad7_score: int = 1, gad7_sev: str = "Minimal") -> dict:
    return {
        "phq9": {"available": True, "score": phq9_score, "severity": phq9_sev},
        "gad7": {"available": True, "score": gad7_score, "severity": gad7_sev},
    }


# =============================================================================
# 1. Primary Rule Matrix Tests (9 combinations)
# =============================================================================

@pytest.mark.parametrize(
    "m1_score, speech_class, p_hc, p_mci, p_dem, expected_interpretation, expected_m1_cat, expected_m3_cat",
    [
        # NORMAL + HC -> NO_ELEVATED_INDICATORS
        (85.0, "HC", 0.80, 0.15, 0.05, "NO_ELEVATED_INDICATORS", "NORMAL", "HC_DOMINANT"),
        # BORDERLINE + HC -> NO_ELEVATED_INDICATORS
        (70.0, "HC", 0.80, 0.15, 0.05, "NO_ELEVATED_INDICATORS", "BORDERLINE", "HC_DOMINANT"),
        # LOW + HC -> FURTHER_ASSESSMENT
        (55.0, "HC", 0.80, 0.15, 0.05, "FURTHER_ASSESSMENT", "LOW", "HC_DOMINANT"),
        # NORMAL + MCI -> FURTHER_ASSESSMENT
        (85.0, "MCI", 0.15, 0.75, 0.10, "FURTHER_ASSESSMENT", "NORMAL", "MCI_INDICATIVE"),
        # BORDERLINE + MCI -> FURTHER_ASSESSMENT
        (70.0, "MCI", 0.15, 0.75, 0.10, "FURTHER_ASSESSMENT", "BORDERLINE", "MCI_INDICATIVE"),
        # LOW + MCI -> ELEVATED_COGNITIVE_INDICATORS
        (55.0, "MCI", 0.15, 0.75, 0.10, "ELEVATED_COGNITIVE_INDICATORS", "LOW", "MCI_INDICATIVE"),
        # NORMAL + Dementia -> FURTHER_ASSESSMENT
        (85.0, "Dementia", 0.10, 0.15, 0.75, "FURTHER_ASSESSMENT", "NORMAL", "DEMENTIA_INDICATIVE"),
        # BORDERLINE + Dementia -> FURTHER_ASSESSMENT
        (70.0, "Dementia", 0.10, 0.15, 0.75, "FURTHER_ASSESSMENT", "BORDERLINE", "DEMENTIA_INDICATIVE"),
        # LOW + Dementia -> ELEVATED_COGNITIVE_INDICATORS
        (55.0, "Dementia", 0.10, 0.15, 0.75, "ELEVATED_COGNITIVE_INDICATORS", "LOW", "DEMENTIA_INDICATIVE"),
    ],
)
def test_fusion_rule_matrix_combinations(
    service: FusionService,
    m1_score: float,
    speech_class: str,
    p_hc: float,
    p_mci: float,
    p_dem: float,
    expected_interpretation: str,
    expected_m1_cat: str,
    expected_m3_cat: str,
):
    m1 = make_model1(m1_score)
    m3 = make_model3(predicted_class=speech_class, p_hc=p_hc, p_mci=p_mci, p_dem=p_dem)
    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh())

    assert res.available is True
    assert res.interpretation == expected_interpretation
    assert res.model1_category == expected_m1_cat
    assert res.model3_category == expected_m3_cat
    assert res.model1_score == m1_score
    assert len(res.rules_triggered) > 0
    assert len(res.explanation) > 0
    assert res.verification_status == "COMPLETE"
    assert res.provisional_warning is None


# =============================================================================
# 2. Uncertain Speech Results Tests
# =============================================================================

def test_uncertain_speech_due_to_close_margin(service: FusionService):
    # Top is HC (0.38), second is MCI (0.35) -> margin 0.03 < 0.08
    m3 = make_model3(predicted_class="HC", p_hc=0.38, p_mci=0.35, p_dem=0.27)
    cat, notes = service.classify_model3("HC", m3["probabilities"])
    assert cat == "UNCERTAIN"
    assert any("margin" in n.lower() for n in notes)


def test_uncertain_speech_due_to_low_dominant_probability(service: FusionService):
    # Equal distribution around 0.33
    m3 = make_model3(predicted_class="HC", p_hc=0.35, p_mci=0.33, p_dem=0.32)
    cat, notes = service.classify_model3("HC", m3["probabilities"])
    assert cat == "UNCERTAIN"


@pytest.mark.parametrize(
    "m1_score",
    [85.0, 70.0, 50.0],
)
def test_uncertain_speech_fusion_resolutions(service: FusionService, m1_score: float):
    m1 = make_model1(m1_score)
    m3 = make_model3(predicted_class="HC", p_hc=0.36, p_mci=0.34, p_dem=0.30)
    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh())

    assert res.model3_category == "UNCERTAIN"
    assert res.interpretation == "FURTHER_ASSESSMENT"
    assert res.conclusion == "Further Assessment Recommended"
    assert any("UNCERTAIN_SPEECH" in r for r in res.rules_triggered)


# =============================================================================
# 3. Model 3 Probability Validation Tests
# =============================================================================

def test_rejects_non_finite_probability(service: FusionService):
    assert service.validate_speech_probabilities({"HC": float("nan"), "MCI": 0.5, "Dementia": 0.5}) is False
    assert service.validate_speech_probabilities({"HC": float("inf"), "MCI": 0.5, "Dementia": 0.5}) is False


def test_rejects_negative_probability(service: FusionService):
    assert service.validate_speech_probabilities({"HC": -0.1, "MCI": 0.6, "Dementia": 0.5}) is False


def test_rejects_probability_above_one(service: FusionService):
    assert service.validate_speech_probabilities({"HC": 1.2, "MCI": -0.1, "Dementia": -0.1}) is False


def test_rejects_deviating_probability_sum(service: FusionService):
    # Sum is 0.70, exceeds tolerance
    assert service.validate_speech_probabilities({"HC": 0.40, "MCI": 0.20, "Dementia": 0.10}) is False


def test_rejects_missing_class_keys(service: FusionService):
    assert service.validate_speech_probabilities({"HC": 0.7, "MCI": 0.3}) is False


# =============================================================================
# 4. Missing Outputs & Error Handling Tests
# =============================================================================

def test_insufficient_data_when_both_missing(service: FusionService):
    res = service.evaluate(model1_data=None, model3_data=None, mental_health_data=make_mh())
    assert res.available is False
    assert res.status == "insufficient_data"
    assert res.interpretation == "INSUFFICIENT_DATA"


def test_insufficient_data_when_model1_missing(service: FusionService):
    m3 = make_model3("HC", 0.8, 0.15, 0.05)
    res = service.evaluate(model1_data={"available": False}, model3_data=m3, mental_health_data=make_mh())
    assert res.available is False
    assert res.interpretation == "INSUFFICIENT_DATA"
    assert res.interpretation_label == "Insufficient Assessment Data"
    assert res.conclusion == "Insufficient Assessment Data"
    assert any("Cognitive games incomplete" in r for r in res.rules_triggered)


def test_insufficient_data_when_model3_missing(service: FusionService):
    m1 = make_model1(80.0)
    res = service.evaluate(model1_data=m1, model3_data={"available": False}, mental_health_data=make_mh())
    assert res.available is False
    assert res.interpretation == "INSUFFICIENT_DATA"
    assert res.interpretation_label == "Insufficient Assessment Data"
    assert res.conclusion == "Insufficient Assessment Data"
    assert any("Speech assessment incomplete" in r for r in res.rules_triggered)


def test_insufficient_data_when_speech_failed(service: FusionService):
    m1 = make_model1(80.0)
    m3 = make_model3(status="failed", available=True)
    res = service.evaluate(model1_data=m1, model3_data=m3, speech_inference_status="failed")
    assert res.available is False
    assert res.interpretation == "INSUFFICIENT_DATA"


# =============================================================================
# 5. Provisional ASR Status Tests
# =============================================================================

def test_provisional_status_when_awaiting_asr_verification(service: FusionService):
    m1 = make_model1(80.0)
    m3 = make_model3(predicted_class="HC", p_hc=0.8, p_mci=0.15, p_dem=0.05, status="awaiting_asr_verification")
    res = service.evaluate(
        model1_data=m1,
        model3_data=m3,
        mental_health_data=make_mh(),
        speech_inference_status="awaiting_asr_verification",
    )

    assert res.available is True
    assert res.status == "provisional"
    assert res.verification_status == "PROVISIONAL"
    assert res.provisional_warning == PROVISIONAL_ASR_WARNING


def test_complete_status_when_verified_or_completed(service: FusionService):
    m1 = make_model1(80.0)
    m3 = make_model3(predicted_class="HC", p_hc=0.8, p_mci=0.15, p_dem=0.05, status="completed")
    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh())

    assert res.status == "completed"
    assert res.verification_status == "COMPLETE"
    assert res.provisional_warning is None


def test_live_example_case_further_assessment_recommended(service: FusionService):
    # Model 1 score: 55.65 (LOW)
    # Model 3: HC leading prediction (47.9%), awaiting verification
    # Model 2: PHQ-9 Moderate (10), GAD-7 Moderately Severe (11)
    m1 = make_model1(55.65)
    m3 = make_model3(
        predicted_class="HC",
        p_hc=0.479,
        p_mci=0.321,
        p_dem=0.200,
        status="awaiting_asr_verification",
    )
    mh = make_mh(
        phq9_score=10,
        phq9_sev="Moderate",
        gad7_score=11,
        gad7_sev="Moderately severe",
    )

    res = service.evaluate(
        model1_data=m1,
        model3_data=m3,
        mental_health_data=mh,
        speech_inference_status="awaiting_asr_verification",
    )

    assert res.available is True
    assert res.interpretation == "FURTHER_ASSESSMENT"
    assert res.interpretation_label == "Further Assessment Recommended"
    assert res.conclusion == "Further Assessment Recommended"
    assert res.verification_status == "PROVISIONAL"
    assert res.model1_category == "LOW"
    assert res.model3_category == "HC_DOMINANT"
    assert res.mental_health_context.depression_elevated is True
    assert res.mental_health_context.anxiety_elevated is True
    assert "cognitive game assessment indicated low performance" in res.explanation.lower()
    assert "speech analysis identified healthy control as its leading prediction" in res.explanation.lower()
    assert "these findings differ, so further assessment is recommended" in res.explanation.lower()
    assert res.key_findings is not None
    assert res.key_findings.cognitive_games.status_label == "Below Expected Range"
    assert "Awaiting Clinician Verification" in res.key_findings.speech_analysis.status_label
    assert "47.9%" in res.key_findings.speech_analysis.status_label
    assert "Elevated Mood & Anxiety Symptoms" in res.key_findings.mental_health.status_label
    assert res.recommended_next_step != ""
    assert len(res.recommended_steps) >= 2


# =============================================================================
# 6. Model 2 Mental Health Contextual Flags (Non-Causal)
# =============================================================================

def test_elevated_depression_generates_contextual_flag_without_affecting_score(service: FusionService):
    m1 = make_model1(70.0)  # BORDERLINE
    m3 = make_model3("HC", 0.8, 0.15, 0.05)
    mh_elevated = make_mh(phq9_score=14, phq9_sev="Moderate", gad7_score=2, gad7_sev="Minimal")

    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=mh_elevated)

    assert res.interpretation == "NO_ELEVATED_INDICATORS"
    assert res.conclusion == "No Elevated Indicators Detected"
    assert res.mental_health_context.depression_elevated is True
    assert res.mental_health_context.anxiety_elevated is False
    assert len(res.contextual_flags) > 0
    assert any("depressive" in f.lower() for f in res.contextual_flags)


def test_elevated_anxiety_generates_contextual_flag(service: FusionService):
    m1 = make_model1(85.0)  # NORMAL
    m3 = make_model3("HC", 0.36, 0.34, 0.30)  # UNCERTAIN
    mh_elevated = make_mh(phq9_score=3, phq9_sev="Minimal", gad7_score=15, gad7_sev="Severe")

    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=mh_elevated)

    assert res.interpretation == "FURTHER_ASSESSMENT"
    assert res.conclusion == "Further Assessment Recommended"
    assert res.mental_health_context.anxiety_elevated is True
    assert any("anxiety" in f.lower() for f in res.contextual_flags)


def test_dual_elevation_contextual_flag(service: FusionService):
    m1 = make_model1(85.0)
    m3 = make_model3("HC", 0.8, 0.15, 0.05)
    mh_both = make_mh(phq9_score=16, phq9_sev="Moderately severe", gad7_score=12, gad7_sev="Moderate")

    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=mh_both)

    assert res.interpretation == "NO_ELEVATED_INDICATORS"
    assert res.conclusion == "No Elevated Indicators Detected"
    assert res.mental_health_context.depression_elevated is True
    assert res.mental_health_context.anxiety_elevated is True
    assert any("concurrent" in f.lower() for f in res.contextual_flags)


# =============================================================================
# 7. Configurable Thresholds Test
# =============================================================================

def test_configurable_model1_thresholds():
    custom_service = FusionService(
        model1_normal_threshold=80.0,
        model1_borderline_threshold=60.0,
    )
    # 78.0 is BORDERLINE under 80/60, but was NORMAL under 75/65
    assert custom_service.classify_model1(78.0) == "BORDERLINE"
    assert custom_service.classify_model1(82.0) == "NORMAL"
    assert custom_service.classify_model1(58.0) == "LOW"


# =============================================================================
# 8. Explicit Final Adjustment Verification Tests (Section 7)
# =============================================================================

def test_explicit_borderline_hc_produces_no_elevated_indicators(service: FusionService):
    m1 = make_model1(70.0)  # BORDERLINE
    m3 = make_model3("HC", 0.8, 0.15, 0.05)
    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh())
    assert res.interpretation == "NO_ELEVATED_INDICATORS"
    assert res.conclusion == "No Elevated Indicators Detected"
    assert "combined assessment did not identify elevated cognitive indicators" in res.explanation.lower()


def test_explicit_low_hc_produces_further_assessment(service: FusionService):
    m1 = make_model1(55.0)  # LOW
    m3 = make_model3("HC", 0.8, 0.15, 0.05)
    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh())
    assert res.interpretation == "FURTHER_ASSESSMENT"
    assert res.conclusion == "Further Assessment Recommended"
    assert "findings differ, so further assessment is recommended" in res.explanation.lower()


def test_explicit_borderline_mci_produces_further_assessment(service: FusionService):
    m1 = make_model1(70.0)  # BORDERLINE
    m3 = make_model3("MCI", 0.15, 0.75, 0.10)
    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh())
    assert res.interpretation == "FURTHER_ASSESSMENT"
    assert res.conclusion == "Further Assessment Recommended"
    assert "further assessment is recommended to understand these findings" in res.explanation.lower()


def test_explicit_low_mci_produces_elevated_cognitive_indicators(service: FusionService):
    m1 = make_model1(55.0)  # LOW
    m3 = make_model3("MCI", 0.15, 0.75, 0.10)
    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh())
    assert res.interpretation == "ELEVATED_COGNITIVE_INDICATORS"
    assert res.conclusion == "Elevated Cognitive Indicators"
    assert "elevated cognitive indicators were identified" in res.explanation.lower()


def test_explicit_borderline_dementia_produces_further_assessment(service: FusionService):
    m1 = make_model1(70.0)  # BORDERLINE
    m3 = make_model3("Dementia", 0.10, 0.15, 0.75)
    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh())
    assert res.interpretation == "FURTHER_ASSESSMENT"
    assert res.conclusion == "Further Assessment Recommended"
    assert "these findings require further assessment and professional review" in res.explanation.lower()


def test_explicit_low_dementia_produces_elevated_cognitive_indicators(service: FusionService):
    m1 = make_model1(55.0)  # LOW
    m3 = make_model3("Dementia", 0.10, 0.15, 0.75)
    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh())
    assert res.interpretation == "ELEVATED_COGNITIVE_INDICATORS"
    assert res.conclusion == "Elevated Cognitive Indicators"
    assert "elevated cognitive indicators were identified" in res.explanation.lower()


def test_explicit_uncertain_speech_produces_further_assessment(service: FusionService):
    m1 = make_model1(85.0)
    m3 = make_model3("HC", 0.36, 0.34, 0.30)  # margin 0.02 < 0.05
    res = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh())
    assert res.model3_category == "UNCERTAIN"
    assert res.interpretation == "FURTHER_ASSESSMENT"
    assert res.conclusion == "Further Assessment Recommended"
    assert "speech analysis did not produce a sufficiently clear leading prediction" in res.explanation.lower()


def test_explicit_missing_outputs_produce_insufficient_data(service: FusionService):
    res_both = service.evaluate(model1_data=None, model3_data=None, mental_health_data=make_mh())
    assert res_both.status == "insufficient_data"
    assert res_both.interpretation == "INSUFFICIENT_DATA"
    assert res_both.conclusion == "Insufficient Assessment Data"

    m3 = make_model3("HC", 0.8, 0.15, 0.05)
    res_m1_missing = service.evaluate(model1_data={"available": False}, model3_data=m3, mental_health_data=make_mh())
    assert res_m1_missing.status == "insufficient_data"
    assert res_m1_missing.interpretation == "INSUFFICIENT_DATA"
    assert res_m1_missing.conclusion == "Insufficient Assessment Data"

    m1 = make_model1(80.0)
    res_m3_missing = service.evaluate(model1_data=m1, model3_data={"available": False}, mental_health_data=make_mh())
    assert res_m3_missing.status == "insufficient_data"
    assert res_m3_missing.interpretation == "INSUFFICIENT_DATA"
    assert res_m3_missing.conclusion == "Insufficient Assessment Data"


def test_explicit_provisional_status_preserved_independently_of_conclusion(service: FusionService):
    # Provisional with NO_ELEVATED_INDICATORS
    m1_norm = make_model1(85.0)
    m3_prov_hc = make_model3("HC", 0.8, 0.15, 0.05, status="awaiting_asr_verification")
    res1 = service.evaluate(model1_data=m1_norm, model3_data=m3_prov_hc, mental_health_data=make_mh(), speech_inference_status="awaiting_asr_verification")
    assert res1.status == "provisional"
    assert res1.verification_status == "PROVISIONAL"
    assert res1.interpretation == "NO_ELEVATED_INDICATORS"
    assert res1.conclusion == "No Elevated Indicators Detected"
    assert res1.provisional_warning is not None
    assert "awaiting clinical verification" in res1.explanation.lower()

    # Provisional with FURTHER_ASSESSMENT
    m1_low = make_model1(55.0)
    res2 = service.evaluate(model1_data=m1_low, model3_data=m3_prov_hc, mental_health_data=make_mh(), speech_inference_status="awaiting_asr_verification")
    assert res2.status == "provisional"
    assert res2.verification_status == "PROVISIONAL"
    assert res2.interpretation == "FURTHER_ASSESSMENT"
    assert res2.conclusion == "Further Assessment Recommended"
    assert res2.provisional_warning is not None

    # Provisional with ELEVATED_COGNITIVE_INDICATORS
    m3_prov_mci = make_model3("MCI", 0.15, 0.75, 0.10, status="awaiting_asr_verification")
    res3 = service.evaluate(model1_data=m1_low, model3_data=m3_prov_mci, mental_health_data=make_mh(), speech_inference_status="awaiting_asr_verification")
    assert res3.status == "provisional"
    assert res3.verification_status == "PROVISIONAL"
    assert res3.interpretation == "ELEVATED_COGNITIVE_INDICATORS"
    assert res3.conclusion == "Elevated Cognitive Indicators"
    assert res3.provisional_warning is not None


def test_explicit_model2_flags_do_not_change_conclusion(service: FusionService):
    m1 = make_model1(85.0)  # NORMAL
    m3 = make_model3("HC", 0.8, 0.15, 0.05)  # HC

    # Baseline with minimal depression/anxiety
    res_base = service.evaluate(model1_data=m1, model3_data=m3, mental_health_data=make_mh(phq9_score=1, gad7_score=1))
    assert res_base.interpretation == "NO_ELEVATED_INDICATORS"
    assert res_base.conclusion == "No Elevated Indicators Detected"

    # With severe depression and anxiety
    res_severe = service.evaluate(
        model1_data=m1,
        model3_data=m3,
        mental_health_data=make_mh(phq9_score=24, phq9_sev="Severe", gad7_score=19, gad7_sev="Severe"),
    )
    # The cognitive fusion conclusion MUST remain strictly unchanged
    assert res_severe.interpretation == "NO_ELEVATED_INDICATORS"
    assert res_severe.conclusion == "No Elevated Indicators Detected"
    assert res_severe.mental_health_context.depression_elevated is True
    assert res_severe.mental_health_context.anxiety_elevated is True
    assert len(res_severe.contextual_flags) > 0
