import time

from typing import Dict, List

from is_wire.core import StatusCode
from is_wire.core import Channel, Subscription, Message, Logger, Tracer

from opencensus.ext.zipkin.trace_exporter import ZipkinExporter
from is_msgs.camera_pb2 import GetCalibrationReply, GetCalibrationRequest, CameraCalibration

class CalibrationFetcher:

    def __init__(self, channel: Channel, subscription: Subscription, exporter: ZipkinExporter):
        self.logger = Logger("CalibrationFetcher")
        self.channel = channel
        self.subscription = subscription
        self.exporter = exporter

        self.fetch_interval = 5
        self.timeout = time.perf_counter() + self.fetch_interval
        self.camera_ids = []
        self.calibrations = {}

    def run(self, cameras: List[int]) -> Dict[int, CameraCalibration]:
        tracer = Tracer(exporter=self.exporter)
        with tracer.span(name="request") as _span:
            calib_request = GetCalibrationRequest()
            calib_request.ids.extend(cameras)
            request = Message(
                content=calib_request,
                reply_to=self.subscription,
            )
            request.topic = "CalibrationServer.GetCalibration"
            request.inject_tracing(_span)
        self.channel.publish(message=request)
        self.logger.info("Requesting calibrations, ids={}", cameras)
        message = self.channel.consume()
        tracer = Tracer(
            exporter=self.exporter,
            span_context=message.extract_tracing(),
        )
        with tracer.span(name="reply"):
            if message.status.code == StatusCode.OK:
                reply = message.unpack(GetCalibrationReply)
                for calibration in reply.calibrations:
                    self.calibrations[calibration.id] = calibration
                    self.logger.info("Updated calibration, id={}".format(calibration.id))
            else:
                self.logger.warn(
                    "RPC failed, code={}, why={}".format(
                        message.status.code,
                        message.status.why,
                    ),
                )
        return self.calibrations
