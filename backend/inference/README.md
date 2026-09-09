# inference — the vision runtime (`vision_runtime`)

Camera capture → model inference → PPE rule → WHIP video publish. Built by CI into
a **per-model OCI image** (one variant per edge backend: `*-cpu`, `*-gpu`) and run
as the `inference` compose service next to the edge agent.

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
  Dockerfile.cpu  Dockerfile.gpu
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

CI, per `model_version`, builds **both** variants from the exported weights and
records the digests on the row:

```
docker build -f Dockerfile.cpu --build-arg MODEL_VERSION=42 -t registry/org/models/ppe:v42-cpu backend
docker build -f Dockerfile.gpu --build-arg MODEL_VERSION=42 -t registry/org/models/ppe:v42-gpu backend
# model_versions.image_repo / image_cpu_digest / image_gpu_digest
```

Deploy is then just: server picks the variant by `device.backend`, sends the
digest; the agent's `ComposeRunner` rewrites `INFERENCE_IMAGE` and
`docker compose up -d --wait inference`. See `docs/flows/edge-server/deploy-model.md`.

## Dev / test

```bash
uv run --extra dev pytest -q          # DummyRuntime, no cv2/GPU needed
```
