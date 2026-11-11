# Chạy từng service

Mọi lệnh chạy từ thư mục `app/`. Có hai cách: **Docker** (từng container) và **máy host** (uvicorn, tiện debug).

Cổng: cloud `8100` (compose publish ra `8200`) · web `8080` · db `5432` · qdrant `6333` · redis `6379` · mosquitto `8883` (TLS).

## 0. Chuẩn bị (một lần)

```bash
cp .env.example .env                                              # biến cho compose: mật khẩu DB, MQTT, Redis, cổng
cp services/cloud/.env.example services/cloud/.env
#   Chat cần Dunly: xem "Trợ lý chat (Dunly)" trong README.md

mkdir -p volume/keys volume/regulations
openssl genrsa -out volume/keys/safety-private.pem 2048           # khóa ký token, chỉ cloud đọc

bash docs/mosquitto/make-certs.sh                                 # chứng chỉ TLS cho MQTT (tạo volume/mosquitto/certs)
mkdir -p volume/mosquitto/data
cp docs/mosquitto/mosquitto.conf docs/mosquitto/acl volume/mosquitto/
docker run --rm -it -v "$PWD/volume/mosquitto:/work" eclipse-mosquitto:2 mosquitto_passwd -c /work/passwd cloud
docker run --rm -it -v "$PWD/volume/mosquitto:/work" eclipse-mosquitto:2 mosquitto_passwd /work/passwd node-1
#   cloud: mật khẩu điền vào MQTT_CLOUD_PASSWORD (.env gốc). Mỗi edge node một user mang tên node id, chỉ ghi được dưới ppe/<node id>/.
#   Đặt REDIS_PASSWORD trong .env gốc.
```

## 1. Chạy bằng Docker, từng container

`--no-deps` để chỉ chạy đúng service được gọi, không kéo theo service phụ thuộc. Vì vậy phải chạy theo thứ tự dưới đây.

```bash
# 1) Hạ tầng
docker compose up -d db
docker compose up -d mosquitto
docker compose up -d redis              # chờ "healthy"
docker compose up -d qdrant
docker compose up -d mediamtx            # camera RTSP giả, không bắt buộc

# 2) Cloud (cần db + mosquitto + redis đã chạy)
docker compose up -d --build --no-deps cloud
docker compose ps cloud                  # chờ "healthy"

# 3) Web (cần cloud)
docker compose up -d --build --no-deps web
```

Mở http://localhost:8080.

Quản lý một service:

```bash
docker compose logs -f cloud             # xem log
docker compose restart cloud             # khởi động lại
docker compose stop web                  # dừng
docker compose up -d --build --no-deps cloud   # sửa code rồi build lại đúng service đó
```

Sửa `.env` của một service thì chạy lại `docker compose up -d --no-deps <service>` để container nhận biến mới.

## 2. Chạy trên máy host (uvicorn)

Cài môi trường một lần (uv workspace, các package nội bộ được cài dạng editable):

```bash
uv sync
```

Hạ tầng vẫn chạy bằng Docker nếu cần (`db`, `mosquitto`, `redis`, `qdrant`). Có thể bỏ qua khi thử nhanh: cloud dùng SQLite trong `volume/data/` và không subscribe MQTT nếu `CLOUD_MQTT_HOST` trống; assistant giữ phiên chat trong bộ nhớ tiến trình (mất khi khởi động lại) nếu `ASSISTANT_REDIS_URL` trống.

Mỗi service chạy trong một terminal riêng. `--env-file` nạp đúng `.env` của service đó.

```bash
# Cloud :8100
uv run uvicorn cloud.interface.main:app --port 8100 --env-file services/cloud/.env
```

Thêm `--reload` khi đang sửa code.

Chạy với PostgreSQL và MQTT của Docker (đặt trước lệnh cloud):

```bash
export CLOUD_DATABASE_URL="postgresql+psycopg://safety:<POSTGRES_PASSWORD>@localhost:5432/safety"
export CLOUD_MQTT_HOST=localhost CLOUD_MQTT_PORT=8883 CLOUD_MQTT_USERNAME=cloud CLOUD_MQTT_PASSWORD=<MQTT_CLOUD_PASSWORD>
export CLOUD_MQTT_TLS_CA=volume/mosquitto/certs/ca.crt
export CLOUD_REDIS_URL="redis://:<REDIS_PASSWORD>@localhost:6379/0"
```

