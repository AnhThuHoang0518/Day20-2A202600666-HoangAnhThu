"""Writer agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import CompletionClient, LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: CompletionClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""

        sources = "\n".join(
            f"[{index}] {source.title}: {source.url}"
            for index, source in enumerate(state.sources, start=1)
        )
        response = self.llm_client.complete(
            system_prompt=(
                "You are the Writer agent. Write a clear final answer for technical "
                "learners using the research and analysis. Include citations like [1]. "
                "Match the language of the user's question exactly. If the question is "
                "in English, write the entire answer in English only."
            ),
            user_prompt=(
                f"Question: {state.request.query}\n"
                f"Audience: {state.request.audience}\n\n"
                f"Research notes:\n{state.research_notes or 'No research notes.'}\n\n"
                f"Analysis notes:\n{state.analysis_notes or 'No analysis notes.'}\n\n"
                f"Sources:\n{sources}\n\n"
                "Write the final answer in the same language as the question. "
                "For this benchmark, if the question is English, use English only. "
                "End with a short 'Sources' list."
            ),
        )
        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                },
            )
        )
        state.add_trace_event(
            "writer.run",
            {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "final_answer_chars": len(response.content),
            },
        )
        return state
