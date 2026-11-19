import io
import os
import tempfile
import unittest.mock
import pytest
import numpy as np
import soundfile as sf

from app.speech.inference import Model3InferenceError
from app.speech.service import AssessmentNotFoundError, InvalidAudioError, SpeechService
from app.speech.transcription_service import (
    BaseTranscriptionService,
    EmptyTranscriptError,
    TranscriptionError,
)


def make_wav_bytes(duration_s: float = 1.0, sr: int = 16000) -> bytes:
    t = np.linspace(0, duration_s, int(sr * duration_s))
    y = (0.4 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, y, sr, format="WAV")
    return buf.getvalue()


class FakeAssessmentRepository:
    def __init__(self, existing_ids: set[str] | None = None):
        self._existing_ids = existing_ids or {"11111111-1111-4111-8111-111111111111"}

    def assessment_exists(self, assessment_id: str) -> bool:
        return assessment_id in self._existing_ids


class FakeSpeechRepository:
    def __init__(self):
        self.records: dict[str, dict] = {}

    def get_by_assessment(self, assessment_id: str):
        return self.records.get(assessment_id)

    def upsert_result(self, *, assessment_id: str, **kwargs):
        record = {"assessment_id": assessment_id, **kwargs}
        self.records[assessment_id] = record
        return record


class FakeTranscriptionService(BaseTranscriptionService):
    def __init__(self, transcript: str = "The boy is taking cookies from the jar, um, while mother washes dishes."):
        self._transcript = transcript
        self.call_count = 0

    @property
    def engine_name(self) -> str:
        return "fake_test_asr"

    async def transcribe(self, audio_path: str) -> str:
        self.call_count += 1
        if not self._transcript:
            raise EmptyTranscriptError("No speech detected.")
        if self._transcript == "__FAIL__":
            raise TranscriptionError("Simulated transcription failure.")
        return self._transcript


class FakeModel3Manager:
    def __init__(self, predicted_class: str = "HC", probabilities: dict | None = None):
        self.predicted_class = predicted_class
        self.probabilities = probabilities or {"HC": 0.85, "MCI": 0.10, "Dementia": 0.05}
        self.call_count = 0

    def predict(self, audio_path: str, transcript: str):
        self.call_count += 1
        if self.predicted_class == "__FAIL__":
            raise Model3InferenceError("Simulated Model 3 execution failure.")
        return {
            "status": "ok",
            "predicted_class": self.predicted_class,
            "probabilities": self.probabilities,
            "hc_probability": self.probabilities.get("HC", 0.0),
            "mci_probability": self.probabilities.get("MCI", 0.0),
            "dementia_probability": self.probabilities.get("Dementia", 0.0),
            "branch_probabilities": {"audio_embedding": self.probabilities},
            "components_used": ["audio_embedding", "acoustic", "transcript"],
            "model_version": "model3-process2-ctd-20261116-full",
            "disclaimer": "Test disclaimer",
        }


@pytest.fixture
def valid_assessment_id():
    return "11111111-1111-4111-8111-111111111111"


@pytest.mark.anyio
async def test_valid_audio_upload_hc_prediction(valid_assessment_id):
    assessment_repo = FakeAssessmentRepository()
    speech_repo = FakeSpeechRepository()
    transcriber = FakeTranscriptionService()
    model_mgr = FakeModel3Manager(predicted_class="HC", probabilities={"HC": 0.82, "MCI": 0.12, "Dementia": 0.06})

    service = SpeechService(assessment_repo, speech_repo, transcriber, model_mgr)
    audio_bytes = make_wav_bytes(duration_s=1.5)

    result = await service.process_speech_upload(
        assessment_id=valid_assessment_id,
        audio_bytes=audio_bytes,
        filename="cookie_theft.wav",
    )

    assert result["status"] == "completed"
    assert result["predicted_class"] == "HC"
    assert result["hc_probability"] == 0.82
    assert result["mci_probability"] == 0.12
    assert result["dementia_probability"] == 0.06
    assert result["transcription_status"] == "completed"
    assert result["inference_status"] == "awaiting_asr_verification"
    assert result["model_version"] == "model3-process2-ctd-20261116-full"

    # Confirmed saved in repository
    stored = speech_repo.get_by_assessment(valid_assessment_id)
    assert stored is not None
    assert stored["predicted_class"] == "HC"


