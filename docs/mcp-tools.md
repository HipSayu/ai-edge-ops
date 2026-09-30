# MCP Server Tools

The Cloud MCP server (`/mcp`) exposes the edge fleet to the AI assistant. Each tool wraps a Cloud service call.

- **Write** tools change state on the cloud or on edge nodes. The assistant must only call them after the user explicitly confirms.
- **Status** is `Done` for tools in `apps/cloud/mcp_server/tools/`, and `Planned` for tools whose Cloud endpoint still has to be built.

## References instead of ids

Users know sites and devices by name or code ("Công trường A", "CT-A", "Hố móng"), not by UUID. So every parameter
typed `ref` takes an **id, a code or a name**, resolved on the Cloud by `EntityResolver`
(`src/cloud/application/services/entity_resolver.py`):

1. id, exact;
2. code, ignoring case and diacritics: `metadata.site_code` for a cluster (`CT-A`), `metadata.code` for a node (`CT-A-01`);
3. name, ignoring case and diacritics (`ho mong` = `Hố móng`);
4. name containing the reference: **read tools only**. Write tools need tiers 1-3, so a partial name never picks what gets changed.

- **Scope.** Node names are unique only within a cluster, and runtime names within a node. Pass `cluster` / `node`, or
  write the scope into the reference: `CT-A/Hố móng`, `Hố móng/ppe-detector`. A deployment is referenced by the name of
  the runtime it deploys.
- **Several matches.** The tool fails with `invalid_request` and lists the candidates, so the assistant asks the user
  which one they mean instead of guessing.
- **No match.** The tool fails with `not_found` and lists what exists in that scope.
- **Results.** Results carry the names of the related cluster and node next to the ids, so the assistant can answer
  and follow up by name.

Planned tools below still show `*_id` parameters where no resolver exists yet (cameras, alerts, violations,
revisions). They take a `ref` too once they are built.

```
MCP
├── Fleet        cluster · node
├── Deployment   deployment · runtime · rollback
├── Model        registry · evaluation · benchmark · compatibility
├── Camera       camera · stream
├── Monitoring   telemetry · events · logs · alerts
├── Inference    metrics · detections · violations
├── Diagnostics  node · runtime · deployment · camera
├── Knowledge    search · document
└── Meta         tool search
```

## Fleet

### Cluster

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `list_clusters` | List clusters with code, status, location and node counts by status. | `query: str?` | Give an overview of every cluster in the fleet. | Done |
| `get_cluster` | Get one cluster and its nodes. | `cluster: ref` | Inspect a cluster's name, location and metadata. | Done |
| `create_cluster` | Create a new cluster. Fails if the name is already taken. | `name: str`, `description: str?`, `location: str?`, `metadata: dict?` | **Write.** Add a new site or group to hold edge nodes. | Done |
| `update_cluster` | Update a cluster; only the given fields change. | `cluster: ref`, `name: str?`, `description: str?`, `location: str?`, `metadata: dict?` | **Write.** Rename a cluster or fix its location. | Planned |
| `delete_cluster` | Delete an empty cluster. Fails if it still has nodes. | `cluster: ref` | **Write, destructive.** Remove a site that is no longer used. | Planned |

### Node

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `list_nodes` | List edge nodes with cluster, status and last heartbeat, optionally filtered. | `cluster: ref?`, `status: NodeStatus?`, `query: str?` | Find nodes and check which ones are down. | Done |
| `get_node` | Get one edge node, including hardware, agent version and heartbeat. | `node: ref`, `cluster: ref?` | Inspect a single node. | Done |
| `get_node_overview` | One call for a node's info, latest telemetry, runtimes and recent events. | `node: ref`, `cluster: ref?` | Answer "how is this node doing?" without chaining four tools. | Done |
| `register_node` | Register a new edge node in a cluster. Fails if the name exists in that cluster. | `cluster: ref`, `name: str`, `metadata: dict?` | **Write.** Onboard a new edge device. | Done |
| `update_node` | Update a node's name, labels or metadata. | `node_id: str`, `name: str?`, `labels: dict[str, str]?`, `metadata: dict?` | **Write.** Keep node information and labels accurate. | Planned |
| `restart_node_agent` | Restart the Edge Agent process on a node. Does not reboot the node OS, and running runtimes keep running. | `node_id: str` | **Write.** Recover an agent that stopped reporting or responding. | Planned |
| `update_node_agent` | Upgrade the Edge Agent on a node to a given version. | `node_id: str`, `version: str` | **Write.** Roll out a new agent release. | Planned |
| `drain_node` | Stop scheduling new deployments on a node and move or stop its runtimes. | `node_id: str`, `migrate: bool = true` | **Write.** Prepare a node for maintenance. | Planned |
| `enable_node` | Allow a node to receive deployments again. | `node_id: str` | **Write.** Bring a node back after maintenance. | Planned |
| `disable_node` | Mark a node as unavailable without removing it. Its runtimes are stopped. | `node_id: str` | **Write.** Take a faulty node out of service. | Planned |

