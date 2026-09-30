"""Evaluate search_tools on the mock query set, with the configured embedder and the Cloud MCP tool definitions.

Run (from repo root):
  python -m evals.assistant.tool_search
  python -m evals.assistant.tool_search --top-k 5 -v
Tools are read from the Cloud MCP server definitions in-process (no running Cloud needed).
Exits non-zero when hit@k is below --min-hit (for CI).
"""

import argparse
import asyncio
import sys
from pathlib import Path

import yaml
from langchain_core.tools import StructuredTool

from apps.cloud.mcp_server.server import mcp
from apps.cloud.mcp_server.tools import deployment_tools, fleet_tools, monitoring_tools  # noqa: F401  (registers)
from src.assistant.config.assistant_settings import AssistantSettings
from src.assistant.infrastructure.embedding.embedder_factory import EmbedderFactory
from src.assistant.application.tools.tool_search import ToolIndex

DATASETS = Path(__file__).resolve().parent / "datasets"


async def main(queries_file: Path, top_k: int, min_hit: float, verbose: bool) -> int:
    specs = await mcp.list_tools()
    tools = [
        StructuredTool.from_function(coroutine=_noop, name=s.name, description=s.description or s.name,
                                     args_schema=s.input_schema)
        for s in specs
    ]
    index = ToolIndex(EmbedderFactory.create(AssistantSettings()), tools)
    await index.build()

    cases = yaml.safe_load(queries_file.read_text(encoding="utf-8"))["queries"]
    hit1 = hitk = 0
    report = []
    for case in cases:
        ranked = [(tool.name, round(score, 3)) for tool, score in await index.search(case["query"], top_k)]
        names = [name for name, _ in ranked]
        ok1, okk = bool(names) and names[0] in case["expected"], any(n in case["expected"] for n in names)
        hit1, hitk = hit1 + ok1, hitk + okk
        if not okk or verbose:
            report.append((okk, case, ranked))

    total = len(cases)
    print(f"tools={len(tools)}  queries={total}  hit@1={hit1 / total:.2%}  hit@{top_k}={hitk / total:.2%}")
    for ok, case, ranked in report:
        print(f"\n{'ok  ' if ok else 'MISS'} {case['query']!r}\n     expected {case['expected']}\n     got      {ranked}")
    return 0 if hitk / total >= min_hit else 1


async def _noop(**_: object) -> None:
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--queries", type=Path, default=DATASETS / "tool_queries.yaml")
    parser.add_argument("--top-k", type=int, default=5, help="search_tools returns 5 tools by default")
    parser.add_argument("--min-hit", type=float, default=0.9)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.queries, args.top_k, args.min_hit, args.verbose)))
