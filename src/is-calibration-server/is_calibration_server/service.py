import re
import sys

from typing import Tuple

from google.protobuf.json_format import Parse
from opencensus.ext.zipkin.trace_exporter import ZipkinExporter
from is_msgs.camera_pb2 import GetCalibrationRequest, GetCalibrationReply

from is_wire.core import Logger, Channel, AsyncTransport
from is_wire.rpc import ServiceProvider, LogInterceptor, TracingInterceptor

from is_calibration_server.calibration import CalibrationServer
from is_calibration_server.conf.options_pb2 import CalibrationServerOptions


def load_json(logger: Logger,
              path: str = "/etc/is-calibration-server/options.json") -> CalibrationServerOptions:
    try:
        with open(path, 'r') as f:
            try:
                op = Parse(f.read(), CalibrationServerOptions())
                logger.info('CalibrationServerOptions: \n{}', op)
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
    options_filename = sys.argv[1] if len(sys.argv) > 1 else "/etc/is-calibration-server/options.json"
    service_name = "CalibrationServer"
    logger = Logger(name="Service")

    options = load_json(logger=logger, path=options_filename)
    server = CalibrationServer(path=options.calibrations_path)

    channel = Channel(uri=options.broker_uri)
    zipkin_uri, zipkin_port = get_zipkin(logger=logger, uri=options.zipkin_uri)
    exporter = ZipkinExporter(
        service_name=service_name,
        host_name=zipkin_uri,
        port=zipkin_port,
        transport=AsyncTransport,
    )

    logging = LogInterceptor()
    tracing = TracingInterceptor(exporter=exporter)
    provider = ServiceProvider(channel=channel)
    provider.add_interceptor(interceptor=logging)
    provider.add_interceptor(interceptor=tracing)    
    provider.delegate(
        topic="{}.GetCalibration".format(service_name),
        function=server.get_calibrations,
        request_type=GetCalibrationRequest,
        reply_type=GetCalibrationReply,
    )
    provider.run()


if __name__ == "__main__":
    main()
