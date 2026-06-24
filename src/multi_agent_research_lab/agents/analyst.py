"""Analyst agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import CompletionClient, LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: CompletionClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""

        response = self.llm_client.complete(
            system_prompt=(
                "You are the Analyst agent. Convert research notes into structured claims, "
                "tradeoffs, risks, and weak-evidence flags. Preserve source citations."
            ),
            user_prompt=(
                f"Research question: {state.request.query}\n\n"
                f"Research notes:\n{state.research_notes or 'No research notes.'}\n\n"
                "Return: key findings, tradeoffs, evidence gaps, and recommendation."
            ),
        )
        state.analysis_notes = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                },
            )
        )
        state.add_trace_event(
            "analyst.run",
            {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            },
        )
        return state
