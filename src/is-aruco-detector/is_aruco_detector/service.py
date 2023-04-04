import re
import sys
import logging

from typing import Tuple

from google.protobuf.json_format import Parse
from is_wire.core import Logger, Subscription, AsyncTransport
from opencensus.ext.zipkin.trace_exporter import ZipkinExporter

from is_aruco_detector.aruco import ArUcoDetector
from is_aruco_detector.channel import CustomChannel
from is_aruco_detector.calibration import CalibrationFetcher
from is_aruco_detector.conf.options_pb2 import ArUcoDetectorOptions


def load_json(logger: Logger,
              path: str = "/etc/is-aruco-detector/options.json") -> ArUcoDetectorOptions:
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


def get_zipkin(logger: Logger, uri: str) -> Tuple[str, str]:
        zipkin_ok = re.match("http:\\/\\/([a-zA-Z0-9\\.]+)(:(\\d+))?", uri)
        if not zipkin_ok:
            logger.critical("Invalid zipkin uri {}, \
                             expected http://<hostname>:<port>".format(uri))
        return zipkin_ok.group(1), int(zipkin_ok.group(3))


def main():
    logger = Logger(name="Service", level=logging.DEBUG)
    options_filename = sys.argv[1] if len(sys.argv) > 1 else '/etc/is-aruco-detector/options.json'
    options = load_json(logger=logger, path=options_filename)

    zipkin_uri, zipkin_port = get_zipkin(logger=logger, uri=options.zipkin_uri)
    exporter = ZipkinExporter(
        service_name=options.service_name,
        host_name=zipkin_uri,
        port=zipkin_port,
        transport=AsyncTransport,
    )
    zipkin_uri_comm = "{}@{}:{}".format(
        options.service_name + ".commtime",
        zipkin_uri,
        zipkin_port,
    )
    channel = CustomChannel(uri=options.rabbitmq_uri, zipkin_uri=zipkin_uri_comm)
    subscription = Subscription(channel=channel, name=options.service_name)
    fetcher = CalibrationFetcher(
        channel=channel,
        subscription=subscription,
        exporter=exporter,
    )
    calibs = fetcher.run(cameras=options.config.cameras)
    detector = ArUcoDetector(
        settings=options.config,
        channel=channel,
        subscription=subscription,
        exporter=exporter,
    )
    while True:
        message, dropped = channel.consume_last(return_dropped=True)
        detector.run(message=message, calibrations=calibs)
        logger.info("Dropped messages, num={}".format(dropped))

if __name__ == "__main__":
    main()