## Deployment

### Deployment

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `list_deployments` | List deployments with node, cluster and image, optionally filtered. | `node: ref?`, `cluster: ref?`, `status: DeploymentStatus?` | Review what is deployed and where. | Done |
| `get_deployment` | Get one deployment, including its spec and status. | `deployment: ref`, `node: ref?`, `cluster: ref?` | Check a deployment's spec and whether it succeeded. | Done |
| `create_deployment` | Deploy a runtime image to an edge node. The edge reports the result asynchronously. | `node: ref`, `cluster: ref?`, `name: str`, `image_uri: str`, `type: RuntimeType = vision`, `image_tag: str = "latest"`, `model_id: str?`, `model_uri: str?`, `config: dict?`, `environment: dict[str, str]?`, `resource_limits: dict?` | **Write.** Roll out an AI runtime or model to an edge node. | Done |
| `update_deployment` | Update an active deployment; only the given fields change. Creates a new revision. | `deployment: ref`, `node: ref?`, `cluster: ref?`, `image_uri: str?`, `image_tag: str?`, `model_id: str?`, `model_uri: str?`, `config: dict?`, `environment: dict[str, str]?`, `resource_limits: dict?` | **Write.** Upgrade the image or model, or change a deployment's config. | Done |
| `remove_deployment` | Remove a deployment: stops and deletes its runtime on the edge node. | `deployment: ref`, `node: ref?`, `cluster: ref?` | **Write, destructive.** Take a runtime off an edge node. | Done |

### Runtime

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `list_runtimes` | List runtimes (deployed containers) with node and cluster, optionally filtered. | `node: ref?`, `cluster: ref?`, `status: RuntimeStatus?` | See which containers run on which nodes. | Done |
| `get_runtime` | Get one runtime. | `runtime: ref`, `node: ref?`, `cluster: ref?` | Inspect a runtime's state and configuration. | Done |
| `control_runtime` | Start, stop or restart a runtime on its edge node. | `runtime: ref`, `node: ref?`, `cluster: ref?`, `action: "start" \| "stop" \| "restart"` | **Write.** Recover or pause a runtime without redeploying it. Covers `start_runtime`, `stop_runtime` and `restart_runtime`. | Done |
| `get_runtime_logs` | Get the recent log lines of one runtime container. | `runtime_id: str`, `tail: int = 200`, `level: str?`, `since: datetime?` | Read what a runtime printed before it failed. | Planned |
| `get_runtime_metrics` | Get resource usage of one runtime container: CPU, memory, GPU and restarts. | `runtime_id: str`, `since: datetime?` | Find runtimes that leak memory or restart in a loop. | Planned |

### Rollback

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `list_deployment_revisions` | List the revisions of a deployment, newest first. | `deployment_id: str`, `limit: int = 20` | See what changed over time and when. | Planned |
| `get_deployment_revision` | Get the full spec of one revision. | `deployment_id: str`, `revision: int` | Compare an old spec with the current one. | Planned |
| `rollback_deployment` | Redeploy a previous revision. Omit `revision` to go back one step. | `deployment_id: str`, `revision: int?` | **Write.** Undo a bad model or config update. | Planned |

## Model

### Registry

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `list_models` | List model images in the registry, optionally filtered. | `query: str?`, `task: str?`, `optimization: "base" \| "pruned" \| "distilled" \| "qat"?`, `limit: int = 50` | Find a model to deploy. | Planned |
| `get_model` | Get one model image by tag, including version, classes, input size, format and file size. | `tag: str` | Inspect a model before deploying it. | Planned |
| `list_model_deployments` | List the deployments that use a given model. | `tag: str` | Find where a model runs before upgrading or removing it. | Planned |
| `update_class_config` | Update the detection class configuration of a model. | `tag: str`, `classes: dict` (enabled flag and confidence threshold per class) | **Write.** Enable, disable or tune PPE classes. | Planned |

