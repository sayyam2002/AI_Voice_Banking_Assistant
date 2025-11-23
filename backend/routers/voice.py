# backend/routers/voice.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from .auth import get_current_user
from ..db.database import get_db
from ..db.models.user import User
from ..utils.voice_utils import (
    enroll_voice_embeddings,
    verify_voice_embedding
)
from ..core.config import settings
import os
# import tempfile
import soundfile as sf
import librosa
import numpy as np
import torch
import traceback

router = APIRouter()

AUDIO_DIR = "backend/temp/audio"
AUDIO_PATH = os.path.join(AUDIO_DIR, "input.wav")

# ------------------------------
#  Enroll Voice (3 samples)
# ------------------------------
@router.post("/enroll")
async def enroll_voice(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    file3: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wavs = [
        await file1.read(),
        await file2.read(),
        await file3.read()
    ]

    avg_emb = await enroll_voice_embeddings(wavs)

    stmt = (
        update(User)
        .where(User.id == current_user.id)
        .values(voice_embedding=avg_emb)
    )
    await db.execute(stmt)
    await db.commit()

    return {"status": "success", "message": "Voice enrolled successfully"}


# ------------------------------
#  Verify Voice
# ------------------------------
@router.post("/verify")
async def verify_voice(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
):
    if not current_user.voice_embedding:
        raise HTTPException(400, "User has not enrolled voice")

    wav = await file.read()
    result = await verify_voice_embedding(
        wav,
        current_user.voice_embedding,
        threshold=settings.VOICE_VERIFICATION_THRESHOLD
    )

    if result["match"]:
        return {
            "status": "verified",
            "score": result["score"],
            "threshold": result["threshold"]
        }

    raise HTTPException(
        401,
        f"Voice mismatch (score={result['score']:.3f} < threshold {result['threshold']})"
    )

@router.post("/asr")
async def voice_asr(file: UploadFile = File(...)):
    """
    Accepts a WAV file and saves it to a stable path, then runs SpeechBrain ASR.
    No temp folders, no random file names.
    """
    try:
        from speechbrain.inference.ASR import EncoderDecoderASR
    except Exception as e:
        return {"error": f"ASR model import failed: {str(e)}"}

    # Ensure folder exists
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # Save uploaded file to a FIXED predictable path
    try:
        content = await file.read()
        with open(AUDIO_PATH, "wb") as f:
            f.write(content)
    except Exception as e:
        return {"error": f"Failed to save audio file: {str(e)}"}

    # Run ASR
    try:
        asr_model = EncoderDecoderASR.from_hparams(
            source="speechbrain/asr-crdnn-rnnlm-librispeech",
            savedir="pretrained_models/asr"
        )

        text = asr_model.transcribe_file(AUDIO_PATH)

        # SpeechBrain sometimes returns list
        if isinstance(text, (list, tuple)):
            text = text[0] if text else ""

        return {"text": str(text)}

    except Exception as e:
        traceback.print_exc()
        return {"error": f"ASR failed: {str(e)}"}



# @router.post("/asr")
# async def voice_asr(
#     file: UploadFile = File(...),
#     current_user = Depends(get_current_user)
# ):
#     """
#     Speech-to-text using SpeechBrain ASR with soundfile + librosa (NO torchaudio).
#     """
#     try:
#         from speechbrain.inference.ASR import EncoderDecoderASR
#     except Exception as e:
#         raise HTTPException(500, f"ASR model load failed: {e}")

#     # ---- Save temp file ----
#     fd, tmp_path = tempfile.mkstemp(suffix=".wav")
#     os.close(fd)

#     try:
#         with open(tmp_path, "wb") as f:
#             f.write(await file.read())

#         # ---- Load WAV using soundfile ----
#         wav, sr = sf.read(tmp_path)

#         # Stereo → mono
#         if wav.ndim > 1:
#             wav = np.mean(wav, axis=1)

#         # Resample to 16k
#         if sr != 16000:
#             wav = librosa.resample(
#                 wav.astype(np.float32),
#                 orig_sr=sr,
#                 target_sr=16000
#             )
#             sr = 16000

#         # Normalize audio
#         wav = wav / (np.max(np.abs(wav)) + 1e-8)

#         # Convert to tensor
#         waveform = torch.from_numpy(wav).float().unsqueeze(0)
#         lengths = torch.tensor([1.0])

#         # ---- Load SpeechBrain ASR ----
#         asr_model = EncoderDecoderASR.from_hparams(
#             source="speechbrain/asr-crdnn-rnnlm-librispeech",
#             savedir="pretrained_models/asr"
#         )

#         # ---- Run transcription ----
#         hyps = asr_model.transcribe_batch(waveform, lengths)

#         # SpeechBrain returns a list
#         if isinstance(hyps, (list, tuple)):
#             text = hyps[0]
#         else:
#             text = str(hyps)

#         return {"text": text}

#     except Exception as e:
#         raise HTTPException(500, f"ASR failed: {e}")

#     finally:
#         try:
#             os.remove(tmp_path)
#         except:
#             pass
