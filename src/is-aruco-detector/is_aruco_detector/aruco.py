import cv2
import numpy as np

# from is_aruco_detector.conf import ArucoSettings
from is_msgs.image_pb2 import Image, ObjectAnnotations

class ArUco:
    def __init__(self, dictionary: int):
        self.dictionary = cv2.aruco.getPredefinedDictionary(dictionary)
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)

    @staticmethod
    def to_array(image: Image) -> np.ndarray:
        buffer = np.frombuffer(image.data, dtype=np.uint8)
        array = cv2.imdecode(buffer, flags=cv2.IMREAD_COLOR)
        return array

    def detect(self, image: Image) -> ObjectAnnotations:
        array = self.to_array(image)
        detections, ids, _ = self.detector.detectMarkers(array)
        annotations = ObjectAnnotations()
        for i, corners in enumerate(detections):
            # corners = corners.reshape((4, 2))
            object = annotations.objects.add()
            object.label = str(ids[i])
            object.id = ids[i]
            for point in corners:
                vertex = object.region.vertices.add()
                vertex.x = point[0]
                vertex.y = point[1]
        annotations.resolution.width = array.shape[1]
        annotations.resolution.height = array.shape[0]
        return annotations

def main():
    aruco = ArUco(dictionary=0)


if __name__ == "__main__":
    main()