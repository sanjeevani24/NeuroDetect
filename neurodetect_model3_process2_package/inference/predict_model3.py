"""NeuroDetect Model 3 (PROCESS-2 / CTD): shared feature extraction + inference.
Used by BOTH the training notebook and inference, so preprocessing is identical.
Experimental research screening model - NOT a medical diagnosis."""
import io, json, re
from pathlib import Path
import numpy as np

W2V_ID = "facebook/wav2vec2-base"
BERT_ID = "distilbert-base-uncased"
SR, CHUNK_S, MIN_TAIL_S = 16000, 30, 1.0
TOP_DB, PAUSE_MIN_S = 30, 0.25
FILLERS = {"um", "uh", "er", "erm", "hmm", "ah", "uhm", "mm"}
PRONOUNS = {"i", "me", "my", "mine", "you", "your", "he", "him", "his", "she", "her", "hers", "it", "its",
            "we", "us", "our", "they", "them", "their", "this", "that", "these", "those"}
SUBORD = {"and", "but", "because", "which", "that", "when", "while", "if", "so", "although", "who", "where"}
DISCLAIMER = ("NeuroDetect Model 3 is an experimental speech-based research screening model. Its predictions are "
              "not a medical diagnosis and must not be used as a substitute for professional clinical assessment.")
ACOUSTIC_NAMES = (["duration_s", "speaking_ratio", "silence_total_s", "pause_count", "pause_mean_s",
                   "pause_rate_per_min", "rms_mean", "rms_std", "rms_p95", "f0_mean", "f0_std", "f0_median",
                   "f0_range_p5_p95", "voiced_fraction", "words_per_min", "articulation_rate_wpm"]
                  + [f"mfcc{i}_{s}" for i in range(13) for s in ("mean", "std")])
LING_NAMES = ["word_count", "sentence_count", "avg_sentence_len", "type_token_ratio", "mattr_50", "unique_words",
              "repeated_word_count", "filler_count", "filler_ratio", "pronoun_ratio", "mean_word_len",
              "subordination_ratio"]


def get_device():
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


# ---------------- audio ----------------
def _read(src):
    import soundfile as sf, librosa
    try:
        y, sr = sf.read(src, dtype="float32", always_2d=True)
        return y.mean(1), sr
    except Exception:
        if hasattr(src, "seek"):
            src.seek(0)
        y, sr = librosa.load(src, sr=None, mono=True)
        return y, sr


def load_audio(obj):
    """Return (mono float32, sample_rate). Handles datasets AudioDecoder, dict(array|bytes|path), file path."""
    if obj is None:
        raise ValueError("audio is missing")
    if hasattr(obj, "get_all_samples"):  # torchcodec AudioDecoder
        s = obj.get_all_samples()
        y = s.data.cpu().numpy() if hasattr(s.data, "cpu") else np.asarray(s.data)
        sr = s.sample_rate
    elif isinstance(obj, dict):
        if obj.get("array") is not None:
            y, sr = np.asarray(obj["array"]), obj["sampling_rate"]
        elif obj.get("bytes"):
            y, sr = _read(io.BytesIO(obj["bytes"]))
        elif obj.get("path"):
            y, sr = _read(obj["path"])
        else:
            raise ValueError("audio dict has no array/bytes/path")
    elif isinstance(obj, (str, Path)):
        y, sr = _read(str(obj))
    else:
        raise TypeError(f"unsupported audio type {type(obj)}")
    y = np.asarray(y, dtype=np.float32)
    if y.ndim > 1:
        y = y.mean(axis=int(np.argmin(y.shape)))
    return y, int(sr)


def prep_audio(y, sr):
    """Resample to 16 kHz, remove NaNs, peak-normalise. Raises on silent/too-short audio."""
    import librosa
    y = np.nan_to_num(np.asarray(y, dtype=np.float32))
    if sr != SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    if len(y) < 0.5 * SR:
        raise ValueError("audio shorter than 0.5 s")
    m = float(np.max(np.abs(y)))
    if m < 1e-6:
        raise ValueError("audio is silent")
    return (y / m).astype(np.float32)


