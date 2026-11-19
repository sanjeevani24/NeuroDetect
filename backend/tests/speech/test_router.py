import io
import pytest
from fastapi.testclient import TestClient
import numpy as np
import soundfile as sf

from app.main import app
from app.speech.inference import Model3InferenceError
from app.speech.router import get_speech_service
from app.speech.service import AssessmentNotFoundError, InvalidAudioError, SpeechService
from app.speech.transcription_service import BaseTranscriptionService, TranscriptionError


def make_test_wav(duration_s: float = 1.0) -> bytes:
    sr = 16000
    t = np.linspace(0, duration_s, int(sr * duration_s))
    y = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, y, sr, format="WAV")
    return buf.getvalue()


class FakeService:
    def __init__(self):
        self.results = {}

    async def process_speech_upload(
        self,
        *,
        assessment_id: str,
        audio_bytes: bytes,
        filename: str = "rec.wav",
        content_type: str | None = None,
        manual_transcript: str | None = None,
    ):
        if assessment_id == "44444444-4444-4444-8444-444444444444":
            raise AssessmentNotFoundError("Assessment not found.")
        if assessment_id == "55555555-5555-4555-8555-555555555555":
            raise InvalidAudioError("Uploaded audio could not be decoded.")
        if assessment_id == "66666666-6666-4666-8666-666666666666":
            raise TranscriptionError("ASR model failed.")
        if assessment_id == "77777777-7777-4777-8777-777777777777":
            raise Model3InferenceError("Model 3 execution failed.")

        record = {
            "assessment_id": assessment_id,
            "status": "completed",
            "transcription_status": "completed",
            "transcription_engine": "fake_test_asr",
            "inference_status": "awaiting_asr_verification",
            "predicted_class": "HC",
            "probabilities": {"HC": 0.88, "MCI": 0.08, "Dementia": 0.04},
            "hc_probability": 0.88,
            "mci_probability": 0.08,
            "dementia_probability": 0.04,
            "branch_probabilities": {},
            "components_used": ["audio_embedding", "acoustic", "transcript"],
            "model_version": "model3-process2-ctd-20261116-full",
            "disclaimer": "Test disclaimer",
        }
        self.results[assessment_id] = record
        return record

    def get_speech_result(self, assessment_id: str):
        return self.results.get(assessment_id)


fake_service = FakeService()


def override_speech_service():
    return fake_service


client = TestClient(app)


def setup_module():
    app.dependency_overrides[get_speech_service] = override_speech_service


def teardown_module():
    app.dependency_overrides.pop(get_speech_service, None)


def test_upload_valid_audio():
    assessment_id = "11111111-1111-4111-8111-111111111111"
    wav_bytes = make_test_wav(1.0)

    response = client.post(
        f"/api/assessments/{assessment_id}/speech/upload",
        files={"audio": ("sample.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["assessment_id"] == assessment_id
    assert payload["predicted_class"] == "HC"
    assert payload["probabilities"]["HC"] == 0.88
    assert payload["model_version"] == "model3-process2-ctd-20261116-full"


def test_upload_invalid_uuid():
    response = client.post(
        "/api/assessments/not-a-uuid/speech/upload",
        files={"audio": ("sample.wav", b"fake", "audio/wav")},
    )
    assert response.status_code == 400
    assert "valid UUID" in response.json()["detail"]


def test_upload_empty_audio_file():
    assessment_id = "11111111-1111-4111-8111-111111111111"
    response = client.post(
        f"/api/assessments/{assessment_id}/speech/upload",
        files={"audio": ("empty.wav", b"", "audio/wav")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_assessment_not_found():
    assessment_id = "44444444-4444-4444-8444-444444444444"
    response = client.post(
        f"/api/assessments/{assessment_id}/speech/upload",
        files={"audio": ("sample.wav", make_test_wav(), "audio/wav")},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Assessment not found."


def test_upload_corrupt_audio_format():
    assessment_id = "55555555-5555-4555-8555-555555555555"
    response = client.post(
        f"/api/assessments/{assessment_id}/speech/upload",
        files={"audio": ("sample.wav", make_test_wav(), "audio/wav")},
    )
    assert response.status_code == 422
    assert "could not be decoded" in response.json()["detail"]


def test_upload_transcription_error():
    assessment_id = "66666666-6666-4666-8666-666666666666"
    response = client.post(
        f"/api/assessments/{assessment_id}/speech/upload",
        files={"audio": ("sample.wav", make_test_wav(), "audio/wav")},
    )
    assert response.status_code == 502
    assert "transcription failed" in response.json()["detail"].lower()


def test_upload_model3_inference_error():
    assessment_id = "77777777-7777-4777-8777-777777777777"
    response = client.post(
        f"/api/assessments/{assessment_id}/speech/upload",
        files={"audio": ("sample.wav", make_test_wav(), "audio/wav")},
    )
    assert response.status_code == 500
    assert "Model 3 inference failed" in response.json()["detail"]


def test_get_speech_result_success():
    assessment_id = "11111111-1111-4111-8111-111111111111"
    # Ensure it's in fake_service results
    fake_service.results[assessment_id] = {
        "assessment_id": assessment_id,
        "inference_status": "completed",
        "transcription_status": "completed",
        "transcription_engine": "pluggable_local_asr",
        "predicted_class": "HC",
        "hc_probability": 0.90,
        "mci_probability": 0.07,
        "dementia_probability": 0.03,
        "branch_probabilities": {},
        "components_used": ["audio_embedding", "acoustic", "transcript"],
        "model_version": "model3-process2-ctd-20261116-full",
        "disclaimer": "Research only.",
    }

    response = client.get(f"/api/assessments/{assessment_id}/speech")
    assert response.status_code == 200
    data = response.json()
    assert data["assessment_id"] == assessment_id
    assert data["predicted_class"] == "HC"
    assert data["hc_probability"] == 0.90
    assert data["probabilities"]["HC"] == 0.90


def test_get_speech_result_not_found():
    response = client.get("/api/assessments/99999999-9999-4999-8999-999999999999/speech")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_speech_result_invalid_uuid():
    response = client.get("/api/assessments/invalid-uuid/speech")
    assert response.status_code == 400
    assert "valid UUID" in response.json()["detail"]
