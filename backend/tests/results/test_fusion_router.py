from fastapi.testclient import TestClient

from app.main import app
from app.results.router import get_results_service
from app.results.service import AssessmentResultsNotFoundError


class FakeResultsServiceWithFusion:
    def get_results(self, assessment_id: str):
        if assessment_id == "55555555-5555-4555-8555-555555555555":
            raise AssessmentResultsNotFoundError
        return {
            "assessment_id": assessment_id,
            "assessment_short_id": "6666...6666",
            "participant_name": "Test User",
            "status": "completed",
            "current_stage": "RESULTS",
            "next_stage": "RESULTS",
            "completion_message": "All components completed.",
            "model1": {
                "available": True,
                "cognitive_performance_score": 82.5,
                "model_name": "NeuroDetect Model 1",
                "model_version": "1.0.0",
                "feature_count": 47,
                "model_type": "Cognitive performance regression",
                "score_scale_max": None,
            },
            "mental_health": {
                "phq9": {"available": True, "score": 3, "score_max": 27, "severity": "minimal"},
                "gad7": {"available": True, "score": 2, "score_max": 21, "severity": "minimal"},
            },
            "model3": {
                "available": True,
                "status": "completed",
                "predicted_class": "HC",
                "probability_hc": 0.85,
                "probability_mci": 0.10,
                "probability_dementia": 0.05,
            },
            "fusion": {
                "available": True,
                "status": "completed",
                "title": "Final Assessment Conclusion",
                "interpretation": "NO_ELEVATED_INDICATORS",
                "interpretation_label": "No Elevated Indicators Detected",
                "conclusion": "No Elevated Indicators Detected",
                "verification_status": "COMPLETE",
                "provisional_warning": None,
                "recommended_next_step": "Continue routine wellness checkups and healthy brain habits.",
                "recommended_steps": [
                    "Routine wellness: Continue annual wellness checkups. Consult a healthcare provider if you notice new or changing cognitive symptoms."
                ],
                "key_findings": {
                    "cognitive_games": {
                        "title": "Cognitive Games",
                        "status_label": "Within Expected Range",
                        "summary": "Performance was within expected range.",
                        "badge_variant": "success",
                    },
                    "speech_analysis": {
                        "title": "Speech Analysis",
                        "status_label": "Healthy Control (HC) (Verified)",
                        "summary": "Speech analysis produced HC as leading prediction.",
                        "badge_variant": "success",
                    },
                    "mental_health": {
                        "title": "Mental Health Context",
                        "status_label": "Minimal to Mild Symptoms (PHQ-9: Minimal, GAD-7: Minimal)",
                        "summary": "Mood and anxiety scores are in the low range.",
                        "badge_variant": "neutral",
                    },
                },
                "model1_score": 82.5,
                "model1_category": "NORMAL",
                "model1_weight_percent": 50,
                "model3_predicted_class": "HC",
                "model3_category": "HC_DOMINANT",
                "model3_weight_percent": 50,
                "model3_probabilities": {"HC": 0.85, "MCI": 0.10, "Dementia": 0.05},
                "mental_health_context": {
                    "phq9_score": 3,
                    "phq9_severity": "minimal",
                    "gad7_score": 2,
                    "gad7_severity": "minimal",
                    "depression_elevated": False,
                    "anxiety_elevated": False,
                    "contextual_flags": [],
                },
                "contextual_flags": [],
                "rules_triggered": ["RULE_FUSION_NORMAL_HC"],
                "explanation": "Test fusion explanation.",
                "disclaimer": "Test disclaimer.",
            },
            "completed_components": [],
            "missing_components": [],
        }


client = TestClient(app)


def setup_module():
    app.dependency_overrides[get_results_service] = lambda: FakeResultsServiceWithFusion()


def teardown_module():
    app.dependency_overrides.pop(get_results_service, None)


def test_fusion_endpoint_returns_fusion_summary():
    response = client.get("/api/assessments/66666666-6666-4666-8666-666666666666/fusion")
    assert response.status_code == 200
    data = response.json()
    assert data["interpretation"] == "NO_ELEVATED_INDICATORS"
    assert data["verification_status"] == "COMPLETE"
    assert data["model1_category"] == "NORMAL"
    assert data["model3_category"] == "HC_DOMINANT"
    assert data["model1_weight_percent"] == 50
    assert data["model3_weight_percent"] == 50


def test_fusion_endpoint_handles_invalid_uuid():
    response = client.get("/api/assessments/invalid-uuid/fusion")
    assert response.status_code == 400


def test_fusion_endpoint_handles_missing_assessment():
    response = client.get("/api/assessments/55555555-5555-4555-8555-555555555555/fusion")
    assert response.status_code == 404
