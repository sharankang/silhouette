from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
import json
import logging
from datetime import datetime
import uuid
import random

from models.schemas import ClothingItem, OutfitItem, OutfitResult
from services.embeddings import embed_text, embed_image_pil, fuse_embeddings
from services.retrieval import expand_query, generate_hyde_description, hybrid_search
from services.knowledge_base import retrieve_fashion_rules
from services import wardrobe_store as store
from services.llm import call_fast, call_smart

logger = logging.getLogger(__name__)


class OutfitState(TypedDict):
    user_text:          str
    audio_tone:         str
    audio_bias:         dict
    inspo_image_pil:    Optional[object]
    mood:               str
    occasion:           str
    season:             str
    expanded_queries:   list[str]
    hyde_description:   str
    query_embedding:    list[float]
    candidate_items:    list[ClothingItem]
    fashion_rules:      list[str]
    selected_items:     list[OutfitItem]
    missing_categories: list[str]
    retry_count:        int
    explanation:        str
    outfit_result:      Optional[OutfitResult]
    error:              Optional[str]


def parse_intent(state: OutfitState) -> OutfitState:
    user_text  = state["user_text"] or ""
    audio_bias = state.get("audio_bias", {})

    prompt = f"""Extract outfit intent from this request. Return ONLY valid JSON.

User request: "{user_text}"
Audio tone bias (if voice input was detected as emotional): {json.dumps(audio_bias)}

Return JSON with exactly these keys:
- mood: brief description of desired vibe (e.g. "casual relaxed", "bold statement", "professional polished")
- occasion: one of [casual, formal, work, party, sport, loungewear, date, any]
- season: one of [spring, summer, autumn, winter, any]
- color_preference: specific color mentioned or "" if none
- style_preference: specific style mentioned or "" if none

Example: {{"mood": "casual comfortable", "occasion": "casual", "season": "any", "color_preference": "pink", "style_preference": ""}}
"""
    try:
        response = call_fast(prompt)
        clean  = response.strip().strip("```json").strip("```").strip()
        parsed = json.loads(clean)
        return {
            **state,
            "mood":     parsed.get("mood", user_text),
            "occasion": parsed.get("occasion", "any"),
            "season":   parsed.get("season", "any"),
        }
    except Exception as e:
        logger.warning(f"Intent parsing failed: {e}")
        return {**state, "mood": user_text, "occasion": "any", "season": "any"}


def expand_queries(state: OutfitState) -> OutfitState:
    queries = expand_query(state["user_text"] or state["mood"], call_fast)
    return {**state, "expanded_queries": queries}


def hyde_retrieve(state: OutfitState) -> OutfitState:
    hyde_desc = generate_hyde_description(state["user_text"] or state["mood"], call_fast)

    if state.get("inspo_image_pil") is not None:
        text_emb  = embed_text(hyde_desc)
        image_emb = embed_image_pil(state["inspo_image_pil"])
        query_emb = fuse_embeddings(text_emb, image_emb, text_weight=0.35, image_weight=0.65)
    else:
        query_emb = embed_text(hyde_desc)

    return {**state, "hyde_description": hyde_desc, "query_embedding": query_emb}


def retrieve_wardrobe(state: OutfitState) -> OutfitState:
    if not state.get("query_embedding"):
        return {**state, "candidate_items": []}

    season_filter  = state["season"] if state["season"] != "any" else None
    all_results    = []
    queries_to_run = state.get("expanded_queries", [state["user_text"]])

    for query_text in queries_to_run[:3]:
        results = hybrid_search(
            query_embedding=state["query_embedding"],
            query_text=query_text,
            season_filter=season_filter,
            top_k=10,
        )
        all_results.extend(results)

    # deduplicate, keep highest score per item
    seen = {}
    for r in all_results:
        if r.item.id not in seen or r.score > seen[r.item.id].score:
            seen[r.item.id] = r

    candidates = sorted(seen.values(), key=lambda x: x.score, reverse=True)
    return {**state, "candidate_items": [r.item for r in candidates[:20]]}


def retrieve_rules(state: OutfitState) -> OutfitState:
    queries = [
        state["mood"],
        f"{state['occasion']} outfit rules",
        f"{state['season']} dressing guidelines",
        "color combination rules",
        "proportion and layering",
    ]

    all_rules    = []
    seen_content = set()
    for q in queries:
        for rule in retrieve_fashion_rules(q, n_results=3):
            if rule not in seen_content:
                all_rules.append(rule)
                seen_content.add(rule)

    return {**state, "fashion_rules": all_rules[:8]}


