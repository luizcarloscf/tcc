import sys
import time
import logging

from is_wire.core import Logger, Subscription
from google.protobuf.json_format import Parse

from is_aruco_detector.aruco import ArUcoDetector
from is_aruco_detector.channel import CustomChannel
from is_aruco_detector.calibration import CalibrationFetcher
from is_aruco_detector.conf.options_pb2 import ArUcoDetectorOptions


def load_json(logger: Logger,
              path: str = "/etc/is_aruco_detector/options.json") -> ArUcoDetectorOptions:
    try:
        with open(path, 'r') as f:
            try:
                op = Parse(f.read(), ArUcoDetectorOptions())
                logger.info('ArUcoDetectorOptions: \n{}', op)
                return op
            except Exception as ex:
                logger.critical('Unable to load options from \'{}\'. \n{}', path, ex)
    except Exception:
        logger.critical('Unable to open file \'{}\'', path)


def main():
    service_name = "ArUcoDetector"
    logger = Logger(name=service_name, level=logging.DEBUG)

    options_filename = sys.argv[1] if len(sys.argv) > 1 else '/etc/is-aruco-detector/options.json'
    options = load_json(logger=logger, path=options_filename)

    channel = CustomChannel(uri=options.rabbitmq_uri)
    subscription = Subscription(channel=channel, name=service_name)

    detector = ArUcoDetector(settings=options.config, channel=channel, subscription=subscription)
    fetcher = CalibrationFetcher(channel=channel, subscription=subscription)

    calibs = {}

    while True:
        messages = channel.consume_all()
        ti = time.perf_counter()
        images_msgs = messages
        for message in messages:
            if message.has_correlation_id and message.correlation_id is not None:
                calibs = fetcher.run(message=message)
                images_msgs.remove(message)
        if len(images_msgs) > 0:
            ok = detector.run(message=images_msgs[-1], calibrations=calibs)
            logger.info("Dropped messages, num={}".format(len(images_msgs) - 1))
            if ok is not None:
                fetcher.find(camera_id=ok)
        fetcher.check()
        tf = time.perf_counter()
        logger.info("Total, took_ms={}".format((tf - ti) * 1000))


if __name__ == "__main__":
    main()
