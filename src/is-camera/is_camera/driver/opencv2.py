from threading import Thread
from queue import Queue, Empty
from typing import Union, Tuple

import cv2
import numpy as np

from turbojpeg import TurboJPEG
from is_wire.core import Status, StatusCode
from google.protobuf.wrappers_pb2 import FloatValue
from is_msgs.image_pb2 import Image, ColorSpace, ColorSpaces, ImageFormat, ImageFormats, Resolution

from is_camera.driver.base import CameraDriver


class OpenCV2CameraDriver(CameraDriver):

    def __init__(self, device: str = "/dev/video0"):
        super(CameraDriver, self).__init__()
        self._encoder = TurboJPEG()
        self._encode_format = ".jpeg"
        self._compression_level = 0.8

        self._camera = cv2.VideoCapture(device, apiPreference=cv2.CAP_V4L2)
        self._camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self._queue = Queue()
        self._stopped = False

    def to_image(self,
                 image: np.ndarray,
                 encode_format: str = '.jpeg',
                 compression_level: float = 0.8,
                 use_turbojpeg: bool = True) -> Image:
        if use_turbojpeg:
            quality = int(compression_level * (100 - 0) + 0)
            return Image(data=self._encoder.encode(image, quality=quality))
        else:
            if encode_format == '.jpeg':
                params = [cv2.IMWRITE_JPEG_QUALITY, int(compression_level * (100 - 0) + 0)]
            elif encode_format == '.png':
                params = [cv2.IMWRITE_PNG_COMPRESSION, int(compression_level * (9 - 0) + 0)]
            elif encode_format == '.webp':
                params = [cv2.IMWRITE_WEBP_QUALITY, int(compression_level * (100 - 1) + 1)]
            else:
                return Image()
            cimage = cv2.imencode(ext=encode_format, img=image, params=params)
            return Image(data=cimage[1].tobytes())

    def get_sampling_rate(self) -> Tuple[Status, Union[FloatValue, None]]:
        rate = FloatValue()
        rate.value = self._camera.get(cv2.CAP_PROP_FPS)
        if rate.value == 0:
            status = Status(
                code=StatusCode.INTERNAL_ERROR,
                why="Error while getting FPS",
            )
            return status, None
        else:
            return status, rate

    def set_sampling_rate(self, sampling_rate: FloatValue) -> Status:
        ret = self._camera.set(cv2.CAP_PROP_FPS, sampling_rate.value)
        if not ret:
            return Status(
                code=StatusCode.INTERNAL_ERROR,
                why="Error while setting sampling rate",
            )
        else:
            return Status(code=StatusCode.OK)

    def get_color_space(self) -> Tuple[Status, Union[ColorSpace, None]]:
        color_space = ColorSpace()
        color_space.value = ColorSpaces.RGB
        return Status(code=StatusCode.OK), color_space

    def get_format(self) -> Tuple[Status, Union[ImageFormat, None]]:
        image_format = ImageFormat()
        if self._encode_format == ".jpeg":
            image_format.format = ImageFormats.Value("JPEG")
        elif self._encode_format == ".png":
            image_format.format = ImageFormats.Value("PNG")
        elif self._encode_format == ".webp":
            image_format.format = ImageFormats.Value("WebP")
        image_format.compression.value = self._compression_level
        status = Status(code=StatusCode.OK)
        return status, image_format

    def set_format(self, image_format: ImageFormat) -> Status:
        if image_format.format == ImageFormats.Value("JPEG"):
            self._encode_format = ".jpeg"
        elif image_format.format == ImageFormats.Value("PNG"):
            self._encode_format = ".png"
        elif image_format.format == ImageFormats.Value("WebP"):
            self._encode_format = ".webp"
        else:
            return Status(
                code=StatusCode.NOT_FOUND,
                why="Not found image format speficied in request.",
            )
        self._compression_level = image_format.compression.value
        return Status(code=StatusCode.OK)

    def get_resolution(self) -> Tuple[Status, Union[Resolution, None]]:
        resolution = Resolution()
        resolution.height = self._camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        resolution.width = self._camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        if (resolution.height == 0) or (resolution.width == 0):
            status = Status(
                code=StatusCode.INTERNAL_ERROR,
                why="Error while getting resolution",
            )
            return status, None
        else:
            status = Status(code=StatusCode.OK)
            return status, resolution

    def set_resolution(self, resolution: Resolution) -> Status:
        ret = self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution.height)
        if not ret:
            status = Status(
                code=StatusCode.INTERNAL_ERROR,
                why="Error while setting resolution",
            )
            return status
        ret = self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution.width)
        if not ret:
            return Status(
                code=StatusCode.INTERNAL_ERROR,
                why="Error while setting resolution",
            )
        return Status(code=StatusCode.OK)

    def start_capture(self):
        self._stopped = False
        self._thread = Thread(target=self._update, daemon=True)
        self._thread.start()

    def stop_capture(self):
        self._stopped = True
        self._thread.join()

    def grab_image(self) -> Image:
        return self.to_image(
            image=self._queue.get(block=True),
            encode_format=self._encode_format,
            compression_level=self._compression_level,
            use_turbojpeg=True,
        )

    def _update(self):
        while not self._stopped:
            self._camera.grab()
            ret, frame = self._camera.retrieve()
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except Empty:
                    pass
            if ret:
                self._queue.put(frame)
