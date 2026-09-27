# edge_agent

Runs on each edge device (Jetson). MQTT link to the control plane, model runtime,
camera → PPE-rule pipeline, local HTTP API on `:9100`.

**Full guide:** [`docs/run-edge-agent.md`](../../../docs/run-edge-agent.md)

```bash
# smoke run, no broker/camera/GPU
TRANSPORT=memory DEVICE_ID=dev-1 edge

# real
DEVICE_ID=1 TRANSPORT=mqtt MQTT__HOST=localhost \
CAMERAS__0__ID=bay-1 CAMERAS__0__SOURCE=0 CAMERAS__0__ZONE=loading-bay \
edge
```

Docker: compose lives in `../../deploy/`. Local demo — from `deploy/`:
`COMPOSE_ENV_FILES=.env.infra,.env.app,.env.edge docker compose --profile edge up`.
On a real device — copy `deploy/compose.edge.yml` → `compose.yml` + `deploy/.env.edge.example`
→ `.env.edge`, then `COMPOSE_ENV_FILES=.env.edge docker compose up -d`.
Real YOLO: `pip install -e ".[inference]"` (uses the vendored `package/ultralytics`).
