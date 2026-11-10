"""The parts of the DeepStream adapter that need no DeepStream: the model output decoder and the property file."""

from pathlib import Path

import numpy as np
import pytest

from edge.infrastructure.deepstream.config import CameraSource, DeepStreamConfig, nvinfer_properties
from edge.infrastructure.deepstream.parser import parse_yolo


def test_an_end_to_end_row_is_mapped_back_to_the_frame():
    # a 1920x1080 frame letterboxed into 960: scale 0.5, 210 rows of padding above and below
    output = np.zeros((1, 300, 6), np.float32)
    output[0, 0] = [100, 250, 300, 450, 0.9, 2]  # in the 960 square
    output[0, 1] = [0, 0, 10, 10, 0.1, 1]  # under the threshold
    [(cls, conf, box)] = parse_yolo(output, 0.35, 960, 1920, 1080)
    assert (cls, round(conf, 2)) == (2, 0.9)
    assert box == (200, 80, 600, 480)


def test_boxes_never_leave_the_frame():
    output = np.array([[[-50, -50, 2000, 2000, 0.8, 0]]], np.float32)
    [(_, _, box)] = parse_yolo(output, 0.35, 960, 1920, 1080)
    assert box == (0, 0, 1920, 1080)


def test_a_raw_output_gets_its_overlapping_boxes_suppressed():
    anchors = np.zeros((4 + 3, 20), np.float32)  # (4 + classes, anchors): cx, cy, w, h, then a score per class
    anchors[:, 0] = [480, 480, 100, 100, 0.0, 0.9, 0.0]
    anchors[:, 1] = [482, 482, 100, 100, 0.0, 0.8, 0.0]  # the same object again
    anchors[:, 2] = [200, 200, 40, 40, 0.0, 0.0, 0.7]
    found = parse_yolo(anchors[None], 0.35, 960, 960, 960)
    assert sorted(c for c, _, _ in found) == [1, 2]


def test_a_shape_it_does_not_know_is_refused():
    with pytest.raises(ValueError):
        parse_yolo(np.zeros((1, 10, 10), np.float32), 0.35, 960, 640, 480)


def config(**kw) -> DeepStreamConfig:
    cameras = (CameraSource(1, "rtsp://a/1"), CameraSource(2, "file:///v.mp4"))
    return DeepStreamConfig(cameras=cameras, engine_path=Path("e.engine"), class_names=("a", "b", "c"), **kw)


def test_the_batch_is_the_number_of_cameras():
    text = nvinfer_properties(config())
    assert "batch-size=2" in text and "num-detected-classes=3" in text and "network-type=100" in text


def test_the_precision_names_the_network_mode():
    assert "network-mode=2" in nvinfer_properties(config(precision="fp16"))
    assert "network-mode=1" in nvinfer_properties(config(precision="int8"))
    with pytest.raises(ValueError):
        nvinfer_properties(config(precision="int4"))


def test_only_a_network_address_is_a_live_camera():
    live = [c.live for c in config().cameras]
    assert live == [True, False]
