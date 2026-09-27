# Edge Inference and Frame Flow

## Current implementation

The edge agent performs inference locally. The current pipeline does **not** send raw video frames to the server.

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#76B900","primaryTextColor":"#000000","primaryBorderColor":"#5C8F00","lineColor":"#333333","fontFamily":"Helvetica, Arial, sans-serif","fontSize":"14px","clusterBkg":"#F2F2F2","clusterBorder":"#CCCCCC","tertiaryColor":"#FFFFFF"}}}%%
flowchart LR
    subgraph EDGE["Edge"]
        E["Edge Agent<br/>capture + inference"]
    end
    subgraph TRANSPORT["Transport"]
        M["MQTT Broker"]
    end
    subgraph CLOUD["Server / Cloud"]
        S["Backend Server"]
    end
    subgraph CLIENT["Client"]
        F["Frontend"]
    end

    E -->|device.violation| M
    M -->|event| S
    S -->|alert via WebSocket| F
    F -->|request evidence| S

    classDef band fill:#F2F2F2,stroke:#CCCCCC,color:#000000
    class EDGE,TRANSPORT,CLOUD,CLIENT band
```

### Current data path

1. `CameraPipeline` reads a frame from the configured camera or video source.
2. `InferenceRuntime.infer(frame)` runs locally on the edge device.
3. `evaluate_ppe()` converts detections into violation types such as `no_helmet`.
4. A cooldown prevents repeated events for the same violation type.
5. `EdgeLink.send_violation()` publishes a JSON envelope through the configured `MessageBus`.
6. The server validates the payload and stores the violation.

The current payload contains metadata only:

```json
{
  "zone": "line-a",
  "violation_type": "no_helmet",
  "confidence": 0.91,
  "image_path": null,
  "recorded_at": "2026-09-05T10:00:00Z"
}
```

`image_path` is populated when the optional edge evidence uploader successfully
uploads a selected JPEG frame to the server. If upload fails, the violation is
still published with `image_path: null`.

## Recommended frame flow

Raw frames should not be sent through MQTT. A frame can be large, slow, and likely to create backpressure for heartbeat and command traffic.

Recommended flow:

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#76B900","primaryTextColor":"#000000","primaryBorderColor":"#5C8F00","lineColor":"#333333","fontFamily":"Helvetica, Arial, sans-serif","fontSize":"14px","actorBkg":"#76B900","actorBorder":"#5C8F00","actorTextColor":"#000000","signalColor":"#333333","signalTextColor":"#000000","labelBoxBkg":"#F2F2F2","labelBoxBorderColor":"#CCCCCC"}}}%%
sequenceDiagram
    participant F as Frontend
    participant S as Backend Server
    participant M as MQTT Broker
    participant E as Edge Agent

    E->>E: Capture frame and run local inference
    alt No violation
        E->>E: Continue local loop
    else Violation detected
        E->>E: Encode evidence and prepare metadata
        E->>M: Publish ViolationPayload
        M->>S: Deliver event
        S->>S: Persist violation and evidence URI
        S-->>F: Push alert via WebSocket
        F->>S: Request evidence image
    end
```

### Recommended responsibilities

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#76B900","primaryTextColor":"#000000","primaryBorderColor":"#5C8F00","lineColor":"#333333","fontFamily":"Helvetica, Arial, sans-serif","fontSize":"13px","clusterBkg":"#F2F2F2","clusterBorder":"#CCCCCC"}}}%%
flowchart LR
    subgraph EDGE["Edge Agent"]
        direction LR
        CP["CameraPipeline<br/>capture · inference<br/>rule eval · cooldown"]
        ES["EvidenceStore<br/>upload bytes<br/>return image URI"]
        EL["EdgeLink<br/>publish metadata<br/>via MessageBus"]
    end
    subgraph INFRA["Shared Infrastructure"]
        direction LR
        MQ["MQTT<br/>small JSON metadata<br/>not binary frames"]
        OS["Object Storage<br/>JPEG / PNG<br/>evidence frames"]
    end
    subgraph SERVER["Server"]
        SG["Server Gateway<br/>validate · persist<br/>expose signed URL"]
    end

    CP --> ES --> OS
    CP --> EL --> MQ --> SG
    OS --> SG

    classDef band fill:#F2F2F2,stroke:#CCCCCC,color:#000000
    class EDGE,INFRA,SERVER band
```

A reusable interface can be introduced in the edge application:

```python
class EvidenceStore(Protocol):
    async def put(self, data: bytes, *, key: str, content_type: str) -> str: ...
```

Possible implementations:

```text
LocalEvidenceStore       local disk, development only
S3EvidenceStore          S3 or MinIO, recommended for production
HttpEvidenceStore        upload to a server endpoint
```

The current implementation provides a local server evidence endpoint for a
working end-to-end flow. It can later be replaced by an S3/MinIO uploader behind
the same edge-side uploader interface.

The preferred production sequence is:

```text
edge inference -> encode evidence -> object storage -> publish image_uri event
```

## Important design rules

- Keep inference local to reduce bandwidth and latency.
- Send only evidence frames, not the complete video stream.
- Resize or JPEG-compress evidence before upload.
- Use a deterministic object key containing device, camera, timestamp, and event ID.
- Include checksum, content type, and retention metadata when needed.
- Make evidence upload and event publishing retryable and idempotent.
- Do not block heartbeat delivery while uploading a large image.
- Treat the image URI as optional so metadata-only operation remains supported.
