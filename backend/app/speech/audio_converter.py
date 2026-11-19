"""
Cross-Platform Audio Converter for NeuroDetect Speech Assessment.

Detects FFmpeg on macOS and Windows, converts browser-recorded audio
(WebM/Opus, OGG, MP4, AAC, WAV) into standard signed 16-bit PCM WAV,
and preserves original sample rate and channel count.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("neurodetect.speech.audio_converter")

DEFAULT_CONVERSION_TIMEOUT_SECONDS = 30


class FFmpegNotFoundError(Exception):
    """Raised when FFmpeg executable cannot be located via PATH or FFMPEG_PATH."""


class AudioConversionError(Exception):
    """Raised when FFmpeg fails to decode or convert audio."""


def get_ffmpeg_path() -> str:
    """
    Locates the FFmpeg binary on the system.
    
    1. Checks the optional FFMPEG_PATH environment variable.
    2. Searches system PATH via shutil.which("ffmpeg").
    3. Handles Windows and macOS/Linux executable conventions.
    
    Raises:
        FFmpegNotFoundError: If FFmpeg cannot be located or custom path is invalid.
    """
    custom_path = os.getenv("FFMPEG_PATH", "").strip()
    if custom_path:
        path = Path(os.path.expanduser(custom_path)).resolve()
        if path.is_file():
            # Check executable permissions where supported
            if os.name == "nt" or os.access(str(path), os.X_OK):
                return str(path)
        raise FFmpegNotFoundError(
            f"FFmpeg executable not found at custom FFMPEG_PATH: '{custom_path}'. "
            "Please verify that the file exists and is executable."
        )

    # Search PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if not system_ffmpeg and os.name == "nt":
        system_ffmpeg = shutil.which("ffmpeg.exe")

    if system_ffmpeg:
        return system_ffmpeg

    raise FFmpegNotFoundError(
        "FFmpeg is not installed or not found in system PATH. "
        "Please install FFmpeg (macOS: 'brew install ffmpeg', Windows: 'winget install Gyan.FFmpeg') "
        "or specify the executable path using the FFMPEG_PATH environment variable."
    )


def convert_to_pcm_wav(
    input_path: Path | str,
    output_path: Optional[Path | str] = None,
    timeout_seconds: int = DEFAULT_CONVERSION_TIMEOUT_SECONDS,
) -> Path:
    """
    Decodes browser-recorded audio into signed 16-bit PCM WAV format (pcm_s16le).
    Preserves original sample rate and channel count for Model 3's own preprocessing.
    
    Equivalent to:
        ffmpeg -y -i <input> -vn -c:a pcm_s16le <output>
    
    Args:
        input_path: Path to the input audio file.
        output_path: Destination path for the converted WAV file.
        timeout_seconds: Maximum time allowed for FFmpeg conversion.
        
    Returns:
        Path to the validated, non-empty output WAV file.
        
    Raises:
        FFmpegNotFoundError: If FFmpeg binary is missing.
        AudioConversionError: If FFmpeg fails, times out, or produces invalid output.
    """
    input_p = Path(input_path).resolve()
    if not input_p.exists():
        raise AudioConversionError(f"Input audio file does not exist: {input_p}")
    if input_p.stat().st_size == 0:
        raise AudioConversionError("Input audio file is empty (0 bytes).")

    if output_path is None:
        output_p = input_p.with_suffix(".pcm.wav")
    else:
        output_p = Path(output_path).resolve()

    ffmpeg_bin = get_ffmpeg_path()

    cmd = [
        ffmpeg_bin,
        "-y",               # Overwrite output without prompting
        "-i", str(input_p), # Input file path
        "-vn",              # Disable video streams if present
        "-c:a", "pcm_s16le",# Standard 16-bit PCM audio codec
        str(output_p),      # Output WAV path
    ]

    logger.debug("Executing FFmpeg conversion: %s", " ".join(cmd))

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("FFmpeg conversion timed out after %ds for %s", timeout_seconds, input_p)
        raise AudioConversionError(
            f"Audio conversion timed out after {timeout_seconds} seconds."
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error executing FFmpeg: %s", exc)
        raise AudioConversionError(f"Failed to execute FFmpeg: {exc}") from exc

    if proc.returncode != 0:
        stderr_msg = proc.stderr.decode("utf-8", errors="replace").strip()
        last_error_line = stderr_msg.splitlines()[-1] if stderr_msg else "Unknown FFmpeg error"
        logger.error("FFmpeg conversion failed (code %d): %s", proc.returncode, last_error_line)
        raise AudioConversionError(
            f"Audio conversion failed: {last_error_line}"
        )

    if not output_p.exists() or output_p.stat().st_size == 0:
        raise AudioConversionError(
            "FFmpeg reported success but produced a missing or empty output WAV file."
        )

    return output_p
