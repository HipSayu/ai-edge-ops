# Services

The services hold the logic (domain, application, infrastructure). Their HTTP layer (routes, schemas, MCP tools,
`main`) lives in `services/cloud/src/cloud/interface`. The chat assistant is an agent in Dunly, which calls the cloud over HTTP
and MCP.

| Service | Owns | Verifies tokens | Depends on |
|---|---|---|---|
| `cloud` | users, login, sites/nodes/cameras, violations, vision, the chat's pictures, reports and regulations | signs them (RS256, private key) | nothing |

The cloud interface serves REST (`/api/v1`) and the MCP tools (`/mcp`, declared in `cloud.interface.mcp.tools`) from one
process, over the same use cases.

**The assistant and the MCP server.** The agent runs in Dunly and reaches the cloud only through the MCP server, which is the one place that knows which tools exist and who may use them:

- It lists every tool to everyone, and says for each whether it only reads (`readOnlyHint`).
- The role is checked when a tool is called (403 if not allowed), with the token of the user who is chatting: the cloud
  sends it to Dunly with every turn and Dunly forwards it (`forward_headers: ["Authorization"]` on the connector).
- A tool that only reads runs at once. A tool that changes data is held for the user's approval in the chat.
- Pictures, reports and regulation search are tools of the cloud too (`detect_ppe`, `export_safety_report`,
  `search_knowledge`), kept by `ChatImageService`, `ReportService` and `KnowledgeService`.

The agent's prompt and skills live in `docs/dunly/`; `tools/setup_dunly.py` creates the agent in Dunly from them.

**Detector app.** `services/detector` is a thin FastAPI app (`POST /detect`), not a DDD service: it has no domain/application
layer of its own and reuses the edge's `YoloDetector`/`JpegRenderer` directly, so a picture is judged by the same model as
the cameras. The cloud calls it over the private compose network (`CLOUD_DETECTOR_URL`, no published port) for
pictures users attach to the chat.

**Edge.** `edge` runs next to the cameras: it reads frames, runs the detector and publishes each violation to an
MQTT broker (snapshot embedded). `cloud` subscribes (set `CLOUD_MQTT_HOST`) and files each event like a local
detection. Neither imports the other's code; both use `package/edge_link`, the link between cloud and edge:
topics (`topics.py`), the message and its wire format (`messages.py`), `EventPublisher` (edge: connects, announces
online/offline, sends) and `EventSubscriber` (cloud: connects, subscribes, drops redeliveries by `event_id`).
Run the edge with `python -m edge` (settings in `EDGE_*` variables: `EDGE_NODE_ID`, `EDGE_CAMERAS`,
`EDGE_MQTT_HOST`).

`shared/` holds only what the services need in common: roles, the viewer, domain errors and the HTTP mapping of them,
and token verification. It holds no business rules.

## Layout of `cloud/src/cloud`

```
domain/          model/ (node, zone, user, cluster)  violation/ (detection, violations, violation_event, priority)
                 policy/ (access_policy, regulation)  repositories.py (the ports)
application/     usecases/ (one service per use case)  dto/ (read_models, views, scope, chat_events)
                 ports.py  unit_of_work.py
infrastructure/  persistence/ (SQLAlchemy)  files/ (image, snapshot, video, report stores)
                 detection/ (HTTP detector client, live feeds, hub)  messaging/ (MQTT, Redis, Dunly)
                 knowledge/  llm/  security/
interface/       rest/ (app, deps, routers/v1, schemas)  mcp/ (server runner and tools)  main.py
bootstrap/       container, settings, edge_events
```

`detector/` and `edge/` use the same `src/<name>/` layout.

Dependency rule (checked by `tests/test_architecture.py` in each service): domain <- application <- infrastructure;
the interface sits outside and calls inward. No service imports another service's code.

Run the whole stack: `docker compose up --build` from `app/`, then open `http://localhost:8080`.

Each service has one dependency file, `requirements.txt`, pinned; the Dockerfile of its interface installs from it.
Test tools (pytest, pytest-asyncio, httpx) are installed by the test runner, not by the image.

Run the interface: from `app/`, `uvicorn cloud.interface.main:app --port 8100` (with services/cloud/src on PYTHONPATH).

Run one service's tests: `pip install -r requirements.txt -e ../shared pytest pytest-asyncio httpx`, then `python -m pytest -q`.

Cloud pins torch from the CPU index (no CUDA packages in the image).
