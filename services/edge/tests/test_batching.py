"""Frames of several cameras go through the model together, and each camera gets its own answer."""

import threading
import time

import numpy as np
import pytest

from edge.domain.detection import Detection
from edge.infrastructure.batching_detector import BatchingDetector


class Model:
    """Marks each detection with the frame's first pixel, so an answer can be matched to its frame."""

    def __init__(self, delay=0.0, fail=False):
        self.sizes, self.delay, self.fail = [], delay, fail

    def detect_batch(self, images):
        time.sleep(self.delay)
        if self.fail:
            raise RuntimeError("model broke")
        self.sizes.append(len(images))
        return [[Detection("person", 0.9, (int(img[0, 0, 0]), 0, 1, 1))] for img in images]


def frame(value):
    return np.full((2, 2, 3), value, np.uint8)


def test_every_camera_gets_the_answer_of_its_own_frame():
    detector = BatchingDetector(Model(), max_batch=8)
    answers = {}

    def camera(value):
        answers[value] = detector.detect(frame(value))[0].box[0]

    threads = [threading.Thread(target=camera, args=(v,)) for v in range(1, 7)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert answers == {v: v for v in range(1, 7)}


def test_frames_that_wait_together_are_one_call():
    model = Model(delay=0.05)
    detector = BatchingDetector(model, max_batch=8, gather_sec=0.02)
    threads = [threading.Thread(target=detector.detect, args=(frame(v),)) for v in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sum(model.sizes) == 6 and len(model.sizes) < 6  # fewer calls than frames


def test_a_batch_is_never_larger_than_the_limit():
    model = Model(delay=0.03)
    detector = BatchingDetector(model, max_batch=3, gather_sec=0.02)
    threads = [threading.Thread(target=detector.detect, args=(frame(v),)) for v in range(9)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert max(model.sizes) <= 3 and sum(model.sizes) == 9


def test_a_broken_model_fails_the_waiting_cameras_and_the_next_call_works():
    model = Model(fail=True)
    detector = BatchingDetector(model, max_batch=4)
    with pytest.raises(RuntimeError):
        detector.detect(frame(1))
    model.fail = False
    assert detector.detect(frame(2))[0].box[0] == 2
