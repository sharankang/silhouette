from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio

from routers import wardrobe, chat, outfits
from services.knowledge_base import ingest_knowledge_base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Silhouette API",
    description="AI-powered personal stylist backend",
    version="1.0.0",
)

# Allow requests from the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wardrobe.router)
app.include_router(chat.router)
app.include_router(outfits.router)


@app.on_event("startup")
async def startup():
    logger.info("Silhouette backend starting...")
    # Ingest fashion knowledge base (only runs if collection is empty)
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, ingest_knowledge_base)
        logger.info("Knowledge base ready.")
    except Exception as e:
        logger.warning(f"Knowledge base ingestion failed (non-fatal): {e}")
    logger.info("Silhouette backend ready.")


@app.get("/health")
async def health():
    from services import wardrobe_store as store
    return {
        "status":        "ok",
        "wardrobe_items": store.count_items(),
    }


@app.get("/")
async def root():
    return {"message": "Silhouette API", "docs": "/docs"}
