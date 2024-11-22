from typing_extensions import override
from binary_evaluator import BinaryEvaluator
from evaluation_result import EvaluationResult
from evaluation_templates import CORRECTNESS_EVALUATION_TEMPLATE


class CorrectnessEvaluator(BinaryEvaluator):
    def __init__(self) -> None:
        super().__init__()
        
    @override
    async def _evaluate(self, response_text: str|None = None, question: str|None = None, answer: str|None = None, contexts: list[str]|None = None) -> EvaluationResult:
        if question is None or answer is None or response_text is None:
            raise ValueError("Question, answer, and response must be provided for correctness evaluation")
        prompt = CORRECTNESS_EVALUATION_TEMPLATE.format(query=question, reference_answer=answer, generated_answer=response_text)
        completion = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content":prompt}
                ],
            temperature=0.0
        )
        if completion.choices[0].message.content is None:
            raise ValueError("No response from the model")
        result: bool = self._extract_result(completion.choices[0].message.content)
        feedback: str = self._extract_feedback(completion.choices[0].message.content)
        return EvaluationResult(query=question, contexts=contexts, response_text=response_text, passing=result, feedback=feedback)
