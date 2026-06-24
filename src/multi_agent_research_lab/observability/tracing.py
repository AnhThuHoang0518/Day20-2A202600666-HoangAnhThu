"""Tracing hooks for local trace events, LangSmith, and Langfuse."""

from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import get_settings


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Create one local span and best-effort provider spans.

    LangSmith is enabled by LANGSMITH_TRACING=true plus LANGSMITH_API_KEY.
    Langfuse is enabled when LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY exist.
    Provider failures are captured in the local span and never fail the lab run.
    """

    settings = get_settings()
    started = perf_counter()
    inputs = attributes or {}
    span: dict[str, Any] = {
        "name": name,
        "attributes": inputs,
        "duration_seconds": None,
        "outputs": {},
    }
    langsmith_manager: Any | None = None
    langsmith_run: Any | None = None
    langfuse_client: Any | None = None
    langfuse_manager: Any | None = None
    langfuse_observation: Any | None = None

    if settings.langsmith_tracing and settings.langsmith_api_key:
        try:
            from langsmith.run_helpers import trace

            langsmith_manager = trace(name=name, run_type="chain", inputs=inputs)
            langsmith_run = langsmith_manager.__enter__()
        except Exception as exc:  # pragma: no cover - depends on external provider config
            span["langsmith_error"] = str(exc)
            langsmith_manager = None
            langsmith_run = None

    if settings.langfuse_public_key and settings.langfuse_secret_key:
        try:
            from langfuse import Langfuse

            langfuse_client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                base_url=settings.langfuse_base_url,
            )
            langfuse_manager = langfuse_client.start_as_current_observation(
                as_type="span",
                name=name,
                input=inputs,
            )
            langfuse_observation = langfuse_manager.__enter__()
        except Exception as exc:  # pragma: no cover - depends on external provider config
            span["langfuse_error"] = str(exc)
            langfuse_client = None
            langfuse_manager = None
            langfuse_observation = None

    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started
        outputs = span.get("outputs", {})

        if langsmith_manager is not None:
            try:
                if langsmith_run is not None and hasattr(langsmith_run, "end"):
                    langsmith_run.end(outputs=outputs)
                langsmith_manager.__exit__(None, None, None)
            except Exception as exc:  # pragma: no cover - tracing should not fail the lab
                span["langsmith_error"] = str(exc)

        if langfuse_manager is not None:
            try:
                if langfuse_observation is not None and hasattr(langfuse_observation, "update"):
                    langfuse_observation.update(output=outputs)
                langfuse_manager.__exit__(None, None, None)
                if langfuse_client is not None and hasattr(langfuse_client, "flush"):
                    langfuse_client.flush()
            except Exception as exc:  # pragma: no cover - tracing should not fail the lab
                span["langfuse_error"] = str(exc)
