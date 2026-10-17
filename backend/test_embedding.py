
from pathlib import Path

from app.services.embedding_service import embedding_service

project_root = Path(__file__).resolve().parents[1]
uploads_dir = project_root / "storage" / "uploads"

images = list(uploads_dir.glob("*"))

if not images:
    print("No uploaded images found. Upload an image first.")
else:
    image_path = images[0]
    embedding = embedding_service.generate_image_embedding(str(image_path))

    print("Image:", image_path.name)
    print("Embedding dimensions:", len(embedding))
    print("First five values:", embedding[:5])
    print("Embedding generated successfully!")
