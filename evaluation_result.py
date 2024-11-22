
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    query: str
    contexts: list[str] | None
    response_text: str
    passing: bool
    feedback: str
    