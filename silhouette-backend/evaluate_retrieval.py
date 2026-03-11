import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.embeddings import embed_text
from services.retrieval import hybrid_search
from services import wardrobe_store as store

TEST_QUERIES = [
    {
        "query": "something casual and comfortable for a lazy day at home",
        "relevant_if": lambda item: (
            item.category in ("tops", "bottoms", "dresses") and
            any(o in item.occasions for o in ("casual", "lounge"))
        ),
    },
    {
        "query": "smart casual work look",
        "relevant_if": lambda item: (
            item.category in ("tops", "bottoms", "outerwear", "shoes") and
            any(o in item.occasions for o in ("work", "casual", "formal")) or
            any(s in item.styles for s in ("smart-casual", "classic", "minimalist"))
        ),
    },
    {
        "query": "ethnic festive outfit",
        "relevant_if": lambda item: (
            any(o in item.occasions for o in ("ethnic", "formal", "party")) or
            any(s in item.styles for s in ("ethnic", "bohemian"))
        ),
    },
    {
        "query": "party night out look",
        "relevant_if": lambda item: (
            any(o in item.occasions for o in ("party", "formal", "date")) and
            item.category in ("tops", "dresses", "bottoms", "shoes", "accessories")
        ),
    },
    {
        "query": "something bohemian and flowy for outdoors",
        "relevant_if": lambda item: (
            any(s in item.styles for s in ("bohemian", "cottagecore", "romantic")) or
            any(o in item.occasions for o in ("outdoor", "casual"))
        ),
    },
    {
        "query": "shoes to wear with a casual outfit",
        "relevant_if": lambda item: item.category == "shoes",
    },
    {
        "query": "a dress for a date night",
        "relevant_if": lambda item: (
            item.category in ("dresses", "tops") and
            any(o in item.occasions for o in ("date", "party", "formal"))
        ),
    },
    {
        "query": "warm cozy winter layers",
        "relevant_if": lambda item: (
            item.season in ("winter", "autumn", "all-season") and
            item.category in ("tops", "outerwear", "bottoms")
        ),
    },
]

K = 10  # Precision@K and Recall@K


def relevance_label(item, relevant_if_fn) -> bool:
    try:
        return bool(relevant_if_fn(item))
    except Exception:
        return False


def precision_at_k(retrieved, relevant_if_fn, k=K) -> float:
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    relevant_count = sum(1 for item in top_k if relevance_label(item, relevant_if_fn))
    return relevant_count / len(top_k)


def recall_at_k(retrieved, all_items, relevant_if_fn, k=K) -> float:
    total_relevant = sum(1 for item in all_items if relevance_label(item, relevant_if_fn))
    if total_relevant == 0:
        return 0.0
    top_k = retrieved[:k]
    retrieved_relevant = sum(1 for item in top_k if relevance_label(item, relevant_if_fn))
    return retrieved_relevant / total_relevant


def reciprocal_rank(retrieved, relevant_if_fn) -> float:
    for rank, item in enumerate(retrieved, start=1):
        if relevance_label(item, relevant_if_fn):
            return 1.0 / rank
    return 0.0


def run_evaluation():
    print("\n" + "="*60)
    print("  SILHOUETTE RETRIEVAL EVALUATION")
    print("="*60)

    # Load all wardrobe items
    all_items = store.get_all_items(active_only=True)
    total_items = len(all_items)
    print(f"\nWardrobe size: {total_items} items")

    if total_items == 0:
        print("⚠️  No items in wardrobe. Add some clothes first.")
        return

    results = []
    precision_scores = []
    recall_scores    = []
    rr_scores        = []

    for test in TEST_QUERIES:
        query_text  = test["query"]
        relevant_if = test["relevant_if"]

        # Embed and search
        query_emb = embed_text(query_text)
        retrieved_items_with_scores = hybrid_search(
            query_embedding=query_emb,
            query_text=query_text,
            top_k=K,
        )
        retrieved_items = [r.item for r in retrieved_items_with_scores]

        p = precision_at_k(retrieved_items, relevant_if, k=K)
        r = recall_at_k(retrieved_items, all_items, relevant_if, k=K)
        rr = reciprocal_rank(retrieved_items, relevant_if)

        precision_scores.append(p)
        recall_scores.append(r)
        rr_scores.append(rr)

        # Show retrieved items for this query
        print(f"\n{'─'*60}")
        print(f"Query: \"{query_text}\"")
        print(f"  Precision@{K}: {p:.3f}  |  Recall@{K}: {r:.3f}  |  RR: {rr:.3f}")
        print(f"  Top {K} retrieved:")
        for i, item in enumerate(retrieved_items, 1):
            rel_marker = "✓" if relevance_label(item, relevant_if) else "✗"
            name = item.name or "(untitled)"
            print(f"    [{rel_marker}] {i}. {name} | {item.category} | occasions:{item.occasions} | styles:{item.styles}")

        results.append({
            "query":        query_text,
            "precision":    round(p, 4),
            "recall":       round(r, 4),
            "mrr":          round(rr, 4),
            "retrieved":    [{"name": item.name, "category": item.category,
                              "occasions": item.occasions, "styles": item.styles}
                             for item in retrieved_items],
        })

    # Aggregate
    mean_precision = sum(precision_scores) / len(precision_scores)
    mean_recall    = sum(recall_scores)    / len(recall_scores)
    mrr            = sum(rr_scores)        / len(rr_scores)

    print(f"\n{'='*60}")
    print("  FINAL SCORES")
    print(f"{'='*60}")
    print(f"  Mean Precision@{K} : {mean_precision:.4f}")
    print(f"  Mean Recall@{K}    : {mean_recall:.4f}")
    print(f"  MRR               : {mrr:.4f}")
    print(f"{'='*60}\n")

    # Save to JSON
    output = {
        "wardrobe_size":   total_items,
        "k":               K,
        "mean_precision":  round(mean_precision, 4),
        "mean_recall":     round(mean_recall, 4),
        "mrr":             round(mrr, 4),
        "per_query":       results,
    }
    out_path = Path(__file__).parent / "eval_results.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Results saved to: {out_path}")
    return output


if __name__ == "__main__":
    run_evaluation()