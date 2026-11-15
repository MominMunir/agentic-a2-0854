from contextlib import contextmanager

from gigbid_core.config import settings

_tracer = None


def tracer():
    global _tracer
    if _tracer is None:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(
            resource=Resource.create({"service.name": "gigbid", "openinference.project.name": "gigbid"})
        )
        endpoint = settings().otel_exporter_otlp_endpoint
        if endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            headers = (
                {"Authorization": "Bearer " + settings().phoenix_api_key}
                if settings().phoenix_api_key
                else None
            )
            provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces", headers=headers)
                )
            )
        _tracer = provider.get_tracer("gigbid")
    return _tracer


@contextmanager
def span(name, **attributes):
    with tracer().start_as_current_span(name, attributes=attributes) as current:
        yield current
