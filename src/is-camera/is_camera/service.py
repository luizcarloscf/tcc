import sys
import logging

from google.protobuf.json_format import Parse
from is_wire.core import Logger, Subscription, Channel

from is_camera.gateway import CameraGateway
from is_camera.conf.options_pb2 import CameraGatewayOptions


def load_json(logger: Logger,
              path: str = "/etc/is-camera/options.json") -> CameraGatewayOptions:
    try:
        with open(path, 'r') as f:
            try:
                op = Parse(f.read(), CameraGatewayOptions())
                logger.info('CameraGatewayOptions: \n{}', op)
                return op
            except Exception as ex:
                logger.critical('Unable to load options from \'{}\'. \n{}', path, ex)
    except Exception:
        logger.critical('Unable to open file \'{}\'', path)


def main():
    service_name = "CameraGateway"
    logger = Logger(name=service_name, level=logging.DEBUG)

    options_filename = sys.argv[1] if len(sys.argv) > 1 else '/etc/is-camera/options.json'
    options = load_json(logger=logger, path=options_filename)
    gateway = CameraGateway(
        broker_uri=options.rabbitmq_uri,
        zipkin_uri=options.zipkin_uri,
        camera=options.camera,
    )
    while True:
        gateway.run()


if __name__ == "__main__":
    main()
