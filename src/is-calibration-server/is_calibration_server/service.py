import sys

from is_wire.core import Logger, Channel
from google.protobuf.json_format import Parse
from is_wire.rpc import ServiceProvider, LogInterceptor
from is_msgs.camera_pb2 import GetCalibrationRequest, GetCalibrationReply

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


def main():
    options_filename = sys.argv[1] if len(sys.argv) > 1 else '/etc/is-calibration-server/options.json'

    service_name = 'CalibrationServer'
    logger = Logger(name=service_name)

    options = load_json(logger=logger, path=options_filename)
    server = CalibrationServer(path=options.calibrations_path)
    channel = Channel(options.broker_uri)
    provider = ServiceProvider(channel)
    provider.add_interceptor(LogInterceptor())
    provider.delegate(topic="{}.GetCalibration".format(service_name),
                      function=server.get_calibrations,
                      request_type=GetCalibrationRequest,
                      reply_type=GetCalibrationReply)
    provider.run()


if __name__ == "__main__":
    main()
