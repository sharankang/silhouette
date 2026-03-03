from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from PIL import Image
import io
import logging

from models.schemas import ChatResponse
from services.audio import transcribe_audio
from pipelines.outfit_generator import generate_outfit
from services.llm import call_fast
import services.wardrobe_store as store
from routers.outfits import save_outfit

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

#Jailbreak prevention

BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "you are now",
    "pretend you are",
    "act as if you",
    "forget your",
    "new persona",
    "disregard your",
    "override",
    "system prompt",
]


def check_jailbreak(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(pattern in lower for pattern in BLOCKED_PATTERNS)


# Topics that are clearly NOT fashion requests
OFF_TOPIC_SIGNALS = [
    "recipe", "cooking", "code", "programming", "math", "calculate",
    "weather", "news", "sports score", "translate", "write an essay",
    "homework", "explain quantum", "history of", "who invented",
    "stock price", "bitcoin", "medical advice", "diagnose",
]

def is_fashion_related(text: str) -> bool:
    if not text or len(text.split()) <= 4:
        return True  # short queries always pass
    lower = text.lower()
    return not any(signal in lower for signal in OFF_TOPIC_SIGNALS)


# Chat endpoint

@router.post("", response_model=ChatResponse)
async def chat(
    text:  Optional[str]        = Form(None),
    audio: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
):
    """
    Multimodal chat endpoint.
    Processes text + audio + image inputs, runs outfit generation pipeline.
    """
    # Step 1: Process audio if present
    audio_tone = "neu"
    audio_bias = {}
    final_text = text or ""

    if audio is not None:
        audio_bytes = await audio.read()
        if len(audio_bytes) > 100:  # ignore empty recordings
            try:
                audio_result = await transcribe_audio(audio_bytes)
                # Merge transcribed text with any typed text
                if audio_result["text"]:
                    if final_text:
                        final_text = f"{final_text}. {audio_result['text']}"
                    else:
                        final_text = audio_result["text"]
                audio_tone = audio_result.get("tone", "neu")
                audio_bias = audio_result.get("bias", {})
                logger.info(f"Audio transcribed: '{audio_result['text']}', tone: {audio_tone}")
            except Exception as e:
                logger.warning(f"Audio processing failed: {e}")

    # Step 2: Process inspo image if present
    inspo_image_pil = None
    if image is not None:
        try:
            image_bytes  = await image.read()
            inspo_image_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            logger.info("Inspo image received and opened.")
        except Exception as e:
            logger.warning(f"Failed to open inspo image: {e}")

    # Step 3: Validate input
    if not final_text and inspo_image_pil is None:
        raise HTTPException(400, "Please provide text, audio, or an inspiration image.")

    # Jailbreak check
    if check_jailbreak(final_text):
        return ChatResponse(
            message="I'm Silhouette, your personal stylist. I can only help you with outfit recommendations from your closet. What would you like to wear today?",
            outfit=None,
        )

    # Off-topic check (for text-heavy queries)
    if final_text and len(final_text.split()) > 5 and not is_fashion_related(final_text):
        return ChatResponse(
            message="I'm only able to help with styling and outfit recommendations! Tell me what you're in the mood to wear and I'll build something from your closet.",
            outfit=None,
        )

    # Step 4: Handle image-only input
    if not final_text and inspo_image_pil is not None:
        final_text = "Build me an outfit inspired by this image"

    # Step 5: Run outfit generation pipeline
    try:
        outfit = await generate_outfit(
            user_text=final_text,
            audio_tone=audio_tone,
            audio_bias=audio_bias,
            inspo_image_pil=inspo_image_pil,
        )

        if outfit is None or not outfit.items:
            wardrobe_count = store.count_items()
            if wardrobe_count == 0:
                msg = "Your closet is empty! Head to the Closet page and add some clothes first, then come back and I'll style you."
            else:
                msg = f"I couldn't find a complete outfit from your {wardrobe_count} items for that request. Try a different vibe, or add more items to your closet!"
            return ChatResponse(message=msg, outfit=None)

        # Persist to outfit history
        try:
            save_outfit(outfit)
        except Exception as e:
            logger.warning(f"Failed to save outfit to history: {e}")

        return ChatResponse(
            message=outfit.explanation,
            outfit=outfit,
        )

    except Exception as e:
        logger.error(f"Outfit generation failed: {e}", exc_info=True)
        raise HTTPException(500, "Something went wrong while generating your outfit. Please try again.")