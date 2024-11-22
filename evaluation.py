import asyncio
from dataclasses import dataclass
import datetime
import os
from pathlib import Path
import pickle
from statistics import mean
from typing import Any

from llama_index.core.base.response.schema import Response
from llama_index.core.schema import NodeWithScore
import nest_asyncio
from openai import OpenAI

from backend.question_answering.app.core.supabase_config import supabase_client
from backend.question_answering.app.services.answer_service.answer_service import (
    AnswerService,
)
from backend.question_answering.app.services.user_service.sign_in_service import (
    SignInService,
)
from evaluation.binary_evaluator import BinaryEvaluator
from evaluation.correctness_evaluator import CorrectnessEvaluator
from evaluation.evaluation_result import EvaluationResult
from evaluation.faithfulness_evaluator import FaithfulnessEvaluator
from evaluation.guideline_compliance_evaluator import GuidelineComplianceEvaluator
from evaluation.relevancy_evaluator import RelevancyEvaluator

nest_asyncio.apply()
import logging
logging.getLogger().setLevel(logging.ERROR)

@dataclass
class EvaluationSummary:
    category: str
    pass_rate: float
    top_performers: list[EvaluationResult]
    worst_performers: list[EvaluationResult]
    distribution_stats: Any | None = None
    error_count: int = 0
    
class EvaluationMetrics:
    @staticmethod
    def get_distribution_stats(results: list[EvaluationResult]) -> dict[str, dict[str, int] | float | str]:
        """Calculate distribution statistics for a category."""
        pass_count = sum(1 for r in results if r.passing)
        fail_count = len(results) - pass_count
        return {
            'distribution': {
                'pass': pass_count,
                'fail': fail_count
            },
            'median': 1.0 if pass_count > fail_count else 0.0,
            'mode': 'PASS' if pass_count > fail_count else 'FAIL'
        }


    @staticmethod
    def get_category_metrics(results: list[EvaluationResult]) -> dict[str, Any]:
        """Calculate metrics for a specific category."""
        scores = [1.0 if r.passing else 0.0 for r in results]
        pass_rate = mean(scores)
        return {
            'passing_rate': pass_rate,
            'total_evaluations': len(results),
            'distribution_stats': EvaluationMetrics.get_distribution_stats(results)
        }

class EvaluationReportFormatter:
    @staticmethod
    def format_distribution(dist_stats: dict[str, Any]) -> str:
        """Format distribution statistics as a string."""
        dist = dist_stats['distribution']
        dist_str = "Distribution Stats:\n"
        dist_str += f"  PASS: {dist['pass']} responses\n"
        dist_str += f"  FAIL: {dist['fail']} responses\n"
        dist_str += f"  Mode: {dist_stats['mode']}"
        return dist_str

    @staticmethod
    def generate_llm_analysis_prompt(report: dict[str, Any]) -> str:
        """Generate the prompt for LLM analysis."""
        prompt = f"""
        Please analyze the following evaluation results and provide a concise summary of the main points:
        
        Overall Score (normalized): {report['overall_score']:.2f}
        """
        
        for category, metrics in report['detailed_metrics'].items():
            prompt += f"\n\n{category.upper()}"
            prompt += f"""\nPass Rate: {metrics['passing_rate']:.2%}
            \nDistribution: {EvaluationReportFormatter.format_distribution(metrics['distribution_stats'])}"""
        
        
        prompt += """
        
        Key observations to include:
        1. Overall performance assessment
        2. Strongest and weakest categories
        3. Notable patterns or areas for improvement
        4. Analysis of score distributions
        5. Specific observations about outliers
        6. Guideline compliance assessment
        """

        return prompt

    @staticmethod
    def format_report(report: dict[str, Any]) -> str:
        """Format the evaluation report as a readable string."""
        output:list[Any] = []
        output.append("=== EVALUATION REPORT ===\n")
        output.append(f"Total Evaluations Done: {report['responses_processed']}")
        output.append(f"Overall Score (normalized): {report['overall_score']:.2f}")
        for category, metrics in report['detailed_metrics'].items():
            output.append(f"{category.upper()} Pass Rate: {metrics['passing_rate']:.2%}")
            
        output.append("\nLLM Analysis:")
        output.append(report['llm_analysis'])
        
        output.append("\nCategory Summaries:")
        for category, summary in report['category_summaries'].items():
            output.append(f"\n{category.upper()}")
            output.append(f"Pass Rate: {summary.pass_rate:.2%}")
            output.append(EvaluationReportFormatter.format_distribution(
                summary.distribution_stats))
            output.append(f"Errors: {summary.error_count}")
            
            output.append("\nTop 3 Performers:")
            for result in summary.top_performers:
                output.append(f"- {'PASS' if result.passing else 'FAIL'}")
                output.append(f"  Query: {result.query}")
                output.append(f"  Generated Response: {result.response_text}")
                output.append(f"  Feedback: {result.feedback}\n")
            
            output.append("Bottom 3 Performers:")
            for result in summary.worst_performers:
                output.append(f"- {'PASS' if result.passing else 'FAIL'}")
                output.append(f"  Query: {result.query}")
                output.append(f"  Generated Response: {result.response_text}")
                output.append(f"  Feedback: {result.feedback}\n")
        
        return "\n".join(output)


