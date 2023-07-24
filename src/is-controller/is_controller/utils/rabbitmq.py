from typing import List, Tuple
from typing_extensions import TypedDict

from requests import post, delete
from urllib.parse import urljoin


class RabbitMQ(TypedDict):
    id: str
    uri: str
    user: str
    password: str
    management_url: str


class Shovel(TypedDict):
    name: str
    rabbitmq_id: str


class RabbitMQClient:
    def __init__(self, brokers: List[RabbitMQ]):
        self._brokers = brokers
        # self._shovels : List[Shovel] = []

    def create_exchange_shovel(self, name: str, topic: str, src: Tuple[str,str], dst: Tuple[str,str]):
        src_rabbitmq = self._brokers[src[0]]
        dst_rabbitmq = self._brokers[dst[0]]
        src_exchange = src[1]
        dst_exchange = dst[1]
        data = {
            "value": {
                "src-exchange-key": topic,
                "src-protocol": "amqp091",
                "src-uri": src_rabbitmq['uri'],
                "src-exchange": src_exchange,
                "dest-protocol": "amqp091",
                "dest-uri": dst_rabbitmq['uri'],
                "dest-exchange": dst_exchange
            }
        }
        response = post(
            url=urljoin(
                src_rabbitmq['management_url'],
                f"/api/parameters/shovel/%2f/{name}"
            ),
            auth=(src_rabbitmq['user'], src_rabbitmq['password']),
            json=data,
            timeout=5,
        )
        response.raise_for_status()
        # self._shovels.append(
        #     Shovel(name=name, rabbitmq_id=src_rabbitmq["id"])
        # )


    def delete_exchange_shovel(self, name: str, src: str):
        src_rabbitmq = self._brokers[src]
        response = delete(
            url=urljoin(
                src_rabbitmq['management_url'],
                f"/api/parameters/shovel/%2f/{name}",
            ),
            auth=(
                src_rabbitmq['user'],
                src_rabbitmq['password'],
            ),
            timeout=5,
        )
        response.raise_for_status()
