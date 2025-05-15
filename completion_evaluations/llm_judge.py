import os  
import base64
import json
from openai import AzureOpenAI  
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import dotenv
from typing import Dict, List, Optional
import re
import ast
import glob
import argparse
import numpy as np
from collections import defaultdict
from pathlib import Path

dotenv.load_dotenv()

# o3-mini endpoint and deployment details - matching generate_completions.py
O3MINI_ENDPOINT = os.getenv("O3MINI_ENDPOINT", "https://deepprompteastus.openai.azure.com")  # Endpoint without the deployment path
O3MINI_DEPLOYMENT = os.getenv("O3MINI_DEPLOYMENT", "deepprompt-o3-mini-2025-01-31")  # The deployment name to use in API calls
O3MINI_API_VERSION = "2024-12-01-preview"

def bootstrap_ci(judge_results, n_bootstrap=10000, confidence=0.95):
    """
    Calculate bootstrap confidence intervals for the given results.
    
    Args:
        judge_results: List of score values
        n_bootstrap: Number of bootstrap samples (default: 10000)
        confidence: Confidence level (default: 0.95)
        
    Returns:
        Tuple of (lower_ci, upper_ci)
    """
    N = len(judge_results)
    bootstrap_means = [
        np.mean(np.random.choice(judge_results, N, replace=True)) for _ in range(n_bootstrap)
    ]
    lower = np.percentile(bootstrap_means, (1 - confidence) / 2 * 100)
    upper = np.percentile(bootstrap_means, (1 + confidence) / 2 * 100)
    return lower, upper

def read_jsonl_file(file_path):
    """Read a JSONL file and return a list of parsed JSON objects."""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:  # Skip empty lines
                    data.append(json.loads(line))
        return data
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return []

def extract_score(response_text):
    """Extract score from the LLM response for single model evaluation."""
    try:
        # Extract score using regex
        score_match = re.search(r'Final\s+Sum\s+Score\s+for\s+Completion:?\s*(?:\*\*)?([0-9.]+)(?:\*\*)?', response_text, re.IGNORECASE)
        score = None
        if score_match:
            score = float(score_match.group(1))
            
        # If no score found, try more aggressive pattern matching
        if score is None:
            # Look for other patterns like "Score: 5" or "Final Score: 5"
            alt_patterns = [
                r'Final\s+Score:?\s*(?:\*\*)?([0-9.]+)(?:\*\*)?',
                r'Score:?\s*(?:\*\*)?([0-9.]+)(?:\*\*)?',
                r'Score\s+for\s+Completion:?\s*(?:\*\*)?([0-9.]+)(?:\*\*)?'
            ]
            
            for pattern in alt_patterns:
                alt_match = re.search(pattern, response_text, re.IGNORECASE)
                if alt_match:
                    score = float(alt_match.group(1))
                    break
        
        print(f"Extracted score: {score}")
        return score
        
    except Exception as e:
        print(f"Error extracting score: {str(e)}")
        return None

def find_all_models(completions_dir: str, include_baseline: bool = False) -> List[str]:
    """
    Find all available models in the completions directory.
    
    Args:
        completions_dir: Directory containing completion files
        include_baseline: Whether to include the baseline model in the results
        
    Returns:
        List of model names found in the directory
    """
    # Set to store unique model names
    models = set()
    
    # Find all JSONL files in the completions directory
    all_files = glob.glob(f"{completions_dir}/**/*.jsonl", recursive=True)
    
    # Extract model names from filenames
    baseline = "4omini_sft39_spm_fix2_5"
    for file_path in all_files:
        # Skip files that don't have a model suffix
        if "-" not in os.path.basename(file_path):
            continue
            
        # Extract the model name part (after the dash, before .jsonl)
        model_part = os.path.basename(file_path).split("-", 1)[1].replace(".jsonl", "")
        
        # Skip formatted files and optionally skip the baseline model
        if "_formatted" in model_part:
            continue
            
        if model_part == baseline and not include_baseline:
            continue
            
        models.add(model_part)
    
    return list(models)