@pytest.mark.anyio
async def test_valid_audio_upload_mci_prediction(valid_assessment_id):
    assessment_repo = FakeAssessmentRepository()
    speech_repo = FakeSpeechRepository()
    transcriber = FakeTranscriptionService()
    model_mgr = FakeModel3Manager(predicted_class="MCI", probabilities={"HC": 0.15, "MCI": 0.75, "Dementia": 0.10})

    service = SpeechService(assessment_repo, speech_repo, transcriber, model_mgr)
    audio_bytes = make_wav_bytes(duration_s=2.0)

    result = await service.process_speech_upload(
        assessment_id=valid_assessment_id,
        audio_bytes=audio_bytes,
    )

    assert result["predicted_class"] == "MCI"
    assert result["mci_probability"] == 0.75


@pytest.mark.anyio
async def test_valid_audio_upload_dementia_prediction(valid_assessment_id):
    assessment_repo = FakeAssessmentRepository()
    speech_repo = FakeSpeechRepository()
    transcriber = FakeTranscriptionService()
    model_mgr = FakeModel3Manager(predicted_class="Dementia", probabilities={"HC": 0.05, "MCI": 0.15, "Dementia": 0.80})

    service = SpeechService(assessment_repo, speech_repo, transcriber, model_mgr)
    audio_bytes = make_wav_bytes(duration_s=2.0)

    result = await service.process_speech_upload(
        assessment_id=valid_assessment_id,
        audio_bytes=audio_bytes,
    )

    assert result["predicted_class"] == "Dementia"
    assert result["dementia_probability"] == 0.80


@pytest.mark.anyio
async def test_invalid_assessment_id_format():
    service = SpeechService(FakeAssessmentRepository(), FakeSpeechRepository(), FakeTranscriptionService(), FakeModel3Manager())
    with pytest.raises(ValueError, match="not a valid UUID"):
        await service.process_speech_upload(
            assessment_id="not-a-valid-uuid",
            audio_bytes=make_wav_bytes(1.0),
        )


@pytest.mark.anyio
async def test_assessment_not_found():
    service = SpeechService(
        FakeAssessmentRepository(existing_ids=set()),
        FakeSpeechRepository(),
        FakeTranscriptionService(),
        FakeModel3Manager(),
    )
    with pytest.raises(AssessmentNotFoundError, match="Assessment not found"):
        await service.process_speech_upload(
            assessment_id="22222222-2222-4222-8222-222222222222",
            audio_bytes=make_wav_bytes(1.0),
        )


@pytest.mark.anyio
async def test_empty_audio_bytes(valid_assessment_id):
    service = SpeechService(FakeAssessmentRepository(), FakeSpeechRepository(), FakeTranscriptionService(), FakeModel3Manager())
    with pytest.raises(InvalidAudioError, match="empty"):
        await service.process_speech_upload(
            assessment_id=valid_assessment_id,
            audio_bytes=b"",
        )


@pytest.mark.anyio
async def test_corrupt_audio_bytes(valid_assessment_id):
    service = SpeechService(FakeAssessmentRepository(), FakeSpeechRepository(), FakeTranscriptionService(), FakeModel3Manager())
    with pytest.raises(InvalidAudioError, match="could not be decoded"):
        await service.process_speech_upload(
            assessment_id=valid_assessment_id,
            audio_bytes=b"RIFF\x00\x00\x00\x00WAVEcorruptdatajunk1234567890",
        )


