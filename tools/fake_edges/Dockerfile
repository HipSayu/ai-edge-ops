# Build context: app/ . A fleet of fake edge nodes: no model, no cameras, only MQTT (see fake_edges.py).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv

RUN pip install paho-mqtt==2.1.0 httpx numpy opencv-python-headless
COPY package/edge_link ./edge_link
COPY tools/fake_edges/fake_edges.py ./fake_edges.py

ENTRYPOINT ["python", "fake_edges.py"]
CMD ["run"]
