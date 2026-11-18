import pytest
from app.repositories.speech_repository import SpeechRepository, SpeechSchemaNotReadyError


class FakeTable:
    def __init__(self, name: str, db: dict):
        self.name = name
        self.db = db
        self._filter_col = None
        self._filter_val = None
        self._op = "select"
        self._payload = None

    def select(self, cols: str = "*"):
        self._op = "select"
        return self

    def eq(self, col: str, val: str):
        self._filter_col = col
        self._filter_val = val
        return self

    def limit(self, count: int):
        return self

    def insert(self, payload: dict):
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload: dict):
        self._op = "update"
        self._payload = payload
        return self

    def execute(self):
        if self.db.get("__fail_table__") == self.name:
            raise RuntimeError(f"relation public.{self.name} does not exist")

        table_rows = self.db.setdefault(self.name, [])

        if self._op == "select":
            matched = [
                row for row in table_rows
                if self._filter_col is None or row.get(self._filter_col) == self._filter_val
            ]
            class Resp:
                data = matched
            return Resp()

        if self._op == "insert":
            table_rows.append(self._payload)
            class Resp:
                data = [self._payload]
            return Resp()

        if self._op == "update":
            for row in table_rows:
                if self._filter_col and row.get(self._filter_col) == self._filter_val:
                    row.update(self._payload)
            class Resp:
                data = [self._payload]
            return Resp()


class FakeSupabaseClient:
    def __init__(self, fail_table: str | None = None):
        self.db = {"__fail_table__": fail_table}

    def table(self, name: str):
        return FakeTable(name, self.db)


def test_speech_repository_upserts_both_tables():
    client = FakeSupabaseClient()
    repo = SpeechRepository(client)
    assessment_id = "11111111-2222-3333-4444-555555555555"

    result = repo.upsert_result(
        assessment_id=assessment_id,
        transcript="The children are taking cookies.",
        transcription_status="completed",
        transcription_engine="pluggable_local_asr",
        audio_duration_seconds=12.5,
        audio_format="webm",
        inference_status="awaiting_asr_verification",
        predicted_class="HC",
        probability_hc=0.85,
        probability_mci=0.10,
        probability_dementia=0.05,
        branch_probabilities={"acoustic": {"HC": 0.8}},
        components_used=["audio_embedding", "acoustic", "transcript"],
        model_version="model3-process2-ctd-20261116-full",
        disclaimer="Research screening only",
    )

    assert result["assessment_id"] == assessment_id
    assert result["predicted_class"] == "HC"
    assert result["probability_hc"] == 0.85
    assert result["hc_probability"] == 0.85
    assert result["audio_duration_seconds"] == 12.5

    # Check speech_assessments table
    speech_rows = client.db["speech_assessments"]
    assert len(speech_rows) == 1
    assert speech_rows[0]["assessment_id"] == assessment_id
    assert speech_rows[0]["transcription_status"] == "completed"
    assert "speech_id" in speech_rows[0]

    # Check model3_results table
    model3_rows = client.db["model3_results"]
    assert len(model3_rows) == 1
    assert model3_rows[0]["assessment_id"] == assessment_id
    assert model3_rows[0]["speech_id"] == speech_rows[0]["speech_id"]
    assert model3_rows[0]["probability_hc"] == 0.85


def test_speech_repository_schema_not_ready():
    client = FakeSupabaseClient(fail_table="speech_assessments")
    repo = SpeechRepository(client)

    with pytest.raises(SpeechSchemaNotReadyError, match="missing in Supabase"):
        repo.upsert_result(
            assessment_id="11111111-2222-3333-4444-555555555555",
            transcript="test",
        )
