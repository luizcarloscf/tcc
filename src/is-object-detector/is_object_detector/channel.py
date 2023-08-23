import socket

from typing import List

from is_wire.core import Channel, Message


class CustomChannel(Channel):

    def __init__(self,
                 zipkin_uri: str,
                 uri="amqp://guest:guest@localhost:5672",
                 exchange="is"):
        super().__init__(uri=uri, zipkin_uri=zipkin_uri, exchange=exchange)

    def consume_last(self, return_dropped: bool = True) -> List[Message]:
        dropped = 0
        msg = super().consume()
        while True:
            try:
                # will raise an exceptin when no message remained
                msg = super().consume(timeout=0.0)
                dropped += 1
            except socket.timeout:
                return (msg, dropped) if return_dropped else msg
