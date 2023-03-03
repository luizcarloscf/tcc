import time

from is_wire.core import StatusCode
from is_wire.core import Channel, Subscription, Message, Logger
from is_msgs.camera_pb2 import GetCalibrationReply, GetCalibrationRequest


class CalibrationFetcher:

    def __init__(self, channel: Channel, subscription: Subscription):
        self.logger = Logger("CalibrationFetcher")
        self.channel = channel
        self.subscription = subscription

        self.fetch_interval = 5
        self.timeout = time.perf_counter()
        self.camera_ids = []
        self.calibrations = {}

    def find(self, camera_id: int):
        if camera_id not in self.camera_ids:
            self.camera_ids.append(camera_id)

    def check(self):
        now = time.perf_counter()
        if now >= self.timeout:
            self.timeout = now + self.fetch_interval
            if len(self.camera_ids) > 0:
                calib_request = GetCalibrationRequest()
                calib_request.ids.extend(self.camera_ids)
                request = Message(
                    content=calib_request,
                    reply_to=self.subscription,
                )
                request.topic = "FrameTransformation.GetCalibration"
                self.channel.publish(message=request)
                self.logger.info("Requesting calibrations, ids={}", self.camera_ids)

    def run(self, message: Message):
        if message.has_correlation_id:
            if message.status.code == StatusCode.OK:
                reply = message.unpack(GetCalibrationReply)
                for calibration in reply.calibrations:
                    self.calibrations[calibration.id] = calibration
                    self.camera_ids.remove(calibration.id)
                    self.logger.info("Updated calibration, id={}".format(calibration.id))
            else:
                self.logger.warn(
                    "RPC failed, code={}, why={}".format(
                        message.status.code,
                        message.status.code.why,
                    ),
                )
        return self.calibrations
