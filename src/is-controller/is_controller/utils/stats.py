from .zipkin import ZipkinResponse


def mean(traces: ZipkinResponse) -> float:
    durations = []
    for trace in traces:
        durations.append(sum([span["duration"] for span in trace]))
    return sum(durations) / len(durations)
