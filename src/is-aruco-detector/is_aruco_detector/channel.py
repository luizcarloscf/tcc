import socket

from is_wire.core import Channel


class CustomChannel(Channel):
    def __init__(self, uri="amqp://guest:guest@localhost:5672", exchange="is"):
        super().__init__(uri=uri, exchange=exchange)

    def consume_all(self, return_dropped=False):
        messages = []
        message = super().consume()
        messages.append(message)
        while True:
            try:
                message = super().consume(timeout=0.0)
                messages.append(message)
            except socket.timeout:
                return messages
