from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
from PIL import Image
import io
import json
import logging

from models.schemas import ChatResponse
from services.audio import transcribe_audio
from pipelines.outfit_generator import generate_outfit, _detect_outfit_edit_intent, swap_outfit_item
from services.llm import call_fast
import services.wardrobe_store as store
from routers.outfits import save_outfit, _load_outfits

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


NON_ACTIONABLE = {
    "i", "hi", "hey", "hello", "ok", "okay", "yes", "no", "sure", "hmm",
    "lol", "haha", "what", "why", "how", "test", "?", "...", "help",
}

def is_meaningful_style_request(text: str) -> bool:
    if not text:
        return True
    stripped = text.strip().lower()
    if stripped in NON_ACTIONABLE:
        return False
    if len(stripped) < 3:
        return False
    return True

def is_fashion_related(text: str) -> bool:
    if not text or len(text.split()) <= 4:
        return True
    prompt = (
        f'Is this message related to fashion, clothing, styling, outfits, or personal appearance? '
        f'Message: "{text}\n Reply with only YES or NO.'
    )
    try:
        result = call_fast(prompt).strip().upper()
        return result.startswith("YES")
    except Exception:
        return True

# Styling questions
STYLING_QUESTIONS = [
    "what jewelry", "which jewelry", "what accessories", "which accessories",
    "what shoes", "which shoes", "what bag", "which bag",
    "what should i wear with", "what goes with", "what matches",
    "how should i style", "how do i style", "can i wear",
    "what color goes", "does this work with",
]

def is_styling_question(text: str) -> bool:
    lower = text.strip().lower()
    return any(q in lower for q in STYLING_QUESTIONS)
    if not text or len(text.split()) <= 4:
        return True  # short queries always pass
    lower = text.lower()
    return not any(signal in lower for signal in OFF_TOPIC_SIGNALS)


