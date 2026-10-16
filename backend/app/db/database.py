
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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
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
