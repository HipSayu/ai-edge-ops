"""Sync the knowledge base's embeddings into the vector store (Qdrant).

Content stays local in ASSISTANT_KNOWLEDGE_DIR (default docs/knowledge, laid out as <kind>/*.md); only each
document's embedding (title + summary) and id go to Qdrant. Run (from repo root):
  python -m apps.assistant.ingest            # embed new/changed documents, drop vectors of deleted ones
  python -m apps.assistant.ingest --force    # re-embed everything
"""

import argparse
import asyncio

from hopquangdo.observability import LoggingSetup

from src.assistant.bootstrap.knowledge_container import KnowledgeContainer
from src.assistant.config.assistant_settings import AssistantSettings


async def main(force: bool) -> None:
    settings = AssistantSettings()
    LoggingSetup.configure(f"{settings.service_name}-ingest", settings.log_level, settings.log_json)
    knowledge = KnowledgeContainer(settings)
    try:
        report = await knowledge.ingestion_service.sync(force)
    finally:
        await knowledge.close()
    print(
        f"ingested={len(report.ingested)} unchanged={len(report.unchanged)} "
        f"skipped={len(report.skipped)} removed={len(report.removed)}"
    )
    for document_id in report.ingested:
        print(f"  + {document_id}")
    for document_id in report.removed:
        print(f"  - {document_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", action="store_true", help="re-embed even if unchanged")
    asyncio.run(main(parser.parse_args().force))
