FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY requirements-assistant.txt .
COPY packages/http packages/http
COPY packages/observability packages/observability
RUN pip install -r requirements-assistant.txt
COPY src/__init__.py src/
COPY src/assistant/ src/assistant/
COPY src/shared/ src/shared/
COPY apps/__init__.py apps/
COPY apps/assistant/ apps/assistant/
# Knowledge content is read from here at runtime; Qdrant keeps only the embeddings
COPY docs/knowledge/ docs/knowledge/
EXPOSE 8100
CMD ["python", "-m", "apps.assistant.main"]
