# Build context: app/ . Needs an NVIDIA GPU. The base image brings DeepStream, GStreamer, TensorRT and pyds:
#   x86 (server):  nvcr.io/nvidia/deepstream:8.0-triton-multiarch
#   Jetson:        nvcr.io/nvidia/deepstream-l4t:<the version of the JetPack on the device>-samples-multiarch
# The TensorRT engine is built for the device it runs on (see docs) and mounted at EDGE_ENGINE_PATH.
ARG DEEPSTREAM_IMAGE=nvcr.io/nvidia/deepstream:8.0-triton-multiarch
FROM ${DEEPSTREAM_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv

COPY services/edge/requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

COPY package/edge_link ./edge_link
RUN pip3 install --no-deps ./edge_link
COPY services/edge ./edge
RUN pip3 install --no-deps ./edge

CMD ["python3", "-m", "edge"]
