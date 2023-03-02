import time
import socket

from is_msgs.camera_pb2 import GetCalibrationReply, GetCalibrationRequest

from is_wire.core import Channel, Subscription, Message, Logger
from is_wire.core import StatusCode


class CalibrationFetcher:

    def __init__(self, rabbitmq_uri: str):
        self.logger = Logger("CalibrationFetcher")
        self.fetch_interval = 5
        self.timeout = time.perf_counter()
        self.camera_ids = []
        self.calibrations = {}
        self.correlation_id = None

        self.rpc_channel = Channel(rabbitmq_uri)
        self.rpc_subscription = Subscription(channel=self.rpc_channel)

    def find(self, camera_id: int):
        if camera_id in self.calibrations:
            return self.calibrations[camera_id]
        else:
            if camera_id not in self.camera_ids:
                self.camera_ids.append(camera_id)

    def eval(self):
        now = time.perf_counter()
        if now >= self.timeout:
            self.timeout = now + self.fetch_interval
            if len(self.camera_ids) > 0:
                calib_request = GetCalibrationRequest()
                calib_request.ids.extend(self.camera_ids)
                request = Message(
                    content=calib_request,
                    reply_to=self.rpc_subscription,
                )
                request.topic = "FrameTransformation.GetCalibration"
                self.correlation_id = request.correlation_id
                self.rpc_channel.publish(message=request)
                self.logger.info("Requesting calibrations, ids={}", self.camera_ids)    
        else:
            try:
                message = self.rpc_channel.consume(timeout=0.0)
                if message.status.code == StatusCode.OK:
                    reply = message.unpack(GetCalibrationReply)
                    for calibration in reply.calibrations:
                        self.calibrations[calibration.id] = calibration
                        print(self.camera_ids)
                        self.camera_ids.remove(calibration.id)
                        self.logger.info("Updated calibration, id={}".format(calibration.id))
                else:
                    self.logger.warn(
                        "RPC failed, code={}, why={}".format(
                            message.status.code,
                            message.status.code.why,
                        ),
                    )                    
            except socket.timeout:
                pass
