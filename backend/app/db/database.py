
import json
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STORAGE_DIR = PROJECT_ROOT / "storage"
DATABASE_PATH = STORAGE_DIR / "eloura.db"


def get_connection() -> sqlite3.Connection:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL UNIQUE,
                format TEXT NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                size_bytes INTEGER NOT NULL,
                embedding TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Add the column to existing databases without deleting data.
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(images)"
            ).fetchall()
        }

        if "embedding" not in columns:
            connection.execute(
                "ALTER TABLE images ADD COLUMN embedding TEXT"
            )


def save_image_metadata(image: dict) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO images (
                id, filename, stored_filename, format,
                width, height, size_bytes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                image["id"],
                image["filename"],
                image["stored_filename"],
                image["format"],
                image["width"],
                image["height"],
                image["size_bytes"],
            ),
        )


def save_image_embedding(image_id: str, embedding: list[float]) -> None:
    embedding_json = json.dumps(embedding)

    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE images SET embedding = ? WHERE id = ?",
            (embedding_json, image_id),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"Image not found: {image_id}")


def get_all_images() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, filename, stored_filename, format,
                   width, height, size_bytes, created_at
            FROM images
            ORDER BY created_at DESC, rowid DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_images_with_embeddings() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, filename, stored_filename, embedding
            FROM images
            WHERE embedding IS NOT NULL
            ORDER BY created_at DESC, rowid DESC
            """
        ).fetchall()

    images = [dict(row) for row in rows]

    for image in images:
        image["embedding"] = json.loads(image["embedding"])

    return images
