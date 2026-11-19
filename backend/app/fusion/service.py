"""
Rule-Based Multimodal Fusion Engine for NeuroDetect.

Combines Model 1 (Cognitive Performance Regressor, 50%) and Model 3 (Multimodal Speech Classifier, 50%)
with Model 2 (PHQ-9 and GAD-7) serving strictly as contextual mental-health background.

This implementation is purely mathematical and rule-based:
- No new ML model is introduced or trained.
- Probabilities are strictly validated for finiteness, range [0, 1], and unit sum.
- Missing data is never zero-filled or fabricated.
- Non-causal contextual flags are generated for elevated depressive or anxiety symptoms.
"""
from __future__ import annotations

import logging
import math
from typing import Any

from app.fusion.config import (
    FUSION_DISCLAIMER,
    GAD7_ELEVATED_THRESHOLD,
    MODEL1_BORDERLINE_THRESHOLD,
    MODEL1_NORMAL_THRESHOLD,
    MODEL1_WEIGHT_PERCENT,
    MODEL3_WEIGHT_PERCENT,
    PHQ9_ELEVATED_THRESHOLD,
    PROBABILITY_SUM_TOLERANCE,
    PROVISIONAL_ASR_WARNING,
    SPEECH_MIN_DOMINANT_PROB,
    SPEECH_UNCERTAINTY_MARGIN,
)
from app.fusion.schemas import (
    FusionInterpretation,
    FusionKeyFindings,
    FusionResultSummary,
    KeyFinding,
    MentalHealthContext,
    Model1CognitiveCategory,
    Model3SpeechCategory,
    VerificationStatus,
)

logger = logging.getLogger("neurodetect.fusion.service")


class FusionEngineError(Exception):
    """Raised when fusion calculation encounters unrecoverable parameter errors."""


