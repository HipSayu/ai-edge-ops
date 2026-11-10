"""The DetectionStream over NVIDIA DeepStream: every camera of a node in one GPU pipeline.

    nvurisrcbin x N -> nvstreammux (one batch, a frame of each camera) -> nvvideoconvert (RGBA)
        -> nvinfer (TensorRT engine, raw tensor out) -> [probe: tensor -> object meta] -> nvtracker -> [probe: detections out] -> fakesink

Decoding, scaling, batching, the model and the tracker all run on the GPU; Python only turns the model's tensor into
objects (before the tracker) and the tracked objects into `Detection`s (after it). Nothing is drawn: the picture is read
back to the CPU only when the camera's logic asks for it, which is when an event has been confirmed.

`gi` and `pyds` exist only where DeepStream is installed, so this module is imported only where it runs (the container
wires it in `bootstrap`); nothing else of the edge imports it."""

import ctypes
import logging
import threading

import cv2
import gi
import numpy as np

gi.require_version("Gst", "1.0")
import pyds  # noqa: E402  (pyds and gi.repository can only be imported once the Gst version is fixed)
from gi.repository import GLib, Gst  # noqa: E402

from edge.application.ports import DetectionHandler
from edge.domain.detection import Detection
from edge.infrastructure.deepstream.config import NO_TRACK, PGIE_ID, DeepStreamConfig, nvinfer_properties
from edge.infrastructure.deepstream.parser import parse_yolo

log = logging.getLogger("edge.deepstream")


