# backend/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from ..db.database import get_db
from ..db.models.user import User
from ..schemas.user import UserCreate, UserOut
from ..core.security import verify_password, hash_password, create_access_token
from ..core.config import settings
from ..utils.voice_utils import (
    enroll_voice_embeddings,
    verify_voice_embedding
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# ------------------------------------------------
#  Helper: Get Current User from JWT
# ------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    from jose import jwt, JWTError

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")

    q = select(User).where(User.id == user_id)
    res = await db.execute(q)
    user = res.scalars().first()

    if not user:
        raise HTTPException(404, "User not found")

    return user


# ------------------------------------------------
#  Register User
# ------------------------------------------------
@router.post("/register", response_model=UserOut)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    q = select(User).where(User.username == payload.username)
    res = await db.execute(q)
    if res.scalars().first():
        raise HTTPException(400, "Username already taken")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        email=payload.email
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ------------------------------------------------
#  Login
# ------------------------------------------------
@router.post("/login")
async def login(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    q = select(User).where(User.username == payload.username)
    res = await db.execute(q)
    user = res.scalars().first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(400, "Incorrect username or password")

    token = create_access_token({
        "sub": str(user.id),
        "username": user.username
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "full_name": user.full_name
        }
    }


# ------------------------------------------------
#  PIN — Set PIN
# ------------------------------------------------
class PinIn(BaseModel):
    pin: str


@router.post("/set-pin")
async def set_pin(
    payload: PinIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    hashed_pin = hash_password(payload.pin)

    stmt = (
        update(User)
        .where(User.id == current_user.id)
        .values(pin_hash=hashed_pin)
    )

    await db.execute(stmt)
    await db.commit()

    return {"status": "success", "message": "PIN saved successfully"}


# ------------------------------------------------
#  PIN — Verify PIN
# ------------------------------------------------
@router.post("/verify-pin")
async def verify_pin(
    payload: PinIn,
    current_user=Depends(get_current_user)
):
    if not current_user.pin_hash:
        raise HTTPException(400, "PIN not set for this user")

    if not verify_password(payload.pin, current_user.pin_hash):
        raise HTTPException(400, "Incorrect PIN")

    return {"status": "verified"}


# ------------------------------------------------
#  Voice Enrollment (3 samples recommended)
# ------------------------------------------------
@router.post("/enroll-voice")
async def enroll_voice(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    file3: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    blobs = [
        await file1.read(),
        await file2.read(),
        await file3.read()
    ]

    # Average embedding of samples
    avg_emb = await enroll_voice_embeddings(blobs)

    stmt = (
        update(User)
        .where(User.id == current_user.id)
        .values(voice_embedding=avg_emb)
    )

    await db.execute(stmt)
    await db.commit()

    return {"status": "success", "message": "Voice enrolled successfully"}


# ------------------------------------------------
#  Voice Verification
# ------------------------------------------------
@router.post("/verify-voice")
async def verify_voice(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):

    if not current_user.voice_embedding:
        raise HTTPException(400, "User has not enrolled voice")

    wav_bytes = await file.read()

    result = await verify_voice_embedding(
        wav_bytes,
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
        f"Voice mismatch (score={result['score']:.3f}, threshold={result['threshold']})"
    )
