"""The property file `nvinfer` reads, and the two values of DeepStream's own that the adapter shares."""

from pathlib import Path

from edge.bootstrap.config.deepstream import DeepStreamConfig

_NETWORK_MODE = {"fp32": 0, "int8": 1, "fp16": 2}  # nvinfer's network-mode; only informative for an engine that is already built
PGIE_ID = 1  # the unique id of the detector (gie-unique-id)
NO_TRACK = 0xFFFFFFFFFFFFFFFF  # the object id DeepStream gives to an object no tracker has followed


def nvinfer_properties(cfg: DeepStreamConfig) -> str:
    """The property file of the detector: the prebuilt engine, its input, and 'no post-processing, give me the tensor'."""
    mode = _NETWORK_MODE.get(cfg.precision.lower())
    if mode is None:
        raise ValueError(f"unknown precision {cfg.precision!r}: use fp32, fp16 or int8")
    return "\n".join([
        "[property]",
        "gpu-id=0",
        "net-scale-factor=0.0039215697906911373",
        "model-color-format=0",  # RGB
        f"model-engine-file={Path(cfg.engine_path).resolve().as_posix()}",
        f"batch-size={cfg.batch_size}",
        f"network-mode={mode}",
        f"num-detected-classes={len(cfg.class_names)}",
        f"interval={cfg.interval}",
        f"gie-unique-id={PGIE_ID}",
        "process-mode=1",
        "network-type=100",  # other: DeepStream does not decode the output, parser.py does
        "output-tensor-meta=1",
        "maintain-aspect-ratio=1",
        "symmetric-padding=1",
        "cluster-mode=4",
        "",
    ])
