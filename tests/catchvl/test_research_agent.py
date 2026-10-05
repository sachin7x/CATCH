from rllm.catchvl.agent import ResearchAgent
from rllm.catchvl.trajectory import Evidence, VerificationResult


class FakeResearch:
    def search(self, query: str, *, limit: int = 8):
        return [Evidence(source="test", claim=query, status="VERIFIED")]


class FakeVerifier:
    def verify(self, task: str, answer: str, context):
        return VerificationResult(passed=True, truth_status="VERIFIED", audit_reward=1.0)


class FakeRedTeam:
    def attack(self, task: str, answer: str, context):
        return [Evidence(source="red-team", claim="no conflict", status="VERIFIED")]


def test_research_agent_preserves_independent_status():
    agent = ResearchAgent(FakeResearch(), FakeVerifier(), FakeRedTeam())
    result = agent.run("test question", context={"draft_answer": "answer"})
    assert result["truth_status"] == "VERIFIED"
    assert result["evidence"][0]["status"] == "VERIFIED"
    assert result["verification"]["audit_reward"] == 1.0


def test_research_agent_promotes_red_team_conflict():
    class ConflictRedTeam:
        def attack(self, task: str, answer: str, context):
            return [Evidence(source="red-team", claim="conflict", status="CONFLICT")]

    agent = ResearchAgent(FakeResearch(), FakeVerifier(), ConflictRedTeam())
    result = agent.run("test question", context={"draft_answer": "answer"})
    assert result["truth_status"] == "CONFLICT"


def test_configuration_hash_is_stable():
    a = ResearchAgent.configuration_hash({"b": 2, "a": 1})
    b = ResearchAgent.configuration_hash({"a": 1, "b": 2})
    assert a == b
