from fastapi.testclient import TestClient

from app.main import app
from app.results.router import get_results_service
from app.results.service import AssessmentResultsNotFoundError


class FakeResultsService:
    def get_results(self, assessment_id: str):
        if assessment_id == "55555555-5555-4555-8555-555555555555":
            raise AssessmentResultsNotFoundError
        return {
            "assessment_id": assessment_id,
            "assessment_short_id": "5555...5555",
            "participant_name": "Alex Doe",
            "status": "completed",
            "current_stage": "RESULTS",
            "next_stage": "RESULTS",
            "completion_message": "All currently available assessment components have been completed.",
            "model1": {
                "available": True,
                "cognitive_performance_score": 81.25,
                "model_name": "NeuroDetect Model 1",
                "model_version": "1.0.0",
                "feature_count": 47,
                "model_type": "Cognitive performance regression",
                "score_scale_max": None,
            },
            "mental_health": {
                "phq9": {"available": True, "score": 7, "score_max": 27, "severity": "mild"},
                "gad7": {"available": True, "score": 5, "score_max": 21, "severity": "mild"},
            },
            "model3": {
                "available": False,
                "status": "pending",
                "title": "Speech Assessment",
                "description": "Speech-based cognitive analysis will be added in a future version of NeuroDetect.",
            },
            "fusion": {
                "available": False,
                "status": "pending",
                "title": "Overall Multimodal Result",
                "description": "Pending completion of speech analysis.",
            },
            "completed_components": [
                {"key": "phq9", "label": "PHQ-9", "completed": True},
                {"key": "model1", "label": "Model 1", "completed": True},
            ],
            "missing_components": [],
        }


def override_service():
    return FakeResultsService()


client = TestClient(app)


def setup_module():
    app.dependency_overrides[get_results_service] = override_service


def teardown_module():
    app.dependency_overrides.pop(get_results_service, None)


def test_results_endpoint_returns_aggregated_payload():
    response = client.get("/api/assessments/66666666-6666-4666-8666-666666666666/results")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["model1"]["feature_count"] == 47
    assert body["mental_health"]["phq9"]["severity"] == "mild"


def test_results_endpoint_rejects_invalid_uuid():
    response = client.get("/api/assessments/not-a-uuid/results")

    assert response.status_code == 400
    assert response.json()["detail"] == "assessment_id must be a valid UUID."


def test_results_endpoint_returns_404_for_missing_assessment():
    response = client.get("/api/assessments/55555555-5555-4555-8555-555555555555/results")

    assert response.status_code == 404
    assert response.json()["detail"] == "Assessment not found."
