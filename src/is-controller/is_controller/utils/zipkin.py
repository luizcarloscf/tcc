from typing import List, TypeVar, Dict
from typing_extensions import TypedDict, NotRequired

from requests import get

import time

K = TypeVar("K")
V = TypeVar("V")


class LocalEndpoint(TypedDict):
    serviceName: str
    port: NotRequired[int]


class Span(TypedDict):
    traceId: str
    id: str
    name: str
    timestamp: int
    duration: int
    parentId: NotRequired[str]
    localEndpoint: LocalEndpoint
    tags: NotRequired[Dict[K, V]]

Trace = List[Span]
ZipkinResponse =  List[Trace]


class ZipkinRequest(TypedDict):
    endTs: int
    loopback: int
    limit: int
    serviceName: NotRequired[str]
    spanName: NotRequired[str]

class ZipkinClient:

    def __init__(self, zipkin: str, loopback: int, drift: int, limit: int) -> None:
        self._zipkin = zipkin
        self._loopback = loopback
        self._drift = drift
        self._limit = limit

    def fetch(self, spans: List[str], services: List[str]) -> ZipkinResponse:
        response = get(
            url=f'{self._zipkin}/api/v2/traces',
            params=self.payload(spans=spans, services=services),
        )
        response.raise_for_status()
        traces: ZipkinResponse = response.json()
        return self.filter(traces, spans=spans, services=services)
    
    def filter(self, response: ZipkinResponse, spans: List[str], services: List[str]) -> ZipkinResponse:
        intermediary = []
        for trace in response:
            if len(spans) > 0:
                names = [span["name"] for span in trace]
                count = 0
                for span_name in spans:
                    for name in names:
                        if name.startswith(span_name):
                            count += 1
                if count == len(spans):
                    intermediary.append(trace)
        traces = []
        for trace in intermediary:
            if len(services) > 0:
                names = [span["localEndpoint"]["serviceName"] for span in trace]
                count = 0
                for service_name in services:
                    for name in names:
                        if name.startswith(service_name):
                            count += 1
                if count == len(spans):
                    traces.append(trace)
        return traces

    @property
    def timestamp(self) -> int:
        return round(time.time() * 1000)

    def payload(self, spans: List[str], services: List[str]) -> ZipkinRequest:
        return ZipkinRequest(
            endTs=self.timestamp - self._drift,
            loopback=self._loopback,
            limit=self._limit,
            serviceName=services[-1],
            spanName=spans[-1],
        )
