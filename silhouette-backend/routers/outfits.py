from fastapi import APIRouter, HTTPException
from pathlib import Path
from datetime import datetime
from typing import List
import json
import uuid
import logging

from models.schemas import OutfitResult, OutfitItem, OutfitListResponse, RateOutfitRequest, ChatResponse
from pipelines.outfit_generator import generate_outfit

router = APIRouter(prefix="/outfits", tags=["outfits"])
logger = logging.getLogger(__name__)

OUTFITS_FILE = Path("./data/outfits.json")
OUTFITS_FILE.parent.mkdir(parents=True, exist_ok=True)

def _load_outfits() -> list[dict]:
    if not OUTFITS_FILE.exists():
        return []
    try:
        return json.loads(OUTFITS_FILE.read_text())
    except Exception:
        return []

def _save_outfits(outfits: list[dict]) -> None:
    OUTFITS_FILE.write_text(json.dumps(outfits, indent=2))

def save_outfit(outfit: OutfitResult) -> None:
    
    outfits = _load_outfits()
    outfits.insert(0, outfit.model_dump()) 
    _save_outfits(outfits)

@router.post("/manual", response_model=OutfitResult)
async def save_manual_outfit(body: dict):
    items_data = body.get("items", [])
    if len(items_data) < 2:
        raise HTTPException(400, "Select at least 2 items to save an outfit.")

    items = [OutfitItem(**i) for i in items_data]
    outfit = OutfitResult(
        id=str(uuid.uuid4()),
        items=items,
        explanation="Manually styled look.",
        query_text="manual",
        created_at=datetime.utcnow().isoformat(),
    )
    save_outfit(outfit)
    return outfit


@router.get("", response_model=OutfitListResponse)
async def get_outfits():
    
    outfits_data = _load_outfits()
    outfits = [OutfitResult(**o) for o in outfits_data]
    return OutfitListResponse(outfits=outfits, total=len(outfits))

@router.patch("/{outfit_id}/rate")
async def rate_outfit(outfit_id: str, body: RateOutfitRequest):
    
    outfits = _load_outfits()
    updated = False

    for outfit in outfits:
        if outfit["id"] == outfit_id:
            outfit["rating"] = body.rating
            outfit["rated_at"] = datetime.utcnow().isoformat()
            updated = True
            break

    if not updated:
        raise HTTPException(404, f"Outfit {outfit_id} not found.")

    _save_outfits(outfits)
    logger.info(f"Rated outfit {outfit_id}: {body.rating}/5")
    return {"id": outfit_id, "rating": body.rating}

@router.delete("/{outfit_id}")
async def delete_outfit(outfit_id: str):
    
    outfits = _load_outfits()
    filtered = [o for o in outfits if o["id"] != outfit_id]

    if len(filtered) == len(outfits):
        raise HTTPException(404, f"Outfit {outfit_id} not found.")

    _save_outfits(filtered)
    return {"deleted": outfit_id}

@router.post("/{outfit_id}/regenerate", response_model=ChatResponse)
async def regenerate_outfit(outfit_id: str):
    
    outfits = _load_outfits()
    original = next((o for o in outfits if o["id"] == outfit_id), None)

    if not original:
        raise HTTPException(404, f"Outfit {outfit_id} not found.")

    query_text = original.get("query_text", "generate a new outfit")

    outfit = await generate_outfit(user_text=query_text)

    if outfit is None:
        raise HTTPException(500, "Could not regenerate outfit.")

    save_outfit(outfit)

    return ChatResponse(message=outfit.explanation, outfit=outfit)