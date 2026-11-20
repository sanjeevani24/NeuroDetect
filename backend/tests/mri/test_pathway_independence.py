import io
import uuid
from typing import Any
import pytest
from PIL import Image

from app.assessments.schemas import PatientCreateRequest
from app.mri.config import DISCLAIMER, MODEL_NAME, MODEL_VERSION
from app.mri.service import MriService
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.mri_repository import MriRepository


class InMemorySupabaseTable:
    def __init__(self, name: str, rows: list[dict] | None = None):
        self.name = name
        self.rows: list[dict] = rows or []

    def insert(self, data: dict):
        self._pending_action = ("insert", data)
        return self

    def select(self, cols: str = "*"):
        self._select_cols = [c.strip() for c in cols.split(",")]
        self._filters = []
        self._pending_action = ("select", None)
        return self

    def eq(self, col: str, val: Any):
        self._filters.append((col, val))
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def upsert(self, data: dict, on_conflict: str = ""):
        self._pending_action = ("upsert", (data, on_conflict))
        return self

    def execute(self):
        action, payload = self._pending_action
        if action == "insert":
            new_row = dict(payload)
            if "patient_id" not in new_row and self.name == "patients":
                new_row["patient_id"] = str(uuid.uuid4())
            if "assessment_id" not in new_row and self.name == "assessments":
                new_row["assessment_id"] = str(uuid.uuid4())
            self.rows.append(new_row)
            class Resp:
                data = [new_row]
            return Resp()
        elif action == "upsert":
            data, on_conflict = payload
            existing = None
            for idx, r in enumerate(self.rows):
                if on_conflict in r and r[on_conflict] == data.get(on_conflict):
                    self.rows[idx] = {**r, **data}
                    existing = self.rows[idx]
                    break
            if existing is None:
                new_row = dict(data)
                if "mri_id" not in new_row and self.name == "mri_assessments":
                    new_row["mri_id"] = str(uuid.uuid4())
                self.rows.append(new_row)
                existing = new_row
            class Resp:
                data = [existing]
            return Resp()
        elif action == "select":
            matched = []
            for r in self.rows:
                match = True
                for fcol, fval in self._filters:
                    if r.get(fcol) != fval:
                        match = False
                        break
                if match:
                    if self._select_cols == ["*"]:
                        matched.append(dict(r))
                    else:
                        matched.append({k: r[k] for k in self._select_cols if k in r})
            class Resp:
                data = matched[:getattr(self, "_limit", len(matched))]
            return Resp()
        raise ValueError(f"Unknown action {action}")


class InMemorySupabaseClient:
    def __init__(self):
        self.tables = {
            "patients": InMemorySupabaseTable("patients"),
            "assessments": InMemorySupabaseTable("assessments"),
            "mri_assessments": InMemorySupabaseTable("mri_assessments"),
            "phq9_results": InMemorySupabaseTable("phq9_results"),
            "gad7_results": InMemorySupabaseTable("gad7_results"),
            "mmse_results": InMemorySupabaseTable("mmse_results"),
            "memory_results": InMemorySupabaseTable("memory_results"),
            "nback_results": InMemorySupabaseTable("nback_results"),
            "boston_naming_results": InMemorySupabaseTable("boston_naming_results"),
            "trail_making_results": InMemorySupabaseTable("trail_making_results"),
            "speech_assessments": InMemorySupabaseTable("speech_assessments"),
            "model3_results": InMemorySupabaseTable("model3_results"),
        }

    def table(self, name: str):
        if name not in self.tables:
            self.tables[name] = InMemorySupabaseTable(name)
        return self.tables[name]


class FakeModel4Manager:
    def predict(self, image_input):
        return {
            "predicted_class": "Non-Demented",
            "predicted_class_index": 0,
            "probability_non_demented": 0.88,
            "probability_very_mild": 0.08,
            "probability_mild": 0.03,
            "probability_moderate": 0.01,
            "class_probabilities": {
                "Non-Demented": 0.88,
                "Very Mildly Demented": 0.08,
                "Mildly Demented": 0.03,
                "Moderately Demented": 0.01,
            },
            "binary_prediction": "No Dementia",
            "binary_probabilities": {
                "no_dementia": 0.88,
                "dementia": 0.12,
            },
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "disclaimer": DISCLAIMER,
        }


def make_png_bytes():
    img = Image.new("RGB", (100, 100), color=(80, 80, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.anyio
async def test_two_independent_pathways_shared_patient():
    client = InMemorySupabaseClient()
    assessment_repo = AssessmentRepository(client)
    mri_repo = MriRepository(client)
    mri_service = MriService(assessment_repo, mri_repo, model_manager=FakeModel4Manager())

    # 1. Create MRI_ONLY assessment
    mri_session = assessment_repo.create_assessment_session(
        full_name="Eleanor Vance",
        age=68,
        sex="Female",
        education_years=16,
        assessment_type="MRI_ONLY",
    )
    patient_id = mri_session["patient_id"]
    mri_aid = mri_session["assessment_id"]

    assert mri_session["assessment_type"] == "MRI_ONLY"
    assert mri_session["current_stage"] == "MRI"
    assert mri_session["completed_stages"] == []

    # 2. Create COGNITIVE assessment for the SAME patient
    cog_session = assessment_repo.create_assessment_session(
        full_name="Eleanor Vance",
        age=68,
        sex="Female",
        education_years=16,
        assessment_type="COGNITIVE",
    )
    cog_aid = cog_session["assessment_id"]

    # Verify independent assessment IDs and shared patient details
    assert mri_aid != cog_aid
    assert cog_session["assessment_type"] == "COGNITIVE"
    assert cog_session["current_stage"] == "PHQ_GAD"
    assert cog_session["completed_stages"] == []

    # 3. Complete MRI upload on the MRI_ONLY session
    mri_result = await mri_service.process_mri_upload(
        assessment_id=mri_aid,
        image_bytes=make_png_bytes(),
        filename="axial_slice_01.png",
        content_type="image/png",
    )

    assert mri_result["assessment_id"] == mri_aid
    assert mri_result["predicted_class"] == "Non-Demented"
    assert mri_result["binary_prediction"] == "No Dementia"

    # 4. Confirm MRI session stage is now RESULTS
    updated_mri_session = assessment_repo.get_assessment_session(mri_aid)
    assert updated_mri_session["current_stage"] == "RESULTS"
    assert updated_mri_session["completed_stages"] == ["MRI"]

    # 5. Confirm COGNITIVE session remains completely unaffected
    unaffected_cog_session = assessment_repo.get_assessment_session(cog_aid)
    assert unaffected_cog_session["assessment_type"] == "COGNITIVE"
    assert unaffected_cog_session["current_stage"] == "PHQ_GAD"
    assert unaffected_cog_session["completed_stages"] == []

    # 6. Verify MRI results exist only for mri_aid, not cog_aid
    assert mri_service.get_mri_result(mri_aid) is not None
    assert mri_service.get_mri_result(cog_aid) is None
