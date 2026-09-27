# Edge Agent and Server Communication

## End-to-end communication

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#76B900","primaryTextColor":"#000000","primaryBorderColor":"#5C8F00","lineColor":"#333333","fontFamily":"Helvetica, Arial, sans-serif","fontSize":"14px","clusterBkg":"#F2F2F2","clusterBorder":"#CCCCCC"}}}%%
flowchart LR
    subgraph CLIENT["Client"]
        F["Frontend"]
    end
    subgraph CLOUD["Server / Cloud"]
        S["Backend Server"]
    end
    subgraph TRANSPORT["Transport"]
        M["MQTT Broker"]
    end
    subgraph EDGE["Edge"]
        E["Edge Agent"]
    end

    F <-->|REST / WebSocket| S
    S <-->|Publish / Subscribe| M
    E <-->|Publish / Subscribe| M

    classDef band fill:#F2F2F2,stroke:#CCCCCC,color:#000000
    class CLIENT,CLOUD,TRANSPORT,EDGE band
```

The system has four communication actors only:

- **Frontend**: sends user actions and receives dashboard updates.
- **Backend Server**: handles API, business logic, persistence, and realtime relay.
- **MQTT Broker**: transports commands and edge messages.
- **Edge Agent**: runs local inference and reports device state/events.

The PostgreSQL reference schema for the backend is available at
[`schema.sql`](../schema.sql). The application currently creates the same ORM
tables during startup through `init_db()`.

## Topic map

| Direction | Topic | Message types | Purpose |
|---|---|---|---|
| Edge -> server | `agent/devices/{id}/state` | `device.heartbeat`, `device.state` | Health, runtime state, model state |
| Edge -> server | `agent/devices/{id}/events` | `device.violation` | PPE or other detected events |
| Edge -> server | `agent/devices/{id}/logs` | `device.log` | Edge runtime logs |
| Edge -> server | `agent/devices/{id}/telemetry` | `device.telemetry` | Batched metrics |
| Server -> edge | `agent/devices/{id}/cmd` | `command.deploy_model`, `command.update_config`, `command.restart`, `command.run_diagnostics` | Remote commands |
| Edge -> server | `agent/devices/{id}/ack` | `command.ack` | Command result |

## Server to frontend realtime flow

The server does not forward MQTT frames directly to the browser. It validates and
persists the edge message first, publishes an application event, and then a relay
converts that event into a WebSocket envelope.

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#76B900","primaryTextColor":"#000000","primaryBorderColor":"#5C8F00","lineColor":"#333333","fontFamily":"Helvetica, Arial, sans-serif","fontSize":"14px","actorBkg":"#76B900","actorBorder":"#5C8F00","actorTextColor":"#000000","signalColor":"#333333","signalTextColor":"#000000","labelBoxBkg":"#F2F2F2","labelBoxBorderColor":"#CCCCCC"}}}%%
sequenceDiagram
    participant F as Frontend
    participant S as Backend Server
    participant M as MQTT Broker
    participant E as Edge Agent

    E->>M: heartbeat / state / violation
    M->>S: MQTT message
    S->>S: Validate and persist data
    S-->>F: WebSocket telemetry or alert
```

### Current WebSocket channels

```text
GET /ws/telemetry
    subscribes to telemetry/#
    receives telemetry.device and telemetry.agent

GET /ws/alerts
    subscribes to alerts/#
    receives alert.created

GET /agent/ws/logs
    subscribes to logs/#
    receives device.log
```

The current relays are:

```text
HeartbeatRecorded -> telemetry/{device_id}
HeartbeatRecorded -> telemetry/agent
AlertRaised       -> alerts/{severity}
```

The WebSocket payload is a JSON-encoded `Envelope` sent as a text frame, so the
frontend can parse `event.data` directly.

