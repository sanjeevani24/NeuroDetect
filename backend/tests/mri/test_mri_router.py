import io
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.mri.config import DISCLAIMER, MODEL_NAME, MODEL_VERSION
from app.mri.router import get_mri_service
from app.mri.service import MriService


class FakeAssessmentRepository:
    def assessment_exists(self, assessment_id: str) -> bool:
        return assessment_id != "55555555-5555-4555-8555-555555555555"

    def get_assessment_session(self, assessment_id: str):
        if assessment_id == "55555555-5555-4555-8555-555555555555":
            return None
        return {
            "assessment_id": assessment_id,
            "patient_id": "33333333-3333-4333-8333-333333333333",
            "full_name": "Test Patient",
            "assessment_type": "MRI_ONLY",
            "current_stage": "MRI",
            "completed_stages": [],
        }


class FakeMriRepository:
    def __init__(self):
        self.data = {
            "66666666-6666-4666-8666-666666666666": {
                "assessment_id": "66666666-6666-4666-8666-666666666666",
                "predicted_class": "Very Mildly Demented",
                "predicted_class_index": 1,
                "probability_non_demented": 0.05,
                "probability_very_mild": 0.85,
                "probability_mild": 0.08,
                "probability_moderate": 0.02,
                "binary_prediction": "Dementia",
                "binary_probability_no_dementia": 0.05,
                "binary_probability_dementia": 0.95,
                "model_name": MODEL_NAME,
                "model_version": MODEL_VERSION,
                "image_filename": "test_slice.png",
                "image_format": "png",
                "image_size_bytes": 1024,
                "disclaimer": DISCLAIMER,
                "created_at": "2026-11-20T00:00:00Z",
                "updated_at": "2026-11-20T00:00:00Z",
            }
        }

    def upsert_mri_result(self, **kwargs):
        assessment_id = kwargs["assessment_id"]
        record = {
            "id": "mri-123",
            **kwargs,
            "created_at": "2026-11-20T00:00:00Z",
            "updated_at": "2026-11-20T00:00:00Z",
        }
        self.data[assessment_id] = record
        return record

    def get_by_assessment(self, assessment_id: str):
        return self.data.get(assessment_id)


class FakeModelManager:
    def predict(self, image_input):
        return {
            "predicted_class": "Non-Demented",
            "predicted_class_index": 0,
            "probability_non_demented": 0.90,
            "probability_very_mild": 0.06,
            "probability_mild": 0.03,
            "probability_moderate": 0.01,
            "class_probabilities": {
                "Non-Demented": 0.90,
                "Very Mildly Demented": 0.06,
                "Mildly Demented": 0.03,
                "Moderately Demented": 0.01,
            },
            "binary_prediction": "No Dementia",
            "binary_probabilities": {
                "no_dementia": 0.90,
                "dementia": 0.10,
            },
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "disclaimer": DISCLAIMER,
        }


def override_mri_service():
    return MriService(
        assessment_repository=FakeAssessmentRepository(),
        mri_repository=FakeMriRepository(),
        model_manager=FakeModelManager(),
    )


client = TestClient(app)


def setup_module():
    app.dependency_overrides[get_mri_service] = override_mri_service


def teardown_module():
    app.dependency_overrides.pop(get_mri_service, None)


def _make_png():
    img = Image.new("RGB", (100, 100), color=(100, 100, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_upload_mri_invalid_uuid():
    response = client.post(
        "/api/assessments/invalid-uuid/mri/upload",
        files={"image": ("test.png", _make_png(), "image/png")},
    )
    assert response.status_code == 400
    assert "valid UUID" in response.json()["detail"]


def test_upload_mri_nonexistent_assessment():
    response = client.post(
        "/api/assessments/55555555-5555-4555-8555-555555555555/mri/upload",
        files={"image": ("test.png", _make_png(), "image/png")},
    )
    assert response.status_code == 404


def test_upload_mri_success():
    response = client.post(
        "/api/assessments/44444444-4444-4444-8444-444444444444/mri/upload",
        files={"image": ("mri_slice.png", _make_png(), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assessment_id"] == "44444444-4444-4444-8444-444444444444"
    assert data["predicted_class"] == "Non-Demented"
    assert data["binary_prediction"] == "No Dementia"
    assert data["binary_probabilities"]["no_dementia"] == 0.90
    assert data["model_name"] == MODEL_NAME


def test_get_mri_result_existing():
    response = client.get("/api/assessments/66666666-6666-4666-8666-666666666666/mri")
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_class"] == "Very Mildly Demented"
    assert data["binary_prediction"] == "Dementia"
    assert data["binary_probabilities"]["dementia"] == 0.95


def test_get_mri_result_not_found():
    # Assessment exists, but no MRI result uploaded yet
    response = client.get("/api/assessments/77777777-7777-4777-8777-777777777777/mri")
    assert response.status_code == 404
    assert response.json()["detail"] == "MRI assessment result not found."


def test_get_mri_result_nonexistent_assessment():
    # Assessment itself does not exist
    response = client.get("/api/assessments/55555555-5555-4555-8555-555555555555/mri")
    assert response.status_code == 404
    assert response.json()["detail"] == "Assessment not found."
