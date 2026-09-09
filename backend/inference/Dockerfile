# Model image — capture + inference + PPE rule + WHIP publish, weights baked in.
# ONE image per model version, multi-arch (linux/amd64 + linux/arm64). The
# runtime auto-detects the accelerator (CUDA / MPS / CPU) at start — GPU vs CPU
# is NOT a build-time choice.
#
# Built by .github/workflows/build-model-image.yml. Local:
#   docker buildx build -f backend/inference/Dockerfile \
#     --platform linux/amd64,linux/arm64 \
#     --build-arg MODEL_VERSION=1.3.0 \
#     -t ghcr.io/hopquangdo/ai-edge-ops-model:1.3.0 --push backend
#
# Jetson with a real TensorRT/DeepStream pipeline: see Dockerfile.jetson (future).
FROM python:3.11-slim

ARG MODEL_VERSION=0
ENV MODEL_VERSION_ID=${MODEL_VERSION} \
    RUNTIME=auto \
    DEVICE=auto \
    SOCKET_PATH=/run/edge/inference.sock \
    MODEL_DIR=/models \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY packages/svc_core        /srv/packages/svc_core
COPY libs/edge_protocol       /srv/libs/edge_protocol
COPY inference                /srv/inference

RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir -e "/srv/packages/svc_core" \
 && pip install --no-cache-dir -e "/srv/libs/edge_protocol" \
 && pip install --no-cache-dir -e "/srv/inference[cpu,inference]"

# CI drops the exported weights here (model.pt / model.onnx)
COPY --chown=root:root models/ /models/

# OCI + model metadata — the server's ModelCatalog reads these labels instead of
# a DB row. build-model-image.yml fills them from workflow inputs.
ARG MODEL_TASK=detect
ARG MODEL_CLASSES=""
ARG MODEL_MAP50_95=""
ARG MODEL_PARAMS_M=""
ARG MODEL_LATENCY_MS=""
ARG MODEL_BASE=""
ARG VCS_REF=""
ARG BUILD_DATE=""
LABEL org.opencontainers.image.title="ai-edge-ops model" \
      org.opencontainers.image.version="${MODEL_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/hopquangdo/ai-edge-ops" \
      ai.edge-ops.model.task="${MODEL_TASK}" \
      ai.edge-ops.model.classes="${MODEL_CLASSES}" \
      ai.edge-ops.model.map50_95="${MODEL_MAP50_95}" \
      ai.edge-ops.model.params_m="${MODEL_PARAMS_M}" \
      ai.edge-ops.model.latency_ms="${MODEL_LATENCY_MS}" \
      ai.edge-ops.model.base="${MODEL_BASE}"

CMD ["vision-runtime"]
