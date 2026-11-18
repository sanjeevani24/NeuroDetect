import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from app.speech.audio_converter import (
    AudioConversionError,
    FFmpegNotFoundError,
    convert_to_pcm_wav,
    get_ffmpeg_path,
)
from app.speech.service import InvalidAudioError, SpeechService


def make_sine_wav(path: Path, duration_s: float = 1.0, sr: int = 16000, silent: bool = False):
    """Creates a valid PCM WAV fixture."""
    t = np.linspace(0, duration_s, int(sr * duration_s))
    if silent:
        y = np.zeros_like(t, dtype=np.float32)
    else:
        y = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    sf.write(str(path), y, sr, subtype="PCM_16")


def make_media_file(output_path: Path, codec: str, duration_s: float = 1.0, sr: int = 16000):
    """Uses real system FFmpeg to generate valid WebM, MP4, or Ogg fixtures."""
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        pytest.skip("FFmpeg binary not available on system.")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:sample_rate={sr}:duration={duration_s}",
        "-c:a", codec,
        str(output_path),
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        pytest.skip(f"FFmpeg does not support generating codec {codec} on this system.")


# ==============================================================================
# 1. FFmpeg Detection Tests
# ==============================================================================

def test_get_ffmpeg_path_from_path(monkeypatch):
    """Detects system FFmpeg via PATH."""
    monkeypatch.delenv("FFMPEG_PATH", raising=False)
    actual_bin = shutil.which("ffmpeg")
    if not actual_bin:
        pytest.skip("FFmpeg not installed in test environment.")
    found = get_ffmpeg_path()
    assert Path(found).exists()
    assert "ffmpeg" in Path(found).name.lower()


def test_get_ffmpeg_path_from_custom_env(tmp_path, monkeypatch):
    """Detects custom FFmpeg via FFMPEG_PATH environment variable."""
    fake_ffmpeg = tmp_path / ("ffmpeg.exe" if os.name == "nt" else "custom_ffmpeg")
    fake_ffmpeg.write_text("#!/bin/sh\necho ffmpeg 9.0\n")
    fake_ffmpeg.chmod(0o755)

    monkeypatch.setenv("FFMPEG_PATH", str(fake_ffmpeg))
    found = get_ffmpeg_path()
    assert Path(found).resolve() == fake_ffmpeg.resolve()


def test_get_ffmpeg_path_missing(monkeypatch):
    """Raises FFmpegNotFoundError when FFmpeg is not in PATH and FFMPEG_PATH is unset."""
    monkeypatch.delenv("FFMPEG_PATH", raising=False)
    monkeypatch.setattr(shutil, "which", lambda cmd: None)

    with pytest.raises(FFmpegNotFoundError, match="FFmpeg is not installed"):
        get_ffmpeg_path()


def test_get_ffmpeg_path_invalid_custom_path(monkeypatch):
    """Raises FFmpegNotFoundError when FFMPEG_PATH points to non-existent file."""
    monkeypatch.setenv("FFMPEG_PATH", "/path/to/nonexistent/ffmpeg_bin")

    with pytest.raises(FFmpegNotFoundError, match="FFmpeg executable not found at custom FFMPEG_PATH"):
        get_ffmpeg_path()


# ==============================================================================
# 2. Audio Conversion Tests (Real FFmpeg where available)
# ==============================================================================

def test_convert_valid_webm_to_pcm_wav(tmp_path):
    """Converts a real WebM/Opus audio file to signed 16-bit PCM WAV."""
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not installed.")

    webm_file = tmp_path / "recording.webm"
    make_media_file(webm_file, codec="libopus", duration_s=1.5, sr=48000)

    out_wav = tmp_path / "converted.wav"
    result_path = convert_to_pcm_wav(webm_file, out_wav)

    assert result_path.exists()
    assert result_path.stat().st_size > 0

    info = sf.info(str(result_path))
    assert info.format == "WAV"
    assert info.subtype == "PCM_16"
    assert info.samplerate == 48000  # Original sample rate preserved
    assert abs(info.duration - 1.5) < 0.2


