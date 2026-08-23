from app.results.service import ResultsService


class FakeResultsRepository:
    def __init__(self, *, session, phq9=None, gad7=None, model1=None):
        self._session = session
        self._phq9 = phq9
        self._gad7 = gad7
        self._model1 = model1

    def get_assessment_session(self, assessment_id: str):
        return self._session

    def get_phq9_result(self, assessment_id: str):
        return self._phq9

    def get_gad7_result(self, assessment_id: str):
        return self._gad7

    def get_model1_result(self, assessment_id: str):
        return self._model1


def test_service_marks_completed_when_all_required_results_exist():
    service = ResultsService(
        FakeResultsRepository(
            session={
                "assessment_id": "66666666-6666-4666-8666-666666666666",
                "full_name": "Alex Doe",
                "current_stage": "RESULTS",
                "completed_stages": ["PHQ_GAD", "MMSE", "MEMORY", "NBACK", "BOSTON_NAMING", "TRAIL_MAKING"],
            },
            phq9={"total_score": 7, "severity": "mild"},
            gad7={"total_score": 5, "severity": "mild"},
            model1={"cognitive_performance_score": 81.25, "model_name": "NeuroDetect Model 1", "model_version": "1.0.0"},
        )
    )

    result = service.get_results("66666666-6666-4666-8666-666666666666")

    assert result["status"] == "completed"
    assert result["missing_components"] == []
    assert result["model1"]["available"] is True


def test_service_marks_awaiting_model1_when_only_model1_is_missing():
    service = ResultsService(
        FakeResultsRepository(
            session={
                "assessment_id": "77777777-7777-4777-8777-777777777777",
                "full_name": "Alex Doe",
                "current_stage": "RESULTS",
                "completed_stages": ["PHQ_GAD", "MMSE", "MEMORY", "NBACK", "BOSTON_NAMING", "TRAIL_MAKING"],
            },
            phq9={"total_score": 7, "severity": "mild"},
            gad7={"total_score": 5, "severity": "mild"},
            model1=None,
        )
    )

    result = service.get_results("77777777-7777-4777-8777-777777777777")

    assert result["status"] == "awaiting_model1"
    assert result["missing_components"] == ["Model 1"]


def test_service_marks_incomplete_when_core_assessment_steps_are_missing():
    service = ResultsService(
        FakeResultsRepository(
            session={
                "assessment_id": "88888888-8888-4888-8888-888888888888",
                "full_name": "Alex Doe",
                "current_stage": "NBACK",
                "completed_stages": ["PHQ_GAD", "MMSE", "MEMORY"],
            },
            phq9={"total_score": 7, "severity": "mild"},
            gad7={"total_score": 5, "severity": "mild"},
            model1=None,
        )
    )

    result = service.get_results("88888888-8888-4888-8888-888888888888")

    assert result["status"] == "incomplete"
    assert result["next_stage"] == "NBACK"
    assert "N-Back" in result["missing_components"]