### Evaluation

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `get_model_evaluation` | Get the offline evaluation of a model on its validation or test set. | `tag: str`, `split: "val" \| "test" = "val"` | Read mAP50, mAP50-95, precision, recall and F1. | Planned |
| `get_model_class_metrics` | Get per-class AP, precision and recall of a model. | `tag: str`, `split: "val" \| "test" = "val"` | Find which PPE classes the model detects poorly. | Planned |
| `compare_models` | Compare evaluation and benchmark results of two or more models side by side. | `tags: list[str]`, `split: "val" \| "test" = "val"` | Choose between models, e.g. base vs. pruned vs. QAT. | Planned |

### Benchmark

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `get_model_benchmark` | Get speed and resource benchmarks of a model per hardware target. | `tag: str`, `device: str?` | Check latency, FPS, memory and model size on edge hardware. | Planned |

### Compatibility

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `check_model_compatibility` | Check whether a model can run on a node: format, accelerator, runtime version, memory and expected FPS. | `tag: str`, `node_id: str` | Catch a bad match before deploying, instead of after it fails. | Planned |

## Camera

### Camera

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `list_cameras` | List cameras, optionally filtered. | `node_id: str?`, `cluster_id: str?`, `status: "online" \| "offline"?`, `query: str?` | Find cameras and see which ones are down. | Planned |
| `get_camera` | Get one camera by id, including source, resolution, zone and the deployment that processes it. | `camera_id: str` | Inspect a camera's configuration. | Planned |
| `add_camera` | Add a camera to an edge node. | `node_id: str`, `name: str`, `source_uri: str`, `zone: str?`, `metadata: dict?` | **Write.** Connect a new RTSP or USB camera. | Planned |
| `update_camera` | Update a camera's settings; only the given fields change. | `camera_id: str`, `name: str?`, `source_uri: str?`, `zone: str?`, `enabled: bool?` | **Write.** Change the source, rename, or enable or disable a camera. | Planned |
| `remove_camera` | Remove a camera from its node. | `camera_id: str` | **Write, destructive.** Take a camera out of service. | Planned |
| `assign_camera` | Attach a camera to a deployment so its runtime runs inference on the stream. | `camera_id: str`, `deployment_id: str` | **Write.** Choose which model processes which camera. | Planned |

### Stream

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `get_stream_status` | Get the live health of a camera stream: connection, FPS, dropped frames and last frame time. | `camera_id: str` | Detect a frozen or disconnected stream. | Planned |
| `get_camera_snapshot` | Get the latest frame of a camera, optionally with detections drawn on it. | `camera_id: str`, `annotated: bool = true` | Let the assistant see what the camera sees. | Planned |

## Monitoring

### Telemetry

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `get_latest_telemetry` | Latest telemetry sample of a node, keyed by kind (system, gpu, runtime). | `node: ref`, `cluster: ref?` | Check a node's current CPU, memory, GPU and temperature. | Done |
| `get_telemetry_history` | Recent telemetry samples of one kind for a node, newest first. | `node: ref`, `cluster: ref?`, `kind: "system" \| "gpu" \| "runtime"`, `limit: int = 100` | Analyse trends such as load spikes. | Done |

### Events

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `get_node_events` | Recent events reported by a node (deployment results, errors, state changes). | `node: ref`, `cluster: ref?`, `limit: int = 50` | Trace what happened on a node. | Done |

### Logs

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `search_logs` | Search logs across agents and runtimes. | `node_id: str?`, `runtime_id: str?`, `level: str?`, `query: str?`, `since: datetime?`, `limit: int = 100` | Find an error message across the fleet. For one runtime, use `get_runtime_logs`. | Planned |

### Alerts

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `list_alerts` | List alerts such as node offline, high temperature, FPS drop or camera down. | `status: "open" \| "acknowledged" \| "resolved"?`, `severity: str?`, `node_id: str?`, `limit: int = 50` | See what needs attention now. | Planned |
| `acknowledge_alert` | Mark an alert as acknowledged, with an optional note. | `alert_id: str`, `note: str?` | **Write.** Record that someone is handling the alert. | Planned |

## Inference

### Metrics

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `get_inference_metrics` | Get live inference statistics: FPS, latency and detection counts. | `deployment_id: str?`, `camera_id: str?`, `model_tag: str?`, `since: datetime?` | Compare real-world performance with the offline benchmark. | Planned |

### Detections

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `list_detections` | List recent detections, optionally filtered. | `camera_id: str?`, `class_name: str?`, `min_confidence: float?`, `since: datetime?`, `limit: int = 50` | Check what the model is detecting on a camera. | Planned |