class ResponseEvaluationPipeline:
    def __init__(
        self,
        llm: OpenAI,
        version: int,
        description: str,
        model: str,
        evaluators: dict[str, BinaryEvaluator],
        output_dir: str = "evaluation",
    ):
        self.evaluators: dict[str, BinaryEvaluator] = evaluators
        self.llm: OpenAI = llm
        self.version: int = version
        self.description: str = description
        self.model: str = model
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir: str = output_dir
        
    def _save_temp_results(self, result_name: str, results: list[EvaluationResult]):
        results_file_path = os.path.join(self.output_dir, f'{result_name}.pkl')
        with open(results_file_path, 'wb') as f:
            pickle.dump(results, f)
            
    async def evaluate_responses(
        self,
        responses: list[Response],
        questions: list[str],
        correct_answers: list[str],
        limit: int = 500
    ) -> dict[str, list[EvaluationResult]]:
        
        responses = responses[:limit]
        questions = questions[:limit]
        correct_answers = correct_answers[:limit]

        """Evaluate a list of responses against questions and correct answers with retry on failure."""
        eval_results = {}
        try:
            for category, evaluator in self.evaluators.items():
                print(f"Evaluating {category}...")
                eval_results[category] = await evaluator.evaluate_responses(questions=questions, answers=correct_answers, responses=responses)
                self._save_temp_results(f"{category}_eval_results", eval_results[category])
        except Exception as e:
            print("ERROR: ", e)
            raise e 
        
        return eval_results

    def generate_report(self, evaluation_results: dict[str, list[EvaluationResult]], responses_processed:int) -> dict[str, Any]:
        """Generate a comprehensive evaluation report."""
        report: dict[str, Any] = {
            'category_summaries': {},
            'overall_score': 0.0,
            'llm_analysis': '',
            'detailed_metrics': {},
            'responses_processed': responses_processed
        }
        
        normalized_averages = []
        for category, results in evaluation_results.items():
            filtered_results = [r for r in results if r.response_text != "ERROR"]
            sorted_results = sorted(filtered_results, key=lambda x: (1 if x.passing else 0, x.query), reverse=True)
            
            top_3 = sorted_results[:3]
            bottom_3 = sorted_results[-3:]
            metrics = EvaluationMetrics.get_category_metrics(filtered_results)

            report['category_summaries'][category] = EvaluationSummary(
                category=category,
                top_performers=top_3,
                worst_performers=bottom_3,
                pass_rate=metrics['passing_rate'],
                distribution_stats=metrics['distribution_stats'],
                error_count=len(results) - len(filtered_results)
            )
            
            report['detailed_metrics'][category] = metrics
            normalized_averages.append(metrics['passing_rate'])
        
        report['overall_score'] = mean(normalized_averages)
        
        # Generate LLM analysis
        analysis_prompt = EvaluationReportFormatter.generate_llm_analysis_prompt(report)
        report['llm_analysis'] = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.0
        ).choices[0].message.content
        
        return report

    def save_report(self, report: dict[str, Any]):
        """Save the evaluation report to a file."""
        formatted_report = EvaluationReportFormatter.format_report(report)
        
        pipeline_metadata = {
            'version': self.version,
            'description': self.description,
            'model': self.model,
            'date_evaluated': datetime.datetime.now().strftime('%B %d %Y %H:%M:%S PST')
        }
            
        pipeline_metadata_str = f'''
        --------------------------
        === PIPELINE METADATA ===
        ----------
        version: {pipeline_metadata['version']}
        description: {pipeline_metadata['description']}
        model: {pipeline_metadata['model']}
        date_evaluated: {pipeline_metadata['date_evaluated']}
        '''
        
        final_report = formatted_report + pipeline_metadata_str
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save report
        output_path = Path(self.output_dir) / f'evaluation_report_p{self.version}.txt'
        with open(output_path, 'w') as f:
            f.write(final_report)

