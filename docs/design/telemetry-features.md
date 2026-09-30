# Telemetry Feature Specification

## 1. Overview

Tài liệu này định nghĩa tập feature telemetry dùng cho hệ thống **Edge AI Early Warning**.

Mục tiêu:

* Chuẩn hóa dữ liệu telemetry từ Edge Node.
* Làm đầu vào cho Anomaly Detection và Early Degradation Prediction.
* Làm contract chung giữa Edge Agent, telemetry storage, simulator và ML pipeline.
* Hỗ trợ sinh dữ liệu synthetic cho quá trình huấn luyện và đánh giá model.

Pipeline:

```mermaid
flowchart LR
    A["Edge Agent"] --> B["Telemetry"]
    B --> C["Time-series Storage"]
    C --> D["Sliding Window"]
    D --> E["Feature Engineering"]
    E --> F["ML Model"]
    F --> G["Risk Score"]
    G --> H["Alert"]
```

---

# 2. Feature Groups

Telemetry được chia thành 7 nhóm:

| Group           | Mục đích                           |
| --------------- | ---------------------------------- |
| Node Resource   | Theo dõi tài nguyên phần cứng      |
| Thermal & Power | Phát hiện quá nhiệt / throttling   |
| Storage         | Phát hiện disk/inode pressure      |
| Network         | Phát hiện suy giảm kết nối         |
| Runtime         | Theo dõi AI inference runtime      |
| Camera / Sensor | Theo dõi chất lượng input          |
| Model Output    | Theo dõi bất thường ở output model |

---

# 3. Node Resource Features

## 3.1 CPU

| Feature                | Type  | Unit | Description              |
| ---------------------- | ----- | ---- | ------------------------ |
| `cpu_usage_pct`        | float | %    | CPU utilization          |
| `cpu_load_1m`          | float | load | CPU load trong 1 phút    |
| `cpu_load_5m`          | float | load | CPU load trong 5 phút    |
| `cpu_iowait_pct`       | float | %    | CPU time waiting for I/O |
| `cpu_context_switches` | float | /sec | Context switch rate      |

### Ý nghĩa

CPU tăng cao kéo dài có thể dẫn tới:

```text
CPU pressure
    ↓
Runtime scheduling delay
    ↓
Inference latency ↑
    ↓
FPS ↓
    ↓
Degraded
```

---

# 4. Memory Features

| Feature               | Type  | Unit   | Description        |
| --------------------- | ----- | ------ | ------------------ |
| `memory_usage_pct`    | float | %      | RAM utilization    |
| `memory_available_mb` | float | MB     | RAM còn khả dụng   |
| `memory_used_mb`      | float | MB     | RAM đang sử dụng   |
| `swap_usage_pct`      | float | %      | Swap utilization   |
| `memory_growth_rate`  | float | MB/min | Tốc độ tăng memory |

Đặc biệt:

```text
memory_growth_rate > 0
```

duy trì trong thời gian dài có thể là dấu hiệu memory leak.

---

# 5. GPU / NPU Features

Đối với Jetson hoặc thiết bị có accelerator:

| Feature                | Type  | Unit | Description             |
| ---------------------- | ----- | ---- | ----------------------- |
| `gpu_usage_pct`        | float | %    | GPU utilization         |
| `gpu_memory_usage_pct` | float | %    | GPU memory utilization  |
| `gpu_memory_used_mb`   | float | MB   | GPU memory đang sử dụng |
| `gpu_frequency_mhz`    | float | MHz  | GPU frequency           |
| `gpu_power_w`          | float | W    | GPU power consumption   |
| `gpu_temperature_c`    | float | °C   | GPU temperature         |

Các feature này giúp phân biệt:

```text
High GPU usage
        +
High latency
        +
Low FPS
        ↓
GPU overload
```

với trường hợp CPU hoặc camera là nguyên nhân.

---

# 6. Thermal Features