(Service `db` trong compose không publish cổng 5432 ra host; muốn dùng thì thêm `ports: ["5432:5432"]` cho `db`.)

Web (Vite, :5173, proxy tới cloud):

```bash
cd apps/web
npm install
npm run dev
```

## 3. Edge giả lập (demo, thử tải)

Không cần camera hay model: mỗi edge giả là một user MQTT riêng, gửi vi phạm ngẫu nhiên.

```bash
# Tạo 12 node x 3 camera trong cloud (ghi volume/data/fake-edges/fleet.json). Chạy lại không tạo trùng.
FAKE_ADMIN_PASSWORD=<mật khẩu admin> uv run python tools/fake_edges/fake_edges.py provision --api http://localhost:8200 --nodes 12 --cameras 3

# User broker cho 12 node (cùng một mật khẩu), rồi nạp lại broker
bash docs/mosquitto/add-users.sh '<mật khẩu edge giả>' $(seq -f 'edge-sim-%02g' 1 12)
docker compose restart mosquitto

# Chạy: bằng Docker (đặt FAKE_EDGE_PASSWORD trong .env gốc)...
docker compose --profile sim up -d --build fake-edges
# ...hoặc từ máy host
FAKE_MQTT_PASSWORD='<mật khẩu edge giả>' uv run python tools/fake_edges/fake_edges.py run --interval 2
```

`--nodes` thay đổi số edge (ví dụ 50), `--interval` là số giây trung bình giữa hai sự kiện của một node, `--duration` để tự dừng.
Dừng: `docker compose --profile sim stop fake-edges`.

## 3b. Vùng cấm và cảnh báo tại chỗ

Trên web, mở một camera (cửa sổ camera ở trang giám sát), bấm **Draw zone**, bấm lên hình để đặt các góc, rồi **Save and send to edge**
(cần quyền OPERATOR). Cloud lưu vùng và gửi xuống node chạy camera đó qua MQTT (thông điệp giữ lại, chủ đề `ppe/config/cameras/{camera_id}/zones`).
Edge kiểm tra điểm chân của từng người đã theo vết; ai đi vào vùng thì có một sự kiện `zone_intrusion` gửi lên cloud và chuông báo vang ngay tại node, không cần mạng.

- Cho phép node đọc cấu hình và cloud ghi cấu hình: dùng `docs/mosquitto/acl` (hai dòng `ppe/config/#`), chép vào `volume/mosquitto/acl` rồi `docker compose restart mosquitto`.
- Edge giữ bản sao vùng ở `EDGE_ZONES_PATH` (mặc định `data/zones.json`; trong Compose là `volume/edge-data`), nên khởi động lại khi mất mạng vẫn có vùng.
- Chuông: luôn có một dòng nhật ký `ALARM ...`. Thêm `EDGE_ALARM_COMMAND` (danh sách tham số dạng JSON, ví dụ `["aplay", "/sounds/alarm.wav"]`; lệnh nhận `PPE_ALARM_CAMERA` và `PPE_ALARM_ZONE`) để phát âm thanh hoặc đóng relay, và/hoặc `EDGE_ALARM_URL` (gọi GET, thay `{camera}` và `{zone}`) cho còi nối mạng.
- Các thông số khác: `EDGE_ZONE_CLASSES` (nhãn tính là người, mặc định `["person"]`), `EDGE_ZONE_COOLDOWN_SEC` (mặc định 10 giây giữa hai lần báo khi người đó còn trong vùng), `EDGE_ZONES_ENABLED`.

## 4. Kiểm tra nhanh

```bash
curl http://localhost:8200/api/health     # cloud (cổng publish của compose; chạy trên host: 8100)
```

## 5. Dừng

```bash
docker compose stop web                   # dừng vài service
docker compose down                       # dừng và xóa container, dữ liệu trong volume/ được giữ
```
