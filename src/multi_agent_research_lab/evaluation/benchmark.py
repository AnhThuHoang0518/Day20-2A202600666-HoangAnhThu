"""Benchmark helpers for single-agent vs multi-agent."""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]

# Estimated OpenAI gpt-4o-mini-style rates. Adjust these constants if the configured
# model uses different pricing; report values are for lab comparison, not billing.
INPUT_COST_PER_1M_TOKENS = 0.15
OUTPUT_COST_PER_1M_TOKENS = 0.60


def token_count(state: ResearchState) -> tuple[int, int]:
    """Return input and output tokens accumulated from agent metadata."""

    input_tokens = 0
    output_tokens = 0
    for result in state.agent_results:
        input_tokens += int(result.metadata.get("input_tokens") or 0)
        output_tokens += int(result.metadata.get("output_tokens") or 0)
    return input_tokens, output_tokens


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    """Estimate run cost from token usage."""

    return (input_tokens / 1_000_000 * INPUT_COST_PER_1M_TOKENS) + (
        output_tokens / 1_000_000 * OUTPUT_COST_PER_1M_TOKENS
    )


def _citation_coverage(state: ResearchState) -> float:
    if not state.sources or not state.final_answer:
        return 0.0
    cited = sum(
        1 for index in range(1, len(state.sources) + 1) if f"[{index}]" in state.final_answer
    )
    return cited / len(state.sources)


def _quality_score(state: ResearchState) -> float:
    score = 4.0
    if state.final_answer and len(state.final_answer) >= 500:
        score += 1.5
    if state.sources:
        score += 1.0
    if state.research_notes:
        score += 1.0
    if state.analysis_notes:
        score += 1.0
    if _citation_coverage(state) >= 0.4:
        score += 1.0
    if not state.errors:
        score += 0.5
    return min(score, 10.0)


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, quality proxy, token usage, citation coverage, and errors."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    input_tokens, output_tokens = token_count(state)
    coverage = _citation_coverage(state)
    notes = (
        f"tokens_in={input_tokens}; tokens_out={output_tokens}; "
        f"citation_coverage={coverage:.0%}; errors={len(state.errors)}; "
        f"routes={','.join(state.route_history) or 'n/a'}"
    )
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=estimate_cost_usd(input_tokens, output_tokens),
        quality_score=_quality_score(state),
        notes=notes,
    )
    return state, metrics
