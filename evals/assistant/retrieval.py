"""Evaluate summary-based retrieval on the mock query set, with the real embedder and a throwaway index.

Run (from repo root; needs ASSISTANT_EMBEDDING_API_KEY):
  python -m evals.assistant.retrieval
  python -m evals.assistant.retrieval --queries evals/assistant/datasets/retrieval_queries.yaml --top-k 3 -v
Each subfolder of docs/knowledge named after a DocumentKind (skill, runbook, doc, guide) is indexed as that
kind into an in-memory Qdrant, so the production collection is never touched.
Exits non-zero when hit@k is below --min-hit (for CI).
"""

import argparse
import asyncio
import sys
from collections import defaultdict
from pathlib import Path

import yaml
from hopquangdo.observability import LoggingSetup
from qdrant_client import AsyncQdrantClient

from src.assistant.bootstrap.knowledge_container import KnowledgeContainer
from src.assistant.config.assistant_settings import AssistantSettings
from src.assistant.infrastructure.knowledge.markdown_loader import MarkdownLoader
from src.assistant.infrastructure.knowledge.local_document_repository import LocalDocumentRepository
from src.assistant.infrastructure.knowledge.qdrant_vector_store import QdrantVectorStore

DATASETS = Path(__file__).resolve().parent / "datasets"


async def main(root: Path, queries_file: Path, top_k: int, min_hit: float, verbose: bool) -> int:
    settings = AssistantSettings()
    LoggingSetup.configure(f"{settings.service_name}-eval", "WARNING", False)
    store = QdrantVectorStore(AsyncQdrantClient(location=":memory:"), "eval_knowledge")
    documents = LocalDocumentRepository(root, [MarkdownLoader()])
    knowledge = KnowledgeContainer(settings, store=store, documents=documents)
    try:
        await knowledge.ingestion_service.sync(force=True)

        cases = yaml.safe_load(queries_file.read_text(encoding="utf-8"))["queries"]
        hits, reciprocal_ranks = 0, 0.0
        by_style: dict[str, list[bool]] = defaultdict(list)
        misses = []
        for case in cases:
            results = await knowledge.retrieval_service.search(case["query"], limit=top_k)
            ranked = [r.document.id for r in results]
            rank = next((i + 1 for i, doc in enumerate(ranked) if doc in case["expected"]), None)
            hit = rank is not None
            hits += hit
            reciprocal_ranks += 1 / rank if hit else 0.0
            by_style[case.get("style", "-")].append(hit)
            if not hit or verbose:
                misses.append((hit, case, ranked, [round(r.score, 3) for r in results]))
            top1 = bool(ranked) and ranked[0] in case["expected"]
            by_style["hit@1"].append(top1)
    finally:
        await knowledge.close()

    total = len(cases)
    hit_rate = hits / total
    print(f"queries={total}  hit@1={sum(by_style.pop('hit@1')) / total:.2%}  hit@{top_k}={hit_rate:.2%}  "
          f"MRR@{top_k}={reciprocal_ranks / total:.3f}")
    for style, results in sorted(by_style.items()):
        print(f"  {style:<6} hit@{top_k}={sum(results) / len(results):.2%} ({len(results)} queries)")
    for hit, case, ranked, scores in misses:
        mark = "ok  " if hit else "MISS"
        print(f"\n{mark} {case['query']!r}\n     expected {case['expected']}\n     got      "
              + ", ".join(f"{doc} ({score})" for doc, score in zip(ranked, scores)))
    return 0 if hit_rate >= min_hit else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path("docs/knowledge"), help="knowledge root folder")
    parser.add_argument("--queries", type=Path, default=DATASETS / "retrieval_queries.yaml")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-hit", type=float, default=0.9, help="required hit@k, 0-1")
    parser.add_argument("-v", "--verbose", action="store_true", help="print every query, not only misses")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.root, args.queries, args.top_k, args.min_hit, args.verbose)))