# Chat endpoint
@router.post("", response_model=ChatResponse)
async def chat(
    text:    Optional[str]        = Form(None),
    audio:   Optional[UploadFile] = File(None),
    image:   Optional[UploadFile] = File(None),
    history: Optional[str]        = Form(None),
):
    # Step 1: Process audio if present
    audio_tone = "neu"
    audio_bias = {}
    final_text = text or ""

    if audio is not None:
        audio_bytes = await audio.read()
        if len(audio_bytes) > 100:  # ignore empty recordings
            try:
                audio_result = await transcribe_audio(audio_bytes)
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

    _early_history = []
    if history:
        try:
            _early_history = json.loads(history)[-6:]
        except Exception:
            pass

    _early_edit = _detect_outfit_edit_intent(final_text) if final_text else {"action": "none", "category": None}
    _is_edit = _early_edit["action"] != "none" and _early_edit["category"] is not None

    if not _is_edit and not is_meaningful_style_request(final_text) and inspo_image_pil is None:
        return ChatResponse(
            message="Tell me how you're feeling today, what you're dressing for, or just a vibe — and I'll put together something from your closet.",
            outfit=None,
        )

    if not _is_edit and final_text and len(final_text.split()) > 5 and not is_fashion_related(final_text):
        return ChatResponse(
            message="I'm only able to help with styling and outfit recommendations! Tell me what you're in the mood to wear and I'll build something from your closet.",
            outfit=None,
        )

    # Step 4: Handle image-only input
    if not final_text and inspo_image_pil is not None:
        final_text = "Build me an outfit inspired by this image"

    # Styling question
    if not _is_edit and is_styling_question(final_text) and inspo_image_pil is None:
        context = ""
        if history:
            try:
                recent = json.loads(history)[-4:]
                outfit_items = next(
                    (msg.get("outfit", {}).get("items", [])
                     for msg in reversed(recent)
                     if msg.get("outfit")),
                    []
                )
                if outfit_items:
                    item_names = ", ".join(i.get("name", i.get("category", "")) for i in outfit_items)
                    context = f"The user's current outfit includes: {item_names}. "
            except Exception:
                pass
        advice = call_fast(
            f"{context}The user asks: \"{final_text}\". "
            "Give a concise, friendly styling tip in 2-3 sentences. "
            "Only recommend items they might already own — do not invent specific products."
        )
        return ChatResponse(message=advice, outfit=None)

    # Step 5: Run outfit generation pipeline
    try:
        conversation_history = _early_history
        edit_action   = _early_edit["action"]
        edit_category = _early_edit["category"]

        last_outfit = next(
            (msg.get("outfit") for msg in reversed(conversation_history)
             if msg.get("role") == "assistant" and msg.get("outfit")),
            None,
        ) if conversation_history else None

        logger.info(f"Edit intent — action: {edit_action}, category: {edit_category}, last_outfit: {last_outfit is not None}")

        if edit_action != "none" and edit_category and not last_outfit:
            return ChatResponse(
                message="I don't have an outfit to edit yet! Generate one first, then I can swap, add, or remove pieces.",
                outfit=None,
            )

        if edit_action != "none" and edit_category and last_outfit:
            edit_hints = ["change","swap","replace","different","another","other",
                          "don't like","dont like","hate","switch","add","include",
                          "only","keep","just the","love the","like the","remove","take off"]
            style_context = final_text
            for msg in reversed(conversation_history):
                if msg.get("role") != "user":
                    continue
                msg_lower = msg.get("text", "").lower()
                if not any(h in msg_lower for h in edit_hints):
                    style_context = msg.get("text", final_text)
                    break
            try:
                current_items = last_outfit.get("items", [])

                if edit_action == "add":
                    existing_ids = {i.get("id") for i in current_items}
                    from services.embeddings import embed_text
                    from services.retrieval import hybrid_search
                    from pipelines.outfit_generator import _make_outfit_item
                    from models.schemas import OutfitItem, OutfitResult
                    import uuid as _uuid
                    from datetime import datetime as _dt
                    from services.llm import call_smart as _cs

                    query_emb = embed_text(f"{style_context} {edit_category}")
                    results = hybrid_search(
                        query_embedding=query_emb,
                        query_text=f"{style_context} {edit_category}",
                        category_filter=edit_category,
                        top_k=15,
                    )
                    new_piece = None
                    for r in results:
                        if r.item.id not in existing_ids:
                            new_piece = _make_outfit_item(r.item)
                            break

                    if new_piece:
                        kept = [OutfitItem(**i) if isinstance(i, dict) else i for i in current_items]
                        final_items = kept + [new_piece]
                        items_list = "\n".join(f"- {i.name or i.category} ({i.category})" for i in final_items)
                        explanation = _cs(
                            f"You are Silhouette, a personal AI stylist.\n"
                            f"The user added a {edit_category} to their outfit. Final items:\n{items_list}\n"
                            f"Write a warm 2-sentence note about the completed look. Mention only these items."
                        )
                        outfit = OutfitResult(
                            id=str(_uuid.uuid4()),
                            items=final_items,
                            explanation=explanation,
                            query_text=style_context,
                            created_at=_dt.utcnow().isoformat(),
                        )
                    else:
                        return ChatResponse(
                            message=f"I couldn't find a {edit_category} in your closet to add. Try uploading one first!",
                            outfit=None,
                        )

                elif edit_action == "keep_only":
                    kept_items = [i for i in current_items if i.get("category") == edit_category]
                    reject_cats = list({i.get("category") for i in current_items} - {edit_category})
                    outfit = await swap_outfit_item(
                        current_items=kept_items,
                        reject_category=reject_cats,
                        style_context=style_context,
                    )
                else:
                    rejected_ids = {i.get("id") for i in current_items if i.get("category") == edit_category}
                    outfit = await swap_outfit_item(
                        current_items=current_items,
                        reject_category=[edit_category],
                        style_context=style_context,
                        rejected_ids=rejected_ids,
                    )

                try:
                    save_outfit(outfit)
                except Exception:
                    pass
                return ChatResponse(message=outfit.explanation, outfit=outfit)
            except Exception as e:
                logger.warning(f"Outfit edit failed, falling back to full generation: {e}", exc_info=True)

        recently_used_ids = set()
        try:
            recent_outfits = _load_outfits()[:3]
            for o in recent_outfits:
                for item in o.get("items", []):
                    recently_used_ids.add(item.get("id", ""))
        except Exception:
            pass

        outfit = await generate_outfit(
            user_text=final_text,
            audio_tone=audio_tone,
            audio_bias=audio_bias,
            inspo_image_pil=inspo_image_pil,
            conversation_history=conversation_history,
            recently_used_ids=recently_used_ids,
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