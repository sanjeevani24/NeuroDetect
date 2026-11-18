import math
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from app.speech.config import MODEL3_PACKAGE_DIR
from app.speech.inference import Model3InferenceError, Model3Manager


class FakeRawModel:
    def __init__(self, raw_return: dict):
        self.raw_return = raw_return
        self.predict_calls = []

    def predict(self, audio_path: str, transcript: str):
        self.predict_calls.append((audio_path, transcript))
        return self.raw_return


def test_model3_manager_valid_prediction(monkeypatch, tmp_path):
    # Setup mock package files
    inference_dir = tmp_path / "inference"
    inference_dir.mkdir(parents=True)
    (inference_dir / "predict_model3.py").write_text("# mock")

    mgr = Model3Manager(package_dir=tmp_path)

    valid_return = {
        "status": "ok",
        "predicted_class": "HC",
        "probabilities": {"HC": 0.85, "MCI": 0.10, "Dementia": 0.05},
        "branch_probabilities": {"audio_embedding": {"HC": 0.85, "MCI": 0.10, "Dementia": 0.05}},
        "components_used": ["audio_embedding", "acoustic", "transcript"],
        "model_version": "model3-process2-ctd-20261116-full",
        "disclaimer": "Test disclaimer",
    }
    fake_model = FakeRawModel(valid_return)
    monkeypatch.setattr(mgr, "load_model", lambda: fake_model)

    res = mgr.predict(audio_path="sample.wav", transcript="test transcript")

    assert res["status"] == "ok"
    assert res["predicted_class"] == "HC"
    assert res["hc_probability"] == 0.85
    assert res["mci_probability"] == 0.10
    assert res["dementia_probability"] == 0.05
    assert res["model_version"] == "model3-process2-ctd-20261116-full"


def test_model3_manager_rejects_missing_class(monkeypatch, tmp_path):
    inference_dir = tmp_path / "inference"
    inference_dir.mkdir(parents=True)
    (inference_dir / "predict_model3.py").write_text("# mock")

    mgr = Model3Manager(package_dir=tmp_path)
    # Missing 'Dementia'
    bad_return = {
        "status": "ok",
        "predicted_class": "HC",
        "probabilities": {"HC": 0.85, "MCI": 0.15},
        "model_version": "model3-test",
    }
    monkeypatch.setattr(mgr, "load_model", lambda: FakeRawModel(bad_return))

    with pytest.raises(Model3InferenceError, match="Missing probability for class 'Dementia'"):
        mgr.predict(audio_path="sample.wav", transcript="test")


def test_model3_manager_rejects_negative_probability(monkeypatch, tmp_path):
    inference_dir = tmp_path / "inference"
    inference_dir.mkdir(parents=True)
    (inference_dir / "predict_model3.py").write_text("# mock")

    mgr = Model3Manager(package_dir=tmp_path)
    bad_return = {
        "status": "ok",
        "predicted_class": "HC",
        "probabilities": {"HC": 1.1, "MCI": -0.1, "Dementia": 0.0},
        "model_version": "model3-test",
    }
    monkeypatch.setattr(mgr, "load_model", lambda: FakeRawModel(bad_return))

    with pytest.raises(Model3InferenceError, match="negative"):
        mgr.predict(audio_path="sample.wav", transcript="test")


def test_model3_manager_rejects_invalid_predicted_class(monkeypatch, tmp_path):
    inference_dir = tmp_path / "inference"
    inference_dir.mkdir(parents=True)
    (inference_dir / "predict_model3.py").write_text("# mock")

    mgr = Model3Manager(package_dir=tmp_path)
    bad_return = {
        "status": "ok",
        "predicted_class": "UNKNOWN_CLASS",
        "probabilities": {"HC": 0.8, "MCI": 0.1, "Dementia": 0.1},
        "model_version": "model3-test",
    }
    monkeypatch.setattr(mgr, "load_model", lambda: FakeRawModel(bad_return))

    with pytest.raises(Model3InferenceError, match="Invalid predicted class"):
        mgr.predict(audio_path="sample.wav", transcript="test")


def test_model3_manager_rejects_missing_version(monkeypatch, tmp_path):
    inference_dir = tmp_path / "inference"
    inference_dir.mkdir(parents=True)
    (inference_dir / "predict_model3.py").write_text("# mock")

    mgr = Model3Manager(package_dir=tmp_path)
    bad_return = {
        "status": "ok",
        "predicted_class": "HC",
        "probabilities": {"HC": 0.8, "MCI": 0.1, "Dementia": 0.1},
        "model_version": "",
    }
    monkeypatch.setattr(mgr, "load_model", lambda: FakeRawModel(bad_return))

    with pytest.raises(Model3InferenceError, match="Model version missing"):
        mgr.predict(audio_path="sample.wav", transcript="test")


def test_real_model3_package_inference(tmp_path):
    """
    Integration test using the genuine trained Model 3 package,
    actual acoustic/text encoders, and real inference execution.
    """
    assert MODEL3_PACKAGE_DIR.exists(), f"Model 3 package directory not found at {MODEL3_PACKAGE_DIR}"
    mgr = Model3Manager(package_dir=MODEL3_PACKAGE_DIR)

    # Generate a genuine valid 16kHz audio sample
    sr = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    synthetic_speech = 0.4 * np.sin(2 * np.pi * 200 * t) + 0.2 * np.sin(2 * np.pi * 400 * t)
    wav_path = tmp_path / "actual_stimulus.wav"
    sf.write(str(wav_path), synthetic_speech.astype(np.float32), sr)

    transcript = "The boy is taking cookies from the jar and the water is overflowing from the sink."

    result = mgr.predict(audio_path=str(wav_path), transcript=transcript)

    assert result["status"] == "ok"
    assert result["predicted_class"] in ("HC", "MCI", "Dementia")
    assert result["model_version"] == "model3-process2-ctd-20261116-full"

    p_hc = result["hc_probability"]
    p_mci = result["mci_probability"]
    p_dem = result["dementia_probability"]

    assert 0.0 <= p_hc <= 1.0
    assert 0.0 <= p_mci <= 1.0
    assert 0.0 <= p_dem <= 1.0
    assert math.isclose(p_hc + p_mci + p_dem, 1.0, abs_tol=1e-2)

    assert "audio_embedding" in result["branch_probabilities"]
    assert "acoustic" in result["branch_probabilities"]
    assert "transcript" in result["branch_probabilities"]
    assert "components_used" in result
    assert "disclaimer" in result

