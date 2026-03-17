"""
RAG Retrieval Evaluation (self-retrieval)
----------------------------------------
Measures how often a query derived from a chunk retrieves that same chunk (or same source)
in the top-K results. This is a practical health check for your embeddings + Chroma index.

Why "self-retrieval"?
- You likely don't yet have a labeled DKUT QA dataset.
- This gives a repeatable signal for: index integrity, embedding model suitability, chunking quality.

Usage:
  cd "vDekai/DEKAI BACKEND"
  python eval_rag.py --n 200 --k 5
"""

from __future__ import annotations

import argparse
import os
import random
import re
from dataclasses import dataclass
from typing import Any, Iterable

from vector_store import chroma_db


SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def pick_query_from_text(text: str) -> str | None:
    """Pick a 'query' sentence from the chunk text."""
    cleaned = " ".join((text or "").strip().split())
    if len(cleaned) < 40:
        return None
    # Prefer a mid-length sentence; avoid very short ones.
    sents = [s.strip() for s in SENT_SPLIT_RE.split(cleaned) if len(s.strip()) >= 40]
    if not sents:
        # fallback: take first ~160 chars
        return cleaned[:160]
    # Pick a random sentence, but not too long.
    sent = random.choice(sents)
    return sent[:240]


def normalize_source(meta: dict[str, Any] | None) -> str | None:
    if not meta:
        return None
    # LangChain DirectoryLoader usually stores "source"
    src = meta.get("source") or meta.get("file_path") or meta.get("path")
    if not src:
        return None
    return os.path.normpath(str(src))


@dataclass(frozen=True)
class ChunkRow:
    doc_id: str
    text: str
    source: str | None


def iter_chunks(limit: int | None = None) -> list[ChunkRow]:
    """
    Pull documents from Chroma. Uses Chroma internal collection getter (fast, no re-embedding).
    """
    col = chroma_db._collection  # noqa: SLF001 (internal, but stable enough for eval)
    data = col.get(include=["documents", "metadatas"])

    ids: list[str] = data.get("ids") or []
    docs: list[str] = data.get("documents") or []
    metas: list[dict[str, Any]] = data.get("metadatas") or []

    rows: list[ChunkRow] = []
    for i in range(min(len(ids), len(docs), len(metas))):
        rows.append(
            ChunkRow(
                doc_id=str(ids[i]),
                text=str(docs[i] or ""),
                source=normalize_source(metas[i]),
            )
        )

    if limit is not None and limit > 0:
        return rows[:limit]
    return rows


def eval_self_retrieval(rows: list[ChunkRow], n: int, k: int, seed: int) -> dict[str, Any]:
    random.seed(seed)

    pool = [r for r in rows if r.text and len(r.text.strip()) >= 40]
    if not pool:
        raise RuntimeError("No usable chunks found in Chroma DB.")

    sample = random.sample(pool, k=min(n, len(pool)))

    hit_same_id = 0
    hit_same_source = 0
    usable = 0

    for r in sample:
        query = pick_query_from_text(r.text)
        if not query:
            continue
        usable += 1

        results = chroma_db.similarity_search_with_score(query, k=k)
        # Results are (Document, score)
        got_ids: list[str] = []
        got_sources: list[str | None] = []
        for doc, _score in results:
            got_ids.append(str(doc.metadata.get("id") or doc.metadata.get("_id") or doc.metadata.get("doc_id") or ""))
            got_sources.append(normalize_source(doc.metadata))

        # LangChain's Chroma wrapper may not expose the original collection id in metadata.
        # So we also check by matching source path when available.
        if r.source and any(s == r.source for s in got_sources):
            hit_same_source += 1

        # Heuristic: exact text match in top-k (helps when ids aren't available)
        if any((doc.page_content or "").strip() == r.text.strip() for doc, _ in results):
            hit_same_id += 1

    denom = max(usable, 1)
    return {
        "n_requested": n,
        "n_usable": usable,
        "k": k,
        "seed": seed,
        "self_retrieval_exact_text_hit_rate": hit_same_id / denom,
        "self_retrieval_same_source_hit_rate": hit_same_source / denom,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200, help="Number of chunks to sample")
    ap.add_argument("--k", type=int, default=5, help="Top-K retrieval")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rows = iter_chunks()
    stats = eval_self_retrieval(rows, n=args.n, k=args.k, seed=args.seed)

    print("\n=== RAG Self-Retrieval Evaluation ===")
    for key, val in stats.items():
        if isinstance(val, float):
            print(f"{key}: {val:.3f}")
        else:
            print(f"{key}: {val}")
    print("====================================\n")


if __name__ == "__main__":
    main()