| Feature              | Type  | Unit   | Description                     |
| -------------------- | ----- | ------ | ------------------------------- |
| `temperature_c`      | float | °C     | Device temperature              |
| `cpu_temperature_c`  | float | °C     | CPU temperature                 |
| `gpu_temperature_c`  | float | °C     | GPU temperature                 |
| `temperature_rate`   | float | °C/min | Tốc độ tăng nhiệt               |
| `thermal_throttling` | bool  | -      | Có thermal throttling hay không |

### Important

Không nên chỉ dùng:

```text
temperature > threshold
```

Mà nên kết hợp:

```text
temperature
temperature_rate
gpu_usage
cpu_usage
inference_latency
inference_fps
thermal_throttling
```

Ví dụ:

```text
Temperature ↑
        +
Temperature slope ↑
        +
GPU usage ↑
        +
FPS ↓
        +
Latency ↑
        ↓
Thermal degradation
```

---

# 7. Power Features

| Feature            | Type  | Unit  | Description            |
| ------------------ | ----- | ----- | ---------------------- |
| `power_w`          | float | W     | Current device power   |
| `power_rate`       | float | W/min | Power change rate      |
| `power_limit_w`    | float | W     | Device power limit     |
| `power_throttling` | bool  | -     | Power throttling state |

Power telemetry đặc biệt hữu ích với Edge device hoạt động liên tục.

---

# 8. Storage Features

| Feature            | Type  | Unit | Description       |
| ------------------ | ----- | ---- | ----------------- |
| `disk_usage_pct`   | float | %    | Disk utilization  |
| `disk_free_gb`     | float | GB   | Free disk space   |
| `inode_usage_pct`  | float | %    | Inode utilization |
| `disk_read_mb_s`   | float | MB/s | Read throughput   |
| `disk_write_mb_s`  | float | MB/s | Write throughput  |
| `disk_io_wait_pct` | float | %    | I/O waiting       |

Ví dụ:

```text
disk_usage ↑
        +
disk_free ↓
        +
disk_write ↑
        ↓
Storage pressure
```

---

# 9. Network Features

| Feature                      | Type  | Unit  | Description                |
| ---------------------------- | ----- | ----- | -------------------------- |
| `network_rtt_ms`             | float | ms    | Round-trip latency         |
| `packet_loss_pct`            | float | %     | Packet loss                |
| `network_rx_mb_s`            | float | MB/s  | Receive throughput         |
| `network_tx_mb_s`            | float | MB/s  | Transmit throughput        |
| `connection_reconnect_count` | int   | count | Reconnection count         |
| `mqtt_publish_latency_ms`    | float | ms    | MQTT publish latency       |
| `telemetry_queue_size`       | int   | count | Pending telemetry messages |

Network degradation có thể biểu hiện:

```text
RTT ↑
Packet loss ↑
Reconnect ↑
Queue size ↑
```

trước khi Edge Node thực sự mất kết nối.

---

# 10. Runtime Features

Đây là nhóm feature quan trọng nhất đối với **AI inference health**.

| Feature                 | Type  | Unit  | Description        |
| ----------------------- | ----- | ----- | ------------------ |
| `runtime_cpu_pct`       | float | %     | Runtime CPU usage  |
| `runtime_memory_mb`     | float | MB    | Runtime memory     |
| `runtime_restart_count` | int   | count | Runtime restarts   |
| `runtime_uptime_sec`    | float | sec   | Runtime uptime     |
| `runtime_error_rate`    | float | %     | Runtime error rate |
| `runtime_queue_size`    | int   | count | Inference queue    |
| `runtime_status`        | enum  | -     | Runtime state      |

Runtime state:

```text
STARTING
RUNNING
DEGRADED
STOPPING
STOPPED
FAILED
```

---

# 11. Inference Performance Features

| Feature                  | Type  | Unit  | Description                 |
| ------------------------ | ----- | ----- | --------------------------- |
| `inference_fps`          | float | FPS   | Actual inference throughput |
| `target_fps`             | float | FPS   | Expected FPS                |
| `effective_fps_ratio`    | float | ratio | Actual / target FPS         |
| `inference_latency_ms`   | float | ms    | Average inference latency   |
| `inference_p50_ms`       | float | ms    | P50 latency                 |
| `inference_p95_ms`       | float | ms    | P95 latency                 |
| `inference_p99_ms`       | float | ms    | P99 latency                 |
| `inference_error_rate`   | float | %     | Inference errors            |
| `inference_timeout_rate` | float | %     | Timeout rate                |