def test_convert_valid_mp4_to_pcm_wav(tmp_path):
    """Converts a real MP4/AAC audio file to signed 16-bit PCM WAV."""
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not installed.")

    mp4_file = tmp_path / "recording.mp4"
    make_media_file(mp4_file, codec="aac", duration_s=2.0, sr=44100)

    out_wav = tmp_path / "converted_mp4.wav"
    result_path = convert_to_pcm_wav(mp4_file, out_wav)

    assert result_path.exists()
    info = sf.info(str(result_path))
    assert info.format == "WAV"
    assert info.subtype == "PCM_16"
    assert info.samplerate == 44100  # Original sample rate preserved
    assert abs(info.duration - 2.0) < 0.2


def test_convert_valid_wav_input(tmp_path):
    """Converts a WAV input and normalizes it to clean pcm_s16le."""
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not installed.")

    src_wav = tmp_path / "input.wav"
    make_sine_wav(src_wav, duration_s=1.2, sr=16000)

    out_wav = tmp_path / "normalized.wav"
    result_path = convert_to_pcm_wav(src_wav, out_wav)

    assert result_path.exists()
    info = sf.info(str(result_path))
    assert info.format == "WAV"
    assert info.subtype == "PCM_16"
    assert info.samplerate == 16000


def test_convert_corrupted_audio(tmp_path):
    """Raises AudioConversionError when converting corrupt input bytes."""
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not installed.")

    corrupt_file = tmp_path / "corrupt.webm"
    corrupt_file.write_bytes(b"\x1a\x45\xdf\xa3RANDOM_GARBAGE_BYTES_THAT_ARE_NOT_VALID_AUDIO")

    out_wav = tmp_path / "out.wav"
    with pytest.raises(AudioConversionError, match="Audio conversion failed"):
        convert_to_pcm_wav(corrupt_file, out_wav)


def test_convert_empty_audio_file(tmp_path):
    """Raises AudioConversionError on empty 0-byte input."""
    empty_file = tmp_path / "empty.webm"
    empty_file.write_bytes(b"")

    with pytest.raises(AudioConversionError, match="empty"):
        convert_to_pcm_wav(empty_file)


# ==============================================================================
# 3. Audio Validation & Silence Tests
# ==============================================================================

def test_validate_audio_valid_duration(tmp_path):
    """Valid WAV passes validation and returns accurate duration."""
    wav_file = tmp_path / "valid.wav"
    make_sine_wav(wav_file, duration_s=2.5, sr=16000)

    duration = SpeechService._validate_audio(str(wav_file))
    assert abs(duration - 2.5) < 0.05


def test_validate_audio_too_short(tmp_path):
    """Rejects audio shorter than minimum duration (0.5s)."""
    wav_file = tmp_path / "short.wav"
    make_sine_wav(wav_file, duration_s=0.2, sr=16000)

    with pytest.raises(InvalidAudioError, match="too short"):
        SpeechService._validate_audio(str(wav_file))


def test_validate_audio_too_long(tmp_path, monkeypatch):
    """Rejects audio longer than maximum duration (300s)."""
    wav_file = tmp_path / "long.wav"
    make_sine_wav(wav_file, duration_s=1.0, sr=16000)

    # Mock sf.info to report 305s duration
    orig_info = sf.info(str(wav_file))
    class MockInfo:
        duration = 305.0
        frames = 305 * 16000
        samplerate = 16000
        channels = 1
    monkeypatch.setattr(sf, "info", lambda path: MockInfo())

    with pytest.raises(InvalidAudioError, match="exceeds maximum allowed duration"):
        SpeechService._validate_audio(str(wav_file))


def test_validate_audio_completely_silent(tmp_path):
    """Rejects completely silent audio."""
    wav_file = tmp_path / "silent.wav"
    make_sine_wav(wav_file, duration_s=2.0, sr=16000, silent=True)

    with pytest.raises(InvalidAudioError, match="completely silent"):
        SpeechService._validate_audio(str(wav_file))
