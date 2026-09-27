# Inference flows

The edge runs inference **locally**. Raw frames never cross MQTT. Per camera, two things
leave the box:

- **detection metadata** over MQTT — `device.bbox_frame` every frame, `device.violation` on a rule hit;
- **raw video** over WHIP to MediaMTX — a separate ffmpeg process ([../streaming/](../streaming/)).

`ComposedBackend` starts one `CameraPipeline` per enabled camera; each loop iteration:
read frame → skip if `not runtime.loaded` → `runtime.infer` → `_emit_bbox_frame` →
`evaluate_ppe` → per-type `_emit`.

| Flow | File |
|---|---|
| Live bbox overlay | [bbox-overlay.md](bbox-overlay.md) |
| Violation → alert | [violation-alert.md](violation-alert.md) |
| Evidence upload / fetch | [evidence.md](evidence.md) |
