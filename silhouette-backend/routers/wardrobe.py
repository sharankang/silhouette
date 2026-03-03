from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime
from pathlib import Path
import json
import aiofiles
import uuid
import logging

from models.schemas import ClothingItem, ClothingTags, ClothingItemResponse
from services.embeddings import embed_image
from services.vision import auto_tag_image
import services.wardrobe_store as store
from config import settings

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])
logger = logging.getLogger(__name__)

IMAGE_STORE = Path(settings.image_store_path)
IMAGE_STORE.mkdir(parents=True, exist_ok=True)


@router.get("", response_model=ClothingItemResponse)
async def get_wardrobe(
    category: str = None,
    season:   str = None,
    occasion: str = None,
):
    items = store.get_all_items(
        category=category,
        season=season,
        occasion=occasion,
        active_only=True,
    )
    return ClothingItemResponse(items=items, total=len(items))


@router.post("", response_model=ClothingItem)
async def add_clothing_item(
    image: UploadFile = File(...),
    tags:  str        = Form("{}"),   # JSON string of ClothingTags
):

    # Validate file type
    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image.")

    # Save image
    item_id   = str(uuid.uuid4())
    ext       = Path(image.filename).suffix or ".jpg"
    filename  = f"{item_id}{ext}"
    file_path = IMAGE_STORE / filename

    contents = await image.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    # Parse tags
    try:
        tags_dict = json.loads(tags)
    except json.JSONDecodeError:
        tags_dict = {}

    # Embed image with CLIP
    try:
        embedding = embed_image(str(file_path))
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        file_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Failed to process image: {str(e)}")

    # Build item
    item = ClothingItem(
        id=item_id,
        image_url=f"/wardrobe/image/{filename}",
        image_path=str(file_path),
        name=tags_dict.get("name", ""),
        category=tags_dict.get("category", ""),
        season=tags_dict.get("season", "all-season"),
        occasions=tags_dict.get("occasions", []),
        styles=tags_dict.get("styles", []),
        colors=tags_dict.get("colors", []),
        date_added=datetime.utcnow().isoformat(),
        last_updated=datetime.utcnow().isoformat(),
    )

    # Store in ChromaDB
    store.add_item(item, embedding)

    logger.info(f"Added item: {item.name} ({item.category})")
    return item


@router.patch("/{item_id}", response_model=ClothingItem)
async def update_clothing_item(item_id: str, tags: ClothingTags):
    existing = store.get_item_by_id(item_id)
    if not existing:
        raise HTTPException(404, f"Item {item_id} not found.")

    updated = ClothingItem(
        id=item_id,
        image_url=existing.image_url,
        image_path=existing.image_path,
        name=tags.name or existing.name,
        category=tags.category or existing.category,
        season=tags.season or existing.season,
        occasions=tags.occasions if tags.occasions else existing.occasions,
        styles=tags.styles if tags.styles else existing.styles,
        colors=tags.colors if tags.colors else existing.colors,
        active=existing.active,
        date_added=existing.date_added,
        last_updated=datetime.utcnow().isoformat(),
    )

    store.update_item(updated)
    return updated


@router.delete("/{item_id}")
async def delete_clothing_item(item_id: str, hard: bool = False):
    # Default: soft delete (marks inactive, keeps in DB for 30 days)
    existing = store.get_item_by_id(item_id)
    if not existing:
        raise HTTPException(404, f"Item {item_id} not found.")

    if hard:
        store.delete_item(item_id)
        # Delete image file
        if existing.image_path:
            Path(existing.image_path).unlink(missing_ok=True)
    else:
        store.soft_delete_item(item_id)

    return {"deleted": item_id, "hard": hard}


@router.get("/image/{filename}")
async def serve_image(filename: str):
    """Serve clothing item images."""
    file_path = IMAGE_STORE / filename
    if not file_path.exists():
        raise HTTPException(404, "Image not found.")
    return FileResponse(str(file_path))


@router.post("/auto-tag")
async def auto_tag_preview(image: UploadFile = File(...)):
    if not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image.")

    # Save to temp location
    tmp_path = IMAGE_STORE / f"tmp_{uuid.uuid4()}.jpg"
    contents = await image.read()
    async with aiofiles.open(tmp_path, "wb") as f:
        await f.write(contents)

    try:
        tags = await auto_tag_image(str(tmp_path))
        return tags
    finally:
        tmp_path.unlink(missing_ok=True)
