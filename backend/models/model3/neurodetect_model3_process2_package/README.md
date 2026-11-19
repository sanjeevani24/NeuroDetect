# NeuroDetect Model 3 (PROCESS-2, CTD) - model3-process2-ctd-20261116-full
NeuroDetect Model 3 is an experimental speech-based research screening model. Its predictions are not a medical diagnosis and must not be used as a substitute for professional clinical assessment.

Research/education use only, subject to the PROCESS-2 Data Use Agreement. Contains no recordings, transcripts, participant IDs, dataset files or tokens
(SVM/RF files hold derived feature vectors only). 

Training mode: **full** | participants analysed: 400 (train 320, test 80) | split: OFFICIAL partition from meta-info.csv column 'Split'
Selected model: **fusion** (fusion inputs: ['audio_embedding', 'acoustic', 'transcript']). Classes: HC, MCI, Dementia. Input: CTD audio + transcript.
Metrics in `evaluation/`: `cv` = nested CV on the training partition (used for selection), `test` = evaluated once after selection was frozen, `train` = resubstitution (optimistic).

Usage: `pip install -r inference/requirements.txt`, then
```python
import sys; sys.path.insert(0, "inference")
from predict_model3 import NeuroDetectModel3
m = NeuroDetectModel3("path/to/package"); print(m.predict(audio_path="sample.wav", transcript="..."))
```
NOT fully offline - required Hugging Face downloads at the pinned revisions in `preprocessing/model_config.json`:
`facebook/wav2vec2-base` @ `0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8` and `distilbert-base-uncased` @ `12040accade4e8a0f71eabdb258fecc2e7e948be` (pretrained weights are not bundled; check their model cards for licences).
