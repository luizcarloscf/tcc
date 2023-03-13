import re
import sys
import logging

from typing import Tuple

from google.protobuf.json_format import Parse
from is_wire.core import Logger, Subscription, AsyncTransport
from opencensus.ext.zipkin.trace_exporter import ZipkinExporter


from is_robot.conf.options_pb2 import RobotOptions
from is_robot.channel import CustomChannel as Channel
from is_robot.robot import RobotService

def load_json(logger: Logger,
              path: str = "/etc/is-aruco-detector/options.json") -> RobotOptions:
    try:
        with open(path, 'r') as f:
            try:
                op = Parse(f.read(), RobotOptions())
                logger.info('RobotOptions: \n{}', op)
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
    service_name = "Robot"
    logger = Logger(name=service_name, level=logging.DEBUG)
    options_filename = sys.argv[1] if len(sys.argv) > 1 else '/etc/is-robot/options.json'
    options = load_json(logger=logger, path=options_filename)

    zipkin_uri, zipkin_port = get_zipkin(logger=logger, uri=options.zipkin_uri)
    exporter = ZipkinExporter(
        service_name=service_name,
        host_name=zipkin_uri,
        port=zipkin_port,
        transport=AsyncTransport,
    )
    zipkin_uri_comm = "{}@{}:{}".format(
        service_name + ".commtime",
        zipkin_uri,
        zipkin_port,
    )
    channel = Channel(uri=options.rabbitmq_uri, zipkin_uri=zipkin_uri_comm)
    subscription = Subscription(channel=channel, name=service_name)
    robot = RobotService(
        settings=options.config,
        subscription=subscription,
        channel=channel,
        exporter=exporter,
    )
    while True:
        message, dropped = channel.consume_last(return_dropped=True)
        robot.run(message=message)
        logger.info("Dropped messages, num={}".format(dropped))

if __name__ == "__main__":
    main()
