from fastapi.testclient import TestClient

from app.assessments.router import get_assessment_repository
from app.main import app


class FakeAssessmentRepository:
    def create_assessment_session(self, **kwargs):
        return {
            "patient_id": "33333333-3333-4333-8333-333333333333",
            "assessment_id": "44444444-4444-4444-8444-444444444444",
            "full_name": kwargs["full_name"],
            "age": kwargs["age"],
            "sex": kwargs["sex"],
            "education_years": kwargs["education_years"],
            "current_stage": "PHQ_GAD",
            "completed_stages": [],
        }

    def get_assessment_session(self, assessment_id: str):
        if assessment_id == "55555555-5555-4555-8555-555555555555":
            return None
        return {
            "patient_id": "33333333-3333-4333-8333-333333333333",
            "assessment_id": assessment_id,
            "full_name": "Alex Doe",
            "age": 61,
            "sex": "Female",
            "education_years": 16,
            "current_stage": "COGNITIVE",
            "completed_stages": ["PHQ_GAD"],
        }


def override_repository():
    return FakeAssessmentRepository()


client = TestClient(app)


def setup_module():
    app.dependency_overrides[get_assessment_repository] = override_repository


def teardown_module():
    app.dependency_overrides.pop(get_assessment_repository, None)


def test_create_assessment_session_returns_patient_and_assessment():
    response = client.post(
        "/api/assessments",
        json={
          "full_name": "Alex Doe",
          "age": 61,
          "sex": "Female",
          "education_years": 16,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["assessment_id"] == "44444444-4444-4444-8444-444444444444"
    assert body["patient_id"] == "33333333-3333-4333-8333-333333333333"
    assert body["current_stage"] == "PHQ_GAD"


def test_get_assessment_session_returns_progress():
    response = client.get("/api/assessments/66666666-6666-4666-8666-666666666666")

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Alex Doe"
    assert body["completed_stages"] == ["PHQ_GAD"]


def test_invalid_assessment_id_returns_400():
    response = client.get("/api/assessments/not-a-uuid")

    assert response.status_code == 400
    assert response.json()["detail"] == "assessment_id must be a valid UUID."


def test_missing_assessment_returns_404():
    response = client.get("/api/assessments/55555555-5555-4555-8555-555555555555")

    assert response.status_code == 404
    assert response.json()["detail"] == "Assessment not found."
