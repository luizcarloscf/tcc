import time

from threading import Thread
from queue import Queue, Empty

import cv2

from is_camera.conf.options_pb2 import Camera


class CameraDriver:

    def __init__(self, config: Camera):
        self.camera = cv2.VideoCapture(config.device, apiPreference=cv2.CAP_V4L2)
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        
        self.framerate = config.framerate
        self.width = config.width
        self.height = config.height
        time.sleep(2)
        self.queue = Queue()
        self.stopped = False

    @property
    def framerate(self) -> float:
        return self.camera.get(cv2.CAP_PROP_FPS)

    @framerate.setter
    def framerate(self, value: float):
        self.camera.set(cv2.CAP_PROP_FPS, value)

    @property
    def width(self) -> int:
        return self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)

    @width.setter
    def width(self, value: int):
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, value)

    @property
    def height(self) -> int:
        return self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)

    @height.setter
    def height(self, value: int):
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, value)

    def start(self):
        self.t = Thread(target=self.update, daemon=True)
        self.t.daemon = True
        self.t.start()

    def update(self):
        while not self.stopped:
            self.camera.grab()
            ret, frame = self.camera.retrieve()
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except Empty:
                    pass
            if ret:
                self.queue.put(frame)

    def read(self):
        return self.queue.get(block=True)

    def stop(self):
        self.stopped = True
        self.t.join()
        self.camera.release()
