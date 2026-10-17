
import numpy as np

from app.db.database import get_images_with_embeddings
from app.services.embedding_service import embedding_service
print("EL0URA SEARCH SERVICE LOADED FROM:", __file__)

# Initial threshold; tune this using relevant and irrelevant test queries.
SIMILARITY_THRESHOLD = 0.20


def search_images(query: str, limit: int = 20) -> dict:
    query = query.strip()

    if not query:
        return {"query": query, "total": 0, "results": []}

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100.")

    query_embedding = np.array(
        embedding_service.generate_text_embedding(query),
        dtype=np.float32,
    )

    images = get_images_with_embeddings()
    results = []

    for image in images:
        image_embedding = np.array(
            image["embedding"],
            dtype=np.float32,
        )

        similarity = float(
            np.dot(query_embedding, image_embedding)
            / (
                np.linalg.norm(query_embedding)
                * np.linalg.norm(image_embedding)
                + 1e-12
            )
        )

        results.append(
            {
                "id": image["id"],
                "filename": image["filename"],
                "stored_filename": image["stored_filename"],
                "url": f"/media/{image['stored_filename']}",
                "similarity": round(similarity, 4),
            }
        )

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )

    print("DEBUG: Search service file:", __file__)
    print("DEBUG: Threshold:", SIMILARITY_THRESHOLD)
    print("DEBUG: Scores before filtering:", [
    item["similarity"] for item in results
    ])

    results = [
    item for item in results
    if item["similarity"] >= SIMILARITY_THRESHOLD
    ]

    print("DEBUG: Results after filtering:", len(results))
    # Keep only images that meet the minimum similarity threshold.
    results = [
        item
        for item in results
        if item["similarity"] >= SIMILARITY_THRESHOLD
    ]

    results = results[:limit]

    return {
        "query": query,
        "total": len(results),
        "results": results,
    }
import numpy as np

from app.db.database import get_images_with_embeddings
from app.services.embedding_service import embedding_service


def search_images(query: str, limit: int = 20) -> dict:
    query = query.strip()

    if not query:
        return {"query": query, "total": 0, "results": []}

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100.")

    query_embedding = np.array(
        embedding_service.generate_text_embedding(query),
        dtype=np.float32,
    )

    images = get_images_with_embeddings()
    results = []

    for image in images:
        image_embedding = np.array(
            image["embedding"],
            dtype=np.float32,
        )

        similarity = float(
            np.dot(query_embedding, image_embedding)
            / (
                np.linalg.norm(query_embedding)
                * np.linalg.norm(image_embedding)
                + 1e-12
            )
        )

        results.append(
            {
                "id": image["id"],
                "filename": image["filename"],
                "stored_filename": image["stored_filename"],
                "url": f"/media/{image['stored_filename']}",
                "similarity": round(similarity, 4),
            }
        )

    results.sort(key=lambda item: item["similarity"], reverse=True)
    results = results[:limit]

    return {
        "query": query,
        "total": len(results),
        "results": results,
    }
