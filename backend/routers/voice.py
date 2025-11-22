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

router = APIRouter()


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
