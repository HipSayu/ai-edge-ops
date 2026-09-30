"""Synthetic edge-node telemetry for training early-degradation models (docs/design/telemetry-features.md).

`generate` simulates node episodes (healthy, benign load, or one failure scenario) at 5 s sampling with
the exact telemetry contract field names; `build` turns them into sliding windows for a sequence model.
"""
