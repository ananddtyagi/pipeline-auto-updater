from abc import abstractmethod
import asyncio
from typing import Any
from collections.abc import Coroutine
from llama_index.core.base.response.schema import Response
from openai import AsyncOpenAI

from evaluation_result import EvaluationResult

class BinaryEvaluator():
    def __init__(self) -> None:
        self.llm: AsyncOpenAI = AsyncOpenAI()
        self._completed_count = 0
        self._total_count = 0
        
    @abstractmethod
    async def _evaluate(self, response_text: str|None = None, question: str|None = None, answer: str|None = None, contexts: list[str]|None = None) -> EvaluationResult:
        pass
    
    def _extract_result(self, response: str) -> bool:
        if "Result:" in response:
            result = response.split("Result:")[1].split("\n")[0].strip()
            if "PASS" in result.strip().upper():
                return True
            else:
                return False
        else:
            return False
        
    def _extract_feedback(self, response: str) -> str:
        if "Feedback:" in response:
            r = response.split("Feedback:")[1].strip()
            if "<" in r:
                return r.split("<")[0].strip()
            else:
                return r
        else:
            return ""
        
    async def evaluate_responses(self, questions: list[str], answers: list[str], 
                               responses: list[Response]) -> list[dict[str, int | EvaluationResult]]:
        self._total_count = len(questions)
        self._completed_count = 0
        
        semaphore = asyncio.Semaphore(20)  # Limit concurrent evaluations
        
        async def evaluate_single_response(i: int) -> dict[str, int | EvaluationResult]:
            async with semaphore:
                question: str = questions[i]
                answer: str = answers[i]
                response_text: str = responses[i].response or ""
                contexts: list[str] = [node.__str__() for node in responses[i].source_nodes]
                
                try:
                    evaluation_result: EvaluationResult = await self._evaluate(response_text, question, answer, contexts)
                    self._completed_count += 1
                    if self._completed_count % 10 == 0:
                        print(f"Completed {self._completed_count} of {self._total_count} responses ({(self._completed_count/self._total_count)*100:.1f}%)")
                    return {
                        'index': i,
                        'evaluation': evaluation_result
                    }
                except Exception as e:
                    print(f'Error evaluating response {i}: {e}')
                    return {
                        'index': i,
                        'evaluation': EvaluationResult(
                            query=question,
                            contexts=None,
                            response_text="ERROR",
                            passing=False,
                            feedback=str(e)
                        )
                    }

        # Use asyncio.gather to run evaluations in parallel
        tasks: list[Coroutine[Any, Any, dict[str, int | EvaluationResult]]] = [evaluate_single_response(i) for i in range(len(questions))]
        results: list[Any] = await asyncio.gather(*tasks)
        sorted_results: list[dict[str, EvaluationResult]] = sorted(results, key=lambda x: x['index'])
        evaluations: list[EvaluationResult] = [result['evaluation'] for result in sorted_results]
        return evaluations
