from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import logging
from models.schemas import ClothingItem, RetrievedItem
import services.wardrobe_store as store

logger = logging.getLogger(__name__)
RRF_K = 60


# MultiQuery expansion 

def expand_query(user_input: str, llm_caller) -> list[str]:
    prompt = f"""You are a fashion retrieval assistant.
Expand the following user request into 4 different search queries
that would help retrieve relevant clothing items from a wardrobe database.
Each query should capture a different angle: style, occasion, mood, or aesthetic.
Return ONLY a JSON array of 4 short query strings. No explanation.

User request: "{user_input}"

Example output: ["casual relaxed top", "everyday comfortable look", "laid back style", "simple going out outfit"]
"""
    try:
        response = llm_caller(prompt)
        import json
        queries = json.loads(response.strip())
        return [user_input] + queries[:4]  # original + 4 expansions
    except Exception as e:
        logger.warning(f"MultiQuery expansion failed: {e}. Using original query only.")
        return [user_input]


# HyDE

def generate_hyde_description(user_input: str, llm_caller) -> str:
    prompt = f"""You are a fashion stylist. A user wants: "{user_input}"

Write a detailed description of the perfect outfit for this request.
Mention specific clothing types, colors, textures, and style characteristics.
Write 2-3 sentences only. Be specific about garment types.

Example: "A relaxed oversized cream linen shirt tucked loosely into straight-leg dark wash jeans,
paired with white leather sneakers and minimal gold jewellery for an effortless weekend look."
"""
    try:
        return llm_caller(prompt).strip()
    except Exception as e:
        logger.warning(f"HyDE generation failed: {e}. Using original query.")
        return user_input


# BM25 Search

def bm25_search(
    query: str,
    items: list[ClothingItem],
    top_k: int = 20,
) -> list[tuple[ClothingItem, float]]:
    if not items:
        return []

    # Build corpus from item text representations
    corpus = [
        f"{item.name} {item.category} {item.season} {' '.join(item.occasions)} {' '.join(item.styles)} {' '.join(item.colors)}"
        for item in items
    ]
    tokenized_corpus = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # Return items with non-zero scores, sorted by score
    results = [(item, float(score)) for item, score in zip(items, scores) if score > 0]
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


# TF-IDF

def tfidf_rerank(
    query: str,
    items: list[ClothingItem],
    top_k: int = 15,
) -> list[tuple[ClothingItem, float]]:
    if not items:
        return []
    corpus = [
        f"{item.name} {item.category} {' '.join(item.styles)} {' '.join(item.colors)}"
        for item in items
    ]
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)
        query_vec = vectorizer.transform([query])
        scores = (tfidf_matrix * query_vec.T).toarray().flatten()
        results = [(item, float(score)) for item, score in zip(items, scores)]
        results.sort(key=lambda x: x[1], reverse=True)
        return [(item, score) for item, score in results if score > 0][:top_k]
    except Exception:
        return []


#  RRF

def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[ClothingItem, float]]],
    k: int = RRF_K,
) -> list[RetrievedItem]:

    rrf_scores: dict[str, float] = {}
    item_map: dict[str, ClothingItem] = {}

    for ranked_list in ranked_lists:
        for rank, (item, _) in enumerate(ranked_list, start=1):
            rrf_scores[item.id] = rrf_scores.get(item.id, 0) + 1 / (k + rank)
            item_map[item.id] = item

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [
        RetrievedItem(item=item_map[item_id], score=score)
        for item_id, score in sorted_items
    ]


# Main hybrid search entry point

def hybrid_search(
    query_embedding: list[float],
    query_text: str,
    season_filter: str = None,
    category_filter: str = None,
    top_k: int = 15,
) -> list[RetrievedItem]:

    # Step 1: Get candidates from ChromaDB with metadata pre-filter
    vector_results = store.similarity_search(
        query_embedding=query_embedding,
        n_results=30,
        season=season_filter,
        category=category_filter,
    )

    # Step 2: Get all items for BM25 
    all_items = store.get_all_items(season=season_filter, active_only=True)

    # Step 3: BM25 on full candidate set
    bm25_results = bm25_search(query_text, all_items, top_k=30)

    # Step 4: Fuse with RRF
    fused = reciprocal_rank_fusion([vector_results, bm25_results])

    return fused[:top_k]
