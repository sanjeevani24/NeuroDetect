from __future__ import annotations

import json
from dataclasses import dataclass

from app.assessments.schemas import AssessmentStage
from app.ml.model1.config import MODEL_METADATA_PATH
from app.ml.model1.exceptions import Model1SchemaNotReadyError
from app.repositories.results_repository import ResultsRepository


RESULT_COMPONENTS: list[tuple[str, str]] = [
    ("phq9", "PHQ-9"),
    ("gad7", "GAD-7"),
    ("mmse", "MMSE"),
    ("memory", "Memory Recall"),
    ("nback", "N-Back"),
    ("boston_naming", "Boston Naming"),
    ("trail_making", "Trail Making"),
    ("model1", "Model 1"),
]


class AssessmentResultsNotFoundError(Exception):
    """Raised when the assessment session cannot be found."""


@dataclass(frozen=True)
class Model1DisplayMetadata:
    model_name: str | None
    model_version: str | None
    feature_count: int | None
    model_type: str | None
    score_scale_max: float | None


class ResultsService:
    def __init__(self, repository: ResultsRepository):
        self._repository = repository
        self._model1_metadata = self._load_model1_metadata()

    def get_results(self, assessment_id: str) -> dict:
        session = self._repository.get_assessment_session(assessment_id)
        if session is None:
            raise AssessmentResultsNotFoundError

        phq9_result = self._repository.get_phq9_result(assessment_id)
        gad7_result = self._repository.get_gad7_result(assessment_id)
        try:
            model1_result = self._repository.get_model1_result(assessment_id)
        except Model1SchemaNotReadyError:
            raise

        completed_stages = set(session["completed_stages"])
        checklist = [
            {"key": "phq9", "label": "PHQ-9", "completed": phq9_result is not None},
            {"key": "gad7", "label": "GAD-7", "completed": gad7_result is not None},
            {"key": "mmse", "label": "MMSE", "completed": "MMSE" in completed_stages},
            {"key": "memory", "label": "Memory Recall", "completed": "MEMORY" in completed_stages},
            {"key": "nback", "label": "N-Back", "completed": "NBACK" in completed_stages},
            {"key": "boston_naming", "label": "Boston Naming", "completed": "BOSTON_NAMING" in completed_stages},
            {"key": "trail_making", "label": "Trail Making", "completed": "TRAIL_MAKING" in completed_stages},
            {"key": "model1", "label": "Model 1", "completed": model1_result is not None},
        ]

        missing_components = [item["label"] for item in checklist if not item["completed"]]
        non_model1_components_complete = all(item["completed"] for item in checklist if item["key"] != "model1")

        if model1_result is not None and not missing_components:
            status = "completed"
            current_stage: AssessmentStage = "RESULTS"
            next_stage: AssessmentStage = "RESULTS"
            completion_message = "All currently available assessment components have been completed."
        elif non_model1_components_complete:
            status = "awaiting_model1"
            current_stage = "RESULTS"
            next_stage = "RESULTS"
            completion_message = "The assessment is complete except for the stored Model 1 cognitive performance result."
        else:
            status = "incomplete"
            current_stage = session["current_stage"]
            next_stage = session["current_stage"]
            completion_message = "Some required assessment components are still incomplete."

        return {
            "assessment_id": session["assessment_id"],
            "assessment_short_id": self._short_assessment_id(session["assessment_id"]),
            "participant_name": session["full_name"],
            "status": status,
            "current_stage": current_stage,
            "next_stage": next_stage,
            "completion_message": completion_message,
            "model1": {
                "available": model1_result is not None,
                "cognitive_performance_score": self._to_float(model1_result, "cognitive_performance_score"),
                "model_name": (model1_result or {}).get("model_name") or self._model1_metadata.model_name,
                "model_version": (model1_result or {}).get("model_version") or self._model1_metadata.model_version,
                "feature_count": self._model1_metadata.feature_count,
                "model_type": self._model1_metadata.model_type,
                "score_scale_max": self._model1_metadata.score_scale_max,
            },
            "mental_health": {
                "phq9": {
                    "available": phq9_result is not None,
                    "score": self._to_int(phq9_result, "total_score"),
                    "score_max": 27,
                    "severity": self._to_str(phq9_result, "severity"),
                },
                "gad7": {
                    "available": gad7_result is not None,
                    "score": self._to_int(gad7_result, "total_score"),
                    "score_max": 21,
                    "severity": self._to_str(gad7_result, "severity"),
                },
            },
            "model3": {
                "available": False,
                "status": "pending",
                "title": "Speech Assessment",
                "description": "Speech-based cognitive analysis will be added in a future version of NeuroDetect.",
            },
            "fusion": {
                "available": False,
                "status": "pending",
                "title": "Overall Multimodal Result",
                "description": "Pending completion of speech analysis.",
            },
            "completed_components": checklist,
            "missing_components": missing_components,
        }

    @staticmethod
    def _short_assessment_id(assessment_id: str) -> str:
        return f"{assessment_id[:4]}...{assessment_id[-4:]}"

    @staticmethod
    def _to_float(row: dict | None, key: str) -> float | None:
        if not row or row.get(key) is None:
            return None
        return float(row[key])

    @staticmethod
    def _to_int(row: dict | None, key: str) -> int | None:
        if not row or row.get(key) is None:
            return None
        return int(row[key])

    @staticmethod
    def _to_str(row: dict | None, key: str) -> str | None:
        if not row or row.get(key) is None:
            return None
        return str(row[key])

    @staticmethod
    def _load_model1_metadata() -> Model1DisplayMetadata:
        try:
            payload = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return Model1DisplayMetadata(None, None, None, None, None)

        score_scale_max = payload.get("target_max")
        if score_scale_max is None and payload.get("target_range"):
            target_range = payload["target_range"]
            if isinstance(target_range, list) and len(target_range) == 2:
                score_scale_max = float(target_range[1])

        return Model1DisplayMetadata(
            model_name=payload.get("model_name"),
            model_version=payload.get("model_version"),
            feature_count=int(payload["feature_count"]) if payload.get("feature_count") is not None else None,
            model_type="Cognitive performance regression",
            score_scale_max=float(score_scale_max) if score_scale_max is not None else None,
        )
