import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from web.config import MAX_PHOTO_SIZE_MB, UPLOAD_DIR, WEB_URL

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}
MAX_BYTES = MAX_PHOTO_SIZE_MB * 1024 * 1024


def validate_image(file: UploadFile) -> None:
    """Check file extension and size. Raises HTTPException on failure."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}. Allowed: JPG, PNG, HEIC",
        )
    if file.size and file.size > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_PHOTO_SIZE_MB} MB",
        )


async def save_upload_file(file: UploadFile) -> str:
    """Save an uploaded file to UPLOAD_DIR with a UUID filename. Returns the stored filename."""
    ext = Path(file.filename or "").suffix.lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_PHOTO_SIZE_MB} MB",
        )
    dest.write_bytes(content)
    return filename


def get_photo_url(filename: str) -> str:
    """Return the public URL for a stored photo."""
    return f"{WEB_URL}/uploads/{filename}"
