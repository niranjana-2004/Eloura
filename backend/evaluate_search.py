from dataclasses import dataclass

import numpy as np

from app.db.database import get_images_with_embeddings, initialize_database
from app.services.embedding_service import embedding_service
from app.services.search_service import search_images

LEGACY_THRESHOLD = 0.10


@dataclass(frozen=True)
class EvaluationCase:
    category: str
    query: str
    expected_relevant: str
    expected_irrelevant: str
    expectation_on_current_db: str  # "reject_all" | "prefer_burgundy" | "match_tops"


EVALUATION_CASES: list[EvaluationCase] = [
    # Objects
    EvaluationCase(
        category="Objects",
        query="a dress",
        expected_relevant="Dresses or closely related women's fitted tops/garments",
        expected_irrelevant="Landscapes, vehicles, non-clothing scenes",
        expectation_on_current_db="match_tops",
    ),
    EvaluationCase(
        category="Objects",
        query="a top",
        expected_relevant="Shirts, blouses, crop tops, and upper-body garments",
        expected_irrelevant="Nature scenes, cars, flowers, night skies",
        expectation_on_current_db="match_tops",
    ),
    EvaluationCase(
        category="Objects",
        query="flowers",
        expected_relevant="Blooming flowers, petals, bouquets, gardens",
        expected_irrelevant="Plain studio clothing cutouts, cars, dark buildings",
        expectation_on_current_db="reject_all",
    ),
    EvaluationCase(
        category="Objects",
        query="a car",
        expected_relevant="Automobiles, sedans, sports cars, street vehicles",
        expected_irrelevant="Clothing items, natural landscapes, flowers",
        expectation_on_current_db="reject_all",
    ),
    # Colors
    EvaluationCase(
        category="Colors",
        query="a red top",
        expected_relevant="Red, crimson, or burgundy upper-body garments ranked first",
        expected_irrelevant="Brown/neutral garments ranked lower; non-clothing objects",
        expectation_on_current_db="prefer_burgundy",
    ),
    EvaluationCase(
        category="Colors",
        query="a blue object",
        expected_relevant="Objects or scenes dominated by blue tones",
        expected_irrelevant="Dark red or brown tops on neutral gray backgrounds",
        expectation_on_current_db="reject_all",
    ),
    EvaluationCase(
        category="Colors",
        query="a colorful photograph",
        expected_relevant="Vibrant, multi-hue photography with strong color richness",
        expected_irrelevant="Muted dark garments on plain light-gray studio backgrounds",
        expectation_on_current_db="reject_all",
    ),
    # Scenes
    EvaluationCase(
        category="Scenes",
        query="a beach at sunset",
        expected_relevant="Coastal ocean/sand scenes with warm sunset lighting",
        expected_irrelevant="Indoor studio clothing screenshots",
        expectation_on_current_db="reject_all",
    ),
    EvaluationCase(
        category="Scenes",
        query="a snowy mountain",
        expected_relevant="Snow-covered mountain peaks and alpine terrain",
        expected_irrelevant="Studio clothing screenshots",
        expectation_on_current_db="reject_all",
    ),
    EvaluationCase(
        category="Scenes",
        query="a city at night",
        expected_relevant="Nighttime urban skylines, street lights, buildings",
        expected_irrelevant="Studio clothing screenshots",
        expectation_on_current_db="reject_all",
    ),
    # Combined descriptions
    EvaluationCase(
        category="Combined",
        query="a dark red long sleeve top",
        expected_relevant="Dark red / burgundy long-sleeve top ranked strongly at #1",
        expected_irrelevant="Sleeveless brown crop top ranked clearly lower",
        expectation_on_current_db="prefer_burgundy",
    ),
    EvaluationCase(
        category="Combined",
        query="a person wearing a red dress",
        expected_relevant="Person visibly wearing a red dress",
        expected_irrelevant="Unworn product cutouts on plain backgrounds (unless partial garment overlap)",
        expectation_on_current_db="reject_all",
    ),
    EvaluationCase(
        category="Combined",
        query="a snowy mountain at night",
        expected_relevant="Snow-covered peaks under a dark nighttime sky",
        expected_irrelevant="Clothing photos or bright daytime scenes",
        expectation_on_current_db="reject_all",
    ),
    EvaluationCase(
        category="Combined",
        query="snowy mountains under a dark sky",
        expected_relevant="Snowy mountain ridges beneath dark/night clouds or sky",
        expected_irrelevant="Studio clothing photos",
        expectation_on_current_db="reject_all",
    ),
    # Descriptive queries
    EvaluationCase(
        category="Descriptive",
        query="something peaceful and calm",
        expected_relevant="Serene natural scenes, calm water, soft light",
        expected_irrelevant="Flat e-commerce clothing product screenshots",
        expectation_on_current_db="reject_all",
    ),
    EvaluationCase(
        category="Descriptive",
        query="something with soft colors",
        expected_relevant="Pastel, gentle, low-contrast aesthetic photography",
        expected_irrelevant="Dark saturated garments or high-contrast neon images",
        expectation_on_current_db="reject_all",
    ),
    EvaluationCase(
        category="Descriptive",
        query="a beautiful outdoor photograph",
        expected_relevant="Outdoor landscapes, sunlight, nature scenery",
        expected_irrelevant="Indoor studio clothing screenshots",
        expectation_on_current_db="reject_all",
    ),
]


