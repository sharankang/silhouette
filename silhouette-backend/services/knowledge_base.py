import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
import logging
from config import settings
from services.embeddings import embed_text

logger = logging.getLogger(__name__)

_client     = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name="fashion_knowledge",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _get_splitter(doc_type: str) -> RecursiveCharacterTextSplitter:
    strategies = {
        "color_theory":   dict(chunk_size=300, chunk_overlap=50),
        "style_guide":    dict(chunk_size=600, chunk_overlap=100),
        "occasion_rules": dict(chunk_size=400, chunk_overlap=80),
        "seasonal_rules": dict(chunk_size=400, chunk_overlap=80),
        "default":        dict(chunk_size=500, chunk_overlap=75),
    }
    cfg = strategies.get(doc_type, strategies["default"])
    return RecursiveCharacterTextSplitter(
        chunk_size=cfg["chunk_size"],
        chunk_overlap=cfg["chunk_overlap"],
        separators=["\n\n", "\n", ". ", " "],
    )


def ingest_knowledge_base():
    col     = _get_collection()
    kb_path = Path(settings.knowledge_base_path)

    if not kb_path.exists():
        _seed_default_knowledge()
        return

    files = list(kb_path.glob("*.txt")) + list(kb_path.glob("*.md"))
    if not files:
        logger.info("No knowledge base files found. Seeding defaults.")
        _seed_default_knowledge()
        return

    doc_count = 0
    for file_path in files:
        doc_type = _infer_doc_type(file_path.stem)
        splitter = _get_splitter(doc_type)
        chunks   = splitter.split_text(file_path.read_text(encoding="utf-8"))

        for i, chunk in enumerate(chunks):
            chunk_id = f"{file_path.stem}_{i}"
            if col.get(ids=[chunk_id])["ids"]:
                continue
            col.add(
                ids=[chunk_id],
                embeddings=[embed_text(chunk)],
                documents=[chunk],
                metadatas=[{"source": file_path.stem, "doc_type": doc_type, "chunk_idx": i}],
            )
            doc_count += 1

    logger.info(f"Knowledge base ingested: {doc_count} new chunks.")


def retrieve_fashion_rules(
    query: str,
    query_embedding: list[float] = None,
    n_results: int = 5,
    doc_type_filter: str = None,
) -> list[str]:
    col = _get_collection()
    if col.count() == 0:
        return []

    if query_embedding is None:
        query_embedding = embed_text(query)

    kwargs = dict(
        query_embeddings=[query_embedding],
        n_results=min(n_results, col.count()),
        include=["documents", "metadatas"],
    )
    if doc_type_filter:
        kwargs["where"] = {"doc_type": {"$eq": doc_type_filter}}

    results = col.query(**kwargs)
    return results["documents"][0] if results["documents"] else []


