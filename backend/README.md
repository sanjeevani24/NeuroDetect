# NeuroDetect Backend & Speech Assessment Pipeline

FastAPI backend providing cognitive assessment scoring, machine learning inference (Model 1 cognitive regression, Model 2 psychiatric screening, Model 3 speech classification), and Supabase persistence.

---

## 1. Speech Assessment Audio Pipeline

The Speech Assessment module accepts speech recordings from the browser (Cookie Theft Picture Description stimulus), decodes browser-encoded audio using FFmpeg, validates audio quality and duration, transcribes speech, and runs Model 3 inference.

```text
Browser MediaRecorder (WebM/Opus, OGG, MP4, WAV)
  -> POST /api/assessments/{assessment_id}/speech/upload
  -> Ephemeral temporary file creation
  -> Cross-platform FFmpeg decoding -> Signed 16-bit PCM WAV (pcm_s16le)
  -> SoundFile validation (sample rate, channels, frames, duration, silence)
  -> Transcription Service -> Cleaned transcript
  -> Model 3 PROCESS-2 Inference (Wav2Vec2 + Acoustic + DistilBERT + Logistic Regression)
  -> Dual-table persistence in Supabase:
       - speech_assessments (metadata & telemetry)
       - model3_results (prediction outputs)
  -> Temporary file cleanup in finally block (both raw and converted WAV deleted)
```

### Privacy & Temporary Files
Audio recordings are processed **ephemerally**: raw audio bytes and converted WAV files are stored in temporary files only during processing and are immediately removed via `os.unlink()` in a `finally` block, regardless of whether processing succeeds or fails. Voice recordings are never stored unencrypted in cloud storage.

---

## 2. Supported Audio Formats

Browser-recorded and uploaded audio is accepted in the following formats:
- **WebM / Opus** (`audio/webm`, `audio/webm;codecs=opus`) — Standard for Chrome, Firefox, Edge
- **Ogg / Opus / Vorbis** (`audio/ogg`, `audio/ogg;codecs=opus`)
- **MP4 / AAC** (`audio/mp4`, `audio/m4a`, `audio/x-m4a`, `audio/aac`) — Standard for Safari
- **WAV** (`audio/wav`, `audio/x-wav`) — Standard uncompressed audio
- **MPEG / MP3** (`audio/mpeg`)

---

## 3. FFmpeg Installation & Configuration

FFmpeg is required to convert containerized browser audio into standard signed 16-bit PCM WAV.

### macOS
Using Homebrew:
```bash
brew install ffmpeg
ffmpeg -version
```

### Windows
Using Windows Package Manager (winget):
```powershell
winget install Gyan.FFmpeg
ffmpeg -version
```
*Note: After installing via winget, close and reopen your PowerShell terminal so PATH environment variables take effect.*

Alternatively, install using Chocolatey or Scoop:
```powershell
choco install ffmpeg
# or
scoop install ffmpeg
```

### Custom FFmpeg Path (`FFMPEG_PATH`)
If FFmpeg is installed in a non-standard location or portable directory, set the `FFMPEG_PATH` environment variable:

- **macOS / Linux**:
  ```bash
  export FFMPEG_PATH="/opt/homebrew/bin/ffmpeg"
  ```
- **Windows (PowerShell)**:
  ```powershell
  $env:FFMPEG_PATH="C:\ffmpeg\bin\ffmpeg.exe"
  ```
- **In `.env` file**:
  ```env
  FFMPEG_PATH=/custom/path/to/ffmpeg
  ```

The backend dynamically checks `FFMPEG_PATH` first, then falls back to searching system `PATH` via `shutil.which("ffmpeg")`.

---

## 4. Local Automatic Speech Recognition (faster-whisper)

NeuroDetect uses `faster-whisper` for local, on-device speech transcription without sending clinical voice recordings to external cloud APIs.

- **Model**: Default is `base` (English), requiring ~140 MB of memory.
- **Compute**: Uses CPU inference with INT8 quantization (`compute_type="int8"` with automatic fallback to `"default"`).
- **Caching**: The model is downloaded on first use, loaded into memory once as a singleton, and reused across all participant requests.
- **Neutral Transcription**: Whisper decoding operates neutrally without scene-specific linguistic guidance, capturing natural spoken content accurately without vocabulary bias.

### Optional ASR Environment Variables
- `WHISPER_MODEL_SIZE`: Whisper model size (`tiny`, `base`, `small`, `medium`). Default: `base`.
- `WHISPER_DEVICE`: Inference device (`cpu` or `cuda`). Default: `cpu`.
- `WHISPER_COMPUTE_TYPE`: Precision (`int8`, `float32`, `default`). Default: `int8`.

---

## 5. Running the Backend

### macOS / Linux
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Windows (PowerShell)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH="."
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 6. Testing Audio Conversion & ASR

Run the full speech, audio converter, and ASR test suite:

```bash
# Run ASR tests
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/speech/test_transcription.py -v

# Run audio converter tests
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/speech/test_audio_converter.py -v

# Run all speech tests
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/speech/ -v

# Run entire backend test suite
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/ -v
```

---

## 7. Troubleshooting

1. **`FFmpeg is not installed or not found in system PATH` (503 Service Unavailable)**:
   - Ensure `ffmpeg -version` works in your terminal.
   - If installed in a custom location, add `FFMPEG_PATH=<path_to_ffmpeg>` to your environment or `.env`.
   - On Windows, restart your IDE/terminal after running `winget install Gyan.FFmpeg`.

2. **`Uploaded audio could not be decoded. Unsupported or corrupted audio format.` (422 Unprocessable Content)**:
   - The uploaded file container was truncated, empty, or corrupted.
   - Verify microphone recording permissions in the browser.

3. **`Audio recording is completely silent.` (422 Unprocessable Content)**:
   - The microphone captured no audible sound (peak amplitude < 1e-5). Check your microphone input levels.

4. **`Audio recording is too short / exceeds maximum allowed duration` (422 Unprocessable Content)**:
   - Speech recordings must be between 0.5 seconds and 300 seconds (5 minutes).
