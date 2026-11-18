from __future__ import annotations

from datetime import datetime, timedelta

from app.games.boston_naming.config import DifficultyLevel
from app.games.boston_naming.schemas import (
    CorrectnessLabel,
    ErrorType,
    RecordingStatus,
    ReconstructedNamingTrial,
    TranscriptionStatus,
)

T0 = datetime(2026, 1, 1, 12, 0, 0)


def make_trial(
    trial_index: int,
    stimulus_id: str,
    difficulty: DifficultyLevel,
    *,
    correctness: CorrectnessLabel,
    error_type: ErrorType = ErrorType.NONE,
    cue_used: bool = False,
    semantic_cue_used: bool = False,
    phonemic_cue_used: bool = False,
    self_corrected: bool | None = None,
    response_latency_ms: float | None = 1200.0,
    response_duration_ms: float | None = 900.0,
    hesitation_duration_ms: float | None = 1200.0,
    timeout: bool = False,
) -> ReconstructedNamingTrial:
    started = T0 + timedelta(seconds=trial_index * 5)
    return ReconstructedNamingTrial(
        trial_id=f"trial-{trial_index}",
        trial_index=trial_index,
        stimulus_id=stimulus_id,
        difficulty=difficulty,
        is_practice=False,
        stimulus_presented_at=started,
        response_started_at=started + timedelta(milliseconds=response_latency_ms or 0),
        response_completed_at=started + timedelta(milliseconds=(response_latency_ms or 0) + (response_duration_ms or 0)),
        audio_start_timestamp=started + timedelta(milliseconds=response_latency_ms or 0),
        audio_end_timestamp=started + timedelta(milliseconds=(response_latency_ms or 0) + (response_duration_ms or 0)),
        response_duration_ms=response_duration_ms,
        response_latency_ms=response_latency_ms,
        transcript="sample response",
        transcript_confidence=0.9,
        transcription_status=TranscriptionStatus.SUCCESS,
        normalized_response="sample response",
        initial_response="sample response",
        final_response="sample response",
        correctness=correctness,
        error_type=error_type,
        cue_used=cue_used,
        semantic_cue_used=semantic_cue_used,
        phonemic_cue_used=phonemic_cue_used,
        time_to_cue_ms=5000.0 if cue_used else None,
        response_after_cue_ms=1300.0 if cue_used else None,
        correct_after_cue=cue_used and correctness == CorrectnessLabel.CORRECT,
        self_corrected=self_corrected,
        self_correction_latency_ms=350.0 if self_corrected else None,
        hesitation_duration_ms=hesitation_duration_ms,
        number_of_hesitation_markers=1 if hesitation_duration_ms else 0,
        timeout=timeout,
        recording_status=RecordingStatus.SUCCESS,
    )
