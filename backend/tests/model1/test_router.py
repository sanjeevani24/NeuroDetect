from fastapi.testclient import TestClient

from app.main import app
from app.ml.model1.router import get_model1_service


class FakeModel1Service:
    def predict(self, assessment_id: str):
        if assessment_id == "99999999-9999-4999-8999-999999999999":
            from app.ml.model1.exceptions import Model1IncompleteAssessmentError

            raise Model1IncompleteAssessmentError(["Trail Making"])
        if assessment_id == "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa":
            from app.ml.model1.exceptions import Model1SchemaNotReadyError

            raise Model1SchemaNotReadyError(
                "Model 1 database table is missing in Supabase. Apply database/schema.sql so the model1_results table exists, then retry."
            )
        return {
            "assessment_id": assessment_id,
            "model": "NeuroDetect Model 1 - Cognitive Performance Regressor",
            "model_version": "1.0.0",
            "cognitive_performance_score": 81.25,
            "status": "success",
        }

    def get_result(self, assessment_id: str):
        return {
            "assessment_id": assessment_id,
            "model": "NeuroDetect Model 1 - Cognitive Performance Regressor",
            "model_version": "1.0.0",
            "cognitive_performance_score": 81.25,
            "feature_vector": {"overall_mmse_score": 24.0},
            "feature_order": ["overall_mmse_score"],
        }


def override_service():
    return FakeModel1Service()


client = TestClient(app)


def setup_module():
    app.dependency_overrides[get_model1_service] = override_service


def teardown_module():
    app.dependency_overrides.pop(get_model1_service, None)


def test_predict_endpoint_returns_prediction():
    response = client.post("/api/assessments/88888888-8888-4888-8888-888888888888/model1/predict")
    assert response.status_code == 200
    assert response.json()["model_version"] == "1.0.0"


def test_predict_endpoint_returns_409_for_incomplete_assessment():
    response = client.post("/api/assessments/99999999-9999-4999-8999-999999999999/model1/predict")
    assert response.status_code == 409
    assert response.json()["detail"]["detail"] == "Cognitive assessment incomplete"


def test_predict_endpoint_returns_503_for_missing_model1_table():
    response = client.post("/api/assessments/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/model1/predict")
    assert response.status_code == 503
    assert "model1_results" in response.json()["detail"]


def test_get_result_endpoint_returns_feature_vector():
    response = client.get("/api/assessments/88888888-8888-4888-8888-888888888888/model1")
    assert response.status_code == 200
    assert response.json()["feature_vector"]["overall_mmse_score"] == 24.0
