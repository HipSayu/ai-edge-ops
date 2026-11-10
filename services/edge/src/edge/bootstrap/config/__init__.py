"""Every setting of the edge runtime, and how they become what the adapters are built with."""

from edge.bootstrap.config.deepstream import CameraSource, DeepStreamConfig, deepstream_config
from edge.bootstrap.config.settings import CameraConfig, NodeConfig, Settings

__all__ = ["CameraConfig", "CameraSource", "DeepStreamConfig", "NodeConfig", "Settings", "deepstream_config"]
