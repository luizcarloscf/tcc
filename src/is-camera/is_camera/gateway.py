import sys
import time

import numpy as np

from turbojpeg import TurboJPEG
from google.protobuf.json_format import Parse

from is_msgs.image_pb2 import Image
from is_wire.core import Channel, Message, Logger

from is_camera.driver import CameraDriver
from is_camera.conf.options_pb2 import CameraGatewayOptions, RabbitMQ, Zipkin


class CameraGateway:
    def __init__(self,
                 options_path: str = "/conf/options.json"):
        self.logger = Logger("CameraGateway")
        self.options = self.load_json(path=options_path)

        rabbitmq_uri = self.rabbitmq_uri(rabbitmq=self.options.rabbitmq)
        self.publish_channel = Channel(rabbitmq_uri)
        self.publish_topic = "CameraGateway.{}.Frame".format(
            self.options.camera.id,
        )

        self.driver = CameraDriver(config=self.options.camera)
        self.driver.start()

        self.encoder = TurboJPEG()

    def load_json(self,
                  path: str = "/etc/is_camera/options.json") -> CameraGatewayOptions:
        try:
            with open(path, 'r') as f:
                try:
                    op = Parse(f.read(), CameraGatewayOptions())
                    self.logger.info('FaceDetectorOptions: \n{}', op)
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

    def to_image(self, input_image: np.ndarray, compression_level=0.8) -> Image:
        # params = [cv2.IMWRITE_JPEG_QUALITY, int(compression_level * (100 - 0) + 0)]
        # cimage = cv2.imencode(ext='.jpeg', img=input_image, params=params)
        quality = int(compression_level * (100 - 0) + 0)
        return Image(data=self.encoder.encode(input_image, quality=quality))

    def run(self):
        while True:
            image = self.driver.read()
            ti = time.perf_counter()
            content = self.to_image(input_image=image)
            message = Message(content=content)
            te = time.perf_counter()
            self.publish_channel.publish(
                message=message,
                topic=self.publish_topic,
            )
            tf = time.perf_counter()
            self.logger.info("Encode image, took_ms={}".format((te-ti)*1000))
            self.logger.info("Publish image, took_ms={}".format((tf-te)*1000))


def main():
    options_path = sys.argv[1] if len(sys.argv) > 1 else 'options.json'
    gateway = CameraGateway(options_path=options_path)
    gateway.run()


if __name__ == "__main__":
    main()
