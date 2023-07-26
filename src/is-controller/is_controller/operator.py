import kopf
import time
import kubernetes

from requests.exceptions import ConnectionError
from google.protobuf.json_format import MessageToDict

from utils.stats import mean
from utils.options import load_options

from utils.zipkin import ZipkinClient
from utils.rabbitmq import RabbitMQClient

OPTIONS = load_options(path="./conf/options.json")

ZIPKIN_CLIENT = ZipkinClient(
    zipkin=OPTIONS.zipkin.uri,
    limit=OPTIONS.zipkin.limit,
    loopback=OPTIONS.zipkin.loopback,
    drift=OPTIONS.zipkin.drift,
)


RABBITMQ_CLIENT = RabbitMQClient(
    default=MessageToDict(OPTIONS.default),
    edges=[
        MessageToDict(OPTIONS.edges[i]) for i in range(len(OPTIONS.edges))
    ]
)

@kopf.timer('iscontrollers', interval=OPTIONS.timer, initial_delay=1)
def update_checker(memo: kopf.Memo, spec, logger, **_):
    if "mean" not in memo or "counter" not in memo:
        memo.mean = 0
        memo.counter = 0
        memo.state = "edge"
    try:
        traces = ZIPKIN_CLIENT.fetch(
            spans=[span["name"] for span in spec["spans"]],
            services=[span["service"] for span in spec["spans"]],
        )
    except ConnectionError:
        logger.warning("Could not fetch traces in ZipkinAPI")
    if len(traces) > 0:
        memo.mean = mean(traces=traces)
        memo.counter += 1
    else:
        memo.counter = 0
        logger.warning("Cannot compute mean")
    logger.info(f"Mean: {memo.mean}")
    logger.info(
        f"traces: {len([trace for trace in traces if len(trace) >= 2])}")

    if memo.counter > 10 and memo.mean > spec["tracesTargetValue"]:
        api = kubernetes.client.AppsV1Api()
        obj = api.patch_namespaced_deployment(
            name=spec["edge"]["deployment"]["name"],
            namespace=spec["edge"]["deployment"]["namespace"],
            body={
                "spec": {
                    "replicas": 0,
                },
            }
        )
        logger.info(f" updated: {obj}")
        for connection in spec["connections"]["stable"]:
            RABBITMQ_CLIENT.create_exchange_shovel(
                name=connection["name"],
                topic=connection["topic"],
                src=connection["src"],
                dest=connection["dest"],
            )
            logger.info(f"setting up {connection['name']}")
        memo.state = "cloud"

    if memo.counter > 10 and memo.mean < spec["tracesTargetValue"]:
        api = kubernetes.client.AppsV1Api()
        obj = api.patch_namespaced_deployment(
            name=spec["edge"]["deployment"]["name"],
            namespace=spec["edge"]["deployment"]["namespace"],
            body={
                "spec": {
                    "replicas": 1,
                },
            }
        )
        logger.info(f" updated: {obj}")
        for connection in spec["connections"]["stable"]:
            RABBITMQ_CLIENT.delete_exchange_shovel(
                name=connection["name"],
            )
            logger.info(f"deleting {connection['name']}")
        memo.state = "edge"



# if __name__ == "__main__":
#     loggers.configure(debug=True, verbose=True, quiet=False)
#     kopf.run(clusterwide=True)


@kopf.timer('iscontrollers', interval=50, initial_delay=1)
def test_flow(memo: kopf.Memo, spec, logger, **_):
    if "state" in memo and memo.state != "cloud":
        for connection in spec["connections"]["test"]:
            RABBITMQ_CLIENT.create_exchange_shovel(
                name=connection["name"],
                topic=connection["topic"],
                src=connection["src"],
                dest=connection["dest"],
            )
            logger.info(f"setting up {connection['name']}")
        time.sleep(30)
        for connection in spec["connections"]["test"]:
            RABBITMQ_CLIENT.delete_exchange_shovel(
                name=connection["name"],
            )
            logger.info(f"deleting {connection['name']}")
    else:
        logger.info("skipping...")
