"""Benchmark report rendering."""

from dataclasses import dataclass

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import estimate_cost_usd, token_count


@dataclass(frozen=True)
class RunSummary:
    name: str
    latency_seconds: float
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float | None
    routes: str
    answer: str


def _answer_for(states_by_run: dict[str, ResearchState], run_name: str) -> str:
    state = states_by_run.get(run_name)
    if state is None or not state.final_answer:
        return f"No {run_name} answer captured."
    return state.final_answer


def _routes_for(states_by_run: dict[str, ResearchState], run_name: str) -> str:
    state = states_by_run.get(run_name)
    if state is None or not state.route_history:
        return "n/a"
    return " -> ".join(state.route_history)


def _metric_for(metrics: list[BenchmarkMetrics], run_name: str) -> BenchmarkMetrics | None:
    return next((metric for metric in metrics if metric.run_name == run_name), None)


def _summary_for(
    metrics: list[BenchmarkMetrics],
    states_by_run: dict[str, ResearchState],
    run_name: str,
) -> RunSummary:
    metric = _metric_for(metrics, run_name)
    state = states_by_run[run_name]
    tokens_in, tokens_out = token_count(state)
    cost = estimate_cost_usd(tokens_in, tokens_out)
    return RunSummary(
        name=run_name,
        latency_seconds=0.0 if metric is None else metric.latency_seconds,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
        quality_score=None if metric is None else metric.quality_score,
        routes=_routes_for(states_by_run, run_name),
        answer=_answer_for(states_by_run, run_name),
    )


def _fmt_seconds(value: float) -> str:
    return f"{value:.2f}s"


def _fmt_usd(value: float) -> str:
    return f"${value:.6f}"


def _winner_smaller(single_value: float, multi_value: float) -> str:
    if single_value < multi_value:
        return "Single-Agent"
    if multi_value < single_value:
        return "Multi-Agent"
    return "Tie"


def _winner_larger(single_value: float, multi_value: float) -> str:
    if single_value > multi_value:
        return "Single-Agent"
    if multi_value > single_value:
        return "Multi-Agent"
    return "Tie"


def _agent_breakdown(state: ResearchState) -> list[tuple[str, int, int, float]]:
    rows = []
    for result in state.agent_results:
        tokens_in = int(result.metadata.get("input_tokens") or 0)
        tokens_out = int(result.metadata.get("output_tokens") or 0)
        rows.append(
            (
                str(result.agent.value),
                tokens_in,
                tokens_out,
                estimate_cost_usd(tokens_in, tokens_out),
            )
        )
    return rows


def _trace_flow(state: ResearchState) -> str:
    chunks = []
    for event in state.trace:
        name = event["name"]
        payload = event.get("payload", {})
        if name == "supervisor.route":
            chunks.append(f"Supervisor(iter {payload.get('iteration')}) -> {payload.get('next')}")
        elif name.endswith(".run"):
            agent = name.removesuffix(".run").title()
            token_bits = []
            if payload.get("input_tokens") is not None:
                token_bits.append(f"in {payload.get('input_tokens')}")
            if payload.get("output_tokens") is not None:
                token_bits.append(f"out {payload.get('output_tokens')}")
            chunks.append(f"{agent}({', '.join(token_bits)})")
        elif name == "workflow.done":
            chunks.append("Done")
    return " -> ".join(chunks)


def _append_overview(lines: list[str], single: RunSummary, multi: RunSummary) -> None:
    lines.extend(
        [
            "## Run Overview",
            "",
            "| Run | Agents / Routes | Latency | Cost | Tokens In | Tokens Out | Quality |",
            "|---|---|---:|---:|---:|---:|---:|",
            f"| Single-Agent | 1 LLM call | {_fmt_seconds(single.latency_seconds)} | {_fmt_usd(single.cost_usd)} | {single.tokens_in:,} | {single.tokens_out:,} | {single.quality_score or 0:.1f} |",
            f"| Multi-Agent | 3 agents / {len(multi.routes.split(' -> '))} routes | {_fmt_seconds(multi.latency_seconds)} | {_fmt_usd(multi.cost_usd)} | {multi.tokens_in:,} | {multi.tokens_out:,} | {multi.quality_score or 0:.1f} |",
            "",
        ]
    )


