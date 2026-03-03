from transformers import pipeline
from PIL import Image
import logging

logger = logging.getLogger(__name__)

_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        logger.info("Loading vision classifier...")
        _classifier = pipeline(
            "zero-shot-image-classification",
            model="openai/clip-vit-base-patch32",
        )
        logger.info("Vision classifier loaded.")
    return _classifier


# Label sets for zero-shot classification

CATEGORY_LABELS = [
    "a top or shirt or blouse or t-shirt",
    "pants or jeans or trousers or shorts",
    "a dress or skirt",
    "an outerwear jacket or coat or blazer",
    "shoes or boots or sneakers or heels",
    "accessories like a bag or belt or hat",
    "jewellery like a necklace or earrings or bracelet",
]

CATEGORY_MAP = {
    "a top or shirt or blouse or t-shirt": "tops",
    "pants or jeans or trousers or shorts": "bottoms",
    "a dress or skirt": "dresses",
    "an outerwear jacket or coat or blazer": "outerwear",
    "shoes or boots or sneakers or heels": "shoes",
    "accessories like a bag or belt or hat": "accessories",
    "jewellery like a necklace or earrings or bracelet": "jewellery",
}

STYLE_LABELS = [
    "minimalist clean simple clothing",
    "streetwear urban casual clothing",
    "bohemian free-spirited flowy clothing",
    "classic timeless elegant clothing",
    "romantic feminine soft clothing",
    "edgy bold statement clothing",
    "preppy polished collegiate clothing",
    "sporty athletic activewear clothing",
]

STYLE_MAP = {
    "minimalist clean simple clothing": "minimalist",
    "streetwear urban casual clothing": "streetwear",
    "bohemian free-spirited flowy clothing": "bohemian",
    "classic timeless elegant clothing": "classic",
    "romantic feminine soft clothing": "romantic",
    "edgy bold statement clothing": "edgy",
    "preppy polished collegiate clothing": "preppy",
    "sporty athletic activewear clothing": "sporty",
}

SEASON_LABELS = [
    "lightweight summer clothing",
    "warm winter clothing",
    "layered spring or autumn clothing",
    "all-season versatile clothing",
]

SEASON_MAP = {
    "lightweight summer clothing": "summer",
    "warm winter clothing": "winter",
    "layered spring or autumn clothing": "autumn",
    "all-season versatile clothing": "all-season",
}

COLOR_LABELS = [
    "black clothing", "white clothing", "grey clothing",
    "navy blue clothing", "blue clothing", "light blue clothing",
    "red clothing", "pink clothing", "burgundy clothing",
    "green clothing", "olive green clothing", "sage green clothing",
    "brown clothing", "camel tan clothing", "beige cream clothing",
    "yellow clothing", "orange clothing", "purple clothing",
    "gold silver metallic clothing", "multicolor pattern clothing",
]

COLOR_MAP = {
    "black clothing": "black", "white clothing": "white", "grey clothing": "grey",
    "navy blue clothing": "navy", "blue clothing": "blue", "light blue clothing": "light blue",
    "red clothing": "red", "pink clothing": "pink", "burgundy clothing": "burgundy",
    "green clothing": "green", "olive green clothing": "olive", "sage green clothing": "sage",
    "brown clothing": "brown", "camel tan clothing": "camel", "beige cream clothing": "cream",
    "yellow clothing": "yellow", "orange clothing": "orange", "purple clothing": "purple",
    "gold silver metallic clothing": "metallic", "multicolor pattern clothing": "multicolor",
}


# Auto-tagging

async def auto_tag_image(image_path: str) -> dict:
    try:
        clf = _get_classifier()
        image = Image.open(image_path).convert("RGB")

        # Category — always pick the top match, never leave blank
        cat_result = clf(image, candidate_labels=CATEGORY_LABELS)
        # Sort by score descending, pick best
        best_cat   = sorted(cat_result, key=lambda x: x["score"], reverse=True)[0]
        category   = CATEGORY_MAP.get(best_cat["label"], "tops")

        # Style
        style_result = clf(image, candidate_labels=STYLE_LABELS)
        styles = [
            STYLE_MAP[r["label"]]
            for r in style_result[:2]
            if r["score"] > 0.08
        ]

        # Season
        season_result = clf(image, candidate_labels=SEASON_LABELS)
        season = SEASON_MAP.get(season_result[0]["label"], "all-season")

        # Colors
        color_result = clf(image, candidate_labels=COLOR_LABELS)
        colors = [
            COLOR_MAP[r["label"]]
            for r in color_result[:2]
            if r["score"] > 0.06
        ]

        return {
            "category": category,
            "styles":   styles,
            "season":   season,
            "colors":   colors,
            "confidence": {
                "category": round(cat_result[0]["score"], 2),
                "season":   round(season_result[0]["score"], 2),
            }
        }

    except Exception as e:
        logger.warning(f"Auto-tagging failed for {image_path}: {e}")
        return {"category": "", "styles": [], "season": "all-season", "colors": []}