class DeepStreamStream:
    def __init__(self, config: DeepStreamConfig) -> None:
        if not config.cameras:
            raise ValueError("a node needs at least one camera")
        self._cfg = config
        self._camera_of_source = [c.camera_id for c in config.cameras]
        self._handler: DetectionHandler | None = None

    # ------------------------------------------------------------------ building

    def _build(self, Gst):
        cfg = self._cfg
        cfg.work_dir.mkdir(parents=True, exist_ok=True)
        infer_cfg = cfg.work_dir / "nvinfer.txt"
        infer_cfg.write_text(nvinfer_properties(cfg), encoding="utf-8")

        pipeline = Gst.Pipeline.new("edge")
        mux = self._make(Gst, "nvstreammux", "mux")
        self._set(mux, **{
            "batch-size": cfg.batch_size, "width": cfg.mux_width, "height": cfg.mux_height,
            "batched-push-timeout": cfg.mux_timeout_us, "live-source": any(c.live for c in cfg.cameras),
            "nvbuf-memory-type": 3 if cfg.unified_memory else 0,
        })
        convert = self._make(Gst, "nvvideoconvert", "convert")
        self._set(convert, **{"nvbuf-memory-type": 3 if cfg.unified_memory else 0})
        caps = self._make(Gst, "capsfilter", "caps")
        caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=RGBA"))
        infer = self._make(Gst, "nvinfer", "infer")
        infer.set_property("config-file-path", str(infer_cfg))
        sink = self._make(Gst, "fakesink", "sink")
        sink.set_property("sync", False)  # as fast as the batches come

        chain = [mux, convert, caps, infer]
        tracker = None
        if cfg.tracking:
            tracker = self._make(Gst, "nvtracker", "tracker")
            self._set(tracker, **{
                "ll-lib-file": cfg.tracker_lib, "ll-config-file": cfg.tracker_config,
                "tracker-width": cfg.tracker_width, "tracker-height": cfg.tracker_height,
            })
            chain.append(tracker)
        chain.append(sink)
        for element in chain:
            pipeline.add(element)
        for a, b in zip(chain, chain[1:]):
            if not a.link(b):
                raise RuntimeError(f"cannot link {a.get_name()} to {b.get_name()}")

        for index, camera in enumerate(cfg.cameras):
            source = self._make(Gst, "nvurisrcbin", f"src{index}")
            self._set(source, **{"uri": camera.uri, "file-loop": not camera.live})
            if camera.live:
                self._set(source, **{"rtsp-reconnect-interval": cfg.reconnect_sec})
            if cfg.unified_memory:
                self._set(source, **{"cudadec-memtype": 2})
            pipeline.add(source)
            source.connect("pad-added", self._on_pad, mux, index, Gst)
        return pipeline, infer, tracker or infer

    @staticmethod
    def _make(Gst, factory: str, name: str):
        element = Gst.ElementFactory.make(factory, name)
        if element is None:
            raise RuntimeError(f"GStreamer element {factory!r} is missing: is DeepStream installed?")
        return element

    @staticmethod
    def _set(element, **props) -> None:
        """Sets what this DeepStream version knows; a property it does not have is skipped (the versions differ)."""
        for key, value in props.items():
            try:
                element.set_property(key.rstrip("_").replace("_", "-") if key.endswith("_") else key, value)
            except TypeError:
                log.warning("%s has no property %s: skipped", element.get_name(), key)

    @staticmethod
    def _on_pad(_source, pad, mux, index: int, Gst) -> None:
        caps = pad.get_current_caps() or pad.query_caps(None)
        if not caps.get_structure(0).get_name().startswith("video"):
            return
        sink_pad = mux.request_pad_simple(f"sink_{index}") if hasattr(mux, "request_pad_simple") else mux.get_request_pad(f"sink_{index}")
        if sink_pad is None or pad.link(sink_pad) != Gst.PadLinkReturn.OK:
            log.error("cannot link camera %s to the muxer", index)

    # ------------------------------------------------------------------ running

    def run(self, handler: DetectionHandler, stop: threading.Event) -> None:
        self._handler, self._pyds = handler, pyds
        Gst.init(None)
        pipeline, infer, last = self._build(Gst)
        infer.get_static_pad("src").add_probe(Gst.PadProbeType.BUFFER, self._tensor_probe)
        last.get_static_pad("src").add_probe(Gst.PadProbeType.BUFFER, self._detection_probe)

        loop = GLib.MainLoop()
        failure: list[str] = []
        bus = pipeline.get_bus()
        bus.add_signal_watch()

        def on_message(_bus, message) -> None:
            if message.type == Gst.MessageType.EOS:
                loop.quit()
            elif message.type == Gst.MessageType.ERROR:
                error, detail = message.parse_error()
                failure.append(f"{error.message} ({detail})")
                loop.quit()

        bus.connect("message", on_message)
        GLib.timeout_add(200, lambda: (loop.quit(), False)[1] if stop.is_set() else True)
        pipeline.set_state(Gst.State.PLAYING)
        try:
            loop.run()
        finally:
            pipeline.set_state(Gst.State.NULL)
        if failure:
            raise RuntimeError(failure[0])

    # ------------------------------------------------------------------ probes

    def _frames(self, buffer):
        """The frame metas of a batch, with the batch meta they belong to."""
        pyds = self._pyds
        batch = pyds.gst_buffer_get_nvds_batch_meta(hash(buffer))
        node = batch.frame_meta_list
        while node is not None:
            yield batch, pyds.NvDsFrameMeta.cast(node.data)
            try:
                node = node.next
            except StopIteration:
                break

    def _tensor_probe(self, pad, info):
        """Between the detector and the tracker: the model's tensor becomes the objects the tracker follows."""
        pyds, cfg = self._pyds, self._cfg
        buffer = info.get_buffer()
        if buffer is None:
            return 0  # Gst.PadProbeReturn.OK
        for batch, frame in self._frames(buffer):
            tensor = self._tensor_of(frame)
            if tensor is None:
                continue
            for cls, conf, (x1, y1, x2, y2) in parse_yolo(tensor, cfg.conf, cfg.net_size, frame.source_frame_width, frame.source_frame_height):
                obj = pyds.nvds_acquire_obj_meta_from_pool(batch)
                obj.unique_component_id = PGIE_ID
                obj.class_id = cls
                obj.confidence = conf
                obj.object_id = NO_TRACK
                obj.obj_label = cfg.class_names[cls] if cls < len(cfg.class_names) else str(cls)
                rect = obj.rect_params
                rect.left, rect.top, rect.width, rect.height = x1, y1, x2 - x1, y2 - y1
                pyds.nvds_add_obj_meta_to_frame(frame, obj, None)
        return 0

    def _tensor_of(self, frame) -> np.ndarray | None:
        pyds = self._pyds
        node = frame.frame_user_meta_list
        while node is not None:
            user = pyds.NvDsUserMeta.cast(node.data)
            if user.base_meta.meta_type == pyds.NvDsMetaType.NVDSINFER_TENSOR_OUTPUT_META:
                meta = pyds.NvDsInferTensorMeta.cast(user.user_meta_data)
                if meta.unique_id == PGIE_ID:
                    layer = pyds.get_nvds_LayerInfo(meta, 0)
                    dims = tuple(layer.inferDims.d[i] for i in range(layer.inferDims.numDims))
                    pointer = ctypes.cast(pyds.get_ptr(layer.buffer), ctypes.POINTER(ctypes.c_float))
                    return np.ctypeslib.as_array(pointer, shape=dims).copy()  # copy: the buffer is DeepStream's
            try:
                node = node.next
            except StopIteration:
                break
        return None

    def _detection_probe(self, pad, info):
        """After the tracker: the tracked objects of each camera go to that camera's logic."""
        pyds, cfg = self._pyds, self._cfg
        buffer = info.get_buffer()
        if buffer is None or self._handler is None:
            return 0
        for _batch, frame in self._frames(buffer):
            detections: list[Detection] = []
            node = frame.obj_meta_list
            while node is not None:
                obj = pyds.NvDsObjectMeta.cast(node.data)
                rect = obj.rect_params
                label = cfg.class_names[obj.class_id] if obj.class_id < len(cfg.class_names) else str(obj.class_id)
                track = None if obj.object_id == NO_TRACK else int(obj.object_id)
                box = (int(rect.left), int(rect.top), int(rect.left + rect.width), int(rect.top + rect.height))
                detections.append(Detection(label, float(obj.confidence), box, track))
                try:
                    node = node.next
                except StopIteration:
                    break
            camera_id = self._camera_of_source[frame.source_id]
            self._handler(
                camera_id, frame.buf_pts / 1e9, frame.source_frame_width, frame.source_frame_height, detections,
                lambda f=frame, b=buffer: self._picture(b, f),
            )
        return 0

    def _picture(self, buffer, frame) -> np.ndarray:
        """The frame as a BGR image on the CPU. Only called inside the probe, while the buffer is still ours."""
        rgba = self._pyds.get_nvds_buf_surface(hash(buffer), frame.batch_id)
        return cv2.cvtColor(np.array(rgba, copy=True), cv2.COLOR_RGBA2BGR)
