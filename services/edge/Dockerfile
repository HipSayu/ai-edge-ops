# Build context: app/ . Dependencies: services/edge/requirements.txt. Runs next to the cameras (amd64 or arm64).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 && rm -rf /var/lib/apt/lists/*
WORKDIR /srv

# torch first, from the index named here: ultralytics would otherwise pull the CUDA build (several GB) from PyPI.
# CPU by default; for a GPU build pass --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cu126 (see docker-compose.gpu.yml)
ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu
RUN pip install --index-url ${TORCH_INDEX} torch==2.14.0 torchvision
COPY services/edge/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY package/edge_link ./edge_link
RUN pip install --no-deps ./edge_link
COPY services/edge ./edge
RUN pip install --no-deps ./edge

CMD ["python", "-m", "edge"]
