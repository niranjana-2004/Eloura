from app.services.search_service import search_images
from fastapi import APIRouter, File, UploadFile,Query

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

@router.get("/search")
def search_images_endpoint(
    query: str = Query(..., min_length=1, max_length=300),
    limit: int = Query(20, ge=1, le=100),
):
    return search_images(query=query, limit=limit)
