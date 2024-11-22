from typing_extensions import override
from binary_evaluator import BinaryEvaluator
from evaluation_result import EvaluationResult
from evaluation_templates import GENERAL_GUIDELINES, GUIDELINES_CHOOSING_TEMPLATE, GUIDELINES_EVALUATION_TEMPLATE, GULAQ_GUIDELINES
class GuidelineComplianceEvaluator(BinaryEvaluator):
    def __init__(self) -> None:
        super().__init__()
        
    def _extract_relevancy(self, response: str) -> bool:
        if "Relevant:" in response:
            result = response.split("Relevant:")[1].split("\n")[0].strip()
            if "YES" in result.upper():
                return True
            else:
                return False
        else:
            return False
        
    async def _get_relevant_guidelines(self, question: str, response_text: str) -> list[str]:
        # Create a new list with a copy of GENERAL_GUIDELINES
        relevant_guidelines: list[str] = GENERAL_GUIDELINES.copy()
        
        for guideline in GULAQ_GUIDELINES:
            prompt = GUIDELINES_CHOOSING_TEMPLATE.format(query=question, generated_answer=response_text, guidelines=guideline)
            completion = await self.llm.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content":prompt}
                    ],  
                temperature=0.1
            )
            if completion.choices[0].message.content is None:
                raise ValueError("No response from the model")
            relevant: bool = self._extract_relevancy(completion.choices[0].message.content)
            if not relevant:
                continue
            relevant_guidelines.append(guideline)
        return relevant_guidelines
            
    @override
    async def _evaluate(self, response_text: str|None = None, question: str|None = None, answer: str|None = None, contexts: list[str]|None = None) -> EvaluationResult:
        if response_text is None or question is None:
            raise ValueError("Question, response_text, must be provided for faithfulness evaluation")
        relevant_guidelines: list[str] = await self._get_relevant_guidelines(question, response_text)
        results: list[bool] = []
        feedbacks: list[str] = []
        for guideline in relevant_guidelines:
            prompt = GUIDELINES_EVALUATION_TEMPLATE.format(query=question, generated_answer=response_text, guidelines=guideline)
            completion = await self.llm.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content":prompt}
                    ],
                temperature=0.0
            )
            if completion.choices[0].message.content is None:
                raise ValueError("No response from the model")
            results.append(self._extract_result(completion.choices[0].message.content))
            feedbacks.append(self._extract_feedback(completion.choices[0].message.content))
        passing: bool = all(results)
        feedback: str = "\n".join(feedbacks)
        return EvaluationResult(query=question, contexts=contexts, response_text=response_text, passing=passing, feedback=feedback)