def _make_outfit_item(item) -> OutfitItem:
    return OutfitItem(
        id=item.id, name=item.name, category=item.category,
        image_url=item.image_url, colors=item.colors,
    )


def _fallback_outfit(candidates: list) -> list[OutfitItem]:
    # pick one item per category in priority order
    priority = ["tops", "dresses", "bottoms", "shoes", "outerwear", "accessories", "jewellery"]
    by_cat: dict = {}
    for item in candidates:
        by_cat.setdefault(item.category, []).append(item)
    return [_make_outfit_item(by_cat[c][0]) for c in priority if c in by_cat][:5]


def build_outfit(state: OutfitState) -> OutfitState:
    if not state["candidate_items"]:
        return {**state, "selected_items": [], "missing_categories": [],
                "error": "No items in wardrobe match your request."}

    candidates = list(state["candidate_items"])

    # keep top 3 by relevance, shuffle the rest so repeat requests vary
    if len(candidates) > 4:
        random.shuffle(candidates[3:])

    # use indices instead of UUIDs — small models hallucinate long IDs
    items_text = "\n".join([
        f"[{i}] {item.category} | {item.name or 'untitled'} | colors:{','.join(item.colors) or 'unknown'} | season:{item.season}"
        for i, item in enumerate(candidates)
    ])

    rules_text = "\n".join(f"• {r}" for r in state["fashion_rules"][:4]) if state["fashion_rules"] else ""

    prompt = f"""You are a personal stylist. Select a COMPLETE, COHERENT outfit from this wardrobe.

USER REQUEST: "{state['user_text']}"
OCCASION: {state['occasion']}
MOOD/VIBE: {state['mood']}

AVAILABLE ITEMS (pick by index number):
{items_text}

CRITICAL OUTFIT RULES:
- Pick items that actually work TOGETHER visually and stylistically
- NEVER mix a mini dress with joggers — pick one silhouette and commit to it
- Cozy/lazy/loungewear = soft fabrics, comfort-first. Avoid formal shoes or structured pieces
- Casual = relaxed tops + jeans/casual bottoms + clean sneakers or flat shoes
- Formal = structured pieces, heels or smart shoes
- If picking a DRESS, do NOT also pick bottoms — a dress is a complete outfit on its own
- Shoes should match the formality of the rest of the outfit
- Aim for 2-4 items max (top + bottom + shoes, OR dress + shoes, OR dress + outerwear + shoes)

Reply with ONLY a JSON object, nothing else before or after:
{{"indices": [0, 2, 4], "reason": "one line explaining why these work together"}}"""

    try:
        response = call_smart(prompt)
        clean    = response.strip()
        for fence in ["```json", "```"]:
            clean = clean.replace(fence, "")
        clean = clean.strip()

        start = clean.find("{")
        end   = clean.rfind("}") + 1
        if start >= 0 and end > start:
            clean = clean[start:end]

        indices = json.loads(clean).get("indices", [])
        selected = [
            _make_outfit_item(candidates[i])
            for i in indices
            if isinstance(i, int) and 0 <= i < len(candidates)
        ]

        if selected:
            return {**state, "selected_items": selected}

    except Exception as e:
        logger.warning(f"outfit selection failed: {e}")

    return {**state, "selected_items": _fallback_outfit(candidates)}


def validate_outfit(state: OutfitState) -> OutfitState:
    categories = {item.category for item in state["selected_items"]}
    missing    = []

    if not categories & {"tops", "dresses", "outerwear"}:
        missing.append("tops")
    if "dresses" not in categories and "bottoms" not in categories:
        missing.append("bottoms")

    return {**state, "missing_categories": missing}


def retry_missing(state: OutfitState) -> OutfitState:
    for category in state["missing_categories"]:
        results = hybrid_search(
            query_embedding=state["query_embedding"],
            query_text=f"{category} for {state['mood']}",
            category_filter=category,
            top_k=5,
        )
        state["candidate_items"] = [r.item for r in results] + state["candidate_items"]
    return {**state, "retry_count": state.get("retry_count", 0) + 1}


