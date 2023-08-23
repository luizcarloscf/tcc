import re

from typing import Union, Dict

import cv2
import numpy as np

from opencensus.trace.span import Span
from opencensus.ext.zipkin.trace_exporter import ZipkinExporter

from dateutil import parser as dp
from is_msgs.image_pb2 import Image, ObjectAnnotations
from is_wire.core import Channel, Subscription, Logger, Message, Tracer

from is_object_detector.yolo import YOLOv8
from is_object_detector.conf.options_pb2 import ObjectSettings


class ObjectDetector:
    def __init__(self,
                 settings: ObjectSettings,
                 channel: Channel,
                 subscription: Subscription,
                 exporter: ZipkinExporter):
        self.logger = Logger("Detector")
        self.channel = channel
        self.settings = settings
        self.exporter = exporter
        self.subscription = subscription
       
        self.model = YOLOv8(self.settings.model_path, conf_threshold=0.3, iou_threshold=0.5)
        
        for camera in self.settings.cameras:
            topic = "{}.{}.Frame".format(self.settings.input_service_name, camera)
            self.subscription.subscribe(topic=topic)
            self.logger.info("Subscribed to receive messages with topic '{}'".format(
                topic
            ))
        self.re_topic = re.compile(r'{service_name}.(\d+).Frame'.format(service_name=self.settings.input_service_name))

    @staticmethod
    def image2array(image: Image) -> np.ndarray:
        buffer = np.frombuffer(image.data, dtype=np.uint8)
        array = cv2.imdecode(buffer, flags=cv2.IMREAD_COLOR)
        return array

    def detect(self, image: Image) -> ObjectAnnotations:
        array = self.image2array(image)
        bounding_boxes, scores, class_ids = self.model(array)
        annotations = ObjectAnnotations()
        for detection, score, class_id in zip(bounding_boxes, scores, class_ids):
            if class_id != 0:
                continue
            x1, y1, x2, y2 = detection.astype(int)
            area = (abs(x2 - x1) // 2) * (abs(y2 - y1) // 2)
            object = annotations.objects.add()
            object.id = class_id
            object.score = score
            vertex1 = object.region.vertices.add()
            vertex1.x = x1
            vertex1.y = y1
            vertex2 = object.region.vertices.add()
            vertex2.x = x2
            vertex2.y = y2
        annotations.resolution.width = array.shape[1]
        annotations.resolution.height = array.shape[0]
        return annotations

    @staticmethod
    def span_duration_ms(span: Span) -> float:
        dt = dp.parse(span.end_time) - dp.parse(span.start_time)
        return dt.total_seconds() * 1000.0

    def run(self,
            message: Message) -> Union[None, int]:
        tracer = Tracer(
            exporter=self.exporter,
            span_context=message.extract_tracing(),
        )
        span = None
        with tracer.span(name="detect") as _span:
            match = self.re_topic.match(message.topic)
            if match is None:
                return
            else:
                camera_id = int(match.group(1))
            image = message.unpack(schema=Image)
            annotations = self.detect(image=image)
            message_ann = Message(content=annotations)
            message_ann.topic = "Object.{}.Detections".format(camera_id)
            span = _span
            message_ann.inject_tracing(span=_span)
        self.channel.publish(message=message_ann)
        took_ms = round(self.span_duration_ms(span), 2)
        self.logger.info("Detect, took_ms={}".format(took_ms))
