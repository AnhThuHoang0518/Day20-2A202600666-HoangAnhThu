# Single-Agent vs Multi-Agent Benchmark Report

Query: _"Do multi-agent LLM systems actually outperform single-agent systems on complex tasks? Produce a structured research brief."_
Model: gpt-4o-mini - Lab 20 - Multi-Agent Research System

Search source: AI-generated mock data for the Researcher because no free search API is required.
Cost note: estimated from token counts for lab comparison, not an invoice.

## Run Overview

| Run | Agents / Routes | Latency | Cost | Tokens In | Tokens Out | Quality |
|---|---|---:|---:|---:|---:|---:|
| Single-Agent | 1 LLM call | 12.26s | $0.000339 | 67 | 548 | 6.0 |
| Multi-Agent | 3 agents / 4 routes | 36.97s | $0.001032 | 1,528 | 1,338 | 10.0 |

## Metric Comparison

| Metric | Single-Agent | Multi-Agent | Winner |
|---|---:|---:|---|
| Latency | 12.26s | 36.97s | Single-Agent |
| Cost | $0.000339 | $0.001032 | Single-Agent |
| Tokens In | 67 | 1,528 | Single-Agent |
| Tokens Out | 548 | 1,338 | Multi-Agent for depth |
| Quality Proxy | 6.0 | 10.0 | Multi-Agent |

## Quality Scoring Method

The quality value is a heuristic proxy score from 0 to 10, not a human-judged grade. It is computed in `evaluation/benchmark.py` so both runs are scored consistently.

| Criterion | Points | Reason |
|---|---:|---|
| Base runnable answer | 4.0 | The workflow produced a state that can be evaluated. |
| Final answer length >= 500 characters | +1.5 | Rewards enough substance for a research-style answer. |
| Sources captured | +1.0 | Rewards evidence collection. Single-agent baseline does not use sources. |
| Research notes present | +1.0 | Rewards a distinct Researcher stage. |
| Analysis notes present | +1.0 | Rewards a distinct Analyst stage. |
| Citation coverage >= 40% | +1.0 | Rewards citing at least 40% of available sources in the final answer. |
| No runtime errors | +0.5 | Rewards successful completion. |

This explains why the single-agent run usually scores lower: it can produce a valid answer, but it has no separate sources, research notes, analysis notes, or citation coverage. The multi-agent run receives those extra points when the Researcher, Analyst, and Writer stages complete successfully.

## Multi-Agent Trace Flow

Supervisor(iter 1) -> researcher -> Researcher(in 330, out 170) -> Supervisor(iter 2) -> analyst -> Analyst(in 250, out 561) -> Supervisor(iter 3) -> writer -> Writer(in 948, out 607) -> Supervisor(iter 4) -> done -> Done

Route history: researcher -> analyst -> writer -> done

## Token and Cost Breakdown - Multi-Agent

| Agent | Tokens In | Tokens Out | Cost | Share of Multi-Agent Cost |
|---|---:|---:|---:|---:|
| Researcher | 330 | 170 | $0.000151 | 15% |
| Analyst | 250 | 561 | $0.000374 | 36% |
| Writer | 948 | 607 | $0.000506 | 49% |
| **Total** | **1,528** | **1,338** | **$0.001032** | **100%** |

## Actual Outputs - Same Query

### Single-Agent Output

1 LLM call - 67 tokens in / 548 tokens out - $0.000339

### Research Brief: Performance of Multi-Agent vs. Single-Agent LLM Systems on Complex Tasks

#### Introduction
Recent advancements in large language models (LLMs) have led to the exploration of multi-agent systems, where multiple LLMs collaborate to solve complex tasks. This brief evaluates whether multi-agent LLM systems outperform single-agent systems in such scenarios.

#### Key Findings

1. **Collaboration and Specialization**:
   - Multi-agent systems can leverage the strengths of individual agents, allowing for specialization in different aspects of a task (e.g., one agent for data retrieval, another for analysis).
   - This division of labor can lead to improved efficiency and accuracy in task completion.

2. **Diversity of Perspectives**:
   - Multiple agents can provide diverse viewpoints, which can enhance problem-solving capabilities and lead to more robust solutions.
   - This diversity can mitigate biases that may be present in a single-agent approach.

3. **Error Reduction**:
   - Collaborative systems can cross-verify outputs, reducing the likelihood of errors that might occur in a single-agent system.
   - Redundancy in processing can lead to higher reliability in results.

4. **Scalability**:
   - Multi-agent systems can scale more effectively to handle larger and more complex tasks by distributing workload among agents.
   - This scalability can be particularly beneficial in dynamic environments where tasks evolve.

#### Limitations

1. **Coordination Overhead**:
   - Multi-agent systems may introduce complexity in coordination and communication among agents, potentially leading to inefficiencies.
   - The overhead of managing interactions can negate some performance benefits.

2. **Resource Intensive**:
   - Multi-agent systems typically require more computational resources, which may not be feasible for all applications.
   - Increased resource demands can limit accessibility for smaller organizations or projects.