Đây là các feature trực tiếp phản ánh chất lượng AI runtime.

Ví dụ:

```text
effective_fps_ratio < 0.7
        +
p95_latency > 2 × baseline
        ↓
Potential degradation
```

---

# 12. Camera / Sensor Features

| Feature                      | Type  | Unit       | Description              |
| ---------------------------- | ----- | ---------- | ------------------------ |
| `camera_fps`                 | float | FPS        | Input camera FPS         |
| `camera_target_fps`          | float | FPS        | Expected camera FPS      |
| `camera_frame_age_ms`        | float | ms         | Age of latest frame      |
| `camera_frame_drop_pct`      | float | %          | Dropped frames           |
| `camera_freeze_duration_sec` | float | sec        | Duration of frozen frame |
| `camera_brightness`          | float | normalized | Average brightness       |
| `camera_blur_score`          | float | score      | Image sharpness          |
| `camera_status`              | enum  | -          | Camera state             |

Camera state:

```text
ONLINE
DEGRADED
FROZEN
DISCONNECTED
```

Ví dụ:

```text
camera_fps ↓
camera_frame_age ↑
camera_freeze_duration ↑
        ↓
Camera degradation
```

---

# 13. Model Output Features

Nhóm này theo dõi hành vi của AI model thay vì chỉ theo dõi hardware.

| Feature                  | Type  | Unit    | Description                |
| ------------------------ | ----- | ------- | -------------------------- |
| `detection_count`        | int   | count   | Number of detections       |
| `confidence_mean`        | float | 0–1     | Mean confidence            |
| `confidence_std`         | float | score   | Confidence variation       |
| `confidence_min`         | float | 0–1     | Minimum confidence         |
| `class_entropy`          | float | entropy | Class distribution entropy |
| `unknown_detection_rate` | float | %       | Unknown/OOD rate           |
| `output_change_rate`     | float | ratio   | Output distribution change |

Ví dụ:

```text
confidence_mean ↓
        +
detection_count ↓
        +
class_distribution_change ↑
        ↓
Possible input/model drift
```

---

# 14. Node Availability Features

| Feature             | Type  | Unit  | Description               |
| ------------------- | ----- | ----- | ------------------------- |
| `heartbeat_age_sec` | float | sec   | Time since last heartbeat |
| `node_uptime_sec`   | float | sec   | Node uptime               |
| `reboot_count`      | int   | count | Number of reboots         |
| `process_count`     | int   | count | Running processes         |
| `agent_status`      | enum  | -     | Edge Agent state          |

Agent state:

```text
ONLINE
DEGRADED
OFFLINE
UNKNOWN
```

---

# 15. Temporal Features

Raw telemetry không nên đưa trực tiếp toàn bộ vào model.

Với mỗi metric quan trọng, tạo temporal features trên sliding window.

Ví dụ window:

```text
Sampling interval = 5 sec
Window = 5 min

5 min / 5 sec = 60 samples
```

Với metric `temperature_c`:

| Feature                | Description                |
| ---------------------- | -------------------------- |
| `temperature_current`  | Giá trị hiện tại           |
| `temperature_mean_5m`  | Mean 5 phút                |
| `temperature_min_5m`   | Minimum                    |
| `temperature_max_5m`   | Maximum                    |
| `temperature_std_5m`   | Standard deviation         |
| `temperature_slope_5m` | Xu hướng tăng/giảm         |
| `temperature_delta_5m` | Thay đổi so với đầu window |

Tương tự áp dụng cho:

```text
CPU
Memory
GPU
Temperature
FPS
Latency
Error rate
Queue size
Network RTT
Camera FPS
Confidence
```

---

# 16. Derived Features

