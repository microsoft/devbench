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
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']

dotenv.load_dotenv()

# o3-mini endpoint and deployment details - matching generate_completions.py
O3MINI_ENDPOINT = os.getenv("O3MINI_ENDPOINT", "<put the endpoint here>")  # Endpoint without the deployment path
O3MINI_DEPLOYMENT = os.getenv("O3MINI_DEPLOYMENT", "<put the deployment here>")  # The deployment name to use in API calls
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

def find_all_models(completions_dir: str) -> List[str]:
    """
    Find all available models in the completions directory.
    
    Args:
        completions_dir: Directory containing completion files
        
    Returns:
        List of model names found in the directory
    """
    # Set to store unique model names
    models = set()
    
    # Find all JSONL files in the completions directory
    all_files = glob.glob(f"{completions_dir}/**/*.jsonl", recursive=True)
    
    # Extract model names from filenames
    for file_path in all_files:
        # Skip files that don't have a model suffix
        if "-" not in os.path.basename(file_path):
            continue
            
        # Extract the model name part (after the dash, before .jsonl)
        model_part = os.path.basename(file_path).split("-", 1)[1].replace(".jsonl", "")
        
        # Skip formatted files
        if "_formatted" in model_part:
            continue
        
        # Remove 'usage_' prefix if present
        if model_part.startswith("usage_"):
            model_part = model_part[6:]
            
        models.add(model_part)
    
    return list(models)

