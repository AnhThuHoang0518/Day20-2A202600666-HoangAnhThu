from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMResponse


class FakeLLMClient:
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if "Researcher" in system_prompt:
            return LLMResponse(content="- Multi-agent systems split work by role [1].")
        if "Analyst" in system_prompt:
            return LLMResponse(content="Key finding: role separation improves reviewability [1].")
        return LLMResponse(content="Final answer with citation [1].")


def test_supervisor_routes_to_missing_stage() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    SupervisorAgent().run(state)
    assert state.route_history == ["researcher"]


def test_agents_populate_state_without_real_api() -> None:
    llm = FakeLLMClient()
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    state = ResearcherAgent(llm_client=llm).run(state)
    state = AnalystAgent(llm_client=llm).run(state)
    state = WriterAgent(llm_client=llm).run(state)
    assert state.sources
    assert state.research_notes
    assert state.analysis_notes
    assert state.final_answer


def test_workflow_reaches_final_answer_without_real_api() -> None:
    llm = FakeLLMClient()
    workflow = MultiAgentWorkflow(
        agents={
            "researcher": ResearcherAgent(llm_client=llm),
            "analyst": AnalystAgent(llm_client=llm),
            "writer": WriterAgent(llm_client=llm),
        }
    )
    state = workflow.run(ResearchState(request=ResearchQuery(query="Explain multi-agent systems")))
    assert state.final_answer == "Final answer with citation [1]."
    assert state.route_history[-1] == "done"