@pytest.mark.anyio
async def test_audio_shorter_than_half_second(valid_assessment_id):
    service = SpeechService(FakeAssessmentRepository(), FakeSpeechRepository(), FakeTranscriptionService(), FakeModel3Manager())
    # 0.2 seconds is shorter than MIN_DURATION_SECONDS (0.5s)
    short_audio = make_wav_bytes(duration_s=0.2)
    with pytest.raises(InvalidAudioError, match="too short"):
        await service.process_speech_upload(
            assessment_id=valid_assessment_id,
            audio_bytes=short_audio,
        )


@pytest.mark.anyio
async def test_transcription_failure_handling(valid_assessment_id):
    speech_repo = FakeSpeechRepository()
    transcriber = FakeTranscriptionService(transcript="__FAIL__")
    service = SpeechService(FakeAssessmentRepository(), speech_repo, transcriber, FakeModel3Manager())

    with pytest.raises(TranscriptionError, match="Simulated transcription failure"):
        await service.process_speech_upload(
            assessment_id=valid_assessment_id,
            audio_bytes=make_wav_bytes(1.0),
        )

    # Repository status updated to failed
    stored = speech_repo.get_by_assessment(valid_assessment_id)
    assert stored is not None
    assert stored["transcription_status"] == "failed"
    assert stored["inference_status"] == "failed"


@pytest.mark.anyio
async def test_empty_transcript_handling(valid_assessment_id):
    speech_repo = FakeSpeechRepository()
    transcriber = FakeTranscriptionService(transcript="")
    service = SpeechService(FakeAssessmentRepository(), speech_repo, transcriber, FakeModel3Manager())

    with pytest.raises(InvalidAudioError, match="no detectable or intelligible words"):
        await service.process_speech_upload(
            assessment_id=valid_assessment_id,
            audio_bytes=make_wav_bytes(1.0),
        )


@pytest.mark.anyio
async def test_model3_inference_failure(valid_assessment_id):
    speech_repo = FakeSpeechRepository()
    transcriber = FakeTranscriptionService()
    model_mgr = FakeModel3Manager(predicted_class="__FAIL__")
    service = SpeechService(FakeAssessmentRepository(), speech_repo, transcriber, model_mgr)

    with pytest.raises(Model3InferenceError, match="Simulated Model 3 execution failure"):
        await service.process_speech_upload(
            assessment_id=valid_assessment_id,
            audio_bytes=make_wav_bytes(1.0),
        )

    stored = speech_repo.get_by_assessment(valid_assessment_id)
    assert stored is not None
    assert stored["inference_status"] == "failed"


@pytest.mark.anyio
async def test_duplicate_submission_upserts_record(valid_assessment_id):
    speech_repo = FakeSpeechRepository()
    service = SpeechService(FakeAssessmentRepository(), speech_repo, FakeTranscriptionService(), FakeModel3Manager())

    audio_bytes = make_wav_bytes(1.0)
    res1 = await service.process_speech_upload(assessment_id=valid_assessment_id, audio_bytes=audio_bytes)
    res2 = await service.process_speech_upload(assessment_id=valid_assessment_id, audio_bytes=audio_bytes)

    assert res1["assessment_id"] == valid_assessment_id
    assert res2["assessment_id"] == valid_assessment_id
    # Only one record in repository for this assessment_id
    assert len(speech_repo.records) == 1


# ==============================================================================
# Temporary File Cleanup & Conversion Integration Tests
# ==============================================================================