def display_score_summary(results_dir: str, specific_model=None):
    """
    Display a summary of single model evaluation scores
    
    Args:
        results_dir: Directory containing evaluation result files
        specific_model: Optional - if provided, only display and save summary for this model
    """
    print("\n\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    
    # Call generate_single_model_summary to create the summary
    summary = generate_single_model_summary(results_dir)
    
    # Filter for specific model if requested
    if specific_model and specific_model in summary:
        summary = {specific_model: summary[specific_model]}
    
    # Display single model evaluation scores
    if summary:
        print("\nSINGLE MODEL EVALUATIONS:")
        print("="*50)
        
        # Sort models by overall score (highest first)
        sorted_models = sorted(
            summary.items(), 
            key=lambda x: x[1]['overall']['score'], 
            reverse=True
        )
        
        for model_name, model_data in sorted_models:
            print(f"\nModel: {model_name}")
            print("-" * 50)
            
            # Display overall score first with confidence intervals if available
            overall = model_data.get('overall', {})
            score_str = f"{overall.get('score'):.2f}/10"
            
            # Add confidence interval if available
            ci_warning = overall.get('ci_warning', False)
            ci_str = f" (95% CI: {overall.get('lower_ci'):.2f}-{overall.get('upper_ci'):.2f})"
            if ci_warning:
                ci_str += " ⚠️ Limited samples"
                
            score_str += ci_str
                
            print(f"OVERALL: Score: {score_str} (across {overall.get('categories_count')} categories, {overall.get('sample_count')} samples)")
            
            # Display language breakdowns if available
            if 'languages' in model_data:
                print("\nLanguage breakdown:")
                for language, lang_data in model_data['languages'].items():
                    lang_score = lang_data.get('score')
                    samples = lang_data.get('sample_count')
                    
                    lang_score_str = f"{lang_score:.2f}"
                    lang_ci_warning = lang_data.get('ci_warning', False)
                    lang_ci_str = f" (95% CI: {lang_data.get('lower_ci'):.2f}-{lang_data.get('upper_ci'):.2f})"
                    if lang_ci_warning:
                        lang_ci_str += " ⚠️ Limited samples"
                        
                    lang_score_str += lang_ci_str
                        
                    print(f"  {language}: {lang_score_str} ({samples} samples)")
            
            # Display each category
            print("\nCategory breakdown:")
            for category, scores in model_data.items():
                if category in ('overall', 'languages'):
                    continue
                
                cat_score_str = f"{scores['score']:.2f}"
                cat_ci_warning = scores.get('ci_warning', False)
                cat_ci_str = f" (95% CI: {scores.get('lower_ci'):.2f}-{scores.get('upper_ci'):.2f})"
                if cat_ci_warning:
                    cat_ci_str += " ⚠️ Limited samples"
                    
                cat_score_str += cat_ci_str
                    
                print(f"  {category}: {cat_score_str}, Evaluations: {scores['evaluations']}")
                
            print(f"\nDetailed results available in: {results_dir}/{model_name}_detailed_results/")
    else:
        print("No evaluation results found.")

def evaluate_single_completion(model_file, output_file, model_name, max_evaluations=None, current_evaluations=0):
    """
    Evaluate a single model's completions using o3 mini.
    
    Args:
        model_file: Path to the model completions JSONL
        output_file: Path to save evaluation results
        model_name: Name of the model being evaluated
        max_evaluations: Maximum number of evaluations to run (for debugging)
        current_evaluations: Number of evaluations already processed
    
    Returns:
        Number of evaluations processed in this run
    """
    print(f"Using o3 mini model for evaluation: {O3MINI_DEPLOYMENT}")

    # Initialize Azure OpenAI Service client with Entra ID authentication (matching generate_completions.py)
    token_provider = get_bearer_token_provider(  
        DefaultAzureCredential(),  
        "https://cognitiveservices.azure.com/.default"
    )  
    
    # Initialize o3-mini client exactly as in generate_completions.py
    client = AzureOpenAI(  
        api_version=O3MINI_API_VERSION,
        azure_endpoint=O3MINI_ENDPOINT,
        azure_ad_token_provider=token_provider,  
    )

    model_data = read_jsonl_file(model_file)
    
    # Extract language and category from the file path
    # Expected structure: ../completions/{language}/{category}/{filename}
    file_path = os.path.normpath(model_file)
    path_parts = file_path.split(os.sep)
    
    # Default values
    actual_language = "unknown"
    actual_category = "unknown"
    
    # Find the "completions" folder in the path to get more reliable indexes
    for i, part in enumerate(path_parts):
        if part == "completions":
            # If we found the completions folder, the structure should be:
            # .../completions/language/category/filename.jsonl
            if i + 2 < len(path_parts):  # Ensure we have enough parts for language
                actual_language = path_parts[i + 1]
            if i + 3 < len(path_parts):  # Ensure we have enough parts for category
                # Category might contain underscores itself (like api_usage)
                actual_category = path_parts[i + 2]
            break
    
    print(f"Path components: Language={actual_language}, Category={actual_category}")

    # Limit the number of evaluations for debugging
    if max_evaluations is not None:
        evaluations_left = max_evaluations - current_evaluations
        if evaluations_left <= 0:
            return 0  # Skip processing if we've already hit the limit
            
        if len(model_data) > evaluations_left:
            print(f"Limiting to {evaluations_left} evaluations (out of {len(model_data)}) due to max_evaluations setting")
            model_data = model_data[:evaluations_left]

    # Single model evaluation prompt template
    single_model_prompt_template = """You are a highly experienced software judge tasked with evaluating the quality of a model-generated code completion. For a given code prefix and suffix, your job is to evaluate a completion based on the criteria below and determine the overall final score (0-10). Assign a score (0-5) for each category. Please solely focus on the completion quality.

    # Evaluation Criteria:
    1. Relevance to Prefix and Suffix (0-5): Does the code completion connect semantically meaningfully to both the prefix and suffix?
    2. Helpfulness (0-5): Does the completion provide non-trivial assistance, adding meaningful content that reduces the user's effort in writing code?

    Based on the evaluation, provide your answer following format:
    Final Sum Score for Completion: <score>
    Detailed Reasoning:
    <your reasoning here>
    
    # Begin:
    Prefix: 
    ```
    {prefix}
    ```
    
    Model Completion: 
    ```
    {completion}
    ```
    
    Suffix: 
    ```
    {suffix}
    ```
    """

    # Store evaluation results
    evaluation_results = []
    processed_count = 0

    try:
        for entry in model_data:
            entry_id = entry.get("id")
            prefix = entry.get("prefix", "")
            suffix = entry.get("suffix", "")
            model_completion = entry.get(model_name, "")
            
            # Use extracted language from path, but allow entry values to override if present
            language = entry.get("language", actual_language)
 
            print(f"\n\nEvaluating single completion for ID: {entry_id}")
            
            formatted_prompt = single_model_prompt_template.format(
                prefix=prefix,
                completion=model_completion,
                suffix=suffix
            )
            
            messages = [{"role": "user", "content": formatted_prompt}]

            try:
                # Call o3-mini model with the same parameters as in generate_completions.py
                completion = client.chat.completions.create(  
                    model=O3MINI_DEPLOYMENT,  
                    messages=messages,
                    stream=False  
                )

                response_content = completion.choices[0].message.content
                print(f"Evaluation result:")
                print(response_content)
                
                # Extract score from response
                score = extract_score(response_content)
                
                # Add result to our collection
                result = {
                    "id": entry_id,
                    "score": score,
                    "language": language,
                    "category": actual_category,
                    "full_response": response_content
                }

                print(f"Final Score for ID {entry_id}: {score}")

                evaluation_results.append(result)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing evaluation: {str(e)}")
                evaluation_results.append({
                    "id": entry_id,
                    "score": None,
                    "language": language,
                    "category": actual_category,
                    "error": str(e)
                })

        # Save all evaluation results to a JSON file
        with open(output_file, 'w', encoding='utf-8') as outfile:
            json.dump(evaluation_results, outfile, indent=2)
        
        print(f"\nEvaluation results saved to {output_file}")
        return processed_count

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return 0

def generate_single_model_summary(results_dir: str, output_file: str = None):
    """
    Generate a properly structured single model summary file that groups all categories
    under their respective models.
    
    Args:
        results_dir: Directory containing evaluation result files
        output_file: Optional path to save the summary JSON (defaults to results_dir/single_model_summary.json)
    
    Returns:
        Dictionary with the summary data
    """
    print("\n\n" + "="*80)
    print("GENERATING SINGLE MODEL SUMMARY")
    print("="*80)
    
    # Find all single model evaluation files
    single_eval_files = glob.glob(f"{results_dir}/*_single_evaluation.json")
    
    # Dictionary to store model scores by category
    model_data = {}
    
    # List of model names to ensure consistent ordering
    model_names = []
    
    # Enhanced data structure to store detailed results by language/category
    detailed_results = {}
    
    # Process all single model evaluation files
    for file_path in single_eval_files:
        try:
            # Extract filename without extension
            filename = os.path.basename(file_path)
            
            # New file naming convention: {language}_{category}_{model_name}_single_evaluation.json
            file_parts = filename.split('_single_evaluation.json')[0]
            
            # Special case for handling complex category names with underscores (like api_usage)
            # First try to find the model name which often has distinctive patterns
            model_patterns = [
                "claude-3", 
                "gpt-", 
                "Ministral-3B", 
                "DeepSeek", 
                "o1-",
                "o3-",
                "4omini"
            ]
            
            found_pattern = False
            for pattern in model_patterns:
                if pattern in file_parts:
                    # Found a known model pattern
                    found_pattern = True
                    
                    # Find the position of the model pattern
                    pattern_pos = file_parts.find(pattern)
                    
                    # Extract parts before the pattern (language_category_)
                    prefix_parts = file_parts[:pattern_pos].strip('_').split('_')
                    
                    # Make sure we have at least language and category
                    if len(prefix_parts) >= 2:
                        language_from_file = prefix_parts[0]
                        # Category might have underscores, so join all remaining parts except the last
                        category_from_file = '_'.join(prefix_parts[1:])
                        
                        # Extract model name (the pattern and everything after it)
                        model_name = file_parts[pattern_pos:]
                        
                        # Remove any "usage_" prefix from model name if present
                        if model_name.startswith("usage_"):
                            model_name = model_name[6:]  # Remove "usage_" prefix
                            
                        break
            
            if not found_pattern:
                # Fallback to simple splitting - this may not handle complex categories well
                parts = file_parts.split('_')
                if len(parts) < 3:
                    print(f"Warning: unexpected filename format for {filename}, skipping.")
                    continue
                    
                language_from_file = parts[0]
                category_from_file = parts[1]
                model_name = '_'.join(parts[2:])
            
            print(f"Processing {filename}: Model={model_name}, Language={language_from_file}, Category={category_from_file}")
            
            # Read the result file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Calculate average score for this category
            scores = []
            all_results = []
            language_category_results = defaultdict(list)
            
            for entry in data:
                if entry.get('score') is not None:
                    score = entry.get('score')
                    scores.append(score)
                    
                    # Extract language and category from the entry
                    # Default to the ones from filename if not present
                    language = entry.get('language', language_from_file)
                    category = entry.get('category', category_from_file)
                    entry_id = entry.get('id', 'unknown')
                    
                    # Store detailed result
                    result_entry = {
                        "id": entry_id,
                        "score": score,
                        "category": category,
                        "language": language
                    }
                    all_results.append(result_entry)
                    
                    # Group by language and category
                    language_category_results[language].append(score)
            
            if not scores:
                print(f"No valid scores found in {file_path}")
                continue
                
            avg_score = sum(scores) / len(scores)
            
            # Calculate confidence intervals regardless of sample size
            # If sample is small, we'll note it in the output
            lower_ci, upper_ci = bootstrap_ci(scores)
            if len(scores) < 5:
                print(f"Warning: Only {len(scores)} samples for {category_from_file} in {model_name}. CI may not be statistically meaningful.")
            
            # Add the model to our list if it's new
            if model_name not in model_data:
                model_data[model_name] = {
                    'overall': {'scores': [], 'categories_count': 0, 'all_scores': []},
                    'categories': {},
                    'languages': defaultdict(list)
                }
                model_names.append(model_name)
                detailed_results[model_name] = []
            
            # Add category scores with confidence intervals
            model_data[model_name]['categories'][category_from_file] = {
                'score': round(avg_score, 2),
                'evaluations': len(scores),
                'lower_ci': round(lower_ci, 2),
                'upper_ci': round(upper_ci, 2),
                'ci_warning': len(scores) < 5
            }
            
            # Group scores by language
            for language, lang_scores in language_category_results.items():
                model_data[model_name]['languages'][language].extend(lang_scores)
            
            # Also append to overall averages
            model_data[model_name]['overall']['scores'].append(avg_score)
            model_data[model_name]['overall']['categories_count'] += 1
            model_data[model_name]['overall']['all_scores'].extend(scores)
            
            # Add detailed results
            detailed_results[model_name].extend(all_results)
                
        except Exception as e:
            print(f"Error processing single evaluation file {file_path}: {str(e)}")
    
    # Calculate overall averages for each model and format the final output
    final_summary = {}
    for model_name in model_names:
        model_info = model_data[model_name]
        
        # Calculate overall confidence intervals
        all_scores = model_info['overall']['all_scores']
        overall_lower_ci, overall_upper_ci = bootstrap_ci(all_scores)
        ci_warning = len(all_scores) < 5
        
        # Create the model entry
        final_summary[model_name] = {
            'overall': {
                'score': round(
                    sum(model_info['overall']['scores']) / 
                    len(model_info['overall']['scores']), 2),
                'categories_count': model_info['overall']['categories_count'],
                'sample_count': len(all_scores),
                'lower_ci': round(overall_lower_ci, 2),
                'upper_ci': round(overall_upper_ci, 2),
                'ci_warning': ci_warning
            }
        }
        
        # Add all categories
        for category, data in model_info['categories'].items():
            final_summary[model_name][category] = data
        
        # Add language statistics
        final_summary[model_name]['languages'] = {}
        for language, scores in model_info['languages'].items():
            lang_lower_ci, lang_upper_ci = bootstrap_ci(scores)
            lang_ci_warning = len(scores) < 5
                
            final_summary[model_name]['languages'][language] = {
                'score': round(sum(scores) / len(scores), 2),
                'sample_count': len(scores),
                'lower_ci': round(lang_lower_ci, 2),
                'upper_ci': round(lang_upper_ci, 2),
                'ci_warning': lang_ci_warning
            }
    
    # Determine the output file path for main summary
    if output_file is None:
        output_file = os.path.join(results_dir, "single_model_summary.json")
    
    # Save the summary
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_summary, f, indent=2)
    
    # Generate more granular output files
    for model_name in model_names:
        model_output_dir = os.path.join(results_dir, f"{model_name}_detailed_results")
        os.makedirs(model_output_dir, exist_ok=True)
        
        # Save detailed stats
        stats_path = os.path.join(model_output_dir, "stats.jsonl")
        with open(stats_path, 'w', encoding='utf-8') as stats_f:
            stats_f.write(json.dumps(final_summary[model_name]) + "\n")
        
        # Save aggregated score
        score_path = os.path.join(model_output_dir, "score.jsonl")
        with open(score_path, 'w', encoding='utf-8') as score_f:
            aggregate_score = {
                "average_score": final_summary[model_name]['overall']['score'],
                "number of samples considered": final_summary[model_name]['overall']['sample_count'],
                "lower_ci": final_summary[model_name]['overall']['lower_ci'],
                "upper_ci": final_summary[model_name]['overall']['upper_ci'],
                "ci_warning": final_summary[model_name]['overall']['ci_warning']
            }
            score_f.write(json.dumps(aggregate_score) + "\n")
        
        # Save detailed results
        outputs_path = os.path.join(model_output_dir, "outputs.jsonl")
        with open(outputs_path, 'w', encoding='utf-8') as output_f:
            for result in detailed_results[model_name]:
                output_f.write(json.dumps(result) + "\n")
        
        print(f"Detailed results for {model_name} saved to {model_output_dir}")
    
    print(f"\nSingle model evaluation summary saved to {output_file}")
    
    return final_summary

