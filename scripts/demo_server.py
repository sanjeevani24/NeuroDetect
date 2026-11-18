"""
Local Demo & Testing Server for NeuroDetect.
Provides in-memory mock repositories and services so the entire UI workflow
(Registration, PHQ/GAD, Cognitive games, Speech Assessment, Results) can be
tested and previewed locally without requiring a live remote Supabase connection.
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from fastapi.testclient import TestClient

from app.main import app
from app.assessments.router import get_assessment_repository
from app.results.router import get_results_service
from app.speech.router import get_speech_service
from app.results.service import ResultsService


class DemoAssessmentRepo:
    def __init__(self):
        self.sessions = {
            "11111111-1111-4111-8111-111111111111": {
                "patient_id": "99999999-9999-4999-8999-999999999999",
                "assessment_id": "11111111-1111-4111-8111-111111111111",
                "full_name": "Eleanor Vance",
                "age": 72,
                "sex": "Female",
                "education_years": 16,
                "current_stage": "SPEECH",
                "completed_stages": ["PHQ_GAD", "MMSE", "MEMORY", "NBACK", "BOSTON_NAMING", "TRAIL_MAKING"],
            }
        }

    def get_assessment_session(self, assessment_id: str):
        if assessment_id in self.sessions:
            return self.sessions[assessment_id]
        return {
            "patient_id": "99999999-9999-4999-8999-999999999999",
            "assessment_id": assessment_id,
            "full_name": "Eleanor Vance",
            "age": 72,
            "sex": "Female",
            "education_years": 16,
            "current_stage": "SPEECH",
            "completed_stages": ["PHQ_GAD", "MMSE", "MEMORY", "NBACK", "BOSTON_NAMING", "TRAIL_MAKING"],
        }

    def assessment_exists(self, assessment_id: str):
        return True

    def create_assessment_session(self, **kwargs):
        aid = "11111111-1111-4111-8111-111111111111"
        return self.get_assessment_session(aid)


class DemoResultsService:
    def get_results(self, assessment_id: str):
        return {
            "assessment_id": assessment_id,
            "assessment_short_id": f"{assessment_id[:4]}...{assessment_id[-4:]}",
            "participant_name": "Eleanor Vance",
            "status": "completed",
            "current_stage": "RESULTS",
            "next_stage": "RESULTS",
            "completion_message": "All currently available assessment components have been completed.",
            "fusion": {
                "available": False,
                "status": "pending",
                "title": "Overall Multimodal Result",
                "description": "Multimodal fusion engine integration pending. Component scores are shown below.",
            },
            "model1": {
                "available": True,
                "cognitive_performance_score": 83.45,
                "model_name": "NeuroDetect Model 1 - Cognitive Performance Regressor",
                "model_version": "1.0.0",
                "feature_count": 47,
                "model_type": "Cognitive performance regression",
                "score_scale_max": 100.0,
            },
            "mental_health": {
                "phq9": {"available": True, "score": 4, "score_max": 27, "severity": "mild"},
                "gad7": {"available": True, "score": 3, "score_max": 21, "severity": "minimal"},
            },
            "model3": {
                "available": True,
                "status": "awaiting_asr_verification",
                "title": "Speech Assessment",
                "description": "Multimodal acoustic and linguistic speech indicators based on Cookie Theft picture description.",
                "predicted_class": "HC",
                "probability_hc": 0.884,
                "hc_probability": 0.884,
                "probability_mci": 0.082,
                "mci_probability": 0.082,
                "probability_dementia": 0.034,
                "dementia_probability": 0.034,
                "probabilities": {
                    "HC": 0.884,
                    "MCI": 0.082,
                    "Dementia": 0.034,
                },
                "branch_probabilities": {
                    "audio_embedding": {"HC": 0.85, "MCI": 0.10, "Dementia": 0.05},
                    "acoustic": {"HC": 0.78, "MCI": 0.14, "Dementia": 0.08},
                    "transcript": {"HC": 0.91, "MCI": 0.06, "Dementia": 0.03},
                },
                "components_used": ["audio_embedding", "acoustic", "transcript"],
                "model_name": "NeuroDetect Model 3 - PROCESS-2 CTD Classifier",
                "model_version": "model3-process2-ctd-20261116-full",
                "disclaimer": "NeuroDetect Model 3 is an experimental speech-based research screening model. Its predictions are not a medical diagnosis and must not be used as a substitute for professional clinical assessment.",
                "transcription_engine": "pluggable_local_asr",
            },
            "completed_components": [
                {"key": "phq9", "label": "PHQ-9", "completed": True},
                {"key": "gad7", "label": "GAD-7", "completed": True},
                {"key": "mmse", "label": "MMSE", "completed": True},
                {"key": "memory", "label": "Memory Recall", "completed": True},
                {"key": "nback", "label": "N-Back", "completed": True},
                {"key": "boston_naming", "label": "Boston Naming", "completed": True},
                {"key": "trail_making", "label": "Trail Making", "completed": True},
                {"key": "speech", "label": "Speech Assessment", "completed": True},
                {"key": "model1", "label": "Model 1", "completed": True},
            ],
            "missing_components": [],
        }


class DemoSpeechService:
    async def process_speech_upload(self, *, assessment_id: str, audio_bytes: bytes, **kwargs):
        return {
            "assessment_id": assessment_id,
            "status": "completed",
            "transcription_status": "completed",
            "transcription_engine": "pluggable_local_asr",
            "inference_status": "awaiting_asr_verification",
            "predicted_class": "HC",
            "probability_hc": 0.884,
            "hc_probability": 0.884,
            "probability_mci": 0.082,
            "mci_probability": 0.082,
            "probability_dementia": 0.034,
            "dementia_probability": 0.034,
            "probabilities": {
                "HC": 0.884,
                "MCI": 0.082,
                "Dementia": 0.034,
            },
            "model_version": "model3-process2-ctd-20261116-full",
            "disclaimer": "NeuroDetect Model 3 is an experimental speech-based research screening model.",
        }

    def get_speech_result(self, assessment_id: str):
        return {
            "assessment_id": assessment_id,
            "speech_id": "88888888-8888-4888-8888-888888888888",
            "status": "completed",
            "transcript": "The boy is taking cookies from the cookie jar while the stool is tipping over. The mother is washing dishes, but the sink is overflowing onto the floor.",
            "transcription_status": "completed",
            "transcription_engine": "pluggable_local_asr",
            "inference_status": "awaiting_asr_verification",
            "predicted_class": "HC",
            "probability_hc": 0.884,
            "hc_probability": 0.884,
            "probability_mci": 0.082,
            "mci_probability": 0.082,
            "probability_dementia": 0.034,
            "dementia_probability": 0.034,
            "probabilities": {
                "HC": 0.884,
                "MCI": 0.082,
                "Dementia": 0.034,
            },
            "branch_probabilities": {
                "audio_embedding": {"HC": 0.85, "MCI": 0.10, "Dementia": 0.05},
                "acoustic": {"HC": 0.78, "MCI": 0.14, "Dementia": 0.08},
                "transcript": {"HC": 0.91, "MCI": 0.06, "Dementia": 0.03},
            },
            "components_used": ["audio_embedding", "acoustic", "transcript"],
            "model_name": "NeuroDetect Model 3 - PROCESS-2 CTD Classifier",
            "model_version": "model3-process2-ctd-20261116-full",
            "disclaimer": "NeuroDetect Model 3 is an experimental speech-based research screening model.",
        }


# Apply overrides for demo mode
app.dependency_overrides[get_assessment_repository] = lambda: DemoAssessmentRepo()
app.dependency_overrides[get_results_service] = lambda: DemoResultsService()
app.dependency_overrides[get_speech_service] = lambda: DemoSpeechService()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
