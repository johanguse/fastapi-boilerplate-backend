from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.common.config import settings
from src.common.security import get_current_active_user
from src.utils.storage import (
    delete_file_from_r2,
    get_file_url,
    upload_file_to_r2,
)

router = APIRouter(tags=["uploads"])


@router.post("/", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    user=Depends(get_current_active_user),
):
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    key = file.filename
    url = await upload_file_to_r2(contents, key, file.content_type)
    if not url:
        raise HTTPException(status_code=500, detail="Upload failed")
    return {"key": key, "url": url}


@router.delete("/{key}")
async def delete_file(key: str, user=Depends(get_current_active_user)):
    ok = await delete_file_from_r2(key)
    if not ok:
        raise HTTPException(status_code=404, detail="File not found or delete failed")
    return {"deleted": True}


@router.get("/{key}/url")
async def get_presigned_url(key: str, user=Depends(get_current_active_user)):
    url = await get_file_url(key)
    if not url:
        raise HTTPException(status_code=404, detail="File not found")
    return {"url": url}
