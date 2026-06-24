# Design Template

## Problem

Build a research assistant that answers complex technical questions by collecting evidence, analyzing tradeoffs, and writing a sourced final answer.

## Why multi-agent?

A single agent can answer quickly, but it mixes research, analysis, and writing in one step. The multi-agent workflow makes responsibilities visible, creates better handoff state, and gives reviewers a trace of who did what.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Route work and stop safely | Shared `ResearchState` | Next route: researcher, analyst, writer, done | Bad routing loop or premature stop |
| Researcher | Find evidence and create cited notes | Query and mock search corpus | `sources`, `research_notes` | Irrelevant or weak sources |
| Analyst | Extract claims, tradeoffs, and risks | Research notes and query | `analysis_notes` | Missed caveats or unsupported claims |
| Writer | Produce final user-facing answer | Research notes, analysis notes, sources | `final_answer` | Hallucinated claims or missing citations |

## Shared state

`ResearchState` stores the query, iteration count, route history, sources, research notes, analysis notes, final answer, agent results, trace events, and errors. These fields make handoff explicit and easy to debug.

## Routing policy

The supervisor checks missing fields in order: if there are no research notes, call Researcher; if there are no analysis notes, call Analyst; if there is no final answer, call Writer; otherwise stop. The workflow also stops at `MAX_ITERATIONS`.

## Guardrails

- Max iterations: configured by `MAX_ITERATIONS`, default 6.
- Timeout: configured by `TIMEOUT_SECONDS` for production extension.
- Retry: should be added around provider calls for production.
- Fallback: mock search data replaces Tavily/Bing/SerpAPI when no free search API is available.
- Validation: state fields and benchmark checks catch missing answer, sources, citations, and errors.

## Benchmark plan

Use the same query for the single-agent baseline and the multi-agent workflow. Compare latency, token usage, quality proxy, citation coverage, route history, and failure count. The report is written to `reports/benchmark_report.md`.
