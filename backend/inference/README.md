# inference — the vision runtime (`vision_runtime`)

Camera capture → model inference → PPE rule → WHIP video publish. Baked (with the
weights) into a **per-model OCI image** and run as the `inference` compose
service next to the edge agent.

> **Building the model image is a separate concern — not part of this app.**
> The model/training pipeline (its own repo/process) exports weights and uses
> `Dockerfile` here as the contract: it must fill the `ai.edge-ops.model.*`
> labels. This app only *consumes* the resulting images from a registry
> (`ModelCatalog` reads those labels; the agent `docker compose pull`s the ref).

```
backend/inference/
  src/vision_runtime/
    config.py            WorkerSettings
    capture/             cv2 frame source (blocking; pulled off the loop)
    runtime/             InferenceRuntime: base / dummy / yolo / deepstream(skeleton)
    publish/             WHIP video publisher (ffmpeg -f whip)
    rules/ppe.py         evaluate_ppe(list[Detection], required)
    pipeline.py          CameraPipeline — one camera
    worker.py            VisionWorker — owns cameras, serves the agent IPC channel
    main.py              serve the unix socket, run the worker forever
  package/ultralytics/   vendored YOLO (submodule), used by the [inference] extra
  Dockerfile             the model-image contract — one multi-arch image (amd64 +
                         arm64), runtime auto-detects CUDA / MPS / CPU
  Dockerfile.jetson      future: DeepStream/TensorRT path for Jetson GPU
```

## IPC with the agent

Unix socket at `SOCKET_PATH` (shared volume). Newline-framed `edge_protocol.Envelope`s
(`edge_protocol.channel`). The agent connects; the worker:

| direction | message |
|---|---|
| worker → agent | `T_VR_HELLO`, `T_VR_HEALTH`, `T_BBOX_FRAME` (every frame), `T_VIOLATION` |
| worker → agent | `T_STREAM_TOKEN_REQUEST` (needs a WHIP token for a camera) |
| agent → worker | `T_VR_SET_CAMERAS` (camera list + thresholds + evidence creds), `T_VR_STREAM_TOKEN` (reply) |

The agent holds the MQTT identity and forwards frames/violations upstream; the
worker has no control-plane credential.

## Model image

One multi-arch image per model version, tagged `…/ai-edge-ops-model:<version>`:

```
docker buildx build -f backend/inference/Dockerfile \
  --platform linux/amd64,linux/arm64 \
  --build-arg MODEL_VERSION=1.3.0 \
  --build-arg MODEL_CLASSES=helmet,vest,person \
  --build-arg MODEL_MAP50_95=0.41 \
  -t ghcr.io/hopquangdo/ai-edge-ops-model:1.3.0 --push backend
```

GPU vs CPU is **not** a build choice — `_resolve_device` probes
`torch.cuda.is_available()` at start. Deploy: server sends the ref, the agent's
`ComposeRunner` rewrites `INFERENCE_IMAGE` and `docker compose up -d --wait
inference`. See `docs/flows/edge-server/deploy-model.md`.

### Labels the pipeline must set

| label | example |
|---|---|
| `org.opencontainers.image.version` | `1.3.0` |
| `ai.edge-ops.model.task` | `detect` |
| `ai.edge-ops.model.classes` | `helmet,vest,person` |
| `ai.edge-ops.model.map50_95` | `0.41` |
| `ai.edge-ops.model.params_m` | `2.6` |
| `ai.edge-ops.model.latency_ms` | `7.8` |
| `ai.edge-ops.model.base` | `yolo11n` |

## Dev / test

```bash
uv run --extra dev pytest -q          # DummyRuntime, no cv2/GPU needed
```
