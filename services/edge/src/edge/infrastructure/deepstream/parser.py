"""The output of a YOLO-style detector as detections in the camera's own pixels.

DeepStream hands over the model's raw output tensor (`network-type=100`), so decoding it is done here, in plain numpy.
An end-to-end export gives one row per object, `x1 y1 x2 y2 confidence class`, with no non-maximum suppression left to do; an
export without it gives `(4 + classes, anchors)`, which needs the suppression. Both are in the pixels of the square the
frame was letterboxed into (centred, padded), so the boxes are mapped back to the frame."""

import numpy as np
import cv2


def parse_yolo(output: np.ndarray, conf: float, net_size: int, width: int, height: int) -> list[tuple[int, float, tuple[int, int, int, int]]]:
    """(class id, confidence, (x1, y1, x2, y2) in the frame's pixels) for every object at or above `conf`."""
    o = np.asarray(output, dtype=np.float32)
    o = o.reshape(o.shape[-2], o.shape[-1]) if o.ndim > 2 else o
    if o.shape[-1] == 6:
        rows = o[o[:, 4] >= conf]
        boxes, scores, classes = rows[:, :4], rows[:, 4], rows[:, 5].astype(int)
    elif o.shape[0] < o.shape[1]:
        boxes, scores, classes = _suppressed(o.T, conf)
    else:
        raise ValueError(f"unexpected YOLO output shape {o.shape}")
    r = min(net_size / height, net_size / width)
    left, top = (net_size - round(width * r)) // 2, (net_size - round(height * r)) // 2
    found = []
    for b, s, c in zip(boxes, scores, classes):
        x1 = int(np.clip((b[0] - left) / r, 0, width))
        y1 = int(np.clip((b[1] - top) / r, 0, height))
        x2 = int(np.clip((b[2] - left) / r, 0, width))
        y2 = int(np.clip((b[3] - top) / r, 0, height))
        if x2 > x1 and y2 > y1:
            found.append((int(c), float(s), (x1, y1, x2, y2)))
    return found


def _suppressed(p: np.ndarray, conf: float, iou: float = 0.7):
    """The raw (anchors, 4 + classes) rows: centre and size, then a score per class. Keeps the best of overlapping boxes."""
    scores = p[:, 4:].max(1)
    keep = scores >= conf
    p, scores = p[keep], scores[keep]
    classes = p[:, 4:].argmax(1)
    xy, wh = p[:, :2], p[:, 2:4]
    boxes = np.concatenate([xy - wh / 2, xy + wh / 2], 1)
    if not len(boxes):
        return boxes, scores, classes
    wanted = cv2.dnn.NMSBoxes(
        [[float(b[0]), float(b[1]), float(b[2] - b[0]), float(b[3] - b[1])] for b in boxes], scores.tolist(), conf, iou,
    )
    idx = np.array(wanted).reshape(-1)
    return boxes[idx], scores[idx], classes[idx]