def acoustic_features(y, transcript=None):
    """Interpretable acoustic features. Anything not reliably computable stays NaN (imputed inside CV folds)."""
    import librosa
    f = {k: np.nan for k in ACOUSTIC_NAMES}
    dur = len(y) / SR
    f["duration_s"] = dur
    speech = np.nan
    try:
        iv = librosa.effects.split(y, top_db=TOP_DB, frame_length=1024, hop_length=256)
        speech = float(sum(e - s for s, e in iv)) / SR
        f["speaking_ratio"], f["silence_total_s"] = speech / dur, dur - speech
        gaps = (iv[1:, 0] - iv[:-1, 1]) / SR if len(iv) > 1 else np.array([])
        p = gaps[gaps >= PAUSE_MIN_S]
        f["pause_count"], f["pause_rate_per_min"] = float(len(p)), len(p) / (dur / 60)
        f["pause_mean_s"] = float(p.mean()) if len(p) else np.nan
    except Exception:
        pass
    try:
        r = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
        f["rms_mean"], f["rms_std"], f["rms_p95"] = float(r.mean()), float(r.std()), float(np.percentile(r, 95))
    except Exception:
        pass
    try:
        f0, vf, _ = librosa.pyin(y, fmin=65, fmax=400, sr=SR, frame_length=1024)
        v = f0[~np.isnan(f0)]
        f["voiced_fraction"] = float(np.mean(vf))
        if len(v) >= 10:
            f["f0_mean"], f["f0_std"], f["f0_median"] = float(v.mean()), float(v.std()), float(np.median(v))
            f["f0_range_p5_p95"] = float(np.percentile(v, 95) - np.percentile(v, 5))
    except Exception:
        pass
    try:
        m = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=13)
        for i in range(13):
            f[f"mfcc{i}_mean"], f[f"mfcc{i}_std"] = float(m[i].mean()), float(m[i].std())
    except Exception:
        pass
    n = len(_words(clean_text(transcript))) if transcript else 0
    if n:
        f["words_per_min"] = n / dur * 60
        if speech and speech > 0:
            f["articulation_rate_wpm"] = n / speech * 60
    return f


# ---------------- text ----------------
def clean_text(t):
    if t is None or (isinstance(t, float) and np.isnan(t)):
        return ""
    t = re.sub(r"\[[^\]]*\]|<[^>]*>|\{[^}]*\}", " ", str(t))
    return re.sub(r"\s+", " ", t).strip()


def _words(text):
    return re.findall(r"[a-z']+", text.lower())


def linguistic_features(text):
    f = {k: np.nan for k in LING_NAMES}
    text = clean_text(text)
    w = _words(text)
    n = len(w)
    if n == 0:
        return f
    ns = max(len([s for s in re.split(r"[.!?]+", text) if _words(s)]), 1)
    f.update(word_count=n, sentence_count=ns, avg_sentence_len=n / ns, type_token_ratio=len(set(w)) / n,
             unique_words=len(set(w)), repeated_word_count=sum(a == b for a, b in zip(w, w[1:])),
             filler_count=sum(x in FILLERS for x in w), filler_ratio=sum(x in FILLERS for x in w) / n,
             pronoun_ratio=sum(x in PRONOUNS for x in w) / n, mean_word_len=float(np.mean([len(x) for x in w])),
             subordination_ratio=sum(x in SUBORD for x in w) / n)  # proxy for syntactic complexity (no parser)
    if n >= 50:
        f["mattr_50"] = float(np.mean([len(set(w[i:i + 50])) / 50 for i in range(n - 49)]))
    return f


# ---------------- frozen encoders ----------------
class Encoders:
    def __init__(self, device=None, revisions=None, batch_size=8):
        self.device, self.rev, self.bs = device or get_device(), revisions or {}, batch_size
        self._w = self._t = None

    def audio_embedding(self, y):
        """Mean-pooled frozen Wav2Vec2 embedding (768-d); long audio is chunked (30 s) and length-weight averaged."""
        import torch
        if self._w is None:
            from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model
            r = self.rev.get(W2V_ID)
            self._wfe = Wav2Vec2FeatureExtractor.from_pretrained(W2V_ID, revision=r)
            self._w = Wav2Vec2Model.from_pretrained(W2V_ID, revision=r).to(self.device).eval()
            for p in self._w.parameters():
                p.requires_grad = False
        n = int(CHUNK_S * SR)
        ch = [y[i:i + n] for i in range(0, len(y), n)]
        if len(ch) > 1 and len(ch[-1]) < MIN_TAIL_S * SR:
            ch = ch[:-1]
        full, rest = [c for c in ch if len(c) == n], [c for c in ch if len(c) != n]
        groups = [full[i:i + self.bs] for i in range(0, len(full), self.bs)] + [[c] for c in rest]
        embs, ws = [], []
        with torch.inference_mode():
            for g in groups:
                x = self._wfe(g, sampling_rate=SR, return_tensors="pt", padding=False)["input_values"].to(self.device)
                h = self._w(x).last_hidden_state.mean(1).float().cpu().numpy()
                embs += list(h)
                ws += [len(c) for c in g]
        return np.average(np.stack(embs), axis=0, weights=ws).astype(np.float32)

    def text_embedding(self, text):
        """Mean-pooled frozen DistilBERT embedding (768-d); long text uses 512-token overlapping windows. None if empty."""
        import torch
        text = clean_text(text)
        if not text:
            return None
        if self._t is None:
            from transformers import AutoTokenizer, AutoModel
            r = self.rev.get(BERT_ID)
            self._tok = AutoTokenizer.from_pretrained(BERT_ID, revision=r)
            self._t = AutoModel.from_pretrained(BERT_ID, revision=r).to(self.device).eval()
            for p in self._t.parameters():
                p.requires_grad = False
        enc = self._tok(text, truncation=True, max_length=512, stride=64, return_overflowing_tokens=True,
                        padding=True, return_tensors="pt")
        ids, mask = enc["input_ids"], enc["attention_mask"]
        out = []
        with torch.inference_mode():
            for i in range(0, len(ids), self.bs):
                a, m = ids[i:i + self.bs].to(self.device), mask[i:i + self.bs].to(self.device)
                h = self._t(input_ids=a, attention_mask=m).last_hidden_state
                mm = m.unsqueeze(-1).float()
                out.append(((h * mm).sum(1) / mm.sum(1)).float().cpu().numpy())
        return np.concatenate(out).mean(0).astype(np.float32)