def _append_metric_comparison(lines: list[str], single: RunSummary, multi: RunSummary) -> None:
    lines.extend(
        [
            "## Metric Comparison",
            "",
            "| Metric | Single-Agent | Multi-Agent | Winner |",
            "|---|---:|---:|---|",
            f"| Latency | {_fmt_seconds(single.latency_seconds)} | {_fmt_seconds(multi.latency_seconds)} | {_winner_smaller(single.latency_seconds, multi.latency_seconds)} |",
            f"| Cost | {_fmt_usd(single.cost_usd)} | {_fmt_usd(multi.cost_usd)} | {_winner_smaller(single.cost_usd, multi.cost_usd)} |",
            f"| Tokens In | {single.tokens_in:,} | {multi.tokens_in:,} | {_winner_smaller(single.tokens_in, multi.tokens_in)} |",
            f"| Tokens Out | {single.tokens_out:,} | {multi.tokens_out:,} | {_winner_larger(single.tokens_out, multi.tokens_out)} for depth |",
            f"| Quality Proxy | {single.quality_score or 0:.1f} | {multi.quality_score or 0:.1f} | {_winner_larger(single.quality_score or 0, multi.quality_score or 0)} |",
            "",
        ]
    )


def _append_quality_method(lines: list[str]) -> None:
    lines.extend(
        [
            "## Quality Scoring Method",
            "",
            "The quality value is a heuristic proxy score from 0 to 10, not a human-judged grade. It is computed in `evaluation/benchmark.py` so both runs are scored consistently.",
            "",
            "| Criterion | Points | Reason |",
            "|---|---:|---|",
            "| Base runnable answer | 4.0 | The workflow produced a state that can be evaluated. |",
            "| Final answer length >= 500 characters | +1.5 | Rewards enough substance for a research-style answer. |",
            "| Sources captured | +1.0 | Rewards evidence collection. Single-agent baseline does not use sources. |",
            "| Research notes present | +1.0 | Rewards a distinct Researcher stage. |",
            "| Analysis notes present | +1.0 | Rewards a distinct Analyst stage. |",
            "| Citation coverage >= 40% | +1.0 | Rewards citing at least 40% of available sources in the final answer. |",
            "| No runtime errors | +0.5 | Rewards successful completion. |",
            "",
            "This explains why the single-agent run usually scores lower: it can produce a valid answer, but it has no separate sources, research notes, analysis notes, or citation coverage. The multi-agent run receives those extra points when the Researcher, Analyst, and Writer stages complete successfully.",
            "",
        ]
    )


def _append_trace_flow(lines: list[str], multi_state: ResearchState) -> None:
    lines.extend(
        [
            "## Multi-Agent Trace Flow",
            "",
            _trace_flow(multi_state),
            "",
            "Route history: " + " -> ".join(multi_state.route_history),
            "",
        ]
    )


