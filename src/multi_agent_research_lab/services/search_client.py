"""Search client abstraction for ResearcherAgent."""

from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client backed by AI-generated mock data.

    If a free search API is not available, the lab allows local mock data. These
    documents simulate search results and keep citation flow testable.
    """

    _mock_corpus = [
        SourceDocument(
            title="Building Effective Multi-Agent Systems",
            url="mock://multi-agent-patterns",
            snippet=(
                "Multi-agent systems work best when a complex task is split into clear "
                "roles such as planning, research, analysis, writing, and critique. "
                "A supervisor should route work using shared state instead of hidden context."
            ),
            metadata={"topic": "multi-agent", "source_type": "ai_mock"},
        ),
        SourceDocument(
            title="Supervisor Routing and Handoffs",
            url="mock://supervisor-routing",
            snippet=(
                "A supervisor agent decides the next worker by inspecting missing fields, "
                "quality gates, errors, and iteration limits. Guardrails include max "
                "iterations, timeout, retry, validation, and fallback paths."
            ),
            metadata={"topic": "orchestration", "source_type": "ai_mock"},
        ),
        SourceDocument(
            title="Research Agent Source Collection",
            url="mock://research-agent-sources",
            snippet=(
                "The researcher should gather concise source notes, preserve citations, "
                "filter irrelevant results, and pass evidence forward to downstream agents."
            ),
            metadata={"topic": "research", "source_type": "ai_mock"},
        ),
        SourceDocument(
            title="Benchmarking Single-Agent vs Multi-Agent Workflows",
            url="mock://agent-benchmarking",
            snippet=(
                "A useful benchmark compares latency, token cost, answer quality, citation "
                "coverage, and failure rate. Multi-agent workflows may improve structure and "
                "reviewability while increasing latency and cost."
            ),
            metadata={"topic": "benchmark", "source_type": "ai_mock"},
        ),
        SourceDocument(
            title="Production Guardrails for LLM Agents",
            url="mock://production-guardrails",
            snippet=(
                "Production agents need bounded execution, input validation, structured "
                "outputs, trace logs, and recovery behavior when tools fail or evidence is weak."
            ),
            metadata={"topic": "guardrails", "source_type": "ai_mock"},
        ),
        SourceDocument(
            title="GraphRAG Research Summary",
            url="mock://graphrag-summary",
            snippet=(
                "GraphRAG combines retrieval augmented generation with graph-structured "
                "representations of entities and relationships. It is useful for synthesis "
                "across large document collections where relationships matter."
            ),
            metadata={"topic": "graphrag", "source_type": "ai_mock"},
        ),
        SourceDocument(
            title="Customer Support Agent Workflows",
            url="mock://customer-support-agents",
            snippet=(
                "For customer support, a single agent is simple and fast for common tickets, "
                "while a multi-agent workflow can separate triage, policy lookup, resolution, "
                "and quality review for complex cases."
            ),
            metadata={"topic": "customer-support", "source_type": "ai_mock"},
        ),
    ]

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""

        query_terms = {term.lower() for term in query.replace("-", " ").split() if len(term) > 3}

        def score(document: SourceDocument) -> int:
            text = f"{document.title} {document.snippet} {document.metadata}".lower()
            return sum(1 for term in query_terms if term in text)

        ranked = sorted(self._mock_corpus, key=score, reverse=True)
        selected = [document for document in ranked if score(document) > 0]
        if not selected:
            selected = ranked
        return selected[:max_results]
