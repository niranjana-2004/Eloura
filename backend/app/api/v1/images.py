
from fastapi import APIRouter, File, UploadFile

from app.db.database import get_all_images
from app.services.image_service import save_uploaded_image

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    return await save_uploaded_image(file)


@router.get("")
def list_images():
    images = get_all_images()

    for image in images:
        image["url"] = f"/media/{image['stored_filename']}"

    return {
        "total": len(images),
        "images": images,
    }
