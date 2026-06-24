"""Optional critic agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append lightweight citation findings."""

        final_answer = state.final_answer or ""
        cited = sum(1 for index in range(1, len(state.sources) + 1) if f"[{index}]" in final_answer)
        finding = (
            f"Citation check: {cited}/{len(state.sources)} available sources referenced. "
            "Review any uncited key claims before production use."
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=finding,
                metadata={"cited_sources": cited, "source_count": len(state.sources)},
            )
        )
        state.add_trace_event(
            "critic.run", {"cited_sources": cited, "source_count": len(state.sources)}
        )
        return state