def _seed_default_knowledge():
    col = _get_collection()

    default_docs = [
        {
            "id": "color_theory_neutrals",
            "text": "Neutral colors — black, white, grey, beige, cream, camel, and navy — form the backbone of any wardrobe. They pair effortlessly with each other and with any accent color. Building outfits around a neutral base with one accent color is the most reliable approach to looking put-together.",
            "type": "color_theory"
        },
        {
            "id": "color_theory_complementary",
            "text": "Complementary color pairs create visual impact: navy and rust/terracotta, olive green and burgundy, camel and deep blue, grey and blush pink. These combinations feel intentional rather than accidental. Use one color as dominant (70%), the other as accent (30%).",
            "type": "color_theory"
        },
        {
            "id": "color_theory_clashes",
            "text": "Color combinations to avoid: mixing warm and cool tones of the same hue (warm red with cool pink), navy and black together (looks like a mistake unless deliberate), more than three distinct colors in one outfit. When in doubt, stick to one color family plus one neutral.",
            "type": "color_theory"
        },
        {
            "id": "color_theory_monochrome",
            "text": "Monochromatic outfits — wearing different shades of the same color — look sophisticated and elongate the silhouette. Pair a camel blazer with cream trousers and a tan top for a tonal look. Add texture variation (silk with wool, matte with shine) to prevent it from looking flat.",
            "type": "color_theory"
        },
        {
            "id": "style_guide_minimalist",
            "text": "Minimalist style: clean lines, neutral palette, no excessive embellishment. Key pieces: well-fitted trousers, crisp white shirts, simple knitwear, quality basics. The fit must be excellent — minimalism has nowhere to hide poor tailoring. Accessories should be sparse and geometric.",
            "type": "style_guide"
        },
        {
            "id": "style_guide_smart_casual",
            "text": "Smart casual bridges formal and relaxed. Combine one elevated piece (blazer, tailored trousers, quality leather shoes) with one casual piece (clean white tee, dark jeans, simple knit). Never pair two casual pieces or two formal pieces — one of each maintains the balance.",
            "type": "style_guide"
        },
        {
            "id": "style_guide_streetwear",
            "text": "Streetwear: oversized silhouettes, graphic elements, athletic influences, premium sneakers. Key to looking intentional rather than sloppy: proportion contrast (oversized top with fitted bottom or vice versa), clean footwear, minimal jewelry that feels earned rather than decorative.",
            "type": "style_guide"
        },
        {
            "id": "style_guide_quiet_luxury",
            "text": "Quiet luxury (also called old money aesthetic): understated quality, no visible logos, neutral palette dominated by camel, cream, white, navy, and forest green. Fabrics matter more than cuts — cashmere, silk, fine wool. Accessories are minimal, gold-toned, and look expensive without being flashy.",
            "type": "style_guide"
        },
        {
            "id": "occasion_casual_daily",
            "text": "Everyday casual: prioritize comfort without sacrificing intention. Dark wash jeans or clean chinos as the base. Layer with a simple tee or lightweight knit. White sneakers or clean loafers keep it looking composed. Avoid graphic tees with graphic bottoms — one statement piece at a time.",
            "type": "occasion_rules"
        },
        {
            "id": "occasion_work",
            "text": "Work/office appropriate dressing: bottoms should be tailored (trousers, midi skirts, well-fitted chinos). Tops should be tucked or structured. Avoid exposed midriff, overly casual graphics, or athletic wear. Blazers instantly elevate any outfit to office-appropriate. Shoes should be closed-toe or smart sandals.",
            "type": "occasion_rules"
        },
        {
            "id": "occasion_dinner_date",
            "text": "Dinner or date outfit: elevate your usual style by one notch. If you wear jeans daily, opt for your best dark jeans or switch to trousers. Add one statement piece — interesting earrings, a silk blouse, or a good coat. Avoid trying an entirely new style; wear a more polished version of what you feel confident in.",
            "type": "occasion_rules"
        },
        {
            "id": "seasonal_summer",
            "text": "Summer dressing: prioritize breathable fabrics (linen, cotton, light silk). Lighter colors reflect heat. Loose silhouettes allow airflow. Sandals and minimal footwear. Avoid heavyweight fabrics, dark colors in direct sun, and heavy layers. Linen blazers work for elevated summer looks.",
            "type": "seasonal_rules"
        },
        {
            "id": "seasonal_autumn",
            "text": "Autumn layering: build outfits in three layers — base (fitted tee or thin knit), mid (shirt, overshirt, or light sweater), outer (coat or jacket). Earth tones — rust, olive, mustard, burgundy, camel — are seasonally appropriate. Ankle boots and loafers anchor autumn outfits.",
            "type": "seasonal_rules"
        },
        {
            "id": "seasonal_winter",
            "text": "Winter dressing: warmth without bulk through smart layering. A thin thermal base layer means your outer layers can remain slim and fitted. Coats are the focal point — invest in one quality coat that works with your wardrobe. Knits add texture and warmth. Dark washes and deep colors feel seasonally right.",
            "type": "seasonal_rules"
        },
        {
            "id": "seasonal_spring",
            "text": "Spring transitional dressing: the challenge is unpredictable temperatures. Lightweight layers that can be removed — a denim jacket, a light blazer, a cardigan. Pastels and fresh whites feel seasonally right. White trainers re-enter the rotation. Lighter fabrics but not yet full summer weight.",
            "type": "seasonal_rules"
        },
        {
            "id": "proportion_rules",
            "text": "Proportion is the most important element in outfit building. Balance volume: oversized top with slim-fit bottom, fitted top with wide-leg trousers. Avoid wearing two oversized or two very fitted pieces together — it loses shape. The 60-30-10 rule: 60% dominant color, 30% secondary, 10% accent.",
            "type": "style_guide"
        },
        {
            "id": "shoes_rule",
            "text": "Shoes set the register of the entire outfit. Clean white sneakers make almost anything look casual and contemporary. Loafers dress up casual pieces. Heels or smart flats elevate denim to dinner-appropriate. Always match shoe formality to the most formal piece in your outfit, not the least formal.",
            "type": "style_guide"
        },
    ]

    for doc in default_docs:
        if col.get(ids=[doc["id"]])["ids"]:
            continue
        col.add(
            ids=[doc["id"]],
            embeddings=[embed_text(doc["text"])],
            documents=[doc["text"]],
            metadatas=[{"source": "default", "doc_type": doc["type"], "chunk_idx": 0}],
        )

    logger.info(f"Seeded {len(default_docs)} default knowledge base documents.")


def _infer_doc_type(filename: str) -> str:
    filename = filename.lower()
    if "color"   in filename: return "color_theory"
    if "style"   in filename: return "style_guide"
    if "occasion" in filename: return "occasion_rules"
    if "season"  in filename: return "seasonal_rules"
    return "default"