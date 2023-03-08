import re

from typing import Union, Dict

import cv2
import numpy as np

from is_msgs.common_pb2 import Tensor, DataType
from is_msgs.image_pb2 import Image, ObjectAnnotations
from is_msgs.camera_pb2 import CameraCalibration, FrameTransformations

from opencensus.trace.span import Span
from opencensus.ext.zipkin.trace_exporter import ZipkinExporter

from dateutil import parser as dp
from is_wire.core import Channel, Subscription, Logger, Message, Tracer

from is_aruco_detector.conf.options_pb2 import ArUcoSettings


class ArUcoDetector:
    def __init__(self, settings: ArUcoSettings, channel: Channel, subscription: Subscription, exporter: ZipkinExporter):
        self.logger = Logger("ArUco")
        self.channel = channel
        self.settings = settings
        self.exporter = exporter
        self.subscription = subscription
        self.subscription.subscribe("CameraGateway.*.Frame")
        self.re_topic = re.compile(r'CameraGateway.(\d+).Frame')
        self.dictionary = cv2.aruco.getPredefinedDictionary(settings.dictionary)
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)

    @staticmethod
    def image2array(image: Image) -> np.ndarray:
        buffer = np.frombuffer(image.data, dtype=np.uint8)
        array = cv2.imdecode(buffer, flags=cv2.IMREAD_COLOR)
        return array

    @staticmethod
    def tensor2array(tensor: Tensor) -> np.ndarray:
        if len(tensor.shape.dims) != 2 or tensor.shape.dims[0].name != 'rows':
            return np.array([])
        shape = (tensor.shape.dims[0].size, tensor.shape.dims[1].size)
        if tensor.type == DataType.Value('INT32_TYPE'):
            return np.array(tensor.ints32, dtype=np.int32, copy=False).reshape(shape)
        if tensor.type == DataType.Value('INT64_TYPE'):
            return np.array(tensor.ints64, dtype=np.int64, copy=False).reshape(shape)
        if tensor.type == DataType.Value('FLOAT_TYPE'):
            return np.array(tensor.floats, dtype=np.float32, copy=False).reshape(shape)
        if tensor.type == DataType.Value('DOUBLE_TYPE'):
            return np.array(tensor.doubles, dtype=np.float64, copy=False).reshape(shape)
        return np.array([])

    @staticmethod
    def array2tensor(array: np.ndarray) -> Tensor:
        tensor = Tensor()
        rows = tensor.shape.dims.add()
        rows.size = array.shape[0]
        rows.name = "rows"
        cols = tensor.shape.dims.add()
        cols.size = array.shape[1]
        cols.name = "cols"
        if array.dtype == np.int32:
            tensor.type = DataType.Value('INT32_TYPE')
            tensor.ints32.extend(array.ravel().tolist())
        elif array.dtype == np.int64:
            tensor.type = DataType.Value('INT64_TYPE')
            tensor.ints64.extend(array.ravel().tolist())
        elif array.dtype == np.float32:
            tensor.type = DataType.Value('FLOAT_TYPE')
            tensor.floats.extend(array.ravel().tolist())
        elif array.dtype == np.float64:
            tensor.type = DataType.Value('DOUBLE_TYPE')
            tensor.doubles.extend(array.ravel().tolist())
        return tensor

    def detect(self, image: Image) -> ObjectAnnotations:
        array = self.image2array(image)
        detections, ids, _ = self.detector.detectMarkers(array)
        annotations = ObjectAnnotations()
        for i, corners in enumerate(detections):
            object = annotations.objects.add()
            object.label = str(ids[i][0])
            object.id = ids[i][0]
            for point in corners[0]:
                vertex = object.region.vertices.add()
                vertex.x = point[0]
                vertex.y = point[1]
        annotations.resolution.width = array.shape[1]
        annotations.resolution.height = array.shape[0]
        return annotations

    def localize(self,
                 annotations: ObjectAnnotations,
                 calibration: CameraCalibration) -> Union[FrameTransformations, None]:
        sx = annotations.resolution.width / calibration.resolution.width
        sy = annotations.resolution.height / calibration.resolution.height
        scale = np.array([[sx, 0.0, 0.0], [0.0, sy, 0.0], [0.0, 0.0, 1.0]])
        intrinsic = np.dot(scale, self.tensor2array(tensor=calibration.intrinsic))
        distorsion = self.tensor2array(tensor=calibration.distortion)
        transformations = FrameTransformations()
        for index in range(len(annotations.objects)):
            object = annotations.objects[index]
            x1 = object.region.vertices[0].x
            y1 = object.region.vertices[0].y
            x2 = object.region.vertices[1].x
            y2 = object.region.vertices[1].y
            x3 = object.region.vertices[2].x
            y3 = object.region.vertices[2].y
            x4 = object.region.vertices[3].x
            y4 = object.region.vertices[3].y
            corners = np.array([[[x1, y1],
                                 [x2, y2],
                                 [x3, y3],
                                 [x4, y4]]], dtype=np.float32)
            if object.id not in self.settings.lengths.keys():
                self.logger.critical(
                    "Detected aruco with ID={}, but not found in configuration \
                        its length".format(object.id))
            marker_length = self.settings.lengths[object.id]
            rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
                corners,
                marker_length,
                intrinsic,
                distorsion,
            )
            rmat, _ = cv2.Rodrigues(rvec)
            tvec = tvec.reshape(3, 1)
            mat = np.hstack((rmat, tvec))
            mat = np.vstack((mat, np.array([[0, 0, 0, 1]])))
            transformation = transformations.tfs.add()
            transformation.tf.CopyFrom(self.array2tensor(array=mat))
            # claramente é gambiarra, em python 'from' é palavra reservada
            setattr(transformation, 'from', 100 + object.id)
            setattr(transformation, 'to', calibration.id)
        return transformations

    @staticmethod
    def span_duration_ms(span: Span) -> float:
        dt = dp.parse(span.end_time) - dp.parse(span.start_time)
        return dt.total_seconds() * 1000.0

    def run(self,
            message: Message,
            calibrations: Dict[int, CameraCalibration]) -> Union[None, int]:
        match = self.re_topic.match(message.topic)
        if match is None:
            return
        else:
            camera_id = int(match.group(1))
            if camera_id not in calibrations:
                return camera_id
        tracer = Tracer(
            exporter=self.exporter,
            span_context=message.extract_tracing(),
        )
        span = None

        with tracer.span(name="detect_and_localize") as _span:
            image = message.unpack(schema=Image)
            annotations = self.detect(image=image)
            message_obs = Message(content=annotations)
            message_obs.topic = "ArUco.{}.Detection".format(camera_id)
            message_obs.inject_tracing(span=_span)
            transformations = self.localize(
                annotations=annotations,
                calibration=calibrations[camera_id],
            )
            message_ann = Message(content=transformations)
            message_ann.topic = "ArUco.{}.FrameTransformations".format(camera_id)
            message_ann.inject_tracing(span=_span)
            span = _span
        self.channel.publish(message=message_obs)
        self.channel.publish(message=message_ann)
        took_ms = round(self.span_duration_ms(span), 2)
        self.logger.info("Publish image, took_ms={}".format(took_ms))