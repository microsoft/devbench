import os  
import base64
import json
from openai import AzureOpenAI  
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import dotenv
from typing import Dict, List
import re
import ast
import glob
import argparse

dotenv.load_dotenv()

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
            
            # Display overall score first
            overall = model_data.get('overall', {})
            print(f"OVERALL: Score: {overall.get('score'):.2f}/10 (across {overall.get('categories_count')} categories)")
            
            # Display each category
            for category, scores in model_data.items():
                if category == 'overall':
                    continue
                print(f"{category}: Score: {scores['score']:.2f}/10, Evaluations: {scores['evaluations']}")
    else:
        print("No evaluation results found.")

def evaluate_single_completion(model_file, output_file, model_name, max_evaluations=None, current_evaluations=0, judge_model="4o"):
    """
    Evaluate a single model's completions.
    
    Args:
        model_file: Path to the model completions JSONL
        output_file: Path to save evaluation results
        model_name: Name of the model being evaluated
        max_evaluations: Maximum number of evaluations to run (for debugging)
        current_evaluations: Number of evaluations already processed
        judge_model: Model to use for judging ("4o" or "o3")
    
    Returns:
        Number of evaluations processed in this run
    """
    endpoint = os.getenv("ENDPOINT_URL", "https://deeppromptnorthcentralus.openai.azure.com/")  
    
    # Select deployment and API version based on judge_model parameter
    if judge_model == "o3":
        deployment = os.getenv("O3_DEPLOYMENT_NAME", "deepprompt-gpt-o3-2024-05-13")
        api_version = "2024-12-01-preview"
    else:  # Default to 4o
        deployment = os.getenv("DEPLOYMENT_NAME", "deepprompt-gpt-4o-2024-05-13")
        api_version = "2024-05-01-preview"
    
    print(f"Using {judge_model} model for evaluation: {deployment}")

    # Initialize Azure OpenAI Service client with Entra ID authentication
    token_provider = get_bearer_token_provider(  
        DefaultAzureCredential(),  
        "https://cognitiveservices.azure.com/.default"
    )  
    
    client = AzureOpenAI(  
        azure_endpoint=endpoint,  
        azure_ad_token_provider=token_provider,  
        api_version=api_version,  
    )

    model_data = read_jsonl_file(model_file)

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
 
            print(f"\n\nEvaluating single completion for ID: {entry_id}")
            
            formatted_prompt = single_model_prompt_template.format(
                prefix=prefix,
                completion=model_completion,
                suffix=suffix
            )
            
            messages = [{"role": "user", "content": formatted_prompt}]

            try:
                if judge_model == "o3":
                    completion = client.chat.completions.create(  
                        model=deployment,  
                        messages=messages,
                        stream=False  
                    )
                else:
                    completion = client.chat.completions.create(  
                        model=deployment,  
                        messages=messages,
                        max_tokens=400,  
                        temperature=0.7,  
                        top_p=0.95,  
                        frequency_penalty=0,  
                        presence_penalty=0,
                        stop=None,  
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
    
    # Process all single model evaluation files
    for file_path in single_eval_files:
        try:
            # Extract filename without extension
            filename = os.path.basename(file_path)
            file_base = filename.split('_single_evaluation.json')[0]
            
            # Read the result file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract model name - for our use case, model names have a specific pattern
            # like "4omini_sft39_spm_16_o3fix_10", "claude-3-5-sonnet", etc.
            # We need to identify the model name correctly from the filename
            model_patterns = [
                "4omini_sft39_spm", 
                "claude-3", 
                "gpt-", 
                "Ministral-3B", 
                "DeepSeek", 
                "o1-",
                "o3-"
            ]
            
            # Find the model name by looking for known patterns
            model_name = None
            for pattern in model_patterns:
                if pattern in file_base:
                    # Find the pattern and everything after it
                    start_index = file_base.find(pattern)
                    if start_index >= 0:
                        # Extract from the pattern to the end or next underscore
                        remaining = file_base[start_index:]
                        if "_" in remaining:
                            model_name = remaining.split("_", 1)[0]
                        else:
                            model_name = remaining
                        
                        # For 4omini models, include all parts
                        if pattern == "4omini_sft39_spm":
                            model_name = "4omini_sft39_spm_16_o3fix_10"
                        break
            
            # If we couldn't determine the model name, skip this file
            if not model_name:
                print(f"Warning: Could not determine model name for {filename}, skipping.")
                continue
            
            # Determine the category by removing the model name from the filename
            category = file_base.replace(model_name, "").strip("_")
            if not category:
                category = "general"
                
            print(f"Processing {filename}: Model={model_name}, Category={category}")
            
            # Calculate average score for this category
            scores = []
            for entry in data:
                if entry.get('score') is not None:
                    scores.append(entry['score'])
            
            if not scores:
                print(f"No valid scores found in {file_path}")
                continue
                
            avg_score = sum(scores) / len(scores)
            
            # Add the model to our list if it's new
            if model_name not in model_data:
                model_data[model_name] = {
                    'overall': {'scores': [], 'categories_count': 0},
                    'categories': {}
                }
                model_names.append(model_name)
            
            # Add category scores
            model_data[model_name]['categories'][category] = {
                'score': round(avg_score, 2),
                'evaluations': len(scores)
            }
            
            # Also append to overall averages
            model_data[model_name]['overall']['scores'].append(avg_score)
            model_data[model_name]['overall']['categories_count'] += 1
                
        except Exception as e:
            print(f"Error processing single evaluation file {file_path}: {str(e)}")
    
    # Calculate overall averages for each model and format the final output
    final_summary = {}
    for model_name in model_names:
        model_info = model_data[model_name]
        
        # Create the model entry
        final_summary[model_name] = {
            'overall': {
                'score': round(
                    sum(model_info['overall']['scores']) / 
                    len(model_info['overall']['scores']), 2),
                'categories_count': model_info['overall']['categories_count']
            }
        }
        
        # Add all categories
        for category, data in model_info['categories'].items():
            final_summary[model_name][category] = data
    
    # Determine the output file path
    if output_file is None:
        output_file = os.path.join(results_dir, "single_model_summary.json")
    
    # Save the summary
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_summary, f, indent=2)
    
    print(f"\nSingle model evaluation summary saved to {output_file}")
    
    return final_summary

