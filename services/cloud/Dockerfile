# Build context: app/ . Dependencies: services/cloud/requirements.txt.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PYTHONPATH=/srv
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 && rm -rf /var/lib/apt/lists/*
WORKDIR /srv

COPY services/cloud/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY services/shared ./shared
RUN pip install --no-deps ./shared
COPY package/trace_id ./trace_id
RUN pip install --no-deps ./trace_id
COPY package/edge_link ./edge_link
RUN pip install --no-deps ./edge_link
COPY services/cloud ./cloud
RUN pip install --no-deps ./cloud

EXPOSE 8100
CMD ["uvicorn", "cloud.interface.main:app", "--no-access-log", "--host", "0.0.0.0", "--port", "8100"]