Một số feature nên được tính từ nhiều telemetry khác nhau.

## 16.1 FPS Ratio

```text
effective_fps_ratio =
    inference_fps / target_fps
```

Ví dụ:

```text
target_fps = 30
inference_fps = 21

effective_fps_ratio = 0.70
```

---

## 16.2 Latency Ratio

```text
latency_ratio =
    current_p95_latency / baseline_p95_latency
```

---

## 16.3 Queue Growth

```text
queue_growth_rate =
    Δqueue_size / Δtime
```

Queue tăng liên tục là dấu hiệu runtime không xử lý kịp input.

---

## 16.4 Resource Pressure

Có thể tạo feature tổng hợp:

```text
resource_pressure =
    weighted(
        cpu_usage,
        memory_usage,
        gpu_usage,
        temperature
    )
```

Feature này có thể dùng cho analysis nhưng **không nên thay thế raw features** trong training.

---

# 17. State Labels

Telemetry được gắn operational state:

```text
NORMAL
WARNING
DEGRADED
CRITICAL
```

### NORMAL

Node hoạt động bình thường.

```text
FPS ≈ target
Latency ≈ baseline
Error rate thấp
Resource ổn định
```

### WARNING

Có dấu hiệu bất thường nhưng chưa ảnh hưởng nghiêm trọng.

```text
Temperature tăng
CPU tăng
Memory tăng
Latency bắt đầu tăng
```

### DEGRADED

AI pipeline đã có dấu hiệu suy giảm rõ ràng.

```text
FPS giảm đáng kể
Latency tăng
Queue tăng
Error rate tăng
Camera input giảm
```

### CRITICAL

Node/runtime gần như không còn đáp ứng yêu cầu vận hành.

```text
Runtime FAILED
Camera DISCONNECTED
Inference FPS ≈ 0
Node OFFLINE
```

---

# 18. Early Warning Target

Đối với XGBoost, target không nên chỉ là:

```text
current_state
```

mà nên dự đoán degradation trong tương lai.

Ví dụ:

```text
Input window:
t - 5 min ─────────────── t

Target:
t ─────────────── t + 10 min
```

Target:

```text
future_degradation = 1
```

nếu trong 10 phút tiếp theo node chuyển sang:

```text
DEGRADED
```

hoặc:

```text
CRITICAL
```

Ngược lại:

```text
future_degradation = 0
```

nếu node tiếp tục hoạt động bình thường.

---

# 19. Feature Priority

Không nhất thiết feature nào cũng cần đưa vào model ngay từ đầu.

## Tier 1 — Core

```text
cpu_usage_pct
memory_usage_pct
gpu_usage_pct
temperature_c
disk_usage_pct
network_rtt_ms
packet_loss_pct
inference_fps
inference_p95_ms
inference_error_rate
runtime_queue_size
camera_fps
camera_frame_age_ms
```

## Tier 2 — Advanced

```text
cpu_iowait_pct
gpu_memory_usage_pct
gpu_power_w
temperature_rate
memory_growth_rate
disk_io_wait_pct
mqtt_publish_latency_ms
runtime_restart_count
camera_frame_drop_pct
camera_blur_score
confidence_mean
confidence_std
detection_count
```

## Tier 3 — Research

```text
class_entropy
unknown_detection_rate
output_change_rate
embedding_distance
input_distribution_shift
model_prediction_drift
```

---

# 20. Recommended Initial Feature Vector

Phiên bản đầu tiên của model có thể sử dụng:

```text
X = [
    cpu_usage_pct,
    cpu_load_5m,

    memory_usage_pct,
    memory_growth_rate,

    gpu_usage_pct,
    gpu_memory_usage_pct,

    temperature_c,
    temperature_rate,

    disk_usage_pct,

    network_rtt_ms,
    packet_loss_pct,

    inference_fps,
    effective_fps_ratio,
    inference_p95_ms,
    inference_error_rate,

    runtime_queue_size,
    runtime_restart_count,

    camera_fps,
    camera_frame_age_ms,
    camera_frame_drop_pct,

    detection_count,
    confidence_mean
]
```