class EvaluationRunner:
    def __init__(self, version: int, description: str, model: str, evaluators: dict[str, BinaryEvaluator]):
        self.output_dir = f"evaluation_v{version}"
        self.pipeline = ResponseEvaluationPipeline(
            llm=OpenAI(),
            version=version,
            description=description,
            model=model,
            evaluators=evaluators,
            output_dir=self.output_dir
        )
        sign_in_service = SignInService()
        sign_in_service.sign_in()     
        self.questions, self.correct_answers = self._load_golden_dataset()

    def _load_golden_dataset(self):
        golden_dataset = supabase_client.schema('question_answering').table('golden_dataset').select('*').execute()
        questions = [d['question'] for d in golden_dataset.data]
        answers = [d['answer'] for d in golden_dataset.data]
        return questions, answers    
        
    def _generate_responses(self, answers, source_nodes):
        return [Response(answer, source_nodes) for answer, source_nodes in zip(answers, source_nodes)]

    def _generate_answers(self, limit: int = 50) -> tuple[list[str], list[list[NodeWithScore]]]:
        answer_service = AnswerService()
        questions = self.questions[:limit]
        async def answer_questions_in_parallel(questions: list[str]):
            async def semaphored_process(question: str):
                async with asyncio.Semaphore(6):
                    return await answer_service.answer_question(question)

            responses = await asyncio.gather(*(semaphored_process(question) for question in questions))
            return responses

        # Call the async function to get answers
        responses: list[tuple[str, list[NodeWithScore]]] = asyncio.run(answer_questions_in_parallel(questions))
        answers, source_nodes = zip(*responses)
        return answers, source_nodes

    def _load_or_generate_responses(self, responses_file: str | None, limit: int) -> list[Response]:
        if responses_file is not None and os.path.exists(responses_file):
            print(f"Loading responses from {responses_file}...")
            with open(responses_file, 'rb') as file:
                responses = pickle.load(file)
            
            # Ensure all loaded responses are of type Response
            if all(isinstance(response, Response) for response in responses):
                print("Responses loaded successfully.")
                return responses
            else:
                print("Invalid response types found. Generating new responses...")
        
        print(f"{responses_file} not found or invalid. Generating new responses...")
        answers, source_nodes = self._generate_answers(limit)
        return self._generate_responses(answers, source_nodes)
    
    async def run(self, responses_file: str | None = None, limit: int = 500):
        responses = self._load_or_generate_responses(responses_file, limit)

        print("Evaluating responses...")
        eval_results = await self.pipeline.evaluate_responses(responses, self.questions, self.correct_answers, limit=limit)

        print("Generating report...")
        report: dict[str, Any] = self.pipeline.generate_report(eval_results, responses_processed=limit)
        
        print("Saving report...")
        self.pipeline.save_report(report)
        
        print("Done!")
        
if __name__ == "__main__":
    evaluators: dict[str, BinaryEvaluator] = {
        'correctness': CorrectnessEvaluator(),
        'faithfulness': FaithfulnessEvaluator(),
        'relevancy': RelevancyEvaluator(),
        'guideline_compliance': GuidelineComplianceEvaluator(),
    }
    runner = EvaluationRunner(version=000, description="", model="gpt-4o", evaluators=evaluators)

    start_time = datetime.datetime.now()
    asyncio.run(runner.run(responses_file="responses_p0_limit_50.pkl", limit=30))
    end_time = datetime.datetime.now()
    print(f"Total execution time: {end_time - start_time}")

