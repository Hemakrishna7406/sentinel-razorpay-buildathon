"""
Sentinel — OpenTelemetry Tracer Factory

Configures the OTLP exporter and provides get_tracer() so any module can
create spans without knowing the backend (Jaeger, Collector, stdout, etc.).

Jaeger is the default development backend, configured via:
    OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317

If OTEL_EXPORTER_OTLP_ENDPOINT is not set, tracing is no-op (stdout-only
fallback or disabled), and authorization is completely unaffected.

Design contract:
- get_tracer() never raises. Returns a no-op tracer on failure.
- Span context propagation uses W3C Trace Context (traceparent header).
- Trace context injected into Kafka message payload as {"traceparent": "..."}.
"""

import os
import logging

logger = logging.getLogger(__name__)

_tracer_provider = None
_tracer_initialized = False


def _init_tracing() -> None:
    global _tracer_provider, _tracer_initialized
    if _tracer_initialized:
        return
    _tracer_initialized = True

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    service_name = os.environ.get("OTEL_SERVICE_NAME", "sentinel")

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.sdk.resources import Resource

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        if endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info(f"OpenTelemetry OTLP exporter configured: {endpoint}")
            except Exception as e:
                # OTLP unavailable — fall back to no-op (no stdout spam in prod)
                logger.warning(f"OTLP exporter unavailable, tracing disabled: {e}")
        else:
            logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set — tracing in no-op mode.")

        trace.set_tracer_provider(provider)
        _tracer_provider = provider

    except ImportError:
        logger.warning("opentelemetry packages not installed — tracing disabled.")
    except Exception as e:
        logger.warning(f"Tracing initialization failed — authorization unaffected: {e}")


def get_tracer(name: str):
    """
    Return an OpenTelemetry Tracer for the given component name.
    Returns a no-op tracer if OTel is not available or not configured.
    Never raises.
    """
    try:
        _init_tracing()
        from opentelemetry import trace
        return trace.get_tracer(name)
    except Exception:
        return _NoOpTracer()


def inject_trace_context(payload: dict) -> dict:
    """
    Inject W3C traceparent into a dict payload for Kafka propagation.
    Returns the payload unmodified if tracing is unavailable.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.propagate import inject
        carrier: dict = {}
        inject(carrier)
        if carrier:
            payload = {**payload, **carrier}
    except Exception:
        pass
    return payload


def extract_trace_context(payload: dict):
    """
    Extract W3C traceparent from a Kafka message payload dict and return
    the OTel context. Returns None if unavailable.
    """
    try:
        from opentelemetry.propagate import extract
        return extract(payload)
    except Exception:
        return None


class _NoOpSpan:
    """Minimal no-op span for when OTel is unavailable."""
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def set_attribute(self, *args): pass
    def set_status(self, *args): pass
    def record_exception(self, *args): pass


class _NoOpTracer:
    """Minimal no-op tracer for when OTel is unavailable."""
    def start_as_current_span(self, name: str, **kwargs):
        return _NoOpSpan()
    def start_span(self, name: str, **kwargs):
        return _NoOpSpan()
