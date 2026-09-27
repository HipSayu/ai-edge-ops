# Flows

One file per business flow. Every flow file follows the same 10-section template:

| # | Section | Contents |
|---|---|---|
| 1 | Overview | Purpose · Scope · Actors / Components |
| 2 | High-Level Flow | `flowchart LR`, main components only — no classes |
| 3 | Sequence Diagram | system-level sequence: Edge Camera · Server · Frontend · MQTT · DB |
| 4 | Component Responsibilities | table |
| 5 | Detailed Service Flow | the only section that goes deep — sequence with real classes / internal services |
| 6 | Data Flow | plain-text data path |
| 7 | Error Handling | failure → handling table |
| 8 | Observability | Logs · Metrics · Tracing |
| 9 | Configuration | knob → description → default table |
| 10 | Related Components | code pointers |

Diagram rules: plain mermaid only (no `%%{init}%%`); in mermaid text avoid `<…>`,
a leading `{`, and a bare `>` (they break rendering). Grouped by domain.

| Domain | Folder | Flows |
|---|---|---|
| Edge ⇄ server control plane (MQTT) | [edge-server/](edge-server/) | heartbeat · telemetry · logs · device-offline · deploy-model · update-config · command-ack |
| Local inference | [inference/](inference/) | bbox-overlay · violation-alert · evidence |
| Video streaming (WebRTC) | [streaming/](streaming/) | edge-publish · frontend-view |
| Frontend ⇄ server | [frontend/](frontend/) | rest-auth · websocket |

Each folder's `README.md` holds the shared context for that domain (topic map, Envelope
contract, token scheme, ...). System-wide map: [../ARCHITECTURE.md](../ARCHITECTURE.md).