def legacy_search_images(query: str, images: list[dict], limit: int = 20) -> dict:
    """Reproduce the original single-prompt cosine >= 0.10 ranking for comparison."""
    query = query.strip()
    if not query or not images:
        return {"query": query, "total": 0, "results": []}

    query_embedding = np.array(
        embedding_service.generate_text_embedding(query),
        dtype=np.float32,
    )
    results = []
    for image in images:
        image_embedding = np.array(image["embedding"], dtype=np.float32)
        sim = float(
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
                "similarity": round(sim, 4),
            }
        )

    results.sort(key=lambda item: item["similarity"], reverse=True)
    results = [item for item in results if item["similarity"] >= LEGACY_THRESHOLD][:limit]
    return {"query": query, "total": len(results), "results": results}


def format_ranked(results: list[dict], include_level: bool) -> str:
    if not results:
        return "none"
    parts = []
    for item in results:
        if include_level:
            parts.append(
                f"{item['filename']} ({item['similarity']:.4f}, {item['match_level']})"
            )
        else:
            parts.append(f"{item['filename']} ({item['similarity']:.4f})")
    return " | ".join(parts)


def main() -> None:
    initialize_database()
    images = get_images_with_embeddings()

    print("=" * 88)
    print("ELOURA SEARCH QUALITY EVALUATION")
    print("=" * 88)
    print(f"Indexed images in SQLite: {len(images)}")
    for img in images:
        print(f"  - {img['filename']} ({img['stored_filename']})")

    if len(images) < 10:
        print(
            "\n[DATASET LIMITATION] The current database contains only "
            f"{len(images)} clothing images. Out-of-domain queries (scenes, flowers, cars, "
            "colorful/descriptive landscapes) can only verify correct rejection of unrelated "
            "clothing items here; positive recall on those categories requires adding matching images."
        )

    old_fp = 0
    new_fp = 0
    reject_cases = 0
    burgundy_wins_old = 0
    burgundy_wins_new = 0
    burgundy_cases = 0

    print("\n" + "-" * 88)
    for case in EVALUATION_CASES:
        old_res = legacy_search_images(case.query, images)
        new_res = search_images(case.query)

        if case.expectation_on_current_db == "reject_all":
            reject_cases += 1
            if old_res["total"] > 0:
                old_fp += 1
            if new_res["total"] > 0:
                new_fp += 1
        elif case.expectation_on_current_db == "prefer_burgundy":
            burgundy_cases += 1
            if old_res["results"] and "154314" in old_res["results"][0]["filename"]:
                burgundy_wins_old += 1
            if new_res["results"] and "154314" in new_res["results"][0]["filename"]:
                burgundy_wins_new += 1

        print(f"[{case.category}] Query: {case.query!r}")
        print(f"  Relevant target   : {case.expected_relevant}")
        print(f"  Irrelevant target : {case.expected_irrelevant}")
        print(
            f"  OLD (count={old_res['total']}): "
            f"{format_ranked(old_res['results'], include_level=False)}"
        )
        print(
            f"  NEW (count={new_res['total']}): "
            f"{format_ranked(new_res['results'], include_level=True)}"
        )
        print("-" * 88)

    print("\nSUMMARY AGAINST CURRENT DATABASE")
    print(f"  Out-of-domain rejection queries : {reject_cases}")
    print(f"  OLD false-positive queries      : {old_fp}/{reject_cases}")
    print(f"  NEW false-positive queries      : {new_fp}/{reject_cases}")
    print(
        f"  Burgundy-top #1 accuracy        : "
        f"OLD {burgundy_wins_old}/{burgundy_cases} | NEW {burgundy_wins_new}/{burgundy_cases}"
    )


if __name__ == "__main__":
    main()