def display_score_summary(results_dir: str, generate_plot=False, generate_heatmap=False, language_filter=None):
    """
    Display a summary of single model evaluation scores
    
    Args:
        results_dir: Directory containing evaluation result files
        generate_plot: Whether to generate a comparison plot
        generate_heatmap: Whether to generate language-category heatmaps
        language_filter: Optional list of languages that were filtered for
    """
    print("\n\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    
    if language_filter:
        print(f"\nNote: Results filtered for languages: {', '.join(language_filter)}")
    
    # Call generate_single_model_summary to create the summary
    summary = generate_single_model_summary(results_dir)
    
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
            
        # Generate plot if requested - allow even with a single model
        if generate_plot and len(summary) > 0:
            # Determine output path with appropriate suffix
            plot_path = os.path.join(results_dir, "model_comparison_plot.png")
                
            create_model_comparison_plot(
                summary, 
                plot_path
            )
            print(f"Plot generated and saved to: {plot_path}")
            
        # Generate language-category heatmaps if requested
        if generate_heatmap:
            create_language_category_heatmap(
                summary,
                results_dir
            )
            
    else:
        print("No evaluation results found.")

def evaluate_single_completion(model_file, output_file, model_name, max_evaluations=None, current_evaluations=0, max_file_evaluations=None):
    """
    Evaluate a single model's completions using o3 mini.
    
    Args:
        model_file: Path to the model completions JSONL
        output_file: Path to save evaluation results
        model_name: Name of the model being evaluated
        max_evaluations: Maximum number of evaluations to run (for debugging)
        current_evaluations: Number of evaluations already processed
        max_file_evaluations: Maximum number of evaluations to run per file
    
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
    
    # Normalize c_sharp and api_usage combinations - don't create "sharp_api_usage"
    # Fix the category name if it's in c_sharp folder with api_usage category
    if actual_language == "c_sharp" and (actual_category == "api_usage" or actual_category == "sharp_api_usage"):
        # Keep them separate, don't combine into "sharp_api_usage"
        actual_category = "api_usage"
    if actual_language == "c_sharp" and (actual_category == "code2NL_NL2code" or actual_category == "sharp_code2NL_NL2code"):
        actual_category = "code2NL_NL2code"
    if actual_language == "c_sharp" and (actual_category == "code_purpose_understanding" or actual_category == "sharp_code_purpose_understanding"):
        actual_category = "code_purpose_understanding"
    if actual_language == "c_sharp" and (actual_category == "low_context" or actual_category == "sharp_low_context"):
        actual_category = "low_context"
    if actual_language == "c_sharp" and (actual_category == "pattern_matching" or actual_category == "sharp_pattern_matching"):
        actual_category = "pattern_matching"
    if actual_language == "c_sharp" and (actual_category == "syntax_completion" or actual_category == "sharp_syntax_completion"):
        actual_category = "syntax_completion"

    print(f"Path components: Language={actual_language}, Category={actual_category}")

    # Limit the number of evaluations for debugging
    if max_evaluations is not None:
        evaluations_left = max_evaluations - current_evaluations
        if evaluations_left <= 0:
            return 0  # Skip processing if we've already hit the limit
            
        if len(model_data) > evaluations_left:
            print(f"Limiting to {evaluations_left} evaluations (out of {len(model_data)}) due to max_evaluations setting")
            model_data = model_data[:evaluations_left]
    
    # Apply max_file_evaluations limit if specified
    if max_file_evaluations is not None and max_file_evaluations > 0:
        if len(model_data) > max_file_evaluations:
            print(f"Limiting to {max_file_evaluations} evaluations per file (out of {len(model_data)}) due to max_file_evaluations setting")
            model_data = model_data[:max_file_evaluations]

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
                completion = client.chat.completions.create(  
                    max_completion_tokens=16384,
                    model=O3MINI_DEPLOYMENT,  
                    messages=messages,
                    stream=False  
                )

                response_content = completion.choices[0].message.content
                print(f"Evaluation result:")
                print(response_content)
                
                # Extract score from response
                score = extract_score(response_content)
                
                # Normalize c_sharp api_usage to prevent "sharp_api_usage"
                if language == "c_sharp" and actual_category == "api_usage":
                    actual_category = "api_usage"
                elif language == "c_sharp" and actual_category == "sharp_api_usage":
                    actual_category = "api_usage"
                elif actual_language == "c_sharp" and (actual_category == "code2NL_NL2code" or actual_category == "sharp_code2NL_NL2code"):
                    actual_category = "code2NL_NL2code"
                elif actual_language == "c_sharp" and (actual_category == "code_purpose_understanding" or actual_category == "sharp_code_purpose_understanding"):
                    actual_category = "code_purpose_understanding"
                elif actual_language == "c_sharp" and (actual_category == "low_context" or actual_category == "sharp_low_context"):
                    actual_category = "low_context"
                elif actual_language == "c_sharp" and (actual_category == "pattern_matching" or actual_category == "sharp_pattern_matching"):
                    actual_category = "pattern_matching"
                elif actual_language == "c_sharp" and (actual_category == "syntax_completion" or actual_category == "sharp_syntax_completion"):
                    actual_category = "syntax_completion"
                
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
                
                # Normalize c_sharp api_usage to prevent "sharp_api_usage"
                if language == "c_sharp" and actual_category == "api_usage":
                    actual_category = "api_usage"
                elif language == "c_sharp" and actual_category == "sharp_api_usage":
                    actual_category = "api_usage"
                elif actual_language == "c_sharp" and (actual_category == "code2NL_NL2code" or actual_category == "sharp_code2NL_NL2code"):
                    actual_category = "code2NL_NL2code"
                elif actual_language == "c_sharp" and (actual_category == "code_purpose_understanding" or actual_category == "sharp_code_purpose_understanding"):
                    actual_category = "code_purpose_understanding"
                elif actual_language == "c_sharp" and (actual_category == "low_context" or actual_category == "sharp_low_context"):
                    actual_category = "low_context"
                elif actual_language == "c_sharp" and (actual_category == "pattern_matching" or actual_category == "sharp_pattern_matching"):
                    actual_category = "pattern_matching"
                elif actual_language == "c_sharp" and (actual_category == "syntax_completion" or actual_category == "sharp_syntax_completion"):
                    actual_category = "syntax_completion"
                
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
                if pattern.lower() in file_parts.lower():
                    # Found a known model pattern
                    found_pattern = True
                    
                    # Find the position of the model pattern (case insensitive)
                    pattern_pos = file_parts.lower().find(pattern.lower())
                    
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
                
                # Also handle usage_ prefix in the fallback case
                if model_name.startswith("usage_"):
                    model_name = model_name[6:]
            
            # Clean model name for consistency
            # If model name has a 'usage_' prefix, remove it
            if model_name.startswith("usage_"):
                model_name = model_name[6:]
                
            # Fix for c_sharp api_usage - prevent creation of "sharp_api_usage"
            if language_from_file == "c_sharp" and category_from_file == "sharp_api_usage":
                category_from_file = "api_usage"
            elif language_from_file == "c_sharp" and (category_from_file == "sharp_code2NL_NL2code"):
                category_from_file = "code2NL_NL2code"
            elif language_from_file == "c_sharp" and (category_from_file == "sharp_code_purpose_understanding"):
                category_from_file = "code_purpose_understanding"
            elif language_from_file == "c_sharp" and (category_from_file == "sharp_low_context"):
                category_from_file = "low_context"
            elif language_from_file == "c_sharp" and (category_from_file == "sharp_pattern_matching"):
                category_from_file = "pattern_matching"
            elif language_from_file == "c_sharp" and (category_from_file == "sharp_syntax_completion"):
                category_from_file = "syntax_completion"
                
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
                    
                    # Standardize language name
                    language = standardize_language_name(language)
                    
                    # Fix for c_sharp api_usage - ensure it's not stored as "sharp_api_usage"
                    if language == "c_sharp" and category == "sharp_api_usage":
                        category = "api_usage"
                    elif language == "c_sharp" and (category == "sharp_code2NL_NL2code"):
                        category = "code2NL_NL2code"
                    elif language == "c_sharp" and (category == "sharp_code_purpose_understanding"):
                        category = "code_purpose_understanding"
                    elif language == "c_sharp" and (category == "sharp_low_context"):
                        category = "low_context"
                    elif language == "c_sharp" and (category == "sharp_pattern_matching"):
                        category = "pattern_matching"
                    elif language == "c_sharp" and (category == "sharp_syntax_completion"):
                        category = "syntax_completion"
                        
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
            # Normalize any sharp_api_usage to api_usage
            if category == "sharp_api_usage":
                category = "api_usage"
            elif category == "sharp_code2NL_NL2code":
                category = "code2NL_NL2code"
            elif category == "sharp_code_purpose_understanding":
                category = "code_purpose_understanding"
            elif category == "sharp_low_context":
                category = "low_context"
            elif category == "sharp_pattern_matching":
                category = "pattern_matching"
            elif category == "sharp_syntax_completion":
                category = "syntax_completion"
                
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

def get_display_name(model_name):
    """
    Convert internal model names to user-friendly display names.
    
    Args:
        model_name: Internal model name (e.g., 'claude-3-7-sonnet')
        
    Returns:
        User-friendly display name (e.g., 'Claude 3.7 Sonnet')
    """
    # Dictionary mapping internal model names to display names
    model_display_names = {
        "claude-3-5-sonnet": "Claude 3.5 Sonnet",
        "claude-3-7-sonnet": "Claude 3.7 Sonnet",
        "gpt-4.1-mini": "GPT-4.1 mini",
        "gpt-4o": "GPT-4o",
        "gpt-4o-mini": "GPT-4o mini",
        "gpt-4o-copilot": "GPT-4o Copilot",
        "gpt-4.1-nano": "GPT-4.1 nano",
        "DeepSeek-R1": "DeepSeek-R1",
        "DeepSeek-V3-0324": "DeepSeek-V3",
        "o3-mini": "o3-mini",
        "Ministral-3B": "Ministral-3B",
    }
    
    # Return the display name if found, otherwise use the original name
    return model_display_names.get(model_name, model_name)

def create_model_comparison_plot(summary_data, output_path=None):
    """
    Create a bar chart comparing model scores with confidence intervals.
    
    Args:
        summary_data: Dictionary containing model summary data
        output_path: Optional path to save the plot image file
    """
    # Extract model names and scores with confidence intervals
    model_names = []  # Internal model names
    display_names = []  # User-friendly display names
    scores = []
    lower_cis = []
    upper_cis = []
    
    # Sort models by overall score (higher first)
    sorted_models = sorted(
        summary_data.items(), 
        key=lambda x: x[1]['overall']['score'], 
        reverse=True
    )
    
    for model_name, model_data in sorted_models:
        # Use overall score
        score_data = model_data['overall']
        score = score_data['score']
        lower_ci = score_data['lower_ci']
        upper_ci = score_data['upper_ci']
        title_suffix = ""
            
        model_names.append(model_name)
        display_names.append(get_display_name(model_name))
        scores.append(score)
        
        # Calculate error bars (distance from score to CI bounds)
        lower_cis.append(scores[-1] - lower_ci)  # Convert to distance from point
        upper_cis.append(upper_ci - scores[-1])  # Convert to distance from point
    
    # Convert to numpy arrays
    y_pos = np.arange(len(model_names))
    scores = np.array(scores)
    
    # Create error bars format for plt.errorbar
    # matplotlib's errorbar needs the errors in the format [lower_errors, upper_errors]
    yerr = np.array([lower_cis, upper_cis])
    
    # Create the figure and axis
    plt.figure(figsize=(10, 6))
    
    # Create light grid with white background
    plt.grid(axis='y', linestyle='-', alpha=0.2)
    
    # Plot with blue dots and error bars
    plt.errorbar(y_pos, scores, yerr=yerr, fmt='o', color='darkblue', capsize=5,
                 markersize=6, elinewidth=2, capthick=2)
    
    # Set x-axis ticks and labels with smaller font if many models
    if len(model_names) > 10:
        plt.xticks(y_pos, display_names, rotation=45, ha='right', fontsize=8)
    else:
        plt.xticks(y_pos, display_names, rotation=45, ha='right')
    
    # Set plot labels and title
    plt.xlabel('Model', fontsize=12, labelpad=10)
    plt.ylabel('Average Score', fontsize=12)
    
    # Add title if filtering by language or category
    if title_suffix:
        plt.title(f"Model Comparison{title_suffix}")
    
    # Set y-axis limits with a bit of padding
    y_min = min(scores - np.array(lower_cis)) - 0.2
    y_max = max(scores + np.array(upper_cis)) + 0.2
    
    # Ensure the y-axis starts at a reasonable value but not below 0
    y_min = max(0, y_min)
    
    # Adjust to have nice round limits
    plt.ylim(y_min, min(10.0, y_max))  # Cap at 10 which is the max score
    
    # Make sure the plot is tight
    plt.tight_layout()
    
    # Save the plot if output path is provided
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")
    
    # Return the figure object
    return plt.gcf()

def create_language_category_heatmap(summary_data, output_dir):
    """
    Create heatmaps that compare scores across languages and categories for each model.
    
    Args:
        summary_data: Dictionary containing model summary data
        output_dir: Directory to save the heatmap images
    """
    # Define standard language and category order for consistent visualization
    # Languages in columns (left to right)
    language_order = ['python', 'javascript', 'typescript', 'java', 'cpp', 'c_sharp']
    
    # Categories in rows (top to bottom)
    category_order = [
        'api_usage', 
        'code2NL_NL2code', 
        'code_purpose_understanding', 
        'low_context', 
        'pattern_matching', 
        'syntax_completion'
    ]
    
    # Display names for languages and categories
    language_display = {
        'python': 'Python',
        'javascript': 'Javascript',
        'typescript': 'Typescript',
        'java': 'Java',
        'cpp': 'Cpp',
        'c_sharp': 'C_sharp'
    }
    
    category_display = {
        'api_usage': 'API Usage',
        'code2NL_NL2code': 'Code2NL/NL2Code',
        'code_purpose_understanding': 'Code Purpose',
        'low_context': 'Low Context',
        'pattern_matching': 'Pattern Matching',
        'syntax_completion': 'Syntax Completion'
    }
    
    # Create a custom colormap that better matches the reference image
    # More orange/yellow for lower values, less intense red for higher values
    custom_cmap = LinearSegmentedColormap.from_list('custom_orange', [
        '#FFF0A0',  # Light yellow
        '#FFDA75',  # Yellow
        '#FFB347',  # Medium orange
        '#FF8E47',  # Darker orange
        '#FF5D3D',  # Orange-red
        '#E5451F',  # Dark orange-red
    ])
    
    # No filtering by models - use all models from summary_data
    filtered_data = summary_data
    
    # Skip individual model heatmaps and only create the combined heatmap
    
    # If we have multiple models, create a combined figure with all heatmaps stacked
    if len(filtered_data) > 0:  # Changed from > 1 to > 0 to always generate the combined heatmap
        # Sort models by overall score
        sorted_models = sorted(
            filtered_data.items(),
            key=lambda x: x[1]['overall']['score'] if 'overall' in x[1] else 0,
            reverse=True
        )
        
        # Number of models to show
        n_models = len(sorted_models)
        
        # Create a larger figure to accommodate all models
        fig, axes = plt.subplots(
            n_models, 1, 
            figsize=(12, 6*n_models), 
            gridspec_kw={'hspace': 0.3}
        )
        
        # If we only have one model, axes won't be an array
        if n_models == 1:
            axes = [axes]
        
        # Create heatmap for each model
        for i, (model_name, model_data) in enumerate(sorted_models):
            # Create a clean model display name
            model_display_name = get_display_name(model_name)
            
            # Get the axis for this model
            ax = axes[i]
            
            # Initialize data matrix for the heatmap
            data_matrix = np.zeros((len(category_order), len(language_order)))
            data_matrix.fill(np.nan)  # Fill with NaN for cells without data
            
            # Collect all scores for this model by language and category
            language_category_scores = {}
            
            # IMPORTANT: Print debug information
            print(f"\nCollecting data for heatmap: {model_name}")
            
            # FIRST METHOD: Check model_data directly for category scores
            # Only use this for data that we know is correctly categorized
            if 'languages' in model_data:
                print("  Languages found in model data:")
                for language, lang_data in model_data['languages'].items():
                    print(f"    {language}: {lang_data['score']}")
            
            # SECOND METHOD: Look for detailed result files
            # This is the most reliable approach for language-specific category data
            result_files = glob.glob(f"{output_dir}/*_{model_name}_single_evaluation.json")
            print(f"  Found {len(result_files)} evaluation files")
            
            for file_path in result_files:
                filename = os.path.basename(file_path)
                
                # Parse the filename to extract language and category
                # Format should be: language_category_modelname_single_evaluation.json
                filename_base = filename.replace("_single_evaluation.json", "")
                filename_parts = filename_base.split('_')
                
                if len(filename_parts) < 3:
                    continue  # Invalid format
                    
                # First part is usually the language
                # Special case for c_sharp which gets split into ['c', 'sharp', ...]
                language = filename_parts[0].lower()
                if language == 'c' and len(filename_parts) > 1 and filename_parts[1].lower() == 'sharp':
                    language = 'c_sharp'
                    # Adjust the remaining parts - remove the 'sharp' part since it's now part of the language
                    filename_parts = [language] + filename_parts[2:]
                
                language = standardize_language_name(language)
                if language not in [lang.lower() for lang in language_order]:
                    continue
                
                # Extract model part to identify where the category ends
                model_part_index = -1
                for j, part in enumerate(filename_parts):
                    if model_name in part:
                        model_part_index = j
                        break
                
                if model_part_index <= 1:  # Need at least language and category
                    continue
                    
                # Category is everything between language and model
                category = '_'.join(filename_parts[1:model_part_index])
                
                print(f"Extracted from filename '{filename}': language='{language}', category='{category}'")
                
                # Special case - fix "sharp_api_usage" to be recognized as "api_usage" for "c_sharp"
                if language == "c_sharp" and category == "sharp_api_usage":
                    category = "api_usage"
                elif language == "c_sharp" and category == "sharp_code2NL_NL2code":
                    category = "code2NL_NL2code"
                elif language == "c_sharp" and category == "sharp_code_purpose_understanding":
                    category = "code_purpose_understanding"
                elif language == "c_sharp" and category == "sharp_low_context":
                    category = "low_context"
                elif language == "c_sharp" and category == "sharp_pattern_matching":
                    category = "pattern_matching"
                elif language == "c_sharp" and category == "sharp_syntax_completion":
                    category = "syntax_completion"
                    
                
                if category not in category_order:
                    continue
                
                # Read the file and calculate average score
                try:
                    with open(file_path, 'r') as f:
                        eval_data = json.load(f)
                        
                    scores = [e.get('score') for e in eval_data if e.get('score') is not None]
                    if scores:
                        avg_score = sum(scores) / len(scores)
                        language_category_scores[(language, category)] = avg_score
                        print(f"    Found score for {language}/{category}: {avg_score}")
                except Exception as e:
                    print(f"    Error reading {file_path}: {str(e)}")
            
            # Fill the data matrix with scores
            for j, category in enumerate(category_order):
                for k, language in enumerate(language_order):
                    # Make language comparison case-insensitive
                    key_matches = [(lang, cat) for lang, cat in language_category_scores.keys() 
                                  if lang.lower() == language.lower() and cat == category]
                    
                    # If a matching key is found, use it
                    if key_matches:
                        key = key_matches[0]
                        data_matrix[j, k] = language_category_scores[key]
            
            # Create the heatmap with our custom colormap
            sns.heatmap(
                data_matrix,
                annot=True,
                fmt=".2f",
                cmap=custom_cmap,
                vmin=7.0,  # Minimum value for color scale
                vmax=10.0,  # Maximum value for color scale
                linewidths=2,
                linecolor='white',
                cbar=False,
                ax=ax
            )
            
            # Set row and column labels
            ax.set_yticks(np.arange(len(category_order)) + 0.5)
            ax.set_yticklabels([category_display[cat] for cat in category_order], rotation=0, fontsize=12)
            
            ax.set_xticks(np.arange(len(language_order)) + 0.5)
            ax.set_xticklabels([language_display[lang] for lang in language_order], rotation=0, fontsize=12)
            
            # Add model name as title
            ax.set_title(model_display_name, fontsize=14, pad=20)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(output_dir, "combined_language_category_heatmap.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Created combined language-category heatmap: {output_path}")

def standardize_language_name(language):
    """
    Standardize language names to ensure consistent casing.
    
    Args:
        language: Language name to standardize
        
    Returns:
        Standardized language name
    """
    # Define standard casing for languages
    standard_languages = {
        'python': 'python',
        'javascript': 'javascript', 
        'typescript': 'typescript',
        'java': 'java',
        'cpp': 'cpp',
        'c_sharp': 'c_sharp',
        'c#': 'c_sharp',
        'csharp': 'c_sharp'
    }
    
    # Try to standardize based on lowercase name
    lower_lang = language.lower()
    if lower_lang in standard_languages:
        return standard_languages[lower_lang]
    
    # If not found, return as is
    return language

def main():
    parser = argparse.ArgumentParser(description='Evaluate code completion models using o3 mini')
    parser.add_argument('--completions_dir', type=str, default='../completions', help='Directory containing completion files')
    parser.add_argument('--output_dir', type=str, default='llm_judge_results', help='Directory to save evaluation results')
    parser.add_argument('--limit', type=int, help='Optional: Limit the number of files to process per model')
    parser.add_argument('--max_evaluations', type=int, help='Optional: Limit the total number of evaluations to run')
    parser.add_argument('--max_file_evaluations', type=int, help='Optional: Limit the number of evaluations per file')
    parser.add_argument('--summary_only', action='store_true', help='Only generate summary for all models without running evaluations')
    parser.add_argument('--specific_models', nargs='+', help='Evaluate only the specified list of models')
    parser.add_argument('--language', nargs='+', help='Evaluate only files for the specified language(s)')
    parser.add_argument('--plot', action='store_true', help='Generate a comparison plot of model scores with confidence intervals')
    parser.add_argument('--heatmap', action='store_true', help='Generate language-category heatmaps for models')
    
    args = parser.parse_args()
    
    # Check if we're only generating a summary for a specific model
    if args.summary_only:
        print(f"Generating summary only for all models")
        display_score_summary(
            args.output_dir, 
            generate_plot=args.plot,
            generate_heatmap=args.heatmap,
            language_filter=args.language
        )
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
    else:
        # Find all models in the completions directory
        models_to_evaluate = find_all_models(completions_dir)
        print(f"Found {len(models_to_evaluate)} models to evaluate: {', '.join(models_to_evaluate)}")
    
    # Track total evaluations
    total_evaluations = 0
    
    # Process all model files
    for model_name in models_to_evaluate:
        print(f"\n{'='*80}")
        print(f"Evaluating model: {model_name}")
        print(f"{'='*80}")
        
        # Search pattern should handle both regular model names and those with 'usage_' prefix
        model_pattern = f"*-{model_name}.jsonl"
        usage_model_pattern = f"*-usage_{model_name}.jsonl"
        
        model_files = glob.glob(f"{completions_dir}/**/{model_pattern}", recursive=True)
        usage_model_files = glob.glob(f"{completions_dir}/**/{usage_model_pattern}", recursive=True)
        
        # Combine both sets of files
        all_model_files = model_files + usage_model_files
        
        if not all_model_files:
            print(f"No files found for model: {model_name}")
            continue
        
        # Filter by language if specified - do this BEFORE limiting
        if args.language:
            languages_to_include = [lang.lower() for lang in args.language]
            filtered_files = []
            
            print(f"Filtering for languages: {languages_to_include}")
            print(f"Processing {len(all_model_files)} files")
            
            for model_file in all_model_files:
                # Extract language from the path
                file_path = os.path.normpath(model_file)
                path_parts = file_path.split(os.sep)
                file_language = None
                
                # Print path parts for debugging
                print(f"\nExamining file: {file_path}")
                print(f"Path parts: {path_parts}")
                
                # Find the "completions" folder in the path
                for i, part in enumerate(path_parts):
                    if part == "completions":
                        # Language should be the next part after "completions"
                        if i + 1 < len(path_parts):
                            # Check for special case of c_sharp
                            file_language = path_parts[i + 1].lower()
                            if file_language == "c_sharp" or file_language == "csharp" or file_language == "c#":
                                file_language = "c_sharp"
                                
                            file_language = standardize_language_name(file_language)
                            print(f"Found language in path: '{file_language}'")
                        break
                
                if file_language and file_language in languages_to_include:
                    print(f"Including file with language: {file_language}")
                    filtered_files.append(model_file)
                else:
                    if file_language:
                        print(f"Skipping file - language '{file_language}' not in filter list")
                    else:
                        print(f"Skipping file - could not determine language")
            
            print(f"Filtered to {len(filtered_files)} files for languages: {', '.join(args.language)}")
            all_model_files = filtered_files
            
            if not all_model_files:
                print(f"No files found for model {model_name} with specified language filter")
                continue
        
        # Apply limit if specified - do this AFTER language filtering
        if args.limit and args.limit > 0:
            original_count = len(all_model_files)
            all_model_files = all_model_files[:args.limit]
            print(f"Limiting to {args.limit} model files as requested (from {original_count} matching files)")
        
        for model_file in all_model_files:
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
            
            # Normalize c_sharp and api_usage combinations - don't create "sharp_api_usage"
            # Fix the category name if it's in c_sharp folder with api_usage category
            if language == "c_sharp" and (category == "api_usage" or category == "sharp_api_usage"):
                # Keep them separate, don't combine into "sharp_api_usage"
                category = "api_usage"
            elif language == "c_sharp" and (category == "code2NL_NL2code" or category == "sharp_code2NL_NL2code"):
                category = "code2NL_NL2code"
            elif language == "c_sharp" and (category == "code_purpose_understanding" or category == "sharp_code_purpose_understanding"):
                category = "code_purpose_understanding"
            elif language == "c_sharp" and (category == "low_context" or category == "sharp_low_context"):
                category = "low_context"
            elif language == "c_sharp" and (category == "pattern_matching" or category == "sharp_pattern_matching"):
                category = "pattern_matching"
            elif language == "c_sharp" and (category == "syntax_completion" or category == "sharp_syntax_completion"):
                category = "syntax_completion"
                
            
            print(f"Extracted from path: language={language}, category={category}")
            
            # Extract the real model name from the file in case it uses usage_ prefix
            file_model_name = os.path.basename(model_file).split("-", 1)[1].replace(".jsonl", "")
            if file_model_name.startswith("usage_"):
                file_model_name = file_model_name[6:]  # Remove 'usage_' prefix
                        
            # Generate output file path - include both language and category
            # Ensure no prefix is added to the model name
            output_file = os.path.join(output_dir, f"{language}_{category}_{file_model_name}_single_evaluation.json")
            
            print(f"Evaluating {file_model_name} for {language}/{category}")
            evaluations_done = evaluate_single_completion(
                model_file,
                output_file,
                file_model_name,  # Use the model name from file which might include usage_ prefix
                max_evaluations=max_evaluations,
                current_evaluations=total_evaluations,
                max_file_evaluations=args.max_file_evaluations
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
    display_score_summary(
        output_dir, 
        generate_plot=args.plot,
        generate_heatmap=args.heatmap,
        language_filter=args.language
    )

if __name__ == "__main__":
    main()
