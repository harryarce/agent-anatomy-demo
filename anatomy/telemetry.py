from contextlib import contextmanager
from time import perf_counter
from typing import Iterator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

_configured = False


def configure_console_tracing() -> None:
    global _configured
    if _configured:
        return
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _configured = True


@contextmanager
def timed_span(name: str, enabled: bool = False) -> Iterator[dict[str, float]]:
    started = perf_counter()
    timing: dict[str, float] = {}
    if not enabled:
        try:
            yield timing
        finally:
            timing["latency_seconds"] = perf_counter() - started
        return

    configure_console_tracing()
    with trace.get_tracer("agent-anatomy-lab").start_as_current_span(name):
        try:
            yield timing
        finally:
            timing["latency_seconds"] = perf_counter() - started
