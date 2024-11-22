# Language Model Response Evaluation Framework

## Project Overview
This framework provides a comprehensive evaluation system for assessing language model responses across multiple dimensions including correctness, faithfulness, relevancy, and guideline compliance. It uses advanced evaluation techniques to analyze responses and generate detailed reports on their quality and adherence to specified criteria.

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Supabase credentials

### Setup Steps
1. Clone the repository:
git clone <repository-url>
cd <repository-name>

2. Install required dependencies:
pip install llama-index openai typing-extensions nest-asyncio pydantic supabase

3. Configure environment variables:
export OPENAI_API_KEY="your-api-key"
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"

## Usage Instructions

### Basic Usage
1. Initialize the evaluation system:
from evaluation import EvaluationRunner
from correctness_evaluator import CorrectnessEvaluator
from faithfulness_evaluator import FaithfulnessEvaluator
from relevancy_evaluator import RelevancyEvaluator
from guideline_compliance_evaluator import GuidelineComplianceEvaluator

# Configure evaluators
evaluators = {
    'correctness': CorrectnessEvaluator(),
    'faithfulness': FaithfulnessEvaluator(),
    'relevancy': RelevancyEvaluator(),
    'guideline_compliance': GuidelineComplianceEvaluator(),
}

# Create runner instance
runner = EvaluationRunner(
    version=1,
    description="Evaluation run description",
    model="gpt-4",
    evaluators=evaluators
)

2. Run evaluation:
import asyncio

# Run evaluation with optional response file and limit
asyncio.run(runner.run(
    responses_file="responses.pkl",
    limit=50
))

### Output
The evaluation results will be saved in an `evaluation_v{version}` directory, containing detailed reports and metrics for each evaluation dimension.

## Codebase Structure

- `evaluation.py`: Main orchestration file containing the EvaluationRunner and pipeline logic
- `evaluation_result.py`: Defines the EvaluationResult data structure for storing evaluation outcomes
- `binary_evaluator.py`: Base class for all evaluators implementing binary evaluation logic
- `correctness_evaluator.py`: Evaluator for assessing response accuracy
- `faithfulness_evaluator.py`: Evaluator for checking response alignment with source material
- `relevancy_evaluator.py`: Evaluator for determining response relevance to queries
- `guideline_compliance_evaluator.py`: Evaluator for checking adherence to specified guidelines
- `evaluation_templates.py`: Contains templates for evaluation prompts

## Dependencies

### Core Dependencies
- `llama-index`: Framework for evaluation and response handling
- `openai`: OpenAI API client for model interactions
- `typing-extensions`: Enhanced type hinting support
- `nest-asyncio`: Async operation handling
- `pydantic`: Data validation
- `supabase`: Database interactions

### API Requirements
- OpenAI API access
- Supabase database access

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Set up development environment following installation steps
4. Make changes following project conventions
5. Add tests for new functionality
6. Submit pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Maintain async/await patterns where implemented
- Add docstrings for new functions/classes

### Testing
- Add unit tests for new features
- Ensure all tests pass before submitting PR
- Include test cases for edge scenarios

### Pull Request Process
1. Update documentation for any new features
2. Add entry to changelog if applicable
3. Ensure CI checks pass
4. Request review from maintainers

For any questions or issues, please open a GitHub issue in the repository.