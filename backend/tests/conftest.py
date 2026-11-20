import os

# Limit OpenMP threads to 1 on macOS to avoid native thread stack exhaustion
# when multiple C/C++ runtimes (PyTorch, ctranslate2, librosa/scipy) run in the same process.
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ.setdefault("KERAS_HOME", "/tmp/.keras")
