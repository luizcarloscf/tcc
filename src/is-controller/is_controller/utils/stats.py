from typing import List
from .zipkin import ZipkinResponse


def mean(traces: ZipkinResponse, services: List[str]) -> float:
    durations = []
    for trace in traces:
        duration = 0
        for span in trace:
            if span["localEndpoint"]["serviceName"] in services:
                duration += span["duration"]
        durations.append(duration)
    return sum(durations) / len(durations)