def generate_explanation(state: OutfitState) -> OutfitState:
    if not state["selected_items"]:
        return {**state, "explanation": "I couldn't find enough items in your closet for this request. Try adding more clothes!"}

    def describe_item(item) -> str:
        if item.name and item.name.lower() not in ("", "untitled"):
            return item.name
        color_str = " and ".join(item.colors[:2]) if item.colors else ""
        return f"{color_str} {item.category}".strip()

    items_list = "\n".join(
        f"- {describe_item(item)} (colors: {', '.join(item.colors) or 'unknown'}, category: {item.category})"
        for item in state["selected_items"]
    )

    prompt = f"""You are Silhouette, a personal AI stylist.

The user asked for: "{state['user_text']}"

You selected these EXACT items from their wardrobe:
{items_list}

Write a 2-3 sentence styling note describing this outfit.
STRICT RULES:
- Describe ONLY the items listed above. Do NOT invent or imagine other items.
- Use the actual colors and categories listed — do not rename them.
- If an item has no name, describe it by its color and category (e.g. "the olive bottoms", "the pink top").
- Explain why these specific pieces work together and suit the user's request.
- Be warm and direct. No generic filler phrases.
"""
    return {**state, "explanation": call_fast(prompt)}


def save_outfit(state: OutfitState) -> OutfitState:
    outfit = OutfitResult(
        id=str(uuid.uuid4()),
        items=state["selected_items"],
        explanation=state["explanation"],
        query_text=state["user_text"],
        created_at=datetime.utcnow().isoformat(),
    )
    return {**state, "outfit_result": outfit}


def should_retry(state: OutfitState) -> str:
    if (
        state["missing_categories"]
        and state.get("retry_count", 0) < 1
        and len(state.get("candidate_items", [])) > 0
    ):
        return "retry"
    return "generate_explanation"


def build_outfit_graph():
    graph = StateGraph(OutfitState)

    graph.add_node("parse_intent",         parse_intent)
    graph.add_node("expand_queries",       expand_queries)
    graph.add_node("hyde_retrieve",        hyde_retrieve)
    graph.add_node("retrieve_wardrobe",    retrieve_wardrobe)
    graph.add_node("retrieve_rules",       retrieve_rules)
    graph.add_node("build_outfit",         build_outfit)
    graph.add_node("validate_outfit",      validate_outfit)
    graph.add_node("retry_missing",        retry_missing)
    graph.add_node("generate_explanation", generate_explanation)
    graph.add_node("save_outfit",          save_outfit)

    graph.set_entry_point("parse_intent")
    graph.add_edge("parse_intent",         "expand_queries")
    graph.add_edge("expand_queries",       "hyde_retrieve")
    graph.add_edge("hyde_retrieve",        "retrieve_wardrobe")
    graph.add_edge("retrieve_wardrobe",    "retrieve_rules")
    graph.add_edge("retrieve_rules",       "build_outfit")
    graph.add_edge("build_outfit",         "validate_outfit")
    graph.add_conditional_edges(
        "validate_outfit",
        should_retry,
        {"retry": "retry_missing", "generate_explanation": "generate_explanation"},
    )
    graph.add_edge("retry_missing",        "build_outfit")
    graph.add_edge("generate_explanation", "save_outfit")
    graph.add_edge("save_outfit",          END)

    return graph.compile()


_outfit_graph = None


def get_outfit_graph():
    global _outfit_graph
    if _outfit_graph is None:
        _outfit_graph = build_outfit_graph()
    return _outfit_graph


async def generate_outfit(
    user_text:       str,
    audio_tone:      str    = "neu",
    audio_bias:      dict   = None,
    inspo_image_pil: object = None,
) -> OutfitResult:
    graph = get_outfit_graph()

    initial_state = OutfitState(
        user_text=user_text,
        audio_tone=audio_tone,
        audio_bias=audio_bias or {},
        inspo_image_pil=inspo_image_pil,
        mood="",
        occasion="any",
        season="any",
        expanded_queries=[],
        hyde_description="",
        query_embedding=[],
        candidate_items=[],
        fashion_rules=[],
        selected_items=[],
        missing_categories=[],
        retry_count=0,
        explanation="",
        outfit_result=None,
        error=None,
    )

    final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 50})
    return final_state.get("outfit_result")