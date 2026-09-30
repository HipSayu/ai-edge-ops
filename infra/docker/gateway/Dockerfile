FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY requirements-gateway.txt .
COPY packages/http packages/http
COPY packages/observability packages/observability
RUN pip install -r requirements-gateway.txt
COPY src/__init__.py src/
COPY src/gateway/ src/gateway/
COPY src/shared/ src/shared/
COPY apps/__init__.py apps/
COPY apps/gateway/ apps/gateway/
EXPOSE 8200
CMD ["python", "-m", "apps.gateway.main"]
