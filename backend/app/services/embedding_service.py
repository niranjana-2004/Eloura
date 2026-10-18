
import open_clip
import torch
from PIL import Image


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
            features /= features.norm(dim=-1, keepdim=True)

        return features[0].cpu().tolist()

    def generate_text_embedding(self, text: str) -> list[float]:
        tokens = self.tokenizer([text]).to(self.device)

        with torch.no_grad():
            features = self.model.encode_text(tokens)
            features /= features.norm(dim=-1, keepdim=True)

        embedding = features[0].cpu().tolist()
        print("TEXT EMBEDDING SAMPLE:", embedding[:5])

        return embedding


embedding_service = EmbeddingService()
