import re
import sys
import time

from is_msgs.image_pb2 import Image
from google.protobuf.json_format import Parse
from is_wire.core import Subscription, Message, Logger

from is_aruco_detector.aruco import ArUco
from is_aruco_detector.channel import StreamChannel
from is_aruco_detector.calibration import CalibrationFetcher
from is_aruco_detector.conf.options_pb2 import ArUcoServiceOptions, RabbitMQ, Zipkin


class ArUcoService:
    def __init__(self,
                 name = "ArUcoDetector",
                 options_path: str = "/etc/is-aruco-detector/options.json"):
        self.logger = Logger("{}".format(name))
        self.options = self.load_json(path=options_path)

        rabbitmq_uri = self.rabbitmq_uri(rabbitmq=self.options.rabbitmq)
        self.channel = StreamChannel(rabbitmq_uri)
        
        subscription = Subscription(channel=self.channel, name=name)
        subscription.subscribe(topic='CameraGateway.*.Frame')           

        self.fetcher = CalibrationFetcher(rabbitmq_uri)

        self.aruco = ArUco(dictionary=0)

    def load_json(self,
                  path: str = "/etc/is_aruco_detector/options.json") -> ArUcoServiceOptions:
        try:
            with open(path, 'r') as f:
                try:
                    op = Parse(f.read(), ArUcoServiceOptions())
                    self.logger.info('ArUcoServiceOptions: \n{}', op)
                    return op
                except Exception as ex:
                    self.logger.critical('Unable to load options from \'{}\'. \n{}', path, ex)
        except Exception:
            self.logger.critical('Unable to open file \'{}\'', path)

    @staticmethod
    def rabbitmq_uri(rabbitmq: RabbitMQ) -> str:
        return "{}://{}:{}@{}:{}".format(
            rabbitmq.protocol,
            rabbitmq.user,
            rabbitmq.password,
            rabbitmq.host,
            rabbitmq.port,
        )

    @staticmethod
    def zipkin_uri(zipkin: Zipkin):
        return "{}://{}:{}".format(
            zipkin.protocol,
            zipkin.host,
            zipkin.port,
        )

    @staticmethod
    def topic_id(topic: str):
        re_topic = re.compile(r'CameraGateway.(\d+).Frame')
        result = re_topic.match(topic)
        if result:
            return result.group(1)

    def eval_message(self, message: Message):
        self.fetcher.eval()
        ti = time.perf_counter()
        camera_id = self.topic_id(topic=message.topic)
        calibration = self.fetcher.find(camera_id=int(camera_id))
        if calibration is not None:
            image = message.unpack(Image)
            annotations = self.aruco.detect(image=image)

            detections = Message()
            detections.pack(annotations)
            detections.topic = 'ArUco.{}.Detection'.format(camera_id)
            self.channel.publish(message=detections)

            tf = time.perf_counter()
            self.logger.info("Total, took_ms={}".format((tf-ti)*1000))

    def run(self):
        while True:
            message = self.channel.consume_last()
            self.eval_message(message=message)


def main():
    options_path = sys.argv[1] if len(sys.argv) > 1 else 'options.json'
    service = ArUcoService(options_path=options_path)
    service.run()


if __name__ == "__main__":
    main()
