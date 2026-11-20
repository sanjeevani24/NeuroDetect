import io
import numpy as np
import pytest
from PIL import Image

from app.mri.config import (
    CLASS_NAMES,
    BINARY_THRESHOLD,
    IMG_SIZE,
    DISCLAIMER,
    NON_DEMENTED_LABEL,
    PROBABILITY_KEYS,
)
from app.mri.inference import (
    MriInferenceError,
    MriModelManager,
    get_mri_manager,
)


def test_preprocess_image_rgb():
    img = Image.new("RGB", (300, 400), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    batch = MriModelManager.preprocess_image(buf, target_size=IMG_SIZE)

    assert batch.shape == (1, IMG_SIZE, IMG_SIZE, 3)
    assert batch.dtype == np.float32
    assert float(np.min(batch)) >= 0.0
    assert float(np.max(batch)) <= 255.0


def test_preprocess_image_grayscale():
    img = Image.new("L", (200, 200), color=128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    batch = MriModelManager.preprocess_image(buf.getvalue(), target_size=IMG_SIZE)

    assert batch.shape == (1, IMG_SIZE, IMG_SIZE, 3)
    assert batch.dtype == np.float32
    # In RGB converted from L, all 3 channels are identical
    assert np.allclose(batch[0, :, :, 0], batch[0, :, :, 1])
    assert np.allclose(batch[0, :, :, 1], batch[0, :, :, 2])


def test_mri_manager_singleton():
    m1 = get_mri_manager()
    m2 = get_mri_manager()
    assert m1 is m2


def test_mri_inference_with_mocked_model(monkeypatch):
    class FakeKerasModel:
        input_shape = (None, 224, 224, 3)

        def predict(self, tensor, verbose=0):
            # Non-Demented (0): 0.10, Very Mild (1): 0.70, Mild (2): 0.15, Moderate (3): 0.05
            return np.array([[0.10, 0.70, 0.15, 0.05]], dtype=np.float32)

    manager = MriModelManager()
    manager._model = FakeKerasModel()
    manager._class_indices = {
        "Non-Demented": 0,
        "Very Mildly Demented": 1,
        "Mildly Demented": 2,
        "Moderately Demented": 3,
    }

    img = Image.new("RGB", (256, 256), color=(50, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    result = manager.predict(buf.getvalue())

    assert result["predicted_class"] == "Very Mildly Demented"
    assert result["predicted_class_index"] == 1
    assert result["class_probabilities"]["Very Mildly Demented"] == pytest.approx(0.70)
    assert result["binary_prediction"] == "Dementia"
    assert result["binary_probabilities"]["dementia"] == pytest.approx(0.90)
    assert result["binary_probabilities"]["no_dementia"] == pytest.approx(0.10)
    assert result["model_name"] == "NeuroDetect-MRI-EfficientNetB0"
    assert result["model_version"] == "1.0.0"
    assert result["disclaimer"] == DISCLAIMER
