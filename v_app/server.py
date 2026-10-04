from fastapi import FastAPI
from .cache import VerifiedCache
from .models import ExecutionClass, Result, Task, VerificationStatus
from .policy import Policy
from .runtime import AgentRuntime

app = FastAPI(title="Open Agent App", version="0.1.0")
runtime = AgentRuntime(cache=VerifiedCache(), policy=Policy())

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/architecture")
def architecture() -> dict:
    return {"control_plane": ["policy", "cache", "routing", "recovery"], "agent_plane": ["CATCH agents", "tools", "models", "realtime"], "evidence_plane": ["trajectory", "trace", "visible_verifier", "independent_verifier"], "cache_rule": "Only VERIFIED, provenance-compatible, non-side-effect results are reusable."}

class EchoVerifier:
    name = "echo-bootstrap"
    def verify(self, task, output):
        return Result(status=VerificationStatus.VERIFIED, output=output, metadata={"verifier": self.name})

@app.post("/execute")
def execute(payload: dict) -> dict:
    task = Task(task_id=payload["task_id"], input=payload.get("input"), model=payload.get("model", "unspecified"), model_revision=payload.get("model_revision", "unknown"), code_revision=payload.get("code_revision", "unknown"), tool_revision=payload.get("tool_revision", "unknown"), policy_revision=payload.get("policy_revision", "v1"), execution_class=ExecutionClass(payload.get("execution_class", "read_only")))
    result = runtime.execute(task, lambda _: payload.get("output"), verifier=EchoVerifier())
    return {"status": result.status.value, "output": result.output, "cache_key": result.cache_key, "metadata": result.metadata}
