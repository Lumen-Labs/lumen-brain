from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True)
class BrainIngestionConnection:
    """BrainAPI engine credentials for ingestion task operations."""

    base_url: str
    brain_id: str
    brain_pat: str

    def task_request(self, task_id: str):
        return (
            f"{self.base_url.rstrip('/')}/tasks/{quote(task_id, safe='')}",
            {"BrainPAT": self.brain_pat, "X-Brain-ID": self.brain_id},
        )