def main():
    parser = argparse.ArgumentParser(description='Evaluate code completion models using o3 mini')
    parser.add_argument('--completions_dir', type=str, default='../completions', help='Directory containing completion files')
    parser.add_argument('--output_dir', type=str, default='llm_judge_results_o3mini', help='Directory to save evaluation results')
    parser.add_argument('--specific_model', type=str, help='Optional: Name of specific model to evaluate (otherwise all models will be evaluated)')
    parser.add_argument('--model', type=str, help='Simple model name to evaluate (will find all matching files)')
    parser.add_argument('--limit', type=int, help='Optional: Limit the number of files to process per model')
    parser.add_argument('--max_evaluations', type=int, help='Optional: Limit the total number of evaluations to run')
    parser.add_argument('--summary_only', type=str, help='Only generate summary for the specified model without running evaluations')
    parser.add_argument('--specific_models', nargs='+', help='Evaluate only the specified list of models')
    
    args = parser.parse_args()
    
    # Check if we're only generating a summary for a specific model
    if args.summary_only:
        print(f"Generating summary only for model: {args.summary_only}")
        display_score_summary(args.output_dir, args.summary_only)
        return
        
    completions_dir = args.completions_dir
    output_dir = args.output_dir
    max_evaluations = args.max_evaluations
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine which models to evaluate
    if args.specific_models:
        models_to_evaluate = args.specific_models
        print(f"Evaluating specified models: {', '.join(models_to_evaluate)}")
    elif args.model:
        # Simple model-focused discovery
        print(f"Looking for files containing model: {args.model}")
        model_files = glob.glob(f"{completions_dir}/**/*-{args.model}*.jsonl", recursive=True)
        if not model_files:
            print(f"No files found for model pattern: {args.model}")
            return
            
        # Extract the actual model name from the first file
        models_to_evaluate = []
        for file_path in model_files:
            if "_formatted" in file_path:
                continue
                
            model_name = os.path.basename(file_path).split("-", 1)[1].replace(".jsonl", "")
            if model_name not in models_to_evaluate:
                models_to_evaluate.append(model_name)
        
        print(f"Found {len(models_to_evaluate)} models: {', '.join(models_to_evaluate)}")
    elif args.specific_model:
        models_to_evaluate = [args.specific_model]
        print(f"Evaluating specific model: {args.specific_model}")
    else:
        # Find all models in the completions directory
        models_to_evaluate = find_all_models(completions_dir, include_baseline=True)
        print(f"Found {len(models_to_evaluate)} models to evaluate: {', '.join(models_to_evaluate)}")
    
    # Track total evaluations
    total_evaluations = 0
    
    # Process all model files
    for model_name in models_to_evaluate:
        print(f"\n{'='*80}")
        print(f"Evaluating model: {model_name}")
        print(f"{'='*80}")
        
        model_files = glob.glob(f"{completions_dir}/**/*-{model_name}.jsonl", recursive=True)
        
        # Apply limit if specified
        if args.limit and args.limit > 0:
            model_files = model_files[:args.limit]
            print(f"Limiting to {args.limit} model files as requested")
        
        for model_file in model_files:
            # Check if we've hit the max evaluations limit
            if max_evaluations is not None and total_evaluations >= max_evaluations:
                print(f"Reached max evaluations limit ({max_evaluations}). Stopping.")
                break
            
            # Extract language and category from path
            # Structure: ../completions/{language}/{category}/{filename}
            file_path = os.path.normpath(model_file)
            path_parts = file_path.split(os.sep)
            
            # Default values
            language = "unknown"
            category = "unknown"
            
            # Find the "completions" folder in the path to get more reliable indexes
            for i, part in enumerate(path_parts):
                if part == "completions":
                    # If we found the completions folder, the structure should be:
                    # .../completions/language/category/filename.jsonl
                    if i + 2 < len(path_parts):  # Ensure we have enough parts for language
                        language = path_parts[i + 1]
                    if i + 3 < len(path_parts):  # Ensure we have enough parts for category
                        # Category might contain underscores itself (like api_usage)
                        category = path_parts[i + 2]
                    break
            
            print(f"Extracted from path: language={language}, category={category}")
                        
            # Generate output file path - include both language and category
            # Ensure no prefix is added to the model name
            output_file = os.path.join(output_dir, f"{language}_{category}_{model_name}_single_evaluation.json")
            
            print(f"Evaluating {model_name} for {language}/{category}")
            evaluations_done = evaluate_single_completion(
                model_file,
                output_file,
                model_name,
                max_evaluations=max_evaluations,
                current_evaluations=total_evaluations
            )
            
            total_evaluations += evaluations_done
            
            # Check if we've hit the max evaluations limit
            if max_evaluations is not None and total_evaluations >= max_evaluations:
                print(f"Reached max evaluations limit ({max_evaluations}). Stopping.")
                break
        
        # Break out of the outer loop if max evaluations reached
        if max_evaluations is not None and total_evaluations >= max_evaluations:
            break

    # Display score summary at the end
    display_score_summary(output_dir, args.specific_model)

if __name__ == "__main__":
    main()