def main():
    parser = argparse.ArgumentParser(description='Evaluate code completion models')
    parser.add_argument('--completions_dir', type=str, default='../completions', help='Directory containing completion files')
    parser.add_argument('--output_dir', type=str, default='llm_judge_results_single_model', help='Directory to save evaluation results')
    parser.add_argument('--specific_model', type=str, help='Optional: Name of specific model to evaluate (otherwise all models will be evaluated)')
    parser.add_argument('--model', type=str, help='Simple model name to evaluate (will find all matching files)')
    parser.add_argument('--limit', type=int, help='Optional: Limit the number of files to process per model')
    parser.add_argument('--max_evaluations', type=int, help='Optional: Limit the total number of evaluations to run')
    parser.add_argument('--summary_only', type=str, help='Only generate summary for the specified model without running evaluations')
    parser.add_argument('--judge_model', type=str, choices=['4o', 'o3'], default='4o', help='Model to use for judging (4o or o3)')
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
            
            # Generate output file path
            category = os.path.basename(os.path.dirname(model_file))
            output_file = os.path.join(output_dir, f"{category}_{model_name}_single_evaluation.json")
            
            print(f"Evaluating {model_name} for {category}")
            evaluations_done = evaluate_single_completion(
                model_file,
                output_file,
                model_name,
                max_evaluations=max_evaluations,
                current_evaluations=total_evaluations,
                judge_model=args.judge_model
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
