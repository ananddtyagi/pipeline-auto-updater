from typing_extensions import override
from binary_evaluator import BinaryEvaluator
from llama_index.core.evaluation.relevancy import RelevancyEvaluator as LlamaIndexRelevancyEvaluator
from evaluation_result import EvaluationResult
from llama_index.core.evaluation.base import EvaluationResult as LlamaIndexEvaluationResult
class RelevancyEvaluator(BinaryEvaluator):
    def __init__(self) -> None:
        super().__init__()
    @override
    async def _evaluate(self, response_text: str|None = None, question: str|None = None, answer: str|None = None, contexts: list[str]|None = None) -> EvaluationResult:
        if response_text is None or question is None or contexts is None:
            raise ValueError("Question, contexts, response_text, must be provided for relevancy evaluation")
        evaluator = LlamaIndexRelevancyEvaluator()
        evaluation_result: LlamaIndexEvaluationResult = await evaluator.aevaluate(query=question, response=response_text, contexts=contexts)
        return EvaluationResult(query=question, contexts=contexts, response_text=response_text, passing=evaluation_result.passing or False, feedback=evaluation_result.feedback or "")