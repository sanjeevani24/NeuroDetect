import io
import pytest
from PIL import Image

from app.mri.config import DISCLAIMER, MODEL_NAME, MODEL_VERSION
from app.mri.service import (
    InvalidMriImageError,
    MriAssessmentNotFoundError,
    MriService,
)


class FakeAssessmentRepo:
    def __init__(self, exists=True):
        self._exists = exists

    def assessment_exists(self, assessment_id: str) -> bool:
        return self._exists and assessment_id != "00000000-0000-0000-0000-000000000000"

    def get_assessment_session(self, assessment_id: str):
        if not self.assessment_exists(assessment_id):
            return None
        return {
            "assessment_id": assessment_id,
            "patient_id": "11111111-1111-1111-1111-111111111111",
            "full_name": "Test Patient",
            "assessment_type": "MRI_ONLY",
            "current_stage": "MRI",
            "completed_stages": [],
        }


class FakeMriRepo:
    def __init__(self):
        self.saved_records = {}

    def upsert_mri_result(self, **kwargs):
        assessment_id = kwargs["assessment_id"]
        record = {
            "id": "mri-rec-123",
            **kwargs,
            "created_at": "2026-11-20T00:00:00Z",
            "updated_at": "2026-11-20T00:00:00Z",
        }
        self.saved_records[assessment_id] = record
        return record

    def get_by_assessment(self, assessment_id: str):
        return self.saved_records.get(assessment_id)


class FakeModelManager:
    def predict(self, image_input):
        return {
            "predicted_class": "Non-Demented",
            "predicted_class_index": 0,
            "probability_non_demented": 0.85,
            "probability_very_mild": 0.10,
            "probability_mild": 0.04,
            "probability_moderate": 0.01,
            "class_probabilities": {
                "Non-Demented": 0.85,
                "Very Mildly Demented": 0.10,
                "Mildly Demented": 0.04,
                "Moderately Demented": 0.01,
            },
            "binary_prediction": "No Dementia",
            "binary_probabilities": {
                "no_dementia": 0.85,
                "dementia": 0.15,
            },
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "disclaimer": DISCLAIMER,
        }


def make_test_png_bytes(width=100, height=100):
    img = Image.new("RGB", (width, height), color=(120, 120, 120))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.anyio
async def test_mri_service_rejects_empty_bytes():
    service = MriService(FakeAssessmentRepo(), FakeMriRepo(), model_manager=FakeModelManager())
    with pytest.raises(InvalidMriImageError, match="empty"):
        await service.process_mri_upload(
            assessment_id="11111111-1111-1111-1111-111111111111",
            image_bytes=b"",
            filename="scan.png",
        )


@pytest.mark.anyio
async def test_mri_service_rejects_corrupted_image():
    service = MriService(FakeAssessmentRepo(), FakeMriRepo(), model_manager=FakeModelManager())
    with pytest.raises(InvalidMriImageError, match="could not be identified"):
        await service.process_mri_upload(
            assessment_id="11111111-1111-1111-1111-111111111111",
            image_bytes=b"not-a-valid-image-byte-stream",
            filename="scan.png",
        )


@pytest.mark.anyio
async def test_mri_service_rejects_unsupported_content_type():
    service = MriService(FakeAssessmentRepo(), FakeMriRepo(), model_manager=FakeModelManager())
    png_bytes = make_test_png_bytes()
    with pytest.raises(InvalidMriImageError, match="Unsupported file format"):
        await service.process_mri_upload(
            assessment_id="11111111-1111-1111-1111-111111111111",
            image_bytes=png_bytes,
            filename="scan.pdf",
            content_type="application/pdf",
        )


@pytest.mark.anyio
async def test_mri_service_rejects_nonexistent_assessment():
    service = MriService(FakeAssessmentRepo(exists=False), FakeMriRepo(), model_manager=FakeModelManager())
    png_bytes = make_test_png_bytes()
    with pytest.raises(MriAssessmentNotFoundError):
        await service.process_mri_upload(
            assessment_id="00000000-0000-0000-0000-000000000000",
            image_bytes=png_bytes,
            filename="scan.png",
        )


@pytest.mark.anyio
async def test_mri_service_successful_upload_and_get():
    fake_mri_repo = FakeMriRepo()
    service = MriService(
        FakeAssessmentRepo(exists=True),
        fake_mri_repo,
        model_manager=FakeModelManager(),
    )
    png_bytes = make_test_png_bytes(200, 250)

    result = await service.process_mri_upload(
        assessment_id="11111111-1111-1111-1111-111111111111",
        image_bytes=png_bytes,
        filename="brain_mri_slice.png",
        content_type="image/png",
    )

    assert result["assessment_id"] == "11111111-1111-1111-1111-111111111111"
    assert result["predicted_class"] == "Non-Demented"
    assert result["binary_prediction"] == "No Dementia"
    assert result["image_filename"] == "brain_mri_slice.png"

    # Verify retrieval
    retrieved = service.get_mri_result("11111111-1111-1111-1111-111111111111")
    assert retrieved is not None
    assert retrieved["predicted_class"] == "Non-Demented"
    assert retrieved["binary_probabilities"]["no_dementia"] == 0.85
