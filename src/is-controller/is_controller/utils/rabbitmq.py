from typing import List
from typing_extensions import TypedDict

from requests import put, delete, get
from urllib.parse import urljoin


class RabbitMQ(TypedDict):
    name: str
    uri: str
    user: str
    password: str
    managementUrl: str


class Shovel(TypedDict):
    node: str
    timestamp: str
    name: str
    vhost: str
    type: str
    state: str
    src_uri: str
    src_protocol: str
    src_exchange: str
    src_exchange_key: str
    dest_uri: str
    dest_protocol: str
    dest_exchange: str
    dest_exchange_key: str


class RabbitMQClient:

    def __init__(self, default: RabbitMQ, edges: List[RabbitMQ]):
        self._default = default
        self._edges = edges

    def get_broker(self, name: str) -> RabbitMQ:
        if self._default["name"] == name:
            return self._default
        else:
            return next(item for item in self._edges if item["name"] == name)

    def create_exchange_shovel(self, name: str, topic: str, src: str,
                               dest: str):
        src_rabbitmq, dest_rabbitmq = self.get_broker(src), self.get_broker(
            dest)
        data = {
            "value": {
                "ack-mode": "no-ack",
                "src-uri": src_rabbitmq['uri'],
                "src-protocol": "amqp091",
                "src-exchange": "is",
                "src-exchange-key": topic,
                "dest-uri": dest_rabbitmq['uri'],
                "dest-protocol": "amqp091",
                "dest-exchange": "is",
                "dest-exchange-key": topic,
            }
        }
        response = put(
            url=urljoin(
                self._default['managementUrl'],
                f"/api/parameters/shovel/%2f/{name}",
            ),
            auth=(
                self._default['user'],
                self._default['password'],
            ),
            json=data,
            timeout=5,
        )
        response.raise_for_status()

    def delete_exchange_shovel(self, name: str):
        shovels = self.list_exchange_shovel()
        for shovel in shovels:
            if shovel["name"] == name:
                response = delete(
                    url=urljoin(
                        self._default['managementUrl'],
                        f"/api/parameters/shovel/%2f/{name}",
                    ),
                    auth=(
                        self._default['user'],
                        self._default['password'],
                    ),
                    timeout=5,
                )
                response.raise_for_status()

    def list_exchange_shovel(self) -> List[Shovel]:
        response: List[Shovel] = get(
            url=urljoin(
                self._default["managementUrl"],
                "/api/shovels/",
            ),
            auth=(
                self._default["user"],
                self._default["password"],
            ),
            timeout=5,
        )
        response.raise_for_status()
        return response.json()
