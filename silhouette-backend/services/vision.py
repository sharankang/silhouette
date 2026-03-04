import base64
import json
import logging
from pathlib import Path
from groq import Groq
from config import settings

logger = logging.getLogger(__name__)

_groq_client = None

def _get_client():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


VALID_CATEGORIES = ["tops", "bottoms", "dresses", "outerwear", "shoes", "accessories", "jewellery"]
VALID_SEASONS    = ["summer", "winter", "autumn", "spring", "all-season"]
VALID_OCCASIONS  = ["casual", "work", "party", "formal", "ethnic", "lounge", "outdoor", "date"]
VALID_STYLES     = ["minimalist", "streetwear", "bohemian", "classic", "romantic", "edgy",
                    "preppy", "sporty", "ethnic", "quiet-luxury", "smart-casual", "cottagecore"]

TAGGING_PROMPT = """You are an expert fashion stylist and wardrobe assistant.

Look at this clothing item carefully and return a JSON object with the following fields:

- name: a short descriptive name (2-5 words, e.g. "navy wide-leg trousers", "pink floral kurta", "brown leather crossbody bag", "white ribbed tank top"). Be specific about color, material if visible, and silhouette.
- category: one of exactly: tops, bottoms, dresses, outerwear, shoes, accessories, jewellery
- colors: list of 1-3 dominant colors as simple color words (e.g. ["navy", "white"] or ["brown"] or ["multicolor"])
- season: one of exactly: summer, winter, autumn, spring, all-season
- occasions: list of 1-3 from: casual, work, party, formal, ethnic, lounge, outdoor, date
- styles: list of 1-2 from: minimalist, streetwear, bohemian, classic, romantic, edgy, preppy, sporty, ethnic, quiet-luxury, smart-casual, cottagecore
- description: one sentence describing the item for a stylist (mention fabric if visible, fit, notable details)

Return ONLY valid JSON. No explanation, no markdown, no extra text.

Example:
{
  "name": "navy floral printed kurta",
  "category": "tops",
  "colors": ["navy", "multicolor"],
  "season": "all-season",
  "occasions": ["ethnic", "casual", "party"],
  "styles": ["ethnic", "bohemian"],
  "description": "A navy blue kurta with intricate floral embroidery, relaxed fit with three-quarter sleeves, suitable for ethnic occasions."
}"""


async def auto_tag_image(image_path: str) -> dict:
    try:
        image_bytes = Path(image_path).read_bytes()
        b64_image   = base64.b64encode(image_bytes).decode("utf-8")

        ext  = Path(image_path).suffix.lower()
        mime = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png",  ".webp": "image/webp",
        }.get(ext, "image/jpeg")

        client   = _get_client()
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type":      "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64_image}"},
                        },
                        {
                            "type": "text",
                            "text": TAGGING_PROMPT,
                        },
                    ],
                }
            ],
            max_tokens=400,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        tags = json.loads(raw)

        category = tags.get("category", "tops")
        if category not in VALID_CATEGORIES:
            category = "tops"

        season = tags.get("season", "all-season")
        if season not in VALID_SEASONS:
            season = "all-season"

        occasions = [o for o in tags.get("occasions", []) if o in VALID_OCCASIONS]
        styles    = [s for s in tags.get("styles",    []) if s in VALID_STYLES]
        colors    = tags.get("colors", [])
        name      = tags.get("name", "").strip()

        logger.info(f"Auto-tagged: {name} | {category} | {colors} | {occasions}")

        return {
            "name":        name,
            "category":    category,
            "colors":      colors,
            "season":      season,
            "occasions":   occasions,
            "styles":      styles,
            "description": tags.get("description", ""),
        }

    except json.JSONDecodeError as e:
        logger.warning(f"Groq vision returned invalid JSON for {image_path}: {e}")
        return _fallback()
    except Exception as e:
        logger.warning(f"Groq vision tagging failed for {image_path}: {e}")
        return _fallback()


def _fallback() -> dict:
    return {
        "name":      "",
        "category":  "",
        "colors":    [],
        "season":    "all-season",
        "occasions": [],
        "styles":    [],
        "description": "",
    }