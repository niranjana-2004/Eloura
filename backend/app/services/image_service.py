
from pathlib import Path
from uuid import uuid4
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException, UploadFile

from app.db.database import save_image_metadata, save_image_embedding
from app.services.embedding_service import embedding_service


UPLOAD_DIR = Path(__file__).resolve().parents[3] / "storage" / "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}


async def save_uploaded_image(file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image must be 10 MB or smaller.",
        )

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()

        with Image.open(BytesIO(content)) as image:
            image_format = image.format
            width, height = image.size

    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
    ):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid image.",
        )

    if image_format not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=415,
            detail="Only JPEG, PNG, and WEBP images are supported.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    image_id = str(uuid4())
    stored_filename = f"{image_id}{ALLOWED_FORMATS[image_format]}"
    destination = UPLOAD_DIR / stored_filename

    image_metadata = {
        "id": image_id,
        "filename": file.filename,
        "stored_filename": stored_filename,
        "format": image_format,
        "width": width,
        "height": height,
        "size_bytes": len(content),
        "status": "uploaded",
    }

    try:
        destination.write_bytes(content)
        save_image_metadata(image_metadata)

        embedding = embedding_service.generate_image_embedding(
            str(destination)
        )
        save_image_embedding(image_id, embedding)

    except Exception as exc:
        destination.unlink(missing_ok=True)

        # Avoid leaving a database record if processing fails.
        from app.db.database import get_connection

        try:
            with get_connection() as connection:
                connection.execute(
                    "DELETE FROM images WHERE id = ?",
                    (image_id,),
                )
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail="Could not process and save the uploaded image.",
        ) from exc

    return image_metadata