## Heartbeat flow

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#76B900","primaryTextColor":"#000000","primaryBorderColor":"#5C8F00","lineColor":"#333333","fontFamily":"Helvetica, Arial, sans-serif","fontSize":"14px","actorBkg":"#76B900","actorBorder":"#5C8F00","actorTextColor":"#000000","signalColor":"#333333","signalTextColor":"#000000","labelBoxBkg":"#F2F2F2","labelBoxBorderColor":"#CCCCCC"}}}%%
sequenceDiagram
    participant F as Frontend
    participant S as Backend Server
    participant M as MQTT Broker
    participant E as Edge Agent

    loop Every heartbeat interval
        E->>E: Collect device metrics
        E->>M: device.heartbeat on state topic
        M->>S: Deliver heartbeat
        S->>S: Store metrics and update online status
        S-->>F: Push telemetry via WebSocket
    end
```

## Deployment command flow

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#76B900","primaryTextColor":"#000000","primaryBorderColor":"#5C8F00","lineColor":"#333333","fontFamily":"Helvetica, Arial, sans-serif","fontSize":"14px","actorBkg":"#76B900","actorBorder":"#5C8F00","actorTextColor":"#000000","signalColor":"#333333","signalTextColor":"#000000","labelBoxBkg":"#F2F2F2","labelBoxBorderColor":"#CCCCCC"}}}%%
sequenceDiagram
    participant F as Frontend
    participant S as Backend Server
    participant M as MQTT Broker
    participant E as Edge Agent

    F->>S: Activate deployment
    S->>M: command.deploy_model
    M->>E: Deliver command
    E->>E: Download and load model
    E->>M: command.ack
    E->>M: device.state
    M->>S: Deliver ACK and state
    S-->>F: Return status via REST/WebSocket
```

## Current implementation caveats

1. The server must use `edge_transport=mqtt` when the edge agent runs with MQTT. If the server uses `InMemoryMessageBus`, it cannot communicate with a separate edge process.
2. `AgentGateway` currently subscribes to state, telemetry, and events. The ACK topic must also be subscribed and handled before command status can be tracked reliably.
3. MQTT reconnect and subscription restoration need to be implemented for production reliability.
4. Heartbeat, command, ACK, and evidence upload should have independent retry/backpressure policies.
5. Correlation IDs should be preserved from the command envelope through the ACK and persisted with the deployment command.

## Recommended command state machine

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#76B900","primaryTextColor":"#000000","primaryBorderColor":"#5C8F00","lineColor":"#333333","fontFamily":"Helvetica, Arial, sans-serif","fontSize":"14px"}}}%%
stateDiagram-v2
    [*] --> Pending
    Pending --> Sent: publish command
    Sent --> Accepted: receive accepted ACK
    Sent --> Failed: receive failed ACK
    Accepted --> InProgress: edge starts work
    InProgress --> Succeeded: state report active
    InProgress --> Failed: state report failed
    Sent --> TimedOut: ACK timeout
    TimedOut --> Retrying: retry policy allows
    Retrying --> Sent
    Succeeded --> [*]
    Failed --> [*]
```

## Complete inference-to-dashboard flow

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#76B900","primaryTextColor":"#000000","primaryBorderColor":"#5C8F00","lineColor":"#333333","fontFamily":"Helvetica, Arial, sans-serif","fontSize":"14px","actorBkg":"#76B900","actorBorder":"#5C8F00","actorTextColor":"#000000","signalColor":"#333333","signalTextColor":"#000000","labelBoxBkg":"#F2F2F2","labelBoxBorderColor":"#CCCCCC"}}}%%
sequenceDiagram
    participant F as Frontend
    participant S as Backend Server
    participant M as MQTT Broker
    participant E as Edge Agent

    E->>E: Capture frame, run inference, evaluate PPE
    E->>M: device.violation + optional evidence URI
    M->>S: Deliver violation event
    S->>S: Store violation and prepare alert
    S-->>F: Push alert via WebSocket
    F->>S: Load evidence through HTTP when needed
```
