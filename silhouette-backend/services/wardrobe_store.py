import chromadb
from chromadb.config import Settings as ChromaSettings
from datetime import datetime
import logging
from config import settings
from models.schemas import ClothingItem

logger = logging.getLogger(__name__)

# ChromaDB client

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
            name="wardrobe",
            metadata={"hnsw:space": "cosine"},  # cosine similarity
        )
        logger.info(f"ChromaDB collection loaded — {_collection.count()} items.")
    return _collection


def add_item(item: ClothingItem, embedding: list[float]) -> None:
    col = _get_collection()
    col.add(
        ids=[item.id],
        embeddings=[embedding],
        documents=[_item_to_document(item)],   # text doc for BM25 fallback
        metadatas=[_item_to_metadata(item)],
    )
    logger.info(f"Added item {item.id} ({item.name}) to wardrobe.")


def update_item(item: ClothingItem, new_embedding: list[float] = None) -> None:
    col = _get_collection()
    # Get existing embedding if not re-embedding
    if new_embedding is None:
        existing = col.get(ids=[item.id], include=["embeddings"])
        new_embedding = existing["embeddings"][0]
    col.delete(ids=[item.id])
    col.add(
        ids=[item.id],
        embeddings=[new_embedding],
        documents=[_item_to_document(item)],
        metadatas=[_item_to_metadata(item)],
    )
    logger.info(f"Updated item {item.id}.")


def delete_item(item_id: str) -> None:
    _get_collection().delete(ids=[item_id])
    logger.info(f"Deleted item {item_id}.")


def soft_delete_item(item_id: str) -> None:
    col = _get_collection()
    existing = col.get(ids=[item_id], include=["embeddings", "metadatas", "documents"])
    if not existing["ids"]:
        return
    meta = existing["metadatas"][0]
    meta["active"] = "false"
    col.update(ids=[item_id], metadatas=[meta])


def get_all_items(
    category: str = None,
    season:   str = None,
    occasion: str = None,
    active_only: bool = True,
) -> list[ClothingItem]:
    col  = _get_collection()
    where = _build_where_filter(category, season, occasion, active_only)

    kwargs = {"include": ["metadatas", "documents"]}
    if where:
        kwargs["where"] = where

    results = col.get(**kwargs)
    return [_metadata_to_item(m, id_) for m, id_ in zip(results["metadatas"], results["ids"])]


def similarity_search(
    query_embedding: list[float],
    n_results: int = 20,
    category: str = None,
    season:   str = None,
    occasion: str = None,
    active_only: bool = True,
) -> list[tuple[ClothingItem, float]]:
    col  = _get_collection()
    where = _build_where_filter(category, season, occasion, active_only)

    kwargs = dict(
        query_embeddings=[query_embedding],
        n_results=min(n_results, max(col.count(), 1)),
        include=["metadatas", "distances", "documents"],
    )
    if where:
        kwargs["where"] = where

    results = col.query(**kwargs)

    items_with_scores = []
    for meta, dist, id_ in zip(
        results["metadatas"][0],
        results["distances"][0],
        results["ids"][0],
    ):
        item  = _metadata_to_item(meta, id_)
        score = 1 - dist  # cosine similarity
        items_with_scores.append((item, score))

    return items_with_scores


def get_item_by_id(item_id: str) -> ClothingItem | None:
    col = _get_collection()
    result = col.get(ids=[item_id], include=["metadatas"])
    if not result["ids"]:
        return None
    return _metadata_to_item(result["metadatas"][0], item_id)


def count_items() -> int:
    return _get_collection().count()


# Helpers
def _build_where_filter(category, season, occasion, active_only):
    conditions = []
    if active_only:
        conditions.append({"active": {"$eq": "true"}})
    if category:
        conditions.append({"category": {"$eq": category}})
    if season and season != "all-season":
        conditions.append({"$or": [
            {"season": {"$eq": season}},
            {"season": {"$eq": "all-season"}},
        ]})
    if occasion:
        conditions.append({"occasions": {"$contains": occasion}})

    if len(conditions) == 0:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def _item_to_document(item: ClothingItem) -> str:
    parts = [
        item.name,
        item.category,
        item.season,
        " ".join(item.occasions),
        " ".join(item.styles),
        " ".join(item.colors),
        item.description,
    ]
    return " ".join(p for p in parts if p).lower()


def _item_to_metadata(item: ClothingItem) -> dict:
    return {
        "name":         item.name,
        "category":     item.category,
        "season":       item.season,
        "occasions":    " ".join(item.occasions),
        "styles":       " ".join(item.styles),
        "colors":       " ".join(item.colors),
        "description":  item.description,
        "image_url":    item.image_url,
        "image_path":   item.image_path,
        "active":       "true" if item.active else "false",
        "date_added":   item.date_added,
        "last_updated": item.last_updated,
    }


def _metadata_to_item(meta: dict, item_id: str) -> ClothingItem:
    return ClothingItem(
        id=item_id,
        name=meta.get("name", ""),
        category=meta.get("category", ""),
        season=meta.get("season", "all-season"),
        occasions=meta.get("occasions", "").split() if meta.get("occasions") else [],
        styles=meta.get("styles", "").split() if meta.get("styles") else [],
        colors=meta.get("colors", "").split() if meta.get("colors") else [],
        description=meta.get("description", ""),
        image_url=meta.get("image_url", ""),
        image_path=meta.get("image_path", ""),
        active=meta.get("active", "true") == "true",
        date_added=meta.get("date_added", ""),
        last_updated=meta.get("last_updated", ""),
    )