3. **Dependence on Task Complexity**:
   - The performance advantage of multi-agent systems may diminish for simpler tasks where a single agent can perform adequately.
   - The effectiveness of multi-agent systems is highly context-dependent.

4. **Evaluation Challenges**:
   - Comparing performance metrics between multi-agent and single-agent systems can be complex and may require careful experimental design.
   - Claims regarding superiority should be verified through rigorous empirical studies.

#### Conclusion
While multi-agent LLM systems show promise in outperforming single-agent systems on complex tasks due to collaboration, specialization, and error reduction, they also face challenges such as coordination overhead and resource demands. Further empirical research is needed to substantiate these claims and explore the contexts in which multi-agent systems are most beneficial. 

### External Verification Needed
Claims regarding specific performance metrics, empirical studies, and case examples should be verified through peer-reviewed research and practical implementations in the field.

### Multi-Agent Output

3 LLM calls - 1,528 tokens in / 1,338 tokens out - $0.001032

### Research Brief: Performance Comparison of Multi-Agent vs. Single-Agent LLM Systems on Complex Tasks

#### Key Findings:
1. **Role Specialization Enhances Performance**: Multi-agent systems demonstrate superior performance on complex tasks when roles are clearly defined (e.g., planning, research, analysis, writing, critique), leading to improved collaboration and efficiency [1].
   
2. **Improved Handling of Complex Cases**: In customer support, multi-agent workflows are more effective for complex cases by allowing for the separation of functions such as triage, policy lookup, and resolution, compared to single-agent systems which excel in straightforward tasks [2].

3. **Output Structure and Reviewability**: Benchmarking studies show that multi-agent workflows can enhance the structure and reviewability of outputs, which is beneficial for quality assurance [3].

4. **Latency and Cost Concerns**: While multi-agent systems can improve output quality, they may introduce increased latency and operational costs relative to single-agent systems [3].

5. **Communication and State Management**: Effective performance in multi-agent systems hinges on clear communication and shared state management to prevent hidden context issues that can negatively impact outcomes [1].

6. **Need for Robust Guardrails**: Production environments for LLM agents require robust guardrails, including input validation and structured outputs, to ensure reliability and accountability in multi-agent interactions [5].

#### Tradeoffs:
- **Performance vs. Complexity**: Multi-agent systems may outperform single-agent systems in complex scenarios but require more intricate setup and management, which can lead to increased latency and costs.
- **Quality vs. Efficiency**: While multi-agent systems can produce higher quality outputs, the need for coordination and communication may slow down the overall process compared to the more straightforward execution of single-agent systems.

#### Evidence Gaps:
- **Quantitative Metrics**: There is a lack of comprehensive quantitative studies comparing the performance metrics (e.g., speed, accuracy, cost) of multi-agent versus single-agent systems across a variety of complex tasks.
- **Longitudinal Studies**: More longitudinal studies are needed to assess the long-term effectiveness and reliability of multi-agent systems in real-world applications.
- **Contextual Performance**: Further research is required to understand how different contexts (e.g., industry-specific applications) influence the performance of multi-agent systems compared to single-agent systems.

#### Recommendation:
To determine the effectiveness of multi-agent LLM systems over single-agent systems, it is recommended to conduct controlled benchmarking studies that evaluate both systems across a range of complex tasks. These studies should focus on quantitative performance metrics, including speed, accuracy, and cost, while also considering the impact of role specialization and communication strategies. Additionally, exploring the implementation of robust guardrails in multi-agent systems is essential to ensure their reliability in production environments.

**Sources**:  
[1] Building Effective Multi-Agent Systems  
[2] Customer Support Agent Workflows  
[3] Benchmarking Single-Agent vs Multi-Agent Workflows  
[5] Production Guardrails for LLM Agents

## Verdict for This Query

### Where Single-Agent Wins

- Lower latency: about 3.0x faster (12.26s vs 36.97s).
- Lower estimated cost: about 3.0x cheaper ($0.000339 vs $0.001032).
- Better fit for fast, cost-sensitive questions where a concise answer is enough.

### Where Multi-Agent Wins

- More detailed output: about 2.4x more output tokens (1,338 vs 548).
- Clearer audit trail: Supervisor -> Researcher -> Analyst -> Writer -> Done.
- Better citation and review structure because the Researcher and Analyst stages are explicit.

### Balanced Judgment

For complex research-style questions, the multi-agent workflow produces a deeper and more auditable answer. The trade-off is significantly higher latency and estimated cost. For simple or urgent questions, the single-agent baseline is more efficient.

## Failure Mode

A likely failure mode is weak or irrelevant mock evidence: the Researcher may pass sources that do not fully support the final answer. The fix is to add source validation, require citations for key claims, and replace mock search with Tavily, Bing, SerpAPI, or internal documents when an API key is available.

## Trace Evidence

The runtime state stores route history and per-agent trace events. The latest local trace artifact is written to `reports/last_trace.json`. If LANGSMITH_TRACING=true and LANGSMITH_API_KEY is configured, provider spans are also attempted during workflow execution.
