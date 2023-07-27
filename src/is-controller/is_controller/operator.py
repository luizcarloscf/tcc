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
    edges=[MessageToDict(OPTIONS.edges[i]) for i in range(len(OPTIONS.edges))])


@kopf.on.create('iscontrollers')
def created_handler(memo: kopf.Memo, spec, logger, **_):
    # make sure any shovel connection exists
    for connection in spec["connections"]["test"]:
        RABBITMQ_CLIENT.delete_exchange_shovel(name=connection["name"])
        logger.info(f"Deleted {connection['name']} shovel.")
    for connection in spec["connections"]["stable"]:
        RABBITMQ_CLIENT.delete_exchange_shovel(name=connection["name"])
        logger.info(f"Deleted {connection['name']} shovel.")
    api = kubernetes.client.AppsV1Api()
    _ = api.patch_namespaced_deployment(
        name=spec["edge"]["deployment"]["name"],
        namespace=spec["edge"]["deployment"]["namespace"],
        body={
            "spec": {
                "replicas": 1,
            },
        },
    )
    _ = api.patch_namespaced_deployment(
        name=spec["cloud"]["deployment"]["name"],
        namespace=spec["cloud"]["deployment"]["namespace"],
        body={
            "spec": {
                "replicas": 1,
            },
        },
    )
    memo.state = "edge"
    memo.bottom_counter = 0
    memo.upper_counter = 0
    memo.mean = 0


@kopf.on.delete('iscontrollers')
def deleted_handler(memo: kopf.Memo, spec, logger, **_):
    # make sure any shovel connection doesnt exists
    for connection in spec["connections"]["test"]:
        RABBITMQ_CLIENT.delete_exchange_shovel(name=connection["name"])
        logger.info(f"Deleted {connection['name']} shovel.")
    for connection in spec["connections"]["stable"]:
        RABBITMQ_CLIENT.delete_exchange_shovel(name=connection["name"])
        logger.info(f"Deleted {connection['name']} shovel.")
    api = kubernetes.client.AppsV1Api()
    _ = api.patch_namespaced_deployment(
        name=spec["edge"]["deployment"]["name"],
        namespace=spec["edge"]["deployment"]["namespace"],
        body={
            "spec": {
                "replicas": 1,
            },
        },
    )
    _ = api.patch_namespaced_deployment(
        name=spec["cloud"]["deployment"]["name"],
        namespace=spec["cloud"]["deployment"]["namespace"],
        body={
            "spec": {
                "replicas": 1,
            },
        },
    )
    memo.state = "edge"
    memo.bottom_counter = 0
    memo.upper_counter = 0
    memo.mean = 0


@kopf.timer('iscontrollers', interval=OPTIONS.timer, initial_delay=1)
def update_checker(memo: kopf.Memo, spec, logger, **_):
    if "mean" not in memo:
        memo.mean = 0
        memo.bottom_counter = 0
        memo.upper_counter = 0
        memo.state = "edge"
    try:
        services = [span["service"] for span in spec["spans"]]
        spans = [span["name"] for span in spec["spans"]]
        traces = ZIPKIN_CLIENT.fetch(
            spans=spans,
            services=services,
        )
        count, filtered = ZIPKIN_CLIENT.filter_by_services(
            response=traces,
            services=services,
        )
        logger.info(f"Grabbed {count} traces")
        if count > 100:
            logger.info(f"Compute mean with {count} traces")
            memo.mean = mean(traces=filtered, services=services)
            logger.info(f"Mean: {memo.mean}")
        else:
            memo.mean = 0
            memo.bottom_counter = 0
            memo.upper_counter = 0
            logger.warning("Cannot compute mean")
    except ConnectionError:
        memo.mean = 0
        memo.bottom_counter = 0
        memo.upper_counter = 0
        logger.warning("Could not fetch traces in ZipkinAPI")

    if memo.mean < spec["tracesTargetValue"]:
        memo.bottom_counter += 1

    if memo.mean > spec["tracesTargetValue"]:
        memo.upper_counter += 1

    logger.info(f"State: {memo.state}")
    logger.info(f"Bottom Counter: {memo.bottom_counter}")
    logger.info(f"Upper Counter: {memo.upper_counter}")

    if memo.bottom_counter > 10 and memo.mean < spec["tracesTargetValue"]:
        api = kubernetes.client.AppsV1Api()
        _ = api.patch_namespaced_deployment(
            name=spec["edge"]["deployment"]["name"],
            namespace=spec["edge"]["deployment"]["namespace"],
            body={
                "spec": {
                    "replicas": 0,
                },
            })
        logger.info("set edge deployment to 0.")
        for connection in spec["connections"]["stable"]:
            RABBITMQ_CLIENT.create_exchange_shovel(
                name=connection["name"],
                topic=connection["topic"],
                src=connection["src"],
                dest=connection["dest"],
            )
            logger.info(f"setting up {connection['name']}")
        for connection in spec["connections"]["test"]:
            RABBITMQ_CLIENT.create_exchange_shovel(
                name=connection["name"],
                topic=connection["topic"],
                src=connection["src"],
                dest=connection["dest"],
            )
            logger.info(f"setting up {connection['name']}")
        memo.state = "cloud"
        memo.bottom_counter = 0

    if memo.upper_counter > 10 and memo.mean > spec["tracesTargetValue"]:
        api = kubernetes.client.AppsV1Api()
        _ = api.patch_namespaced_deployment(
            name=spec["edge"]["deployment"]["name"],
            namespace=spec["edge"]["deployment"]["namespace"],
            body={
                "spec": {
                    "replicas": 1,
                },
            },
        )
        logger.info("set edge deployment to 1.")
        for connection in spec["connections"]["stable"]:
            RABBITMQ_CLIENT.delete_exchange_shovel(name=connection["name"])
            logger.info(f"deleting {connection['name']}")
        memo.state = "edge"
        memo.upper_counter = 0


@kopf.timer('iscontrollers', interval=60, initial_delay=1)
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
        if memo.state != "cloud":
            for connection in spec["connections"]["test"]:
                RABBITMQ_CLIENT.delete_exchange_shovel(name=connection["name"])
                logger.info(f"deleting {connection['name']}")
    else:
        logger.info("skipping...")


# if __name__ == "__main__":
#     loggers.configure(debug=True, verbose=True, quiet=False)
#     kopf.run(clusterwide=True)
