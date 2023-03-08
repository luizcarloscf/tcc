import socket

from typing import List

from is_wire.core import Channel, Message


class CustomChannel(Channel):
    def __init__(self, uri="amqp://guest:guest@localhost:5672", exchange="is"):
        super().__init__(uri=uri, exchange=exchange)

    def consume_all(self) -> List[Message]:
        messages = []
        # waits forever of a message
        message = super().consume()
        messages.append(message)
        while True:
            try:
                # if queue has more than one message, append it to list
                message = super().consume(timeout=0.0)
                messages.append(message)
            except socket.timeout:
                return messages
