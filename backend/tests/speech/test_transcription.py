import os
import shutil
import subprocess
import pytest

from app.speech.transcription_service import (
    EmptyTranscriptError,
    PluggableLocalASRService,
    TranscriptionError,
    _MODEL_CACHE,
    get_transcription_service,
)


@pytest.fixture
def spoken_audio_wav(tmp_path):
    """Generates a small speech WAV file using macOS 'say' or FFmpeg if available."""
    wav_path = tmp_path / "test_speech.wav"
    say_bin = shutil.which("say")
    ffmpeg_bin = shutil.which("ffmpeg")

    if say_bin and ffmpeg_bin:
        aiff_path = tmp_path / "test_speech.aiff"
        subprocess.run(
            [say_bin, "-o", str(aiff_path), "The boy is taking cookies from the jar, um, while his mother washes dishes."],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            [ffmpeg_bin, "-y", "-i", str(aiff_path), "-c:a", "pcm_s16le", str(wav_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return wav_path

    pytest.skip("Audio synthesis tools ('say' + 'ffmpeg') not available.")


def test_faster_whisper_imports_and_engine_name():
    """Verifies that faster-whisper imports and reports the correct engine name."""
    service = PluggableLocalASRService(model_size="base")
    assert service.engine_name == "faster_whisper_base"


def test_model_loaded_once_and_reused():
    """Verifies that the faster-whisper model is cached in _MODEL_CACHE and reused."""
    service = PluggableLocalASRService(model_size="base")
    backend1, model1 = service._get_or_load_model()
    assert backend1 == "faster_whisper"

    # Second call should return the exact same model instance from cache
    backend2, model2 = service._get_or_load_model()
    assert backend2 == "faster_whisper"
    assert model1 is model2


@pytest.mark.anyio
async def test_transcribe_actual_speech_wav(spoken_audio_wav):
    """Verifies that faster-whisper transcribes actual speech and preserves words."""
    service = PluggableLocalASRService(model_size="base")
    transcript = await service.transcribe(str(spoken_audio_wav))

    assert transcript is not None
    assert len(transcript.strip()) > 0
    # Expected key words from spoken stimulus
    lower = transcript.lower()
    assert any(w in lower for w in ("boy", "cookie", "cookies", "jar", "mother", "dishes"))


@pytest.mark.anyio
async def test_transcribe_missing_file_raises_error():
    """Verifies that transcription fails cleanly when input file is missing."""
    service = PluggableLocalASRService(model_size="base")
    with pytest.raises(TranscriptionError, match="not found"):
        await service.transcribe("/path/to/nonexistent/audio.wav")


@pytest.mark.anyio
async def test_transcribe_silent_or_non_speech_raises_empty_transcript(tmp_path):
    """Verifies that non-speech audio raises EmptyTranscriptError without fabricating."""
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not installed.")

    tone_wav = tmp_path / "tone.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1.5", "-c:a", "pcm_s16le", str(tone_wav)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    service = PluggableLocalASRService(model_size="base")
    with pytest.raises(EmptyTranscriptError, match="no intelligible words"):
        await service.transcribe(str(tone_wav))


@pytest.mark.anyio
async def test_no_scene_specific_initial_prompt_passed(tmp_path):
    """
    Verifies that the faster-whisper transcription engine receives no Cookie Theft
    or scene-specific initial prompt, ensuring neutral and unbiased transcription.
    """
    service = PluggableLocalASRService(model_size="base")
    assert service._initial_prompt is None

    test_wav = tmp_path / "dummy.wav"
    test_wav.write_bytes(b"RIFF....WAVEfmt ....data....")

    captured_kwargs = {}

    class DummySegment:
        text = "Hello world"

    class MockWhisperModel:
        def transcribe(self, audio_path, **kwargs):
            captured_kwargs.update(kwargs)
            return ([DummySegment()], None)

    # Patch model loading to return our mock
    service._get_or_load_model = lambda: ("faster_whisper", MockWhisperModel())

    result = await service.transcribe(str(test_wav))
    assert result == "Hello world"

    # Confirm no scene-specific prompt is passed
    prompt = captured_kwargs.get("initial_prompt")
    assert prompt is None or prompt == "", f"Expected no initial_prompt, got: {prompt!r}"
    if prompt:
        lower_prompt = prompt.lower()
        assert "cookie" not in lower_prompt
        assert "theft" not in lower_prompt
        assert "jar" not in lower_prompt
        assert "overflowing" not in lower_prompt


def test_get_transcription_service_factory():
    """Verifies factory returns PluggableLocalASRService by default."""
    service = get_transcription_service()
    assert isinstance(service, PluggableLocalASRService)
    assert service.engine_name == "faster_whisper_base"


@pytest.mark.anyio
async def test_full_pipeline_with_real_faster_whisper(spoken_audio_wav):
    """
    End-to-end integration test: Real spoken audio passes through SpeechService,
    converts via FFmpeg, transcribes with faster-whisper, and passes the transcript
    and converted WAV to Model 3.
    """
    from app.speech.service import SpeechService
    from tests.speech.test_service import FakeAssessmentRepository, FakeSpeechRepository, FakeModel3Manager

    aid = "11111111-1111-4111-8111-111111111111"
    captured = {}

    class SpyingModelManager(FakeModel3Manager):
        def predict(self, audio_path: str, transcript: str):
            captured["audio_path"] = audio_path
            captured["transcript"] = transcript
            return super().predict(audio_path, transcript)

    service = SpeechService(
        FakeAssessmentRepository({aid}),
        FakeSpeechRepository(),
        PluggableLocalASRService(model_size="base"),
        SpyingModelManager(predicted_class="HC"),
    )

    audio_bytes = spoken_audio_wav.read_bytes()
    result = await service.process_speech_upload(
        assessment_id=aid,
        audio_bytes=audio_bytes,
        filename="cookie_theft.wav",
    )

    assert result["status"] == "completed"
    assert result["predicted_class"] == "HC"
    assert result["transcription_status"] == "completed"
    assert result["inference_status"] == "awaiting_asr_verification"
    assert "transcript" in captured
    assert len(captured["transcript"]) > 0
    assert captured["audio_path"].endswith(".wav")

