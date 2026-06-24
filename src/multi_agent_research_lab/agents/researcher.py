"""Researcher agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import CompletionClient, LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(
        self,
        search_client: SearchClient | None = None,
        llm_client: CompletionClient | None = None,
    ) -> None:
        self.search_client = search_client or SearchClient()
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""

        sources = self.search_client.search(state.request.query, state.request.max_sources)
        state.sources = sources
        source_block = "\n".join(
            f"[{index}] {source.title} ({source.url}) - {source.snippet}"
            for index, source in enumerate(sources, start=1)
        )
        response = self.llm_client.complete(
            system_prompt=(
                "You are the Researcher agent. Extract concise evidence notes from the "
                "provided sources only. Keep citations as [1], [2], etc."
            ),
            user_prompt=(
                f"Research question: {state.request.query}\n"
                f"Audience: {state.request.audience}\n\n"
                f"Sources:\n{source_block}\n\n"
                "Return 4-6 bullet notes with citations."
            ),
        )
        state.research_notes = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=response.content,
                metadata={
                    "source_count": len(sources),
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                },
            )
        )
        state.add_trace_event(
            "researcher.run",
            {
                "source_count": len(sources),
                "titles": [source.title for source in sources],
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            },
        )
        return state
