"""Multi-agent workflow orchestration."""

from collections.abc import Mapping

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    The implementation is intentionally lightweight for the lab: routing lives in
    SupervisorAgent, while this class executes the selected worker and records trace
    events. It can be replaced with a LangGraph StateGraph without changing agents.
    """

    def __init__(self, agents: Mapping[str, BaseAgent] | None = None) -> None:
        self.supervisor = SupervisorAgent()
        self.agents: dict[str, BaseAgent] = dict(
            agents
            or {
                "researcher": ResearcherAgent(),
                "analyst": AnalystAgent(),
                "writer": WriterAgent(),
            }
        )

    def build(self) -> dict[str, list[str]]:
        """Return a simple graph description for review and debugging."""

        return {
            "supervisor": ["researcher", "analyst", "writer", "done"],
            "researcher": ["supervisor"],
            "analyst": ["supervisor"],
            "writer": ["supervisor"],
        }

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""

        settings = get_settings()
        while state.iteration < settings.max_iterations:
            with trace_span("supervisor", {"iteration": state.iteration}) as span:
                state = self.supervisor.run(state)
                span["outputs"] = {"route": state.route_history[-1]}

            route = state.route_history[-1]
            if route == "done":
                state.add_trace_event("workflow.done", {"iteration": state.iteration})
                return state

            agent = self.agents.get(route)
            if agent is None:
                message = f"No agent registered for route: {route}"
                state.errors.append(message)
                state.add_trace_event("workflow.error", {"error": message})
                return state

            with trace_span(route, {"iteration": state.iteration}) as span:
                state = agent.run(state)
                span["outputs"] = {"errors": len(state.errors)}

        state.errors.append("Max iterations reached before workflow completed.")
        state.add_trace_event(
            "workflow.max_iterations", {"max_iterations": settings.max_iterations}
        )
        return state
