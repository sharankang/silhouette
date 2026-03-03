from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


# Clothing Item
class ClothingTags(BaseModel):
    name:      str       = ""
    category:  str       = ""
    season:    str       = "all-season"
    occasions: list[str] = []
    styles:    list[str] = []
    colors:    list[str] = []


class ClothingItem(BaseModel):
    id:           str       = Field(default_factory=lambda: str(uuid.uuid4()))
    image_url:    str       = ""
    image_path:   str       = ""
    name:         str       = ""
    category:     str       = ""
    season:       str       = "all-season"
    occasions:    list[str] = []
    styles:       list[str] = []
    colors:       list[str] = []
    active:       bool      = True
    date_added:   str       = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str       = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ClothingItemResponse(BaseModel):
    items: list[ClothingItem]
    total: int


# Chat
class OutfitItem(BaseModel):
    id:        str
    name:      str
    category:  str
    image_url: str       = ""
    colors:    list[str] = []


class OutfitResult(BaseModel):
    id:          str            = Field(default_factory=lambda: str(uuid.uuid4()))
    items:       list[OutfitItem]
    explanation: str
    query_text:  Optional[str] = None
    rating:      Optional[int] = None
    created_at:  str            = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ChatResponse(BaseModel):
    message: str
    outfit:  Optional[OutfitResult] = None


# Outfit History
class OutfitListResponse(BaseModel):
    outfits: list[OutfitResult]
    total:   int


class RateOutfitRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)


# Retrieval
class RetrievedItem(BaseModel):
    item:  ClothingItem
    score: float
