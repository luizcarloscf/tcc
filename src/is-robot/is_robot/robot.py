import re
import time

import numpy as np

from is_msgs.common_pb2 import Tensor, DataType
from is_msgs.camera_pb2 import FrameTransformations

from opencensus.trace.span import Span
from opencensus.ext.zipkin.trace_exporter import ZipkinExporter

from dateutil import parser as dp
from is_wire.core import Subscription, Logger, Message, Tracer

from is_robot.channel import CustomChannel
from is_robot.conf.options_pb2 import RobotConfig


class RobotService:
    def __init__(self,
                 settings: RobotConfig,
                 channel: CustomChannel,
                 subscription: Subscription,
                 exporter: ZipkinExporter):
        self.logger = Logger("Robot")
        self.channel = channel
        self.exporter = exporter
        self.settings = settings
        self.subscription = subscription
        for camera in self.settings.cameras:
            topic = "ArUco.{}.FrameTransformations".format(camera)
            self.subscription.subscribe(topic=topic)
            self.logger.info("Subscribed to receive messages with topic '{}'".format(
                topic
            ))
        self.re_topic = re.compile(r'ArUco.(\d+).FrameTransformations')

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
    def span_duration_ms(span: Span) -> float:
        dt = dp.parse(span.end_time) - dp.parse(span.start_time)
        return dt.total_seconds() * 1000.0

    def run(self, message: Message):
        tracer = Tracer(
            exporter=self.exporter,
            span_context=message.extract_tracing(),
        )
        span = None
        with tracer.span(name="robot") as _span:
            match = self.re_topic.match(message.topic)
            if match is None:
                return
            else:
                camera_id = int(match.group(1))
                if camera_id not in self.settings.cameras:
                        return
            transformations = message.unpack(schema=FrameTransformations)
            for index in range(len(transformations.tfs)):
                transformation = transformations.tfs[index]
                aruco_id = getattr(transformation, 'from')
                if aruco_id not in self.settings.arucos:
                    continue
                array = self.tensor2array(tensor=transformation.tf)
            time.sleep(self.settings.processing_time)
            span = _span
        took_ms = round(self.span_duration_ms(span), 2)
        self.logger.info("Processed, took_ms={}".format(took_ms))