### Violations

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `list_violations` | List PPE violations, optionally filtered. | `camera_id: str?`, `cluster_id: str?`, `violation_type: str?`, `since: datetime?`, `limit: int = 50` | Review safety violations and find the worst areas. | Planned |
| `get_violation` | Get one violation, including its evidence image and detections. | `violation_id: str` | Verify a violation or check for a false positive. | Planned |

## Diagnostics

Each diagnostic tool gathers status, recent events, logs and metrics for one target and returns a list of findings with likely causes. The assistant calls one tool instead of chaining five or six.

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `diagnose_node` | Check a node's heartbeat, agent, resources and runtimes. | `node_id: str` | Answer "why is this node offline or slow?" | Planned |
| `diagnose_runtime` | Check a runtime's state, restarts, logs and resource use. | `runtime_id: str` | Answer "why does this runtime keep crashing?" | Planned |
| `diagnose_deployment` | Check a deployment's rollout, revisions, runtime health and model compatibility. | `deployment_id: str` | Answer "why did this deployment fail?" | Planned |
| `diagnose_camera` | Check a camera's connection, stream health and the inference running on it. | `camera_id: str` | Answer "why does this camera show no detections?" | Planned |

## Knowledge

Retrieval over the project's own documents: operator runbooks, deployment guides, hardware notes, model cards and PPE safety regulations. Documents are chunked, embedded and stored in a vector index.

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `search_knowledge` | Semantic search over the knowledge base. Returns the most relevant chunks with their source document and section. | `query: str`, `category: "runbook" \| "deployment" \| "hardware" \| "model" \| "regulation"?`, `top_k: int = 5` | Ground answers in the project's documentation, e.g. how to fix a known error or which PPE rule a violation breaks. | Planned |
| `get_knowledge_document` | Get the full text of one knowledge document or section. | `document_id: str`, `section: str?` | Read the whole procedure when a search result is only a fragment. | Planned |

## Meta

Tool discovery. With 60 domain tools, only a small core set is loaded into the assistant's context at the start of a conversation; the rest are found and loaded on demand through `search_tools`.

| Tool name | Description | Parameters | Purpose | Status |
|---|---|---|---|---|
| `search_tools` | Search the MCP tool catalog by what the user wants to do. Returns matching tool names with their description and full parameter schema, so the assistant can call them next. | `query: str`, `group: "fleet" \| "deployment" \| "model" \| "camera" \| "monitoring" \| "inference" \| "diagnostics" \| "knowledge"?`, `top_k: int = 5` | Keep the context small: load only the tools a request needs instead of all 60. | Planned |

Always-loaded core set: `search_tools`, `search_knowledge`, `list_clusters`, `list_nodes`, `list_deployments`, `list_alerts` and the four `diagnose_*` tools. Every other tool is loaded through `search_tools`.

## Not exposed to the assistant

These dashboard features stay REST-only. They are admin actions or only make sense in a browser.

| Feature | Endpoints | Reason |
|---|---|---|
| Users | `GET/POST /users`, `GET/PATCH /users/{id}` | Account management is admin-only. |
| Audit logs | `GET /system/audit-logs` | Admin-only. |
| Settings | `GET/PATCH /system/settings` | Admin-only; a mistake affects the whole system. |
| Stream view token | `GET /streaming/cameras/{id}/view-token` | Only useful to a browser opening a stream. The assistant uses `get_camera_snapshot`. |

## Summary

| Group | Done | Planned | Total |
|---|---|---|---|
| Fleet | 7 | 8 | 15 |
| Deployment | 8 | 5 | 13 |
| Model | 0 | 9 | 9 |
| Camera | 0 | 8 | 8 |
| Monitoring | 3 | 3 | 6 |
| Inference | 0 | 4 | 4 |
| Diagnostics | 0 | 4 | 4 |
| Knowledge | 0 | 2 | 2 |
| Meta | 0 | 1 | 1 |
| **All** | **18** | **44** | **62** |

`control_runtime` stands in for `start_runtime`, `stop_runtime` and `restart_runtime`, so those three are not counted separately.

## Design notes

- Search is part of the `list_*` tools through filter parameters (`query`, `status`, `limit`). The only separate search tool is `search_logs`, because logs have no list endpoint.
- At 62 tools the assistant does not load every tool at once. It starts with the core set and loads the rest through `search_tools` (see [Meta](#meta)).
- `search_tools` and `search_knowledge` can share the same embedding model and vector store, each with its own index.