# ---------------- inference ----------------
class NeuroDetectModel3:
    def __init__(self, package_dir=None, device=None, batch_size=8):
        import joblib
        self.dir = Path(package_dir) if package_dir else Path(__file__).resolve().parent.parent
        self.cfg = json.load(open(self.dir / "preprocessing" / "model_config.json"))
        lm = json.load(open(self.dir / "preprocessing" / "label_mapping.json"))
        self.labels = {int(k): v for k, v in lm["id_to_label"].items()}
        self.clf = {k: joblib.load(self.dir / "models" / f) for k, f in self.cfg["model_files"].items()}
        self.enc = Encoders(device, self.cfg.get("encoder_revisions"), batch_size)
        self.version = self.cfg["model_version"]

    def _branches(self):
        c = self.cfg
        return list(c["fusion_inputs"]) if c["final_model"] == "fusion" else [c["final_model"]]

    def required_inputs(self):
        b = set(self._branches())
        return {"audio": bool(b & {"audio_embedding", "acoustic"}), "transcript": "transcript" in b}

    def predict(self, audio_path=None, transcript=None):
        need, errs = self.required_inputs(), []
        if need["audio"] and (not audio_path or not Path(audio_path).is_file()):
            errs.append("audio_path missing or file not found (audio is required by this model)")
        if need["transcript"] and not clean_text(transcript):
            errs.append("transcript missing or empty (transcript is required by this model)")
        if errs:
            return {"status": "error", "errors": errs, "model_version": self.version, "disclaimer": DISCLAIMER}
        y = prep_audio(*load_audio(audio_path)) if need["audio"] else None
        probs = {}
        for b in self._branches():
            if b == "audio_embedding":
                x = self.enc.audio_embedding(y)[None]
            elif b == "acoustic":
                a = acoustic_features(y, transcript)
                x = np.array([[a[k] for k in self.cfg["acoustic_feature_names"]]], dtype=float)
            else:
                e = self.enc.text_embedding(transcript)
                l = linguistic_features(transcript)
                x = np.concatenate([e, [l[k] for k in self.cfg["linguistic_feature_names"]]])[None].astype(float)
            probs[b] = self.clf[b].predict_proba(x)[0]
        if self.cfg["final_model"] == "fusion":
            final = self.clf["fusion"].predict_proba(np.hstack([probs[b] for b in self.cfg["fusion_inputs"]])[None])[0]
            classes = self.clf["fusion"].classes_
        else:
            b = self.cfg["final_model"]
            final, classes = probs[b], self.clf[b].classes_
        d = {self.labels[int(c)]: float(p) for c, p in zip(classes, final)}
        return {"status": "ok", "predicted_class": max(d, key=d.get), "probabilities": d,
                "branch_probabilities": {b: {self.labels[i]: float(p) for i, p in enumerate(v)} for b, v in probs.items()},
                "components_used": self._branches(), "model_version": self.version, "disclaimer": DISCLAIMER}


if __name__ == "__main__":
    import sys
    m = NeuroDetectModel3()
    print(json.dumps(m.predict(sys.argv[1] if len(sys.argv) > 1 else None, sys.argv[2] if len(sys.argv) > 2 else None), indent=2))
