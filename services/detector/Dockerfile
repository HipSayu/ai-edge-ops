# Build context: app/ . The PPE model behind HTTP, for the pictures users attach to the chat.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PYTHONPATH=/srv
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 && rm -rf /var/lib/apt/lists/*
WORKDIR /srv

# torch first, from the index named here (CPU by default; docker-compose.gpu.yml passes the CUDA one)
ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu
RUN pip install --index-url ${TORCH_INDEX} torch==2.14.0 torchvision
COPY services/detector/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# the edge's detector and renderer, so a picture is judged like a camera frame
COPY package/edge_link ./edge_link
RUN pip install --no-deps ./edge_link
COPY services/edge ./edge
RUN pip install --no-deps ./edge
COPY services/detector/src/detector ./detector

EXPOSE 8400
CMD ["uvicorn", "detector.app:app", "--no-access-log", "--host", "0.0.0.0", "--port", "8400"]