class FusionService:
    def __init__(
        self,
        *,
        model1_normal_threshold: float = MODEL1_NORMAL_THRESHOLD,
        model1_borderline_threshold: float = MODEL1_BORDERLINE_THRESHOLD,
        speech_uncertainty_margin: float = SPEECH_UNCERTAINTY_MARGIN,
        speech_min_dominant_prob: float = SPEECH_MIN_DOMINANT_PROB,
        prob_sum_tolerance: float = PROBABILITY_SUM_TOLERANCE,
    ):
        self.model1_normal_threshold = model1_normal_threshold
        self.model1_borderline_threshold = model1_borderline_threshold
        self.speech_uncertainty_margin = speech_uncertainty_margin
        self.speech_min_dominant_prob = speech_min_dominant_prob
        self.prob_sum_tolerance = prob_sum_tolerance

    # -------------------------------------------------------------------------
    # 1. Model 1 Interpretation
    # -------------------------------------------------------------------------
    def classify_model1(self, score: float | None) -> Model1CognitiveCategory:
        """
        Categorizes continuous cognitive performance score into NORMAL, BORDERLINE, or LOW.
        Higher score = better performance.
        """
        if score is None or not isinstance(score, (int, float)) or not math.isfinite(score):
            return "UNKNOWN"

        if score >= self.model1_normal_threshold:
            return "NORMAL"
        if score >= self.model1_borderline_threshold:
            return "BORDERLINE"
        return "LOW"

    # -------------------------------------------------------------------------
    # 2. Model 3 Speech Interpretation
    # -------------------------------------------------------------------------
    def validate_speech_probabilities(self, probs: dict[str, Any] | None) -> bool:
        """
        Validates that all probabilities are finite, in [0, 1], and sum to ~1.0.
        """
        if not isinstance(probs, dict):
            return False

        required_classes = ("HC", "MCI", "Dementia")
        for cls in required_classes:
            if cls not in probs:
                return False
            val = probs[cls]
            if not isinstance(val, (int, float)) or not math.isfinite(val):
                return False
            if val < 0.0 or val > 1.0:
                return False

        total_p = sum(float(probs[c]) for c in required_classes)
        return math.isclose(total_p, 1.0, rel_tol=self.prob_sum_tolerance, abs_tol=self.prob_sum_tolerance)

    def classify_model3(
        self,
        predicted_class: str | None,
        probs: dict[str, float] | None,
    ) -> tuple[Model3SpeechCategory, list[str]]:
        """
        Interprets Model 3 output into HC_DOMINANT, MCI_INDICATIVE, DEMENTIA_INDICATIVE, or UNCERTAIN.
        Returns the category and explanation notes.
        """
        notes: list[str] = []

        if not probs or not self.validate_speech_probabilities(probs):
            if predicted_class in ("HC", "MCI", "Dementia"):
                notes.append("Probabilities were absent or failed sum validation; falling back to predicted class.")
                mapping: dict[str, Model3SpeechCategory] = {
                    "HC": "HC_DOMINANT",
                    "MCI": "MCI_INDICATIVE",
                    "Dementia": "DEMENTIA_INDICATIVE",
                }
                return mapping[predicted_class], notes
            return "UNKNOWN", ["Missing or invalid speech prediction probabilities."]

        p_hc = float(probs["HC"])
        p_mci = float(probs["MCI"])
        p_dem = float(probs["Dementia"])

        sorted_probs = sorted(
            [("HC", p_hc), ("MCI", p_mci), ("Dementia", p_dem)],
            key=lambda x: x[1],
            reverse=True,
        )
        top_class, top_p = sorted_probs[0]
        second_class, second_p = sorted_probs[1]
        margin = top_p - second_p

        # Uncertainty check: close top classes or low dominant probability
        if margin < self.speech_uncertainty_margin:
            notes.append(
                f"Close margin between top class {top_class} ({top_p:.1%}) and second class {second_class} "
                f"({second_p:.1%}) (delta={margin:.1%}, threshold={self.speech_uncertainty_margin:.1%})."
            )
            return "UNCERTAIN", notes

        if top_p < self.speech_min_dominant_prob:
            notes.append(
                f"Top probability for {top_class} ({top_p:.1%}) is below dominant threshold "
                f"({self.speech_min_dominant_prob:.1%})."
            )
            return "UNCERTAIN", notes

        if top_class == "HC":
            return "HC_DOMINANT", notes
        if top_class == "MCI":
            return "MCI_INDICATIVE", notes
        if top_class == "Dementia":
            return "DEMENTIA_INDICATIVE", notes

        return "UNKNOWN", ["Unrecognized top speech class."]

    # -------------------------------------------------------------------------
    # 3. Model 2 Contextual Interpretation
    # -------------------------------------------------------------------------
    def evaluate_mental_health_context(
        self,
        mental_health_data: dict[str, Any] | None,
        model1_cat: Model1CognitiveCategory,
        model3_cat: Model3SpeechCategory,
    ) -> MentalHealthContext:
        """
        Evaluates PHQ-9 and GAD-7 screening results purely as clinical context.
        Generates non-causal contextual flags if symptoms are elevated.
        """
        if not mental_health_data:
            return MentalHealthContext()

        phq9_raw = mental_health_data.get("phq9") or {}
        gad7_raw = mental_health_data.get("gad7") or {}

        phq9_score = phq9_raw.get("score") if phq9_raw.get("available") else None
        phq9_severity = phq9_raw.get("severity") if phq9_raw.get("available") else None

        gad7_score = gad7_raw.get("score") if gad7_raw.get("available") else None
        gad7_severity = gad7_raw.get("severity") if gad7_raw.get("available") else None

        # Check clinical elevation (Moderate to Severe)
        dep_elevated = (
            (phq9_score is not None and phq9_score >= PHQ9_ELEVATED_THRESHOLD)
            or (isinstance(phq9_severity, str) and phq9_severity.lower() in ("moderate", "moderately severe", "severe"))
        )
        anx_elevated = (
            (gad7_score is not None and gad7_score >= GAD7_ELEVATED_THRESHOLD)
            or (isinstance(gad7_severity, str) and gad7_severity.lower() in ("moderate", "moderately severe", "severe"))
        )

        flags: list[str] = []

        if dep_elevated and anx_elevated:
            flags.append(
                f"Concurrent elevated depressive ({phq9_severity or phq9_score}) and anxiety ({gad7_severity or gad7_score}) "
                "symptoms were reported. Affective factors are known to influence processing speed, working memory, and "
                "verbal fluency. These screening results represent important non-cognitive context for interpreting findings."
            )
        elif dep_elevated:
            if model1_cat in ("LOW", "BORDERLINE"):
                flags.append(
                    f"Elevated depressive symptoms were reported ({phq9_severity or phq9_score}). Depression can "
                    "affect cognitive task engagement, reaction time, and subjective recall. This symptom context should "
                    "be considered alongside lower cognitive game scores."
                )
            else:
                flags.append(
                    f"Elevated depressive symptoms were reported ({phq9_severity or phq9_score}) in the presence of "
                    "intact cognitive task performance. Follow-up for affective wellbeing is recommended."
                )
        elif anx_elevated:
            if model3_cat == "UNCERTAIN" or model1_cat in ("BORDERLINE", "LOW"):
                flags.append(
                    f"Elevated anxiety symptoms were reported ({gad7_severity or gad7_score}). Elevated situational "
                    "or generalized anxiety can increase hesitation, speech disfluency, and response latency during "
                    "timed testing."
                )
            else:
                flags.append(
                    f"Elevated anxiety symptoms were reported ({gad7_severity or gad7_score}). Anxiety symptoms provide "
                    "relevant context for overall wellbeing and test-taking comfort."
                )

        return MentalHealthContext(
            phq9_score=phq9_score,
            phq9_severity=phq9_severity,
            gad7_score=gad7_score,
            gad7_severity=gad7_severity,
            depression_elevated=dep_elevated,
            anxiety_elevated=anx_elevated,
            contextual_flags=flags,
        )

    def _build_recommendations(
        self,
        interpretation: FusionInterpretation,
        is_provisional: bool,
        mh_context: MentalHealthContext,
        m1_available: bool,
        m3_available: bool,
    ) -> tuple[str, list[str]]:
        steps: list[str] = []

        if not m1_available or not m3_available:
            primary = "Complete remaining assessment activities to obtain an overall multimodal synthesis."
            steps.append("Complete pending tasks: Return to the assessment dashboard to record speech or complete cognitive tasks.")
            return primary, steps

        if is_provisional:
            steps.append(
                "Verify automated speech transcript: Speech analysis is currently based on automated speech recognition (ASR). "
                "A clinician or evaluator should verify the transcript before relying on speech results."
            )

        if interpretation == "FURTHER_ASSESSMENT":
            primary = "Consult a healthcare provider for further cognitive evaluation and professional review."
            steps.append(
                "Clinical review & follow-up: Because findings indicate borderline performance, differing indicators between games and speech, "
                "or speech uncertainty, a healthcare professional should review individual domain scores and consider follow-up testing."
            )
        elif interpretation == "ELEVATED_COGNITIVE_INDICATORS":
            primary = "Consult a qualified healthcare specialist for comprehensive diagnostic evaluation."
            steps.append(
                "Specialist consultation: Schedule an appointment with a neurologist, geriatrician, or clinical neuropsychologist "
                "for formal cognitive evaluation and medical history review."
            )
        else:  # NO_ELEVATED_INDICATORS
            primary = "Continue routine wellness checkups and healthy brain habits."
            steps.append(
                "Routine wellness: Continue annual wellness checkups. Consult a healthcare provider if you notice new or changing cognitive symptoms."
            )

        if mh_context.depression_elevated or mh_context.anxiety_elevated:
            steps.append(
                "Address mood and wellbeing: Screening indicated elevated depressive or anxiety symptoms. Discuss these with a doctor or counselor, "
                "as stress and affective factors can significantly impact day-to-day focus and cognitive test performance."
            )

        return primary, steps

    def _build_key_findings(
        self,
        m1_cat: Model1CognitiveCategory,
        m1_available: bool,
        m3_class: str | None,
        m3_cat: Model3SpeechCategory,
        m3_available: bool,
        is_provisional: bool,
        mh_context: MentalHealthContext,
        m3_probs: dict[str, float] | None = None,
    ) -> FusionKeyFindings:
        # Cognitive Games
        if not m1_available or m1_cat == "UNKNOWN":
            cg_status = "Incomplete"
            cg_summary = "Cognitive game tasks have not been completed."
            cg_badge = "neutral"
        elif m1_cat == "NORMAL":
            cg_status = "Within Expected Range"
            cg_summary = "Performance on memory, attention, and executive tasks was within the expected range for healthy cognition."
            cg_badge = "success"
        elif m1_cat == "BORDERLINE":
            cg_status = "Borderline Performance"
            cg_summary = "Scores indicated subtle variations in recall speed or attention, placing performance in a borderline range."
            cg_badge = "warning"
        else:  # LOW
            cg_status = "Below Expected Range"
            cg_summary = "Performance across cognitive tasks was below the expected range defined by the experimental model."
            cg_badge = "error"

        # Speech Analysis
        if not m3_available or m3_cat == "UNKNOWN":
            sp_status = "Incomplete"
            sp_summary = "Speech recording and analysis have not been completed."
            sp_badge = "neutral"
        else:
            class_labels = {
                "HC": "Healthy Control (HC)",
                "MCI": "Mild Cognitive Impairment (MCI)",
                "Dementia": "Dementia Indicative",
            }
            pred_label = class_labels.get(m3_class, m3_class or "Speech Analysis")
            prob_pct = ""
            if m3_probs and m3_class and m3_class in m3_probs:
                prob_pct = f" — {m3_probs[m3_class] * 100:.1f}%"

            if is_provisional:
                sp_status = f"{pred_label}{prob_pct} (Awaiting Clinician Verification)"
                sp_badge = "warning"
                sp_summary = f"Speech analysis produced {pred_label} as its leading prediction. The automated transcript is awaiting clinical verification."
            else:
                sp_status = f"{pred_label}{prob_pct} (Verified)"
                sp_badge = "success" if m3_class == "HC" else "warning" if m3_class == "MCI" else "error"
                sp_summary = f"Speech analysis produced {pred_label} as its leading prediction based on verified acoustic and linguistic features."

        # Mental Health Context
        p_sev = mh_context.phq9_severity or "Minimal"
        g_sev = mh_context.gad7_severity or "Minimal"
        if mh_context.depression_elevated and mh_context.anxiety_elevated:
            mh_status = f"Elevated Mood & Anxiety Symptoms (PHQ-9: {p_sev}, GAD-7: {g_sev})"
            mh_badge = "warning"
            mh_summary = "Elevated depressive and anxiety symptoms noted — provides non-cognitive context for test performance."
        elif mh_context.depression_elevated:
            mh_status = f"Elevated Depressive Symptoms (PHQ-9: {p_sev})"
            mh_badge = "warning"
            mh_summary = "Elevated depressive symptoms noted — provides non-cognitive context for test performance."
        elif mh_context.anxiety_elevated:
            mh_status = f"Elevated Anxiety Symptoms (GAD-7: {g_sev})"
            mh_badge = "warning"
            mh_summary = "Elevated anxiety symptoms noted — provides non-cognitive context for test performance."
        else:
            mh_status = f"Minimal to Mild Symptoms (PHQ-9: {p_sev}, GAD-7: {g_sev})"
            mh_badge = "neutral"
            mh_summary = "Mood and anxiety scores are in the low range, suggesting affective symptoms are unlikely to have impacted test performance."

        return FusionKeyFindings(
            cognitive_games=KeyFinding(title="Cognitive Games", status_label=cg_status, summary=cg_summary, badge_variant=cg_badge),
            speech_analysis=KeyFinding(title="Speech Analysis", status_label=sp_status, summary=sp_summary, badge_variant=sp_badge),
            mental_health=KeyFinding(title="Mental Health Context", status_label=mh_status, summary=mh_summary, badge_variant=mh_badge),
        )

    # -------------------------------------------------------------------------
    # 4. Multimodal Fusion Evaluation
    # -------------------------------------------------------------------------
    def evaluate(
        self,
        *,
        model1_data: dict[str, Any] | None,
        model3_data: dict[str, Any] | None,
        mental_health_data: dict[str, Any] | None = None,
        speech_inference_status: str | None = None,
    ) -> FusionResultSummary:
        """
        Executes rule-based multimodal fusion combining Model 1 and Model 3.
        """
        rules_triggered: list[str] = []

        # Check Model 1 availability
        m1_available = bool(model1_data and model1_data.get("available"))
        m1_score = model1_data.get("cognitive_performance_score") if m1_available else None
        m1_cat = self.classify_model1(m1_score) if m1_available else "UNKNOWN"

        # Check Model 3 availability
        m3_available = bool(model3_data and model3_data.get("available"))
        m3_status = speech_inference_status or (model3_data.get("status") if m3_available else "pending")

        if m3_status == "failed":
            m3_available = False

        m3_class = model3_data.get("predicted_class") if m3_available else None
        m3_probs = (
            model3_data.get("probabilities")
            or {
                "HC": model3_data.get("hc_probability") or model3_data.get("probability_hc"),
                "MCI": model3_data.get("mci_probability") or model3_data.get("probability_mci"),
                "Dementia": model3_data.get("dementia_probability") or model3_data.get("probability_dementia"),
            }
            if m3_available
            else None
        )

        m3_cat, m3_notes = self.classify_model3(m3_class, m3_probs) if m3_available else ("UNKNOWN", [])

        # Evaluate Model 2 mental health context
        mh_context = self.evaluate_mental_health_context(mental_health_data, m1_cat, m3_cat)

        # Verification Status (PROVISIONAL if awaiting ASR verification)
        is_provisional = m3_status == "awaiting_asr_verification"
        verif_status: VerificationStatus = "PROVISIONAL" if is_provisional else "COMPLETE"
        provisional_warning = PROVISIONAL_ASR_WARNING if is_provisional else None

        # Handle Missing Data cases
        if not m1_available and not m3_available:
            primary_rec, rec_steps = self._build_recommendations("INSUFFICIENT_DATA", False, mh_context, False, False)
            return FusionResultSummary(
                available=False,
                status="insufficient_data",
                interpretation="INSUFFICIENT_DATA",
                interpretation_label="Insufficient Assessment Data",
                conclusion="Insufficient Assessment Data",
                verification_status="UNVERIFIED",
                recommended_next_step=primary_rec,
                recommended_steps=rec_steps,
                key_findings=self._build_key_findings(m1_cat, False, None, m3_cat, False, False, mh_context),
                model1_category="UNKNOWN",
                model3_category="UNKNOWN",
                mental_health_context=mh_context,
                contextual_flags=mh_context.contextual_flags,
                rules_triggered=["RULE_INSUFFICIENT_DATA: Missing both Model 1 and Model 3."],
                explanation="Primary assessment components (cognitive games and speech assessment) have not been completed. Final multimodal fusion requires both indicators.",
                disclaimer=FUSION_DISCLAIMER,
            )

        if not m1_available:
            primary_rec, rec_steps = self._build_recommendations("INSUFFICIENT_DATA", is_provisional, mh_context, False, True)
            return FusionResultSummary(
                available=False,
                status="insufficient_data",
                interpretation="INSUFFICIENT_DATA",
                interpretation_label="Insufficient Assessment Data",
                conclusion="Insufficient Assessment Data",
                verification_status=verif_status,
                provisional_warning=provisional_warning,
                recommended_next_step=primary_rec,
                recommended_steps=rec_steps,
                key_findings=self._build_key_findings(m1_cat, False, m3_class, m3_cat, True, is_provisional, mh_context, m3_probs),
                model1_category="UNKNOWN",
                model3_predicted_class=m3_class,
                model3_category=m3_cat,
                model3_probabilities=m3_probs,
                mental_health_context=mh_context,
                contextual_flags=mh_context.contextual_flags,
                rules_triggered=["RULE_MISSING_MODEL1: Cognitive games incomplete."],
                explanation=f"Speech analysis was completed ({m3_cat}), but Model 1 cognitive performance score is missing. Multimodal fusion requires both cognitive games and speech.",
                disclaimer=FUSION_DISCLAIMER,
            )

        if not m3_available:
            primary_rec, rec_steps = self._build_recommendations("INSUFFICIENT_DATA", False, mh_context, True, False)
            return FusionResultSummary(
                available=False,
                status="insufficient_data",
                interpretation="INSUFFICIENT_DATA",
                interpretation_label="Insufficient Assessment Data",
                conclusion="Insufficient Assessment Data",
                verification_status="UNVERIFIED",
                recommended_next_step=primary_rec,
                recommended_steps=rec_steps,
                key_findings=self._build_key_findings(m1_cat, True, None, m3_cat, False, False, mh_context),
                model1_score=m1_score,
                model1_category=m1_cat,
                model3_category="UNKNOWN",
                mental_health_context=mh_context,
                contextual_flags=mh_context.contextual_flags,
                rules_triggered=["RULE_MISSING_MODEL3: Speech assessment incomplete or failed."],
                explanation=f"Model 1 cognitive performance score is {m1_score:.2f} ({m1_cat}), but speech assessment has not been completed. Multimodal fusion requires both cognitive games and speech.",
                disclaimer=FUSION_DISCLAIMER,
            )

        # ---------------------------------------------------------------------
        # Matrix Rule Evaluation (Both Model 1 and Model 3 present)
        # ---------------------------------------------------------------------
        interpretation: FusionInterpretation
        explanation: str

        # Note any speech classification uncertainty
        if m3_notes:
            rules_triggered.extend(m3_notes)

        # Revised Decision Matrix (9 Combinations + UNCERTAIN)
        if m3_cat == "UNCERTAIN":
            interpretation = "FURTHER_ASSESSMENT"
            rules_triggered.append(f"RULE_FUSION_UNCERTAIN_SPEECH: Speech margins inconclusive; Model 1 was {m1_cat}.")
            if is_provisional:
                explanation = (
                    "Speech analysis did not produce a sufficiently clear leading prediction on the automated transcript. "
                    "Further assessment is recommended before drawing conclusions."
                )
            else:
                explanation = (
                    "Speech analysis did not produce a sufficiently clear leading prediction. "
                    "Further assessment is recommended before drawing conclusions."
                )

        elif m1_cat == "NORMAL" and m3_cat == "HC_DOMINANT":
            interpretation = "NO_ELEVATED_INDICATORS"
            rules_triggered.append("RULE_FUSION_NORMAL_HC: Cognitive games NORMAL and speech HC dominant.")
            if is_provisional:
                explanation = (
                    "The cognitive game and speech assessments produced broadly consistent findings, with no elevated indicators "
                    "identified by the experimental screening system. Speech analysis is based on an automated transcript awaiting clinical verification."
                )
            else:
                explanation = (
                    "The cognitive game and speech assessments produced broadly consistent findings, with no elevated indicators "
                    "identified by the experimental screening system."
                )

        elif m1_cat == "BORDERLINE" and m3_cat == "HC_DOMINANT":
            interpretation = "NO_ELEVATED_INDICATORS"
            rules_triggered.append("RULE_FUSION_BORDERLINE_HC: Cognitive games BORDERLINE and speech HC dominant.")
            if is_provisional:
                explanation = (
                    "Although cognitive game performance fell within the borderline category, speech analysis identified Healthy Control "
                    "as its leading prediction on an automated transcript awaiting verification. The combined assessment did not identify elevated cognitive indicators."
                )
            else:
                explanation = (
                    "Although cognitive game performance fell within the borderline category, speech analysis identified Healthy Control "
                    "as its leading prediction. The combined assessment did not identify elevated cognitive indicators."
                )

        elif m1_cat == "LOW" and m3_cat == "HC_DOMINANT":
            interpretation = "FURTHER_ASSESSMENT"
            rules_triggered.append("RULE_FUSION_LOW_HC: Differing indicators (games LOW, speech HC dominant).")
            if is_provisional:
                explanation = (
                    "The cognitive game assessment indicated low performance, while speech analysis identified Healthy Control "
                    "as its leading prediction on an automated transcript awaiting verification. These findings differ, so further assessment is recommended."
                )
            else:
                explanation = (
                    "The cognitive game assessment indicated low performance, while speech analysis identified Healthy Control "
                    "as its leading prediction. These findings differ, so further assessment is recommended."
                )

        elif m1_cat == "NORMAL" and m3_cat == "MCI_INDICATIVE":
            interpretation = "FURTHER_ASSESSMENT"
            rules_triggered.append("RULE_FUSION_NORMAL_MCI: Differing indicators (games NORMAL, speech MCI indicative).")
            if is_provisional:
                explanation = (
                    "Cognitive game performance was in the normal range, while speech analysis identified MCI as its leading "
                    "prediction on an automated transcript awaiting verification. These findings require further assessment and professional review."
                )
            else:
                explanation = (
                    "Cognitive game performance was in the normal range, while speech analysis identified MCI as its leading "
                    "prediction. These findings require further assessment and professional review."
                )

        elif m1_cat == "BORDERLINE" and m3_cat == "MCI_INDICATIVE":
            interpretation = "FURTHER_ASSESSMENT"
            rules_triggered.append("RULE_FUSION_BORDERLINE_MCI: Cognitive games BORDERLINE and speech MCI indicative.")
            if is_provisional:
                explanation = (
                    "The cognitive game assessment indicated borderline performance, while speech analysis identified MCI "
                    "as its leading prediction on an automated transcript awaiting verification. Further assessment is recommended to understand these findings."
                )
            else:
                explanation = (
                    "The cognitive game assessment indicated borderline performance, while speech analysis identified MCI "
                    "as its leading prediction. Further assessment is recommended to understand these findings."
                )

        elif m1_cat == "LOW" and m3_cat == "MCI_INDICATIVE":
            interpretation = "ELEVATED_COGNITIVE_INDICATORS"
            rules_triggered.append("RULE_FUSION_LOW_MCI: Both cognitive games LOW and speech MCI indicative.")
            if is_provisional:
                explanation = (
                    "Both cognitive game performance and speech analysis produced findings warranting further evaluation. "
                    "Elevated cognitive indicators were identified by the experimental screening system based on an automated speech transcript awaiting verification. "
                    "A comprehensive professional assessment is recommended."
                )
            else:
                explanation = (
                    "Both cognitive game performance and speech analysis produced findings warranting further evaluation. "
                    "Elevated cognitive indicators were identified by the experimental screening system. A comprehensive professional assessment is recommended."
                )

        elif m1_cat == "NORMAL" and m3_cat == "DEMENTIA_INDICATIVE":
            interpretation = "FURTHER_ASSESSMENT"
            rules_triggered.append("RULE_FUSION_NORMAL_DEMENTIA: Differing indicators (games NORMAL, speech Dementia indicative).")
            if is_provisional:
                explanation = (
                    "Speech analysis produced Dementia as its leading prediction on an automated transcript awaiting verification, "
                    "while cognitive game performance did not show low performance. These findings require further assessment and professional review."
                )
            else:
                explanation = (
                    "Speech analysis produced Dementia as its leading prediction, while cognitive game performance did not show low performance. "
                    "These findings require further assessment and professional review."
                )

        elif m1_cat == "BORDERLINE" and m3_cat == "DEMENTIA_INDICATIVE":
            interpretation = "FURTHER_ASSESSMENT"
            rules_triggered.append("RULE_FUSION_BORDERLINE_DEMENTIA: Differing indicators (games BORDERLINE, speech Dementia indicative).")
            if is_provisional:
                explanation = (
                    "Speech analysis produced Dementia as its leading prediction on an automated transcript awaiting verification, "
                    "while cognitive game performance did not show low performance. These findings require further assessment and professional review."
                )
            else:
                explanation = (
                    "Speech analysis produced Dementia as its leading prediction, while cognitive game performance did not show low performance. "
                    "These findings require further assessment and professional review."
                )

        elif m1_cat == "LOW" and m3_cat == "DEMENTIA_INDICATIVE":
            interpretation = "ELEVATED_COGNITIVE_INDICATORS"
            rules_triggered.append("RULE_FUSION_LOW_DEMENTIA: Both cognitive games LOW and speech Dementia indicative.")
            if is_provisional:
                explanation = (
                    "Both cognitive game performance and speech analysis produced findings warranting further evaluation. "
                    "Elevated cognitive indicators were identified by the experimental screening system based on an automated speech transcript awaiting verification. "
                    "A comprehensive professional assessment is recommended."
                )
            else:
                explanation = (
                    "Both cognitive game performance and speech analysis produced findings warranting further evaluation. "
                    "Elevated cognitive indicators were identified by the experimental screening system. A comprehensive professional assessment is recommended."
                )

        else:
            interpretation = "INSUFFICIENT_DATA"
            rules_triggered.append(f"RULE_FALLBACK_UNKNOWN: Unexpected categories (Model 1: {m1_cat}, Model 3: {m3_cat}).")
            explanation = "Unable to compute multimodal fusion due to unclassified model outputs."

        # Format user-facing label and conclusion (Exactly 3 participant-facing conclusions + INSUFFICIENT_DATA)
        labels = {
            "NO_ELEVATED_INDICATORS": "No Elevated Indicators Detected",
            "FURTHER_ASSESSMENT": "Further Assessment Recommended",
            "ELEVATED_COGNITIVE_INDICATORS": "Elevated Cognitive Indicators",
            "INSUFFICIENT_DATA": "Insufficient Assessment Data",
        }
        interpretation_label = labels.get(interpretation, interpretation)
        conclusion = interpretation_label

        primary_rec, rec_steps = self._build_recommendations(interpretation, is_provisional, mh_context, True, True)
        key_findings = self._build_key_findings(m1_cat, True, m3_class, m3_cat, True, is_provisional, mh_context, m3_probs)

        return FusionResultSummary(
            available=True,
            status="provisional" if is_provisional else "completed",
            title="Final Assessment Conclusion",
            interpretation=interpretation,
            interpretation_label=interpretation_label,
            conclusion=conclusion,
            verification_status=verif_status,
            provisional_warning=provisional_warning,
            recommended_next_step=primary_rec,
            recommended_steps=rec_steps,
            key_findings=key_findings,
            model1_score=m1_score,
            model1_category=m1_cat,
            model1_weight_percent=MODEL1_WEIGHT_PERCENT,
            model3_predicted_class=m3_class,
            model3_category=m3_cat,
            model3_weight_percent=MODEL3_WEIGHT_PERCENT,
            model3_probabilities=m3_probs,
            mental_health_context=mh_context,
            contextual_flags=mh_context.contextual_flags,
            rules_triggered=rules_triggered,
            explanation=explanation,
            disclaimer=FUSION_DISCLAIMER,
        )


_global_fusion_service: FusionService | None = None


def get_fusion_service() -> FusionService:
    global _global_fusion_service
    if _global_fusion_service is None:
        _global_fusion_service = FusionService()
    return _global_fusion_service
