# PPE Vision

Hệ thống giám sát an toàn lao động (PPE) gồm service `cloud` (Python) và 1 web app, chạy bằng Docker Compose. Trợ lý chat là một agent trong Dunly.

| Container | Vai trò | Cổng |
|---|---|---|
| `ppe-db` | PostgreSQL 16 | 5432 |
| `ppe-mosquitto` | MQTT broker (TLS): nhận sự kiện từ edge | 8883 |
| `ppe-redis` | Redis Stack: chống trùng sự kiện edge | 6379 (chỉ localhost) |
| `ppe-qdrant` | Kho vector cho tra cứu quy định | 6333 |
| `ppe-embedding` | Model embedding tiếng Việt (Hugging Face TEI) | nội bộ |
| `ppe-mediamtx` | Camera RTSP giả (lặp video) | 8554 |
| `ppe-cloud` | Người dùng, site/node/camera, vi phạm, vision, ảnh/báo cáo/quy định của chat (REST + MCP) | 8200 (API và `/mcp`) |
| `ppe-web` | Giao diện web (nginx) | **8080** |

Chi tiết kiến trúc các service: [services/README.md](services/README.md).

## Yêu cầu

- Docker Desktop đang chạy (`docker info` không báo lỗi).
- Chạy mọi lệnh bên dưới từ thư mục `app/`.

## Chuẩn bị lần đầu

```bash
# 1. File cấu hình
cp .env.example .env                  # biến cho compose: POSTGRES_PASSWORD, MQTT_CLOUD_PASSWORD, REDIS_PASSWORD, cổng
cp services/cloud/.env.example services/cloud/.env
#    Đổi các mật khẩu `change-me-...`. Chat cần Dunly: xem mục "Trợ lý chat (Dunly)" bên dưới.

# 2. Khóa ký token RS256 (chỉ service cloud đọc, không commit)
mkdir -p volume/keys
openssl genrsa -out volume/keys/safety-private.pem 2048

# 3. Trọng số model

# 4. Thư mục quy định cho trợ lý (có thể để trống)
mkdir -p volume/regulations

# 5. MQTT (TLS): chứng chỉ, ACL, cấu hình broker
bash docs/mosquitto/make-certs.sh        # thêm tên/IP máy chủ mà edge dùng để nối vào, nếu có
mkdir -p volume/mosquitto/data
cp docs/mosquitto/mosquitto.conf docs/mosquitto/acl volume/mosquitto/

# 6. Tài khoản MQTT: một user cho cloud, mỗi edge node một user mang tên node id (ACL chỉ cho node ghi dưới ppe/<node id>/)
docker run --rm -it -v "$PWD/volume/mosquitto:/work" eclipse-mosquitto:2 mosquitto_passwd -c /work/passwd cloud
docker run --rm -it -v "$PWD/volume/mosquitto:/work" eclipse-mosquitto:2 mosquitto_passwd /work/passwd node-1
#    mật khẩu của `cloud` điền vào MQTT_CLOUD_PASSWORD trong .env; của node-1 điền vào EDGE_MQTT_PASSWORD của edge đó
```

Video cho camera giả đặt trong `volume/data/video/`, cấu hình RTSP trong `volume/mediamtx/`.

## Build và chạy

```bash
docker compose up --build -d     # build tất cả image rồi chạy nền
docker compose ps                # xem trạng thái (cloud phải "healthy")
```

Mở http://localhost:8080.

## Build lại

```bash
docker compose build                     # build lại tất cả
docker compose build cloud              # chỉ một service: cloud | web
docker compose build --no-cache cloud   # bỏ cache khi nghi ngờ image cũ
docker compose up -d                     # áp dụng image mới (chỉ tạo lại container đổi)
```

Sau khi sửa code một service: `docker compose up -d --build <service>`.
Sửa `.env` thì chạy lại `docker compose up -d` để container nhận biến mới.

## Lệnh hay dùng

```bash
docker compose logs -f cloud        # xem log
docker compose restart cloud         # khởi động lại một service
docker compose down                  # dừng và xóa container (dữ liệu trong volume/ được giữ)
```

Xóa sạch dữ liệu DB: `docker compose down`, rồi xóa thư mục `volume/postgres/`.

## Trợ lý chat (Dunly)

Trợ lý là agent `ppe-assistant` trong [Dunly](https://github.com/hopquangdo/dunly). Cloud nhận chat của web, gọi Dunly bằng
API key và gửi kèm token của chính người đang chat; Dunly chuyển token đó sang MCP của cloud (`/mcp`), nên mọi thao tác
đọc/ghi đều theo quyền của người dùng. Thay đổi dữ liệu cần người dùng duyệt trong chat.

```bash
# Dunly đang chạy (mặc định http://localhost:8790) và đã có provider model. Tạo connector, agent và API key:
python tools/setup_dunly.py --model <tên model trong Dunly> --email <admin Dunly> --password <mật khẩu> \
    --mcp-url http://host.docker.internal:8200/mcp --new-key
# rồi ghi vào services/cloud/.env:
#   CLOUD_DUNLY_URL=http://host.docker.internal:8790
#   CLOUD_DUNLY_API_KEY=<key vừa in ra>
docker compose up -d cloud
```

Prompt của agent nằm ở `docs/dunly/ppe-assistant.md`, các skill ở `docs/dunly/skills/<tên>/SKILL.md` (kèm `assets/`). Script nạp skill qua API của Dunly (kiểu `inline`) và agent chỉ dùng chúng theo tên; chạy lại script để cập nhật. Ảnh đính kèm, báo cáo Word và tra
cứu quy định (Qdrant + embedding) là các tool của cloud, nên cloud cần `detector`, `qdrant` và `embedding` như trong compose.

## Chạy test (không cần Docker)

Mỗi service chạy test riêng từ thư mục của nó, ví dụ:

```bash
cd services/cloud
PYTHONPATH="../shared/src:src:../.." ../../.venv/Scripts/python.exe -m pytest -q
```

## Lỗi thường gặp

- `POSTGRES_PASSWORD ... Set POSTGRES_PASSWORD in .env`: chưa tạo `.env` hoặc thiếu biến này.
- `cloud` không lên healthy: kiểm tra `volume/keys/safety-private.pem` có tồn tại; xem `docker compose logs cloud`.
- `failed to connect to the docker API`: Docker Desktop chưa chạy.
- Chat không trả lời: chưa cấu hình `CLOUD_DUNLY_URL` / `CLOUD_DUNLY_API_KEY` (xem "Trợ lý chat (Dunly)"), hoặc Dunly chưa có API key của model.
- Chat báo `MCP server 'ppe-cloud' failed: ConnectError`: Dunly không gọi tới được cloud; kiểm tra `--mcp-url` đã đặt khi chạy `tools/setup_dunly.py`.
