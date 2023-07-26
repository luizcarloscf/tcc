from google.protobuf.json_format import Parse
from is_controller.conf.options_pb2 import IsControllerOptions

def load_options(path: str):
    file = open(path, 'r', encoding="utf-8")
    options = Parse(file.read(), IsControllerOptions())
    return options
