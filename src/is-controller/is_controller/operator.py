import kopf

from requests.exceptions import ConnectionError

from utils.zipkin import ZipkinClient
from utils.controller import mean

ZIPKIN_CLIENT = ZipkinClient(
    zipkin="http://10.20.5.2:30200",
    limit=1000,
    loopback=300000,
    drift=100000,
)

@kopf.timer('iscontrollers', interval=10, initial_delay=1)
def update_checker(memo: kopf.Memo, spec, logger, **kwargs):
    if "mean" not in memo:
        memo.mean = 0
    try:
        traces = ZIPKIN_CLIENT.fetch(
            spans=[span["name"] for span in spec["spans"]],
            services=[span["service"] for span in spec["spans"]],
        )
    except ConnectionError:
        logger.warn("Could not fetch traces in ZipkinAPI")
    if len(traces) > 0:
        memo.mean = mean(traces=traces)
    else:
        logger.warn("Cannot compute mean")
    logger.info(f"Mean: {memo.mean}")
    logger.info(f"traces: {len([trace for trace in traces if len(trace) >= 2])}")
