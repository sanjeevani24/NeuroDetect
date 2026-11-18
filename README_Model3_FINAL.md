# NeuroDetect Model 3 – PROCESS-2 (CTD) – FINAL full-training notebook

**Deliverable:** `NeuroDetect_Model3_PROCESS2_Training_FINAL.ipynb`
**Output of the notebook:** `neurodetect_model3_process2_package.zip` (auto-downloaded in Colab)

> NeuroDetect Model 3 is an experimental speech-based research screening model. Its predictions are not a medical diagnosis and must not be used as a substitute for professional clinical assessment.

## Status – read this first

* The notebook has **not** been trained on PROCESS-2 and **no metrics exist yet**. Nothing in it is pre-filled.
* What *was* checked: every code cell was executed end-to-end, in order, against a **synthetic mock** of the PROCESS-2 repository (fake participants, tones, dummy transcripts, a mocked Hugging Face Hub, and **stubbed Wav2Vec2/DistilBERT encoders**). This exercised the full-mode selection, both exclusion paths, official-split and generated-split paths, nested CV, fusion, selection freeze, test evaluation, export, the inference parity check, ZIP verification, cache resume/corruption recovery, debug mode, and a set of negative tests (leakage, token/ID/audio in package, wrong mode, export before evaluation, test before selection).
* What was **not** checked (impossible here): real dataset access/authentication, real encoder downloads and numerics, GPU/MPS behaviour, real runtime/memory, and the Colab `files.download()` call.

## How to run (friend's Colab)

1. Upload the `.ipynb` to Colab. Choose a **GPU** runtime (CPU works but is much slower).
2. Add a Colab Secret named `HF_TOKEN` (notebook access ON) containing a Hugging Face **read** token from an account that has **accepted the PROCESS-2 Data Use Agreement**. The Hugging Face account does not have to match the Google account. Without a secret, the notebook prompts interactively. The token is never printed, stored in a variable after login, or exported.
3. Run all cells. `MODE = "full"` is already set. No manual switching.
4. The final cell verifies the package and downloads `neurodetect_model3_process2_package.zip`.

If the runtime disconnects: re-run from the top. Feature extraction (§13, §16) resumes from its cache; nested CV (§19–22) re-runs. If you hit out-of-memory, lower `BATCH_SIZE`; the code also halves it automatically. It never shrinks the dataset.

## Modes

| | `full` (default) | `debug` |
|---|---|---|
| Participants | **all eligible** CTD participants (asserted) | `DEBUG_PER_CLASS` per class per partition |
| Cache | `work/cache/full/<fingerprint>/` | `work/cache/debug/<fingerprint>/` |
| Model version | `model3-process2-ctd-<date>-full` | `…-DEBUG` |
| Package | `neurodetect_model3_process2_package` | `…_package_DEBUG` (never downloaded) |
| Printed results | normal | tagged `[DEBUG - NOT MEANINGFUL]` |

## Validation design

* **Participant-level only.** One CTD recording per participant (asserted), so no recording can straddle partitions. A PASS/FAIL leakage report (disjoint IDs, one partition per participant, one row per participant, all 3 classes in train, non-empty test) runs after the split and again on the final analysed cohort; any FAIL stops the run. The literal `isdisjoint` assertion is included.
* **Split.** The official partition from `meta-info.csv` is used if a split column exists. Otherwise a participant-level stratified grouped 80/20 hold-out is generated and is labelled **GENERATED (not official)** in the console, the test headings, `model_metadata.json` (`split_is_official: false`) and the metrics file.
* **Nested, fold-contained model selection** (all inside `StratifiedGroupKFold` on the training partition):
  * Outer folds are fixed once and shared by all four experiments.
  * In each outer fold, using outer-training rows only: each branch runs inner grouped-CV grid search (LR/SVM/RF, macro-F1), is refit, and produces inner out-of-fold probabilities. The fusion step then selects its variant (audio+transcript vs audio+acoustic+transcript) and `C` on those probabilities and is fitted on them. The outer-validation rows are only scored.
  * Stacked outer-validation predictions are the **nested CV estimate** for all four experiments, and the only thing the final model is selected on.
  * The deployed models repeat the same procedure on the whole training partition.
* **Selection is frozen before the test set is touched.** Test predictions are first computed after selection; the test cell asserts the freeze. Fusion is chosen only if it has the best CV macro-F1 (ties go to the simpler model). A note is printed if the winning margin is smaller than the fold-to-fold std.
* **Fusion inputs** are asserted to be finite, correctly shaped out-of-fold probabilities.
* Imputer/scaler live inside the sklearn pipelines, so they are fitted on training folds only (asserted via `n_samples_seen_`).
* **Missing data.** Participants with no CTD wav, no/empty transcript, or unusable audio are **excluded and counted**, not median-imputed (`REQUIRE_COMPLETE_MODALITIES=True`). The exported model needs both inputs anyway. Individual missing features are still imputed inside folds.

