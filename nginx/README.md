# Infra services

Postgres, Redis, EMQX (MQTT), MinIO, MediaMTX + a small nginx that exposes
MediaMTX's WHIP/WHEP under `/edgeops`. Runs on the services box
(`192.168.100.35`). server / frontend / edge agent are configured separately.

```
   192.168.100.35   (docker compose up -d in this folder — project "edgeops")
   ┌──────────────────────────────────────────────────────┐
   │ nginx      :80      /edgeops/cam_*/whip|whep -> mediamtx
   │ postgres   :55432
   │ redis      :56379   (password)
   │ emqx       :51883   MQTT      :58083  dashboard
   │ minio      :59000   S3        :59001  console
   │ mediamtx   :58889   WHIP/WHEP HTTP     :58189/udp  WebRTC media
   └──────────────────────────────────────────────────────┘
```

## Run

```bash
cd nginx
# .env already has the generated secrets. Set VPS_HOST to whatever address
# browsers/edge reach MediaMTX on (192.168.100.35 for LAN-only, or the public IP).
docker compose up -d
docker compose ps
curl http://localhost/edgeops/          # -> "ai-edge-ops infra ok"
```

Ports to open on `192.168.100.35`: `80 55432 56379 51883 58083 59000 59001` TCP, `58189` UDP.

## What connects here

| from | to |
|---|---|
| server (`.35`) | `db:5432` `redis:6379` `mqtt:1883` `minio:9000` — internal docker network |
| server, run outside docker | `192.168.100.35:55432 / :56379 / :51883 / :59000` |
| edge agent | `192.168.100.35:51883` (MQTT) |
| browser (WHEP video) | `http://192.168.100.35/edgeops/cam_X/whep` + UDP `58189` |

## Public VPS proxy (210.245.52.119)

Two configs for the VPS's **system nginx** so the internet can reach the stack:

| file | into | forwards |
|---|---|---|
| `proxy.conf` | `/etc/nginx/conf.d/edgeops.conf` | `:58080` → `192.168.100.35:58889` : `/cam_*/whip\|whep` (MediaMTX signaling) |
| `proxy.stream.conf` | `/etc/nginx/stream.d/edgeops.conf` | TCP `51883` (MQTT) + optional `55432/56379/59000` + UDP `58189` (WebRTC) → `192.168.100.35` |

```bash
sudo cp proxy.conf        /etc/nginx/conf.d/edgeops.conf
sudo cp proxy.stream.conf /etc/nginx/stream.d/edgeops.conf   # see file header: add `stream {}` to nginx.conf first
sudo nginx -t && sudo systemctl reload nginx
# firewall: open 58080/tcp, 51883/tcp, 58189/udp (+ 55432/56379/59000 if used)
```

When serving video through the VPS, set `VPS_HOST=210.245.52.119` in `.env` and
re-`up` mediamtx.

## Notes

- Project prefix `edgeops` (`COMPOSE_PROJECT_NAME` in `.env`) — containers
  `edgeops-*`, volumes `edgeops_*`, network `edgeops_default`.
- No TLS — plain HTTP + raw TCP, guarded only by the passwords in `.env`.
- MediaMTX token auth is `internal` (open). Set `MTX_AUTH_METHOD=http` +
  `BACKEND_AUTH_URL=http://<server>/api/v1/streaming/auth` when ready.
- `.env` holds real secrets and is git-ignored — scp it to the box, or
  `git add -f nginx/.env`.