def _append_token_breakdown(lines: list[str], multi_state: ResearchState) -> None:
    rows = _agent_breakdown(multi_state)
    total_in = sum(row[1] for row in rows)
    total_out = sum(row[2] for row in rows)
    total_cost = sum(row[3] for row in rows)
    lines.extend(
        [
            "## Token and Cost Breakdown - Multi-Agent",
            "",
            "| Agent | Tokens In | Tokens Out | Cost | Share of Multi-Agent Cost |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for agent, tokens_in, tokens_out, cost in rows:
        percent = 0 if total_cost == 0 else cost / total_cost * 100
        lines.append(
            f"| {agent.title()} | {tokens_in:,} | {tokens_out:,} | {_fmt_usd(cost)} | {percent:.0f}% |"
        )
    lines.extend(
        [
            f"| **Total** | **{total_in:,}** | **{total_out:,}** | **{_fmt_usd(total_cost)}** | **100%** |",
            "",
        ]
    )


def _append_output_comparison(lines: list[str], single: RunSummary, multi: RunSummary) -> None:
    lines.extend(
        [
            "## Actual Outputs - Same Query",
            "",
            "### Single-Agent Output",
            "",
            f"1 LLM call - {single.tokens_in:,} tokens in / {single.tokens_out:,} tokens out - {_fmt_usd(single.cost_usd)}",
            "",
            single.answer,
            "",
            "### Multi-Agent Output",
            "",
            f"3 LLM calls - {multi.tokens_in:,} tokens in / {multi.tokens_out:,} tokens out - {_fmt_usd(multi.cost_usd)}",
            "",
            multi.answer,
            "",
        ]
    )


def _append_verdict(lines: list[str], single: RunSummary, multi: RunSummary) -> None:
    latency_ratio = multi.latency_seconds / single.latency_seconds if single.latency_seconds else 0
    cost_ratio = multi.cost_usd / single.cost_usd if single.cost_usd else 0
    output_ratio = multi.tokens_out / single.tokens_out if single.tokens_out else 0
    lines.extend(
        [
            "## Verdict for This Query",
            "",
            "### Where Single-Agent Wins",
            "",
            f"- Lower latency: about {latency_ratio:.1f}x faster ({_fmt_seconds(single.latency_seconds)} vs {_fmt_seconds(multi.latency_seconds)}).",
            f"- Lower estimated cost: about {cost_ratio:.1f}x cheaper ({_fmt_usd(single.cost_usd)} vs {_fmt_usd(multi.cost_usd)}).",
            "- Better fit for fast, cost-sensitive questions where a concise answer is enough.",
            "",
            "### Where Multi-Agent Wins",
            "",
            f"- More detailed output: about {output_ratio:.1f}x more output tokens ({multi.tokens_out:,} vs {single.tokens_out:,}).",
            "- Clearer audit trail: Supervisor -> Researcher -> Analyst -> Writer -> Done.",
            "- Better citation and review structure because the Researcher and Analyst stages are explicit.",
            "",
            "### Balanced Judgment",
            "",
            "For complex research-style questions, the multi-agent workflow produces a deeper and more auditable answer. The trade-off is significantly higher latency and estimated cost. For simple or urgent questions, the single-agent baseline is more efficient.",
            "",
        ]
    )


def render_markdown_report(
    metrics: list[BenchmarkMetrics],
    states_by_run: dict[str, ResearchState] | None = None,
    query: str | None = None,
    model_name: str | None = None,
) -> str:
    """Render a complete English benchmark report."""

    lines = [
        "# Single-Agent vs Multi-Agent Benchmark Report",
        "",
        f'Query: _"{query or "N/A"}"_',
        f"Model: {model_name or 'configured OpenAI model'} - Lab 20 - Multi-Agent Research System",
        "",
        "Search source: AI-generated mock data for the Researcher because no free search API is required.",
        "Cost note: estimated from token counts for lab comparison, not an invoice.",
        "",
    ]

    if states_by_run and "single-agent" in states_by_run and "multi-agent" in states_by_run:
        single = _summary_for(metrics, states_by_run, "single-agent")
        multi = _summary_for(metrics, states_by_run, "multi-agent")
        multi_state = states_by_run["multi-agent"]
        _append_overview(lines, single, multi)
        _append_metric_comparison(lines, single, multi)
        _append_quality_method(lines)
        _append_trace_flow(lines, multi_state)
        _append_token_breakdown(lines, multi_state)
        _append_output_comparison(lines, single, multi)
        _append_verdict(lines, single, multi)
    else:
        lines.extend(
            [
                "## Metric Summary",
                "",
                "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
                "|---|---:|---:|---:|---|",
            ]
        )
        for item in metrics:
            cost = "" if item.estimated_cost_usd is None else _fmt_usd(item.estimated_cost_usd)
            quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
            notes = item.notes.replace("|", "/")
            lines.append(
                f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | {notes} |"
            )
        lines.append("")
        _append_quality_method(lines)

    lines.extend(
        [
            "## Failure Mode",
            "",
            "A likely failure mode is weak or irrelevant mock evidence: the Researcher may pass sources that do not fully support the final answer. The fix is to add source validation, require citations for key claims, and replace mock search with Tavily, Bing, SerpAPI, or internal documents when an API key is available.",
            "",
            "## Trace Evidence",
            "",
            "The runtime state stores route history and per-agent trace events. The latest local trace artifact is written to `reports/last_trace.json`. If LANGSMITH_TRACING=true and LANGSMITH_API_KEY is configured, provider spans are also attempted during workflow execution.",
        ]
    )
    return "\n".join(lines) + "\n"
