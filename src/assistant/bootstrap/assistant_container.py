import logging

from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from redis.asyncio import Redis

from src.assistant.application.agent.agent_node import AgentNode
from src.assistant.application.agent.graph import ChatGraph
from src.assistant.application.agent.orchestrator import AgentOrchestrator
from src.assistant.application.agent.tools_node import ToolsNode
from src.assistant.bootstrap.knowledge_container import KnowledgeContainer
from src.assistant.application.services.chat_stream_service import ChatStreamService
from src.assistant.infrastructure.messaging.redis_stream_queue import RedisStreamQueue
from src.assistant.config.assistant_settings import AssistantSettings
from src.assistant.application.ports.chat_model_provider import ChatModelProvider
from src.assistant.application.ports.embedder import Embedder
from src.assistant.application.ports.mcp_client import McpClient
from src.assistant.application.ports.stream_queue import StreamQueue
from src.assistant.application.ports.tool_provider import ToolProvider
from src.assistant.application.ports.tracer import Tracer
from src.assistant.infrastructure.llm.chat_model_factory import ChatModelFactory
from src.assistant.application.tools.knowledge_search import KnowledgeSearch
from src.assistant.infrastructure.mcp.cloud_mcp_client import CloudMcpClient
from src.assistant.infrastructure.mcp.cloud_mcp_toolkit import CloudMcpToolkit
from src.assistant.application.tools.registry import ToolRegistry
from src.assistant.application.tools.tool_runner import ToolRunner
from src.assistant.infrastructure.tracing.langfuse_tracer import LangfuseTracer

logger = logging.getLogger(__name__)


class AssistantContainer:
    """Wires the LLM, all Cloud MCP tools, the knowledge base, the agent graph and the Redis-backed
    stream service. Tools come from the Cloud MCP server, so the graph is built in `start()` once they are listed.
    """

    def __init__(
        self,
        settings: AssistantSettings,
        redis: Redis | None = None,
        knowledge: KnowledgeContainer | None = None,
        embedder: Embedder | None = None,
    ) -> None:
        self.settings = settings
        self.cloud_mcp: McpClient = CloudMcpClient(settings.cloud_api_url, settings.cloud_api_key, settings.cloud_timeout_sec)
        self._toolkit: ToolProvider = CloudMcpToolkit(self.cloud_mcp)
        self._models: ChatModelProvider = ChatModelFactory(settings)
        self.redis = redis or Redis.from_url(settings.redis_url)
        self.stream_queue: StreamQueue = RedisStreamQueue(self.redis, settings.stream_ttl_sec, settings.stream_idle_timeout_sec)
        # The embedder is only needed by the knowledge base, so none is created when it is off
        self.knowledge = knowledge or (
            KnowledgeContainer(settings, embedder=embedder) if settings.knowledge_enabled else None
        )
        self.tracer: Tracer | None = LangfuseTracer(settings, settings.service_name) if settings.tracing_enabled else None
        self.orchestrator: AgentOrchestrator | None = None
        self.chat_stream_service: ChatStreamService | None = None

    async def start(self) -> None:
        settings = self.settings
        # Every Cloud MCP tool is bound on every model call (no search_tools activation step)
        core = await self._toolkit.tools()
        if self.knowledge is not None:
            core.append(KnowledgeSearch(self.knowledge.retrieval_service).tool())
        registry = ToolRegistry(core, [])
        logger.info("agent tools bound: %s", [tool.name for tool in core])

        graph = ChatGraph(
            AgentNode(self._models.create(settings.llm_model), registry, settings.agent_max_rounds),
            ToolsNode(registry, ToolRunner(registry.all(), timeout=settings.tool_timeout_sec)),
        )
        # Conversation memory and paused (awaiting approval) turns live in Redis (needs RedisJSON + RediSearch,
        # i.e. Redis 8 / Redis Stack), so any replica can continue a session.
        checkpointer = AsyncRedisSaver(
            redis_client=self.redis,
            ttl={"default_ttl": settings.session_ttl_min, "refresh_on_read": True},
        )
        await checkpointer.asetup()
        self.orchestrator = AgentOrchestrator(graph.build(checkpointer), tracer=self.tracer)
        logger.info("langfuse tracing %s", f"on ({settings.langfuse_host})" if self.tracer else "off")
        self.chat_stream_service = ChatStreamService(self.orchestrator, self.stream_queue)

    async def stop(self) -> None:
        if self.chat_stream_service is not None:
            await self.chat_stream_service.stop()
        if self.knowledge is not None:
            await self.knowledge.close()
        if self.tracer is not None:
            self.tracer.shutdown()
        await self.redis.aclose()

    async def check_cloud(self) -> bool:
        return await self.cloud_mcp.ping()

    async def check_redis(self) -> bool:
        return await self.stream_queue.ping()

    async def check_knowledge(self) -> bool:
        return self.knowledge is None or await self.knowledge.store.ping()
