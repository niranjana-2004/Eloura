
from pathlib import Path
import re

import numpy as np

from app.db.database import get_images_with_embeddings, save_image_visual_features
from app.services.embedding_service import embedding_service
from app.services.visual_features import (
    compute_visual_modifier,
    extract_visual_features,
    extract_visual_query_cues,
)

UPLOADS_DIR = Path(__file__).resolve().parents[3] / "storage" / "uploads"

MIN_ABSOLUTE_SIMILARITY = 0.16
STRONG_MATCH_THRESHOLD = 0.26
GOOD_MATCH_THRESHOLD = 0.20
NOISE_FLOOR_CEILING = 0.195
MIN_SPREAD_ABOVE_MEDIAN = 0.025
SINGLE_IMAGE_MIN_SIMILARITY = 0.18

_FACET_SPLIT_PATTERN = re.compile(
    r"\s+(?:with|under|during|wearing|and|at|in)\s+|,\s*",
    re.IGNORECASE,
)
_LEADING_FILLER_PATTERN = re.compile(
    r"^(?:something|anything|a\s+photo\s+of|a\s+photograph\s+of|a\s+photo\s+with|a\s+picture\s+of)\s+",
    re.IGNORECASE,
)
_NON_OBJECT_MODIFIERS = {
    "peaceful",
    "calm",
    "quiet",
    "serene",
    "soft",
    "gentle",
    "bright",
    "dark",
    "warm",
    "cool",
    "colorful",
    "colourful",
    "beautiful",
    "atmospheric",
    "moody",
}


def extract_query_facets(query: str) -> list[str]:
    """Conservatively extract up to 3 visual sub-clauses from multi-concept queries."""
    cleaned = _LEADING_FILLER_PATTERN.sub("", " ".join(query.strip().split())).strip()
    if not cleaned:
        return []

    parts = [part.strip(" ,.") for part in _FACET_SPLIT_PATTERN.split(cleaned)]
    parts = [part for part in parts if len(part) >= 3]
    if len(parts) < 2:
        return []

    # Avoid splitting pure synonym mood pairs like "peaceful and calm".
    if all(part.lower() in _NON_OBJECT_MODIFIERS for part in parts):
        return []

    facets: list[str] = []
    seen: set[str] = set()

    for part in parts:
        key = part.lower()
        if key not in seen:
            seen.add(key)
            if key in _NON_OBJECT_MODIFIERS or key == "night":
                facets.append(f"a {part} scene")
            else:
                facets.append(f"a photo of {part}")

    return facets[:3] if len(facets) >= 2 else []


def classify_match_level(score: float) -> str:
    if score >= STRONG_MATCH_THRESHOLD:
        return "strong"
    if score >= GOOD_MATCH_THRESHOLD:
        return "good"
    return "related"


def _resolve_visual_features(image: dict) -> dict | None:
    """Return cached visual features or compute/persist them if the image file exists."""
    if image.get("visual_features") is not None:
        return image["visual_features"]

    stored_filename = image.get("stored_filename")
    if not stored_filename:
        return None

    image_path = UPLOADS_DIR / stored_filename
    if not image_path.is_file():
        return None

    try:
        features = extract_visual_features(str(image_path))
        save_image_visual_features(image["id"], features)
        return features
    except Exception:
        return None


def filter_relevant_results(scored_items: list[dict]) -> list[dict]:
    """Filter ranked results using absolute floor, noise-floor flatness, and top-gap margin."""
    if not scored_items:
        return []

    all_scores = np.array([item["similarity"] for item in scored_items], dtype=np.float32)
    top_score = float(all_scores[0])

    if top_score < MIN_ABSOLUTE_SIMILARITY:
        return []

    if len(all_scores) == 1 and top_score < SINGLE_IMAGE_MIN_SIMILARITY:
        return []

    # Reject borderline low-confidence responses that fail to stand out from the corpus median.
    if len(all_scores) >= 2:
        median_score = float(np.median(all_scores))
        if (
            top_score < NOISE_FLOOR_CEILING
            and (top_score - median_score) < MIN_SPREAD_ABOVE_MEDIAN
        ):
            return []

    max_drop = 0.095 if top_score >= STRONG_MATCH_THRESHOLD else 0.075
    dynamic_cutoff = max(MIN_ABSOLUTE_SIMILARITY, top_score - max_drop)

    return [item for item in scored_items if item["similarity"] >= dynamic_cutoff]


def score_candidates(
    query: str,
    images: list[dict],
    allow_lazy_visual_backfill: bool = True,
) -> list[dict]:
    """Rank image records against a query using vectorized CLIP similarity and visual checks."""
    if not images:
        return []

    query_embedding = np.array(
        embedding_service.generate_query_embedding(query),
        dtype=np.float32,
    )
    q_norm = float(np.linalg.norm(query_embedding))
    if q_norm > 1e-12:
        query_embedding = query_embedding / q_norm

    emb_matrix = np.array([image["embedding"] for image in images], dtype=np.float32)
    row_norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
    emb_matrix = emb_matrix / np.maximum(row_norms, 1e-12)

    # Vectorized cosine similarity across all images.
    primary_sims = emb_matrix @ query_embedding

    facets = extract_query_facets(query)
    if facets:
        facet_matrix = np.array(
            embedding_service.generate_text_embeddings(facets),
            dtype=np.float32,
        )
        facet_norms = np.linalg.norm(facet_matrix, axis=1, keepdims=True)
        facet_matrix = facet_matrix / np.maximum(facet_norms, 1e-12)
        facet_sims = emb_matrix @ facet_matrix.T
        min_facets = np.min(facet_sims, axis=1)
        facet_adjustments = np.clip(
            0.08 * np.maximum(0.0, min_facets - 0.14)
            - 0.25 * np.maximum(0.0, 0.14 - min_facets),
            -0.035,
            0.015,
        )
    else:
        facet_adjustments = np.zeros(len(images), dtype=np.float32)

    semantic_scores = primary_sims + facet_adjustments
    visual_cues = extract_visual_query_cues(query)

    results: list[dict] = []
    for idx, image in enumerate(images):
        semantic_score = float(semantic_scores[idx])
        visual_modifier = 0.0

        if visual_cues["has_any"]:
            vf = (
                _resolve_visual_features(image)
                if allow_lazy_visual_backfill
                else image.get("visual_features")
            )
            visual_modifier = compute_visual_modifier(vf, visual_cues, semantic_score)

        final_score = semantic_score + visual_modifier

        results.append(
            {
                "id": image["id"],
                "filename": image["filename"],
                "stored_filename": image["stored_filename"],
                "url": f"/media/{image['stored_filename']}",
                "similarity": round(final_score, 4),
                "match_level": classify_match_level(final_score),
            }
        )

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )
    return results


def search_images(query: str, limit: int = 20) -> dict:
    query = query.strip()

    if not query:
        return {"query": query, "total": 0, "results": []}

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100.")

    images = get_images_with_embeddings()
    if not images:
        return {"query": query, "total": 0, "results": []}

    ranked = score_candidates(query=query, images=images)
    filtered = filter_relevant_results(ranked)[:limit]

    return {
        "query": query,
        "total": len(filtered),
        "results": filtered,
    }