@pytest.mark.anyio
async def test_same_converted_wav_passed_to_transcription_and_model3(valid_assessment_id):
    """Verifies that transcription and Model 3 receive the exact same converted PCM WAV file."""
    captured_paths = {}

    class TrackingTranscriber(BaseTranscriptionService):
        @property
        def engine_name(self) -> str:
            return "tracking_asr"

        async def transcribe(self, audio_path: str) -> str:
            captured_paths["transcribe"] = audio_path
            assert os.path.exists(audio_path), "Audio file must exist during transcription"
            return "The woman is drying dishes while the water overflows."

    class TrackingModelManager:
        def predict(self, audio_path: str, transcript: str):
            captured_paths["predict_audio"] = audio_path
            captured_paths["predict_transcript"] = transcript
            assert os.path.exists(audio_path), "Audio file must exist during Model 3 inference"
            return {
                "status": "ok",
                "predicted_class": "HC",
                "hc_probability": 0.90,
                "mci_probability": 0.08,
                "dementia_probability": 0.02,
                "probabilities": {"HC": 0.90, "MCI": 0.08, "Dementia": 0.02},
                "model_version": "1.0.0",
            }

    service = SpeechService(
        FakeAssessmentRepository(),
        FakeSpeechRepository(),
        TrackingTranscriber(),
        TrackingModelManager(),
    )

    audio_bytes = make_wav_bytes(1.5)
    await service.process_speech_upload(
        assessment_id=valid_assessment_id,
        audio_bytes=audio_bytes,
        filename="speech.wav",
    )

    assert "transcribe" in captured_paths
    assert "predict_audio" in captured_paths
    # Both services received the exact same converted WAV path
    assert captured_paths["transcribe"] == captured_paths["predict_audio"]
    assert captured_paths["transcribe"].endswith(".wav")
    # And after the call completes, the temporary file has been cleaned up
    assert not os.path.exists(captured_paths["transcribe"])


@pytest.mark.anyio
async def test_temp_file_cleanup_on_success(valid_assessment_id):
    """Verifies that both raw and converted temporary files are deleted after success."""
    created_files = []
    import tempfile
    orig_named_temp = tempfile.NamedTemporaryFile

    def tracking_temp_file(*args, **kwargs):
        tf = orig_named_temp(*args, **kwargs)
        created_files.append(tf.name)
        return tf

    service = SpeechService(
        FakeAssessmentRepository(),
        FakeSpeechRepository(),
        FakeTranscriptionService(),
        FakeModel3Manager(),
    )

    import unittest.mock
    with unittest.mock.patch("tempfile.NamedTemporaryFile", side_effect=tracking_temp_file):
        await service.process_speech_upload(
            assessment_id=valid_assessment_id,
            audio_bytes=make_wav_bytes(1.2),
        )

    assert len(created_files) == 2, f"Expected 2 temp files created (raw + converted wav), got {created_files}"
    for path in created_files:
        assert not os.path.exists(path), f"Temp file was not cleaned up on success: {path}"


@pytest.mark.anyio
async def test_temp_file_cleanup_on_transcription_failure(valid_assessment_id):
    """Verifies that temporary files are deleted when transcription fails."""
    created_files = []
    orig_named_temp = tempfile.NamedTemporaryFile

    def tracking_temp_file(*args, **kwargs):
        tf = orig_named_temp(*args, **kwargs)
        created_files.append(tf.name)
        return tf

    service = SpeechService(
        FakeAssessmentRepository(),
        FakeSpeechRepository(),
        FakeTranscriptionService(transcript="__FAIL__"),
        FakeModel3Manager(),
    )

    import unittest.mock
    with unittest.mock.patch("tempfile.NamedTemporaryFile", side_effect=tracking_temp_file):
        with pytest.raises(TranscriptionError):
            await service.process_speech_upload(
                assessment_id=valid_assessment_id,
                audio_bytes=make_wav_bytes(1.2),
            )

    assert len(created_files) == 2
    for path in created_files:
        assert not os.path.exists(path), f"Temp file was not cleaned up on transcription failure: {path}"


