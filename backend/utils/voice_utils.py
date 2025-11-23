# backend/utils/voice_utils.py
import os
import tempfile
import asyncio
import threading
from typing import List, Optional, Dict

# The heavy ML libraries are imported lazily inside functions to avoid
# importing them at module import time (which can crash the uvicorn worker
# if system libs are incompatible).
_model = None
_model_lock = threading.Lock()
_MODEL_DIR = "pretrained_models/spkrec-ecapa-voxceleb"

# --- Helper: lazy model loader ---
def _get_model():
    """
    Lazily load and return the SpeechBrain SpeakerRecognition model.
    Uses a lock to avoid race conditions when multiple workers import at once.
    """
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        if _model is not None:
            return _model

        try:
            # Import inside function to avoid heavy imports at module load
            from speechbrain.inference.speaker import SpeakerRecognition
        except Exception as e:
            raise RuntimeError("Failed to import SpeechBrain: " + str(e))

        try:
            _model = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir=_MODEL_DIR
            )
        except Exception as e:
            raise RuntimeError("Failed to load speaker model: " + str(e))

        return _model


# --- Blocking helper that does the audio load & embedding generation ---
def _compute_embedding_sync(wav_path: str):
    """
    Blocking function that loads wav at wav_path, resamples, normalizes and returns a 1D list embedding.
    Designed to be called in a threadpool (run_in_executor).
    """

    # ---- Use soundfile + librosa instead of torchaudio ----
    import torch
    import soundfile as sf
    import librosa
    import numpy as np

    model = _get_model()  # Load SpeechBrain ECAPA

    # Load audio safely on Windows
    wav, sr = sf.read(wav_path)      # wav -> numpy array

    # If stereo → make mono
    if len(wav.shape) > 1:
        wav = np.mean(wav, axis=1)

    # Resample to 16 kHz for SpeechBrain
    if sr != 16000:
        wav = librosa.resample(wav.astype(np.float32), orig_sr=sr, target_sr=16000)
        sr = 16000

    # Normalize
    wav = wav / (np.max(np.abs(wav)) + 1e-8)

    # Convert to torch tensor
    waveform = torch.from_numpy(wav).float().unsqueeze(0)  # shape [1, time]

    # Generate embedding
    with torch.no_grad():
        emb = model.encode_batch(waveform).squeeze()

    # Convert to list
    try:
        return emb.cpu().tolist()
    except:
        return emb.cpu().numpy().tolist()



# --- Public async API ---
async def compute_embedding_from_wav_bytes(wav_bytes: bytes) -> List[float]:
    """
    Accept raw WAV bytes and return the speaker embedding (list of floats).
    This runs audio decoding + model encoding in a thread so it doesn't block asyncio loop.
    """
    loop = asyncio.get_running_loop()

    # Write bytes to a secure temp file
    fd, tmp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        with open(tmp_path, "wb") as f:
            f.write(wav_bytes)

        # Run the heavy operation in executor
        emb = await loop.run_in_executor(None, _compute_embedding_sync, tmp_path)
        return emb
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


async def enroll_voice_embeddings(wav_bytes_list: List[bytes]) -> List[float]:
    """
    Given a list of WAV byte blobs (3 or more recommended), compute embeddings for each,
    average them and return the averaged embedding (list of floats).
    """
    if not isinstance(wav_bytes_list, (list, tuple)) or len(wav_bytes_list) == 0:
        raise ValueError("wav_bytes_list must be a non-empty list of bytes")

    # Concurrently compute embeddings (in threadpool)
    tasks = [compute_embedding_from_wav_bytes(b) for b in wav_bytes_list]
    embeddings = await asyncio.gather(*tasks)  # List[List[float]]

    # Average elementwise (use Python sums to avoid numpy dependency here)
    length = len(embeddings[0])
    # verify equal lengths
    for e in embeddings:
        if len(e) != length:
            raise ValueError("Embeddings length mismatch between samples")

    averaged = [0.0] * length
    for e in embeddings:
        for i, v in enumerate(e):
            averaged[i] += v
    averaged = [x / len(embeddings) for x in averaged]

    return averaged


async def verify_voice_embedding(
    wav_bytes: bytes,
    stored_embedding: List[float],
    threshold: Optional[float] = None
) -> Dict:
    """
    Compute embedding for wav_bytes and compare with stored_embedding using model similarity.
    Returns dict: { "score": float, "match": bool, "threshold": float }
    """
    if stored_embedding is None:
        raise ValueError("No stored embedding provided")

    # compute new embedding
    new_emb = await compute_embedding_from_wav_bytes(wav_bytes)

    # compute similarity score (calls the model similarity method synchronously)
    score = similarity_score(new_emb, stored_embedding)

    # default threshold (tunable by user of this module)
    if threshold is None:
        # try to get threshold from env var or default 0.15
        try:
            from ..core.config import settings
            threshold_val = getattr(settings, "VOICE_VERIFICATION_THRESHOLD", 0.15)
        except Exception:
            threshold_val = 0.15
    else:
        threshold_val = threshold

    match = (score > threshold_val)
    return {"score": float(score), "match": bool(match), "threshold": float(threshold_val)}


# --- low-level similarity helper ---
def similarity_score(embedding1, embedding2) -> float:
    """
    Compute similarity score between two embeddings using the model.similarity function.
    Accepts lists or numeric sequences.
    """
    model = _get_model()

    try:
        import torch
    except Exception:
        raise RuntimeError("Missing torch for similarity computation")

    # Convert to tensors shaped [1,1,N] as the model expects
    a = torch.tensor(embedding1, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    b = torch.tensor(embedding2, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

    with torch.no_grad():
        score_tensor = model.similarity(a, b)  # returns a tensor-like value
    try:
        score_val = float(score_tensor.item())
    except Exception:
        score_val = float(score_tensor)

    return score_val
