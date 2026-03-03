import open_clip
import torch
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Singleton model loader

_model      = None
_preprocess = None
_tokenizer  = None


def _load_model():
    global _model, _preprocess, _tokenizer
    if _model is None:
        logger.info("Loading CLIP model (ViT-B-32)...")
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai"
        )
        _tokenizer = open_clip.get_tokenizer("ViT-B-32")
        _model.eval()
        logger.info("CLIP model loaded.")
    return _model, _preprocess, _tokenizer


# Public API

def embed_image(image_path: str) -> list[float]:
    model, preprocess, _ = _load_model()
    image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        features = model.encode_image(image)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.squeeze().tolist()


def embed_text(text: str) -> list[float]:
    model, _, tokenizer = _load_model()
    tokens = tokenizer([text])
    with torch.no_grad():
        features = model.encode_text(tokens)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.squeeze().tolist()


def embed_image_pil(pil_image: Image.Image) -> list[float]:
    model, preprocess, _ = _load_model()
    image = preprocess(pil_image.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        features = model.encode_image(image)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.squeeze().tolist()


def fuse_embeddings(
    text_embedding: list[float],
    image_embedding: list[float],
    text_weight: float = 0.4,
    image_weight: float = 0.6,
) -> list[float]:

    t = np.array(text_embedding)
    i = np.array(image_embedding)
    fused = (text_weight * t) + (image_weight * i)
    fused = fused / np.linalg.norm(fused)
    return fused.tolist()
