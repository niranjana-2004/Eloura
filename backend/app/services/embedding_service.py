
import re

import numpy as np
import open_clip
import torch
from PIL import Image

_PHOTO_FRAME_WORDS = {"photo", "photograph", "picture", "image", "snapshot", "shot"}
_LEADING_PHOTO_PREFIX = re.compile(
    r"^(?:a|an)\s+(?:photo|photograph|picture|image)\s+(?:of|with|showing)\s+",
    re.IGNORECASE,
)


def build_query_prompts(query: str) -> list[tuple[str, float]]:
    """Build a compact, deterministic prompt ensemble with the raw query as primary signal."""
    clean_query = " ".join(query.strip().split())
    if not clean_query:
        return []

    prompts: list[tuple[str, float]] = [(clean_query, 2.0)]
    lower = clean_query.lower()
    words = lower.split()
    has_photo_word = bool(_PHOTO_FRAME_WORDS & set(words))

    if has_photo_word:
        core = _LEADING_PHOTO_PREFIX.sub("", clean_query).strip()
        if core and core.lower() != lower:
            prompts.append((core, 0.9))
            prompts.append((f"a photograph of {core}", 0.7))
        elif "photograph" in words:
            prompts.append(
                (re.sub(r"\bphotograph\b", "photo", clean_query, flags=re.IGNORECASE), 0.9)
            )
        elif "photo" in words:
            prompts.append(
                (re.sub(r"\bphoto\b", "photograph", clean_query, flags=re.IGNORECASE), 0.8)
            )
    elif lower.startswith("something ") and len(words) >= 2:
        core = clean_query[len("something "):].strip()
        if core.lower().startswith("with "):
            prompts.append((f"a photo {core}", 1.1))
            prompts.append((f"a photograph {core}", 0.8))
        else:
            prompts.append((f"a {core} photo", 1.1))
            prompts.append((f"a photo of a {core} scene", 0.8))
    elif len(words) <= 10:
        prompts.append((f"a photo of {clean_query}", 1.1))
        prompts.append((f"a photograph of {clean_query}", 0.8))
    else:
        prompts.append((f"a photo of {clean_query}", 0.9))

    deduped: list[tuple[str, float]] = []
    seen: set[str] = set()
    for prompt_text, weight in prompts:
        key = prompt_text.lower()
        if key not in seen:
            seen.add(key)
            deduped.append((prompt_text, weight))

    return deduped


class EmbeddingService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32",
            pretrained="laion2b_s34b_b79k",
        )

        self.model = self.model.to(self.device)
        self.model.eval()

        self.tokenizer = open_clip.get_tokenizer("ViT-B-32")

    def generate_image_embedding(self, image_path: str) -> list[float]:
        image = Image.open(image_path).convert("RGB")
        image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self.model.encode_image(image_tensor)
            features = features / features.norm(dim=-1, keepdim=True).clamp(min=1e-12)

        return features[0].cpu().tolist()

    def generate_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Encode and L2-normalize multiple text prompts in a single model pass."""
        if not texts:
            return []

        tokens = self.tokenizer(texts).to(self.device)

        with torch.no_grad():
            features = self.model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True).clamp(min=1e-12)

        return features.cpu().tolist()

    def generate_text_embedding(self, text: str) -> list[float]:
        return self.generate_text_embeddings([text])[0]

    def generate_query_embedding(self, query: str) -> list[float]:
        """Generate a normalized weighted ensemble embedding for a search query."""
        prompt_weights = build_query_prompts(query)
        if not prompt_weights:
            raise ValueError("Query must not be empty.")

        prompts = [prompt for prompt, _ in prompt_weights]
        weights = np.array([weight for _, weight in prompt_weights], dtype=np.float32)

        embeddings = np.array(self.generate_text_embeddings(prompts), dtype=np.float32)
        combined = np.sum(embeddings * weights[:, None], axis=0)
        norm = float(np.linalg.norm(combined))
        if norm > 1e-12:
            combined = combined / norm

        return combined.tolist()


embedding_service = EmbeddingService()