@pytest.mark.anyio
async def test_temp_file_cleanup_on_model3_failure(valid_assessment_id):
    """Verifies that temporary files are deleted when Model 3 inference fails."""
    created_files = []
    orig_named_temp = tempfile.NamedTemporaryFile

    def tracking_temp_file(*args, **kwargs):
        tf = orig_named_temp(*args, **kwargs)
        created_files.append(tf.name)
        return tf

    service = SpeechService(
        FakeAssessmentRepository(),
        FakeSpeechRepository(),
        FakeTranscriptionService(),
        FakeModel3Manager(predicted_class="__FAIL__"),
    )

    import unittest.mock
    with unittest.mock.patch("tempfile.NamedTemporaryFile", side_effect=tracking_temp_file):
        with pytest.raises(Model3InferenceError):
            await service.process_speech_upload(
                assessment_id=valid_assessment_id,
                audio_bytes=make_wav_bytes(1.2),
            )

    assert len(created_files) == 2
    for path in created_files:
        assert not os.path.exists(path), f"Temp file was not cleaned up on Model 3 failure: {path}"


@pytest.mark.anyio
async def test_temp_file_cleanup_on_ffmpeg_failure(valid_assessment_id):
    """Verifies that temporary files are deleted when FFmpeg conversion fails on corrupt audio."""
    created_files = []
    orig_named_temp = tempfile.NamedTemporaryFile

    def tracking_temp_file(*args, **kwargs):
        tf = orig_named_temp(*args, **kwargs)
        created_files.append(tf.name)
        return tf

    service = SpeechService(
        FakeAssessmentRepository(),
        FakeSpeechRepository(),
        FakeTranscriptionService(),
        FakeModel3Manager(),
    )

    import unittest.mock
    corrupt_bytes = b"\x1a\x45\xdf\xa3CORRUPT_NOT_AUDIO"
    with unittest.mock.patch("tempfile.NamedTemporaryFile", side_effect=tracking_temp_file):
        with pytest.raises(InvalidAudioError, match="could not be decoded"):
            await service.process_speech_upload(
                assessment_id=valid_assessment_id,
                audio_bytes=corrupt_bytes,
                filename="corrupt.webm",
                content_type="audio/webm",
            )

    for path in created_files:
        assert not os.path.exists(path), f"Temp file was not cleaned up on FFmpeg failure: {path}"


@pytest.mark.anyio
async def test_real_webm_audio_upload_integration(valid_assessment_id, tmp_path):
    """Tests end-to-end processing of a real WebM/Opus audio recording using FFmpeg."""
    import shutil
    import subprocess
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not installed.")

    # Generate real WebM/Opus audio file using FFmpeg
    raw_webm = tmp_path / "fixture.webm"
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "sine=frequency=440:sample_rate=48000:duration=1.8",
        "-c:a", "libopus",
        str(raw_webm),
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        pytest.skip("FFmpeg does not support libopus encoding.")

    webm_bytes = raw_webm.read_bytes()
    assert len(webm_bytes) > 0

    speech_repo = FakeSpeechRepository()
    transcriber = FakeTranscriptionService(transcript="The boy is climbing on a stool to reach the cookie jar.")
    model_mgr = FakeModel3Manager(predicted_class="HC", probabilities={"HC": 0.88, "MCI": 0.09, "Dementia": 0.03})

    service = SpeechService(FakeAssessmentRepository(), speech_repo, transcriber, model_mgr)

    result = await service.process_speech_upload(
        assessment_id=valid_assessment_id,
        audio_bytes=webm_bytes,
        filename="recording.webm",
        content_type="audio/webm;codecs=opus",
    )

    assert result["status"] == "completed"
    assert result["predicted_class"] == "HC"
    assert abs(result["probability_hc"] - 0.88) < 1e-4
    assert result["transcription_status"] == "completed"
    assert result["inference_status"] == "awaiting_asr_verification"

    # Confirmed in repository
    record = speech_repo.get_by_assessment(valid_assessment_id)
    assert record is not None
    assert record["predicted_class"] == "HC"
    assert record["audio_format"] == "wav"
    assert record["audio_duration_seconds"] > 1.0