## Verification report (printed twice: after the split, and for the final cohort)

Participants in metadata; with CTD wav; with CTD transcript; eligible; HC/MCI/Dementia; excluded + reasons; train/test counts; class distribution per partition; split strategy. All computed at run time. Counts only; no IDs are printed. Warnings are printed when a test class has fewer than `MIN_TEST_PER_CLASS_WARN` (10) participants.

## Cache safety

Per-participant cache under a folder named by a fingerprint of: mode, dataset **commit hash** (all files are fetched at that commit), both encoder revisions, and the SHA-256 of `predict_model3.py` (the feature code). `manifest.json` is checked on load, saves are atomic, corrupt caches are moved aside, and transient errors (download, OOM) are never cached as failures. Batch size is deliberately *not* in the key.

## Package contents (unchanged layout)

`models/` (4 joblib classifiers) · `preprocessing/` (feature configs, label map, `model_config.json`) · `evaluation/` (metrics, reports, confusion matrices, comparison CSV) · `inference/` (`predict_model3.py`, `requirements.txt`) · `README.md` · `model_metadata.json`.

`model_metadata.json` includes: `mode`, eligible / analysed / train / test counts, exclusion counts by reason, train/test class distributions, actual split strategy and whether it is official, selected model, validation scheme, model version, encoder revisions, dataset commit, dependency versions, device, and all metrics (CV, test, resubstitution).

Not exported: recordings, transcripts, participant IDs, dataset files, tokens, personal data, pretrained weights. Downloads required at inference time: `facebook/wav2vec2-base` and `distilbert-base-uncased` at the pinned revisions. Check their model cards for licences. SVM/RF files hold derived feature vectors, so keep the package research-restricted under the DUA.

**Before the ZIP is built/downloaded** the notebook verifies: training, evaluation and a parity check all completed; all 16 expected files exist; metadata says `full`; no DEBUG marker; no audio/weights/data files; no participant-ID or token-like strings in any file; prints size and listing. Parity check: 3 *training* participants go through the exported inference code and must reproduce the in-memory pipeline's probabilities (identical preprocessing and feature order).

## Change log

**Changed**
1. Config: `MODE="full"`, `BATCH_SIZE=4`; `MODE` validated; separate cache tree; debug kept; new knobs `INNER_SPLITS`, `REQUIRE_COMPLETE_MODALITIES`, `MIN_TEST_PER_CLASS_WARN`, `RESET_CACHE`.
2. Dataset: pinned to one dataset commit; hard errors (with DUA hint) instead of silent fallbacks; transcript-download failures no longer become "empty transcripts"; split column consistency check; full verification report; exclusion accounting; full-mode "all eligible participants used" assertion.
3. Leakage: PASS/FAIL report + assertions, re-run on the final cohort.
4. Validation: replaced "tune on training CV, then use those OOF predictions" with the nested scheme above; fusion variant and `C` now selected inside folds; test predictions no longer computed before selection; selection frozen and guarded.
5. Caching/execution: fingerprinted per-participant cache (previously keyed by row index, which would have gone stale if the cohort changed), atomic saves, corruption recovery, no caching of transient failures, OOM backoff, cost notices, MPS fallback env var, CPU warning.
6. Export/ZIP: new metadata fields, `-full` model version, pinned-revision README with required downloads, `requirements.txt` strips local version tags such as `+cu121`, debug package isolated, extended ZIP verification, parity check gate, `TRAINING_OK`/`EVAL_OK`/`PARITY_OK` gating.
7. Removed "start with debug, then switch to full" instructions; rewrote limitations.

**Preserved unchanged:** `predict_model3.py` (features, encoders, inference), model grid/pipelines, metrics, plots, authentication flow, package structure, ZIP + Colab download.

## Still to check during the real full run

* Printed counts (§11c) match what you expect for PROCESS-2: especially the diagnosis-column / label mapping and which split strategy was used. If it says GENERATED, check the dataset card for an official split.
* How many participants are excluded and why (§18 report).
* Extraction runs on GPU, not CPU; pYIN (CPU-bound) is likely the slowest part. Watch the tqdm ETA.
* Test-class sizes and the printed warnings; interpret per-class test metrics cautiously if they appear.
* Whether the selected model's CV margin is within fold-to-fold noise (the notebook prints a note).
* Parity check passes with real encoders (tolerance 5e-3 on probabilities; small GPU nondeterminism is expected).
* Total nested-CV time (about 1,200 model fits across three branches, plus small fusion fits).
* Delete the Hugging Face cache and `work/` folder afterwards, per the DUA.

## Remaining limitations

Single (non-repeated) grouped CV; small Dementia/MCI counts likely; fusion's training inputs inside each fold come from branch models tuned on the same rows (standard stacking, no outer-validation leakage); no confidence intervals on test metrics; CTD-only; distribution shift to other recording setups is untested.
