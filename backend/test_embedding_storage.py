
from pathlib import Path

from app.db.database import (
    get_all_images,
    get_images_with_embeddings,
    initialize_database,
    save_image_embedding,
)
from app.services.embedding_service import embedding_service

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPLOADS_DIR = PROJECT_ROOT / "storage" / "uploads"


def main():
    initialize_database()

    images = get_all_images()

    if not images:
        print("No images found in the database.")
        return

    image = images[0]
    image_path = UPLOADS_DIR / image["stored_filename"]

    if not image_path.is_file():
        print(f"Image file not found: {image_path}")
        return

    embedding = embedding_service.generate_image_embedding(
        str(image_path)
    )

    save_image_embedding(image["id"], embedding)

    saved_images = get_images_with_embeddings()
    saved_image = next(
        item for item in saved_images if item["id"] == image["id"]
    )

    print("Image:", saved_image["filename"])
    print("Embedding dimensions:", len(saved_image["embedding"]))
    print("Embedding successfully saved and retrieved from SQLite!")


if __name__ == "__main__":
    main()
