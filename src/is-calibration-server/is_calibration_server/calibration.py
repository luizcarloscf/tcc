import os

from typing import List

from google.protobuf.json_format import Parse

from is_wire.rpc.context import Context
from is_wire.core import Logger, Status, StatusCode
from is_msgs.camera_pb2 import CameraCalibration, GetCalibrationRequest, GetCalibrationReply


class CalibrationServer:

    def __init__(self, path: str):
        self.logger = Logger("CalibrationServer")
        self.calibrations = dict()
        for calibration in self.find_calibrations(path):
            self.calibrations[calibration.id] = calibration
            self.logger.info("NewCalibration, id={}", calibration.id)

    def load_calibrations(self, filename: str) -> CameraCalibration:
        try:
            with open(filename, 'r') as f:
                try:
                    calibration = Parse(f.read(), CameraCalibration())
                    return calibration
                except Exception as ex:
                    self.logger.warning('Unable to load calibrations from \'{}\'. \n{}',
                                        filename, ex)
        except Exception as ex:
            self.logger.warning('Unable to open calibrations file \'{}\'. \n{}', filename, ex)

    def find_calibrations(self,
                          directory: str,
                          extension: str = ".json") -> List[CameraCalibration]:
        calibrations = list()
        for filename in os.listdir(directory):
            if filename.endswith(extension):
                calibration_filename = os.path.join(directory, filename)
                calibrations.append(self.load_calibrations(calibration_filename))
        return calibrations

    def get_calibrations(self,
                         request: GetCalibrationRequest,
                         context: Context) -> GetCalibrationReply:
        reply = GetCalibrationReply()
        for id in request.ids:
            if id not in self.calibrations.keys():
                error = "CameraCalibration with id '{}' not found".format(id)
                self.logger.warn(error)
                return Status(code=StatusCode.NOT_FOUND, why=error)
            calib = reply.calibrations.add()
            try:
                calib.CopyFrom(self.calibrations[id])
            except Exception:
                error = "CameraCalibration with id '{}' found but an error occurred".format(id)
                self.logger.warn(error)
                return Status(code=StatusCode.INTERNAL_ERROR, why=error)
        return reply