Sau đó áp dụng temporal aggregation:

```text
current
mean_5m
max_5m
std_5m
slope_5m
delta_5m
```

Do đó số feature thực tế có thể tăng lên đáng kể.

---

# 21. Feature → Failure Scenario Mapping

| Scenario                 | Main Features                            |
| ------------------------ | ---------------------------------------- |
| CPU Pressure             | CPU, latency, FPS                        |
| Memory Leak              | memory, memory growth, swap              |
| GPU Overload             | GPU, GPU memory, latency, FPS            |
| Thermal Throttling       | temperature, temperature slope, GPU, FPS |
| Power Pressure           | power, temperature, frequency            |
| Disk Pressure            | disk, inode, I/O                         |
| Network Degradation      | RTT, packet loss, reconnect, queue       |
| Camera Degradation       | camera FPS, frame age, frame drop        |
| Inference Worker Failure | runtime status, FPS, errors, restart     |
| Model/Input Drift        | confidence, detection count, entropy     |
| Node Failure             | heartbeat, agent status, uptime          |

---

# 22. Data Schema

Một telemetry record:

```json
{
  "timestamp": "2026-09-27T10:00:00Z",
  "node_id": "node-001",

  "cpu_usage_pct": 72.4,
  "memory_usage_pct": 61.2,

  "gpu_usage_pct": 84.5,
  "gpu_memory_usage_pct": 67.3,

  "temperature_c": 74.2,
  "power_w": 18.4,

  "disk_usage_pct": 71.5,

  "network_rtt_ms": 24.5,
  "packet_loss_pct": 0.2,

  "inference_fps": 24.8,
  "target_fps": 30,
  "inference_p95_ms": 61.4,
  "inference_error_rate": 0.3,

  "runtime_queue_size": 4,
  "runtime_restart_count": 0,

  "camera_fps": 29.7,
  "camera_frame_age_ms": 42,
  "camera_frame_drop_pct": 0.8,

  "detection_count": 7,
  "confidence_mean": 0.81
}
```

Label của training dataset:

```json
{
  "state": "WARNING",
  "future_degradation": 1,
  "scenario": "thermal_degradation"
}
```

---

# 23. Design Principles

### 23.1 Raw telemetry phải được giữ lại

Không chỉ lưu feature đã aggregate.

```text
Raw telemetry
      ↓
Feature Engineering
      ↓
Training features
```

Điều này cho phép thay đổi feature engineering mà không cần thu thập lại dữ liệu.

### 23.2 Không phụ thuộc threshold trong feature

Ví dụ không nên biến:

```text
temperature > 80
```

thành feature duy nhất.

Nên giữ:

```text
temperature_c
temperature_mean_5m
temperature_max_5m
temperature_slope_5m
```

để model tự học quan hệ giữa các tín hiệu.

### 23.3 Không dùng feature gây leakage

Không đưa các thông tin chỉ xuất hiện **sau khi failure xảy ra** vào input của early-warning model.

Ví dụ:

```text
node_failed = true
runtime_status = FAILED
```

không được dùng để dự đoán failure trước đó.

### 23.4 Feature definition phải thống nhất

Simulator, Edge Agent và training pipeline phải dùng cùng schema:

```text
Edge Agent
     │
     ├── telemetry schema
     │
     ▼
Simulator ───────► Training Dataset
     │
     ▼
Production Telemetry
```

---

# 24. Initial Model Input

Phiên bản MVP:

```text
Telemetry
    ↓
5-second sampling
    ↓
5-minute sliding window
    ↓
Temporal Feature Engineering
    ↓
~20–30 core metrics
    ↓
XGBoost
    ↓
Degradation Probability
```

Isolation Forest sử dụng cùng telemetry nhưng phục vụ mục tiêu khác:

```text
Isolation Forest
    └── "Is current behavior abnormal?"

XGBoost
    └── "Will degradation happen soon?"
```

Đây là hai bài toán khác nhau và nên được đánh giá riêng.
