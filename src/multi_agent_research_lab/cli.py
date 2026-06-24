"""Command-line entrypoint for the lab."""

import json
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _ascii_safe(text: str) -> str:
    """Avoid Windows cp1252 console crashes when model output contains Vietnamese."""

    return text.encode("ascii", errors="backslashreplace").decode("ascii")


def _json_safe(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=True, indent=2)


def run_baseline_state(query: str) -> ResearchState:
    """Run one OpenAI call as the single-agent baseline."""

    state = ResearchState(request=ResearchQuery(query=query))
    response = LLMClient().complete(
        system_prompt=(
            "You are a single-agent research assistant. Answer directly and mention when "
            "claims would need external verification."
        ),
        user_prompt=(
            f"Question: {query}\n"
            "Write a concise answer for technical learners. Include a short limitations section."
        ),
    )
    state.final_answer = response.content
    state.agent_results.append(
        AgentResult(
            agent=AgentName.WRITER,
            content=response.content,
            metadata={
                "mode": "single_agent_baseline",
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            },
        )
    )
    state.add_trace_event(
        "baseline.run",
        {"input_tokens": response.input_tokens, "output_tokens": response.output_tokens},
    )
    return state


def run_multi_agent_state(query: str) -> ResearchState:
    """Run the Supervisor -> Researcher -> Analyst -> Writer workflow."""

    state = ResearchState(request=ResearchQuery(query=query))
    return MultiAgentWorkflow().run(state)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the single-agent OpenAI baseline."""

    _init()
    state = run_baseline_state(query)
    console.print(Panel.fit(_ascii_safe(state.final_answer or ""), title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    result = run_multi_agent_state(query)
    console.print(_json_safe(result.model_dump()))


@app.command()
def benchmark(
    query: Annotated[
        str,
        typer.Option(
            "--query",
            "-q",
            help="Research query used for both baseline and multi-agent runs",
        ),
    ] = "Research GraphRAG state-of-the-art and write a 500-word summary",
) -> None:
    """Run benchmark and write reports/benchmark_report.md."""

    _init()
    settings = get_settings()
    baseline_state, baseline_metrics = run_benchmark("single-agent", query, run_baseline_state)
    multi_state, multi_metrics = run_benchmark("multi-agent", query, run_multi_agent_state)
    store = LocalArtifactStore()
    report = render_markdown_report(
        [baseline_metrics, multi_metrics],
        states_by_run={"single-agent": baseline_state, "multi-agent": multi_state},
        query=query,
        model_name=settings.openai_model,
    )
    report_path = store.write_text("benchmark_report.md", report)
    trace_path = store.write_text(
        "last_trace.json",
        json.dumps(
            {
                "query": query,
                "route_history": multi_state.route_history,
                "trace": multi_state.trace,
                "agent_results": [result.model_dump() for result in multi_state.agent_results],
                "errors": multi_state.errors,
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    console.print(Panel.fit(str(report_path), title="Benchmark report written"))
    console.print(Panel.fit(str(trace_path), title="Local trace written"))
    console.print(
        Panel.fit(
            f"final_answer_chars={len(multi_state.final_answer or '')}; "
            f"trace_events={len(multi_state.trace)}; routes={','.join(multi_state.route_history)}",
            title="Multi-Agent Run Summary",
        )
    )


if __name__ == "__main__":
    app()
