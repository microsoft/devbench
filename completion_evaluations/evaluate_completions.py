import os
import json
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from Levenshtein import distance as levenshtein_distance
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import Levenshtein
import argparse

def strip_trivial_characters(text):
    """Strip trivial characters like whitespace, quotes, etc."""
    if not text:
        return ""
    return text.strip().rstrip(";").rstrip(",")

def index_of_first_non_space_char(text):
    """
    Returns the index of the first non-space or non-newline or non-tab character in a string.
    """
    if not text:
        return 0
    for i, char in enumerate(text):
        if char not in [' ', '\n', '\t']:
            return i
    return len(text)

def remove_special_chars_fn(completion):
    """Remove special characters from text."""
    if not completion:
        return ""
    special_chars = ['<|endoftext|>']
    for spec in special_chars:
        completion = completion.replace(spec, '')
    return completion

def get_fully_cleansed_first_line(text):
    """Clean the first line of text for comparison."""
    if not text:
        return ""
    try:
        fl_text = text
        fl_text = fl_text[index_of_first_non_space_char(fl_text):].split('\n')[0].strip()
        fl_text = remove_special_chars_fn(strip_trivial_characters(fl_text))
        return fl_text
    except Exception as e:
        print(f"Error in get_fully_cleansed_first_line: {e}")
        return ""

def calculate_cosine_similarity(text1, text2):
    """Calculate cosine similarity between two texts with robust error handling."""
    # Return 1.0 if both texts are identical
    if text1 == text2:
        return 1.0
    
    # Return 0.0 if either text is empty
    if not text1 or not text2:
        return 0.0
    
    try:
        # Try with default settings first
        vectorizer = CountVectorizer(analyzer='word', token_pattern=r'\b\w+\b')
        try:
            vectors = vectorizer.fit_transform([text1, text2])
            if vectors.shape[1] > 0:  # Check if vocabulary is not empty
                return cosine_similarity(vectors)[0, 1]
        except ValueError:
            # If default fails, try with more permissive tokenization
            pass
        
        # More permissive approach - include single characters and special chars
        vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 3))
        vectors = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(vectors)[0, 1]
    
    except Exception as e:
        print(f"Error calculating cosine similarity: {e}")
        # Fallback to a simple character-based comparison
        common_chars = set(text1) & set(text2)
        all_chars = set(text1) | set(text2)
        return len(common_chars) / len(all_chars) if all_chars else 0.0

def load_benchmark_files(benchmark_dir):
    """Load benchmark files containing golden completions."""
    benchmark_data = {}
    
    for root, dirs, files in os.walk(benchmark_dir):
        for file in files:
            if file.endswith('.jsonl'):
                # Normalize path separators
                normalized_root = root.replace('\\', '/')
                parts = normalized_root.split('/')
                
                # Extract language and category
                language = None
                category = None
                
                # Find language directly from the path
                benchmark_index = parts.index('benchmark') if 'benchmark' in parts else -1
                if benchmark_index >= 0 and benchmark_index + 1 < len(parts):
                    language = parts[benchmark_index + 1]
                    if benchmark_index + 2 < len(parts):
                        category = parts[benchmark_index + 2]
                
                if not language or not category:
                    print(f"Could not determine language/category for {root}")
                    continue
                
                file_path = os.path.join(root, file)
                
                # Create key based on language and category
                key = f"{language}/{category}"
                benchmark_data[key] = {}
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            # Use id as the key for each test case
                            test_id = data.get('id')
                            if test_id:
                                benchmark_data[key][test_id] = data
                        except json.JSONDecodeError:
                            print(f"Error parsing JSON in benchmark file: {file_path}")
                            continue
    
    return benchmark_data

def load_and_compare_completions(completions_dir, benchmark_dir, debug=False):
    """Load and compare model completions with golden completions."""
    # Load all benchmark files first
    benchmark_data = load_benchmark_files(benchmark_dir)
    
    # Initialize results structure
    # Model -> metrics
    results = defaultdict(lambda: {
        'total': 0, 
        'line0_exact_matches': 0,
        'cosine_similarities': [],
        'avg_cosine': 0,
        'categories': defaultdict(lambda: {
            'total': 0,
            'line0_exact_matches': 0,
            'cosine_similarities': [],
            'avg_cosine': 0,
        }),
        'languages': defaultdict(lambda: {
            'total': 0,
            'line0_exact_matches': 0,
            'cosine_similarities': [],
            'avg_cosine': 0,
        })
    })
    
    # For debug mode, we'll collect test cases and their metadata
    if debug:
        test_cases = defaultdict(list)
    
    # Walk through the completions directory structure
    for root, dirs, files in os.walk(completions_dir):
        for file in files:
            # Only process jsonl files, skip formatted files
            if file.endswith('.jsonl') and not file.endswith('_formatted.jsonl'):
                
                file_path = os.path.join(root, file)
                
                # Normalize path separators (handle both Windows and Unix paths)
                normalized_path = file_path.replace('\\', '/') 
                path_parts = normalized_path.split('/')
                
                # Initialize language and category to None
                language = None
                category = None
                
                # Find language from the path
                completions_index = path_parts.index('completions') if 'completions' in path_parts else -1
                if completions_index >= 0 and completions_index + 1 < len(path_parts):
                    language = path_parts[completions_index + 1]
                    if completions_index + 2 < len(path_parts):
                        category = path_parts[completions_index + 2]
                
                if not language or not category:
                    print(f"Could not determine language/category for {file_path}")
                    continue
                
                # Create benchmark key to locate corresponding benchmark data
                benchmark_key = f"{language}/{category}"
                
                if benchmark_key not in benchmark_data:
                    print(f"No benchmark data found for {benchmark_key}")
                    continue
                
                print(f"Processing {file_path}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            test_id = data.get('id')
                            
                            if not test_id or test_id not in benchmark_data[benchmark_key]:
                                print(f"Test ID {test_id} not found in benchmark data for {benchmark_key}")
                                continue
                            
                            # Get golden completion from benchmark data
                            golden_completion = benchmark_data[benchmark_key][test_id].get('golden_completion', '')
                            
                            # Process each model completion in the data
                            for model_name, model_completion in data.items():
                                # Skip the id field and any empty completions
                                if model_name == 'id' or not model_completion:
                                    continue
                                
                                # Update total count
                                results[model_name]['total'] += 1
                                results[model_name]['categories'][category]['total'] += 1
                                results[model_name]['languages'][language]['total'] += 1
                                
                                # Line0 exact match comparison
                                model_line0 = model_completion.strip().split('\n')[0].strip()
                                golden_line0 = golden_completion.strip().split('\n')[0].strip()
                                
                                if model_line0 == golden_line0:
                                    results[model_name]['line0_exact_matches'] += 1
                                    results[model_name]['categories'][category]['line0_exact_matches'] += 1
                                    results[model_name]['languages'][language]['line0_exact_matches'] += 1
                                
                                # Cosine similarity for first line
                                cosine_sim = calculate_cosine_similarity(model_line0, golden_line0)
                                results[model_name]['cosine_similarities'].append(cosine_sim)
                                results[model_name]['categories'][category]['cosine_similarities'].append(cosine_sim)
                                results[model_name]['languages'][language]['cosine_similarities'].append(cosine_sim)
                                
                                # Store detailed test case info for debug mode
                                if debug:
                                    prompt = benchmark_data[benchmark_key][test_id].get('prompt', '')
                                    test_cases[model_name].append({
                                        'test_id': test_id,
                                        'language': language,
                                        'category': category,
                                        'prompt': prompt,
                                        'golden_completion': golden_completion,
                                        'model_completion': model_completion,
                                        'cosine_similarity': cosine_sim
                                    })
                            
                        except json.JSONDecodeError:
                            print(f"Error parsing JSON in file: {file_path}")
                            continue
    
    # Calculate average metrics for each model
    for model_name in results:
        # Overall averages
        cosine_sims = results[model_name]['cosine_similarities']
        results[model_name]['avg_cosine'] = sum(cosine_sims) / len(cosine_sims) if cosine_sims else 0
        
        # Category averages
        for category in results[model_name]['categories']:
            cat_cosine_sims = results[model_name]['categories'][category]['cosine_similarities']
            results[model_name]['categories'][category]['avg_cosine'] = sum(cat_cosine_sims) / len(cat_cosine_sims) if cat_cosine_sims else 0
        
        # Language averages
        for language in results[model_name]['languages']:
            lang_cosine_sims = results[model_name]['languages'][language]['cosine_similarities']
            results[model_name]['languages'][language]['avg_cosine'] = sum(lang_cosine_sims) / len(lang_cosine_sims) if lang_cosine_sims else 0
    
    if debug:
        return results, test_cases
    return results

def format_results(results):
    """Format results into a JSON-friendly dictionary with computed statistics."""
    formatted_results = {}
    
    # List of non-model sources to exclude from the output
    excluded_models = [
        'testsource', 'language', 'prefix', 'suffix', 
        'golden_completion', 'LLM_justification', 'assertions'
    ]
    
    for model_name, model_data in results.items():
        # Skip non-model sources
        if model_name in excluded_models:
            continue
            
        formatted_results[model_name] = {
            "overall": {
                "total_comparisons": model_data['total'],
                "line0_exact_matches": model_data['line0_exact_matches'],
                "line0_exact_match_rate": round((model_data['line0_exact_matches'] / model_data['total'] * 100) if model_data['total'] > 0 else 0, 2),
                "avg_cosine": round(model_data['avg_cosine'], 2)
            },
            "categories": {},
            "languages": {}
        }
        
        # Format category data with the new metric
        for category, category_data in model_data['categories'].items():
            if category_data['total'] > 0:
                formatted_results[model_name]["categories"][category] = {
                    "total_comparisons": category_data['total'],
                    "line0_exact_matches": category_data['line0_exact_matches'],
                    "line0_exact_match_rate": round((category_data['line0_exact_matches'] / category_data['total'] * 100) if category_data['total'] > 0 else 0, 2),
                    "avg_cosine": round(category_data['avg_cosine'], 2)
                }
        
        # Format language data with the new metric
        for language, language_data in model_data['languages'].items():
            if language_data['total'] > 0:
                formatted_results[model_name]["languages"][language] = {
                    "total_comparisons": language_data['total'],
                    "line0_exact_matches": language_data['line0_exact_matches'],
                    "line0_exact_match_rate": round((language_data['line0_exact_matches'] / language_data['total'] * 100) if language_data['total'] > 0 else 0, 2),
                    "avg_cosine": round(language_data['avg_cosine'], 2)
                }
    
    return formatted_results

def create_specific_category_comparisons(formatted_results, plots_dir="plots"):
    """
    Create specific graphs comparing key categories across all languages for selected models.
    
    This creates two graphs (one for cosine similarity and line 0 exact match rate) showing 
    how different models perform across 6 specific categories, with data aggregated across all languages.
    """
    # Set style
    sns.set_palette("husl")
    plt.rcParams['figure.autolayout'] = True
    
    # Create directory for plots if it doesn't exist
    os.makedirs(plots_dir, exist_ok=True)
    
    # Specific models to compare with clean display names mapping
    selected_models = ['claude-3-7-sonnet', 'gpt-4.5-preview', 'o3-mini', 'DeepSeek-V3-0324']
    model_display_names = {
        'claude-3-7-sonnet': 'Claude 3.7 Sonnet',
        'gpt-4.5-preview': 'GPT-4.5 Preview',
        'o3-mini': 'o3-mini',
        'DeepSeek-V3-0324': 'DeepSeek-V3'
    }
    
    # Specific categories to compare with clean display names mapping
    selected_categories = [
        'code_purpose_understanding',
        'code2NL_NL2code',
        'low_context',
        'pattern_matching',
        'api_usage',
        'syntax_completion'
    ]
    category_display_names = {
        'code_purpose_understanding': 'Code Purpose Understanding',
        'code2NL_NL2code': 'Code2NL/NL2Code',
        'low_context': 'Low Context',
        'pattern_matching': 'Pattern Matching',
        'api_usage': 'API Usage',
        'syntax_completion': 'Syntax Completion'
    }
    
    # Metrics to plot - only keep the two required metrics
    metrics = [
        ('avg_cosine', 'Average Cosine Similarity'),
        ('line0_exact_match_rate', 'Line 0 Exact Match Rate (%)')
    ]
    
    # Collect data across all languages for the selected models and categories
    comparison_data = []
    
    # For each model
    for model_name, model_data in formatted_results.items():
        if model_name in selected_models:
            # For each selected category
            for category in selected_categories:
                if category in model_data["categories"]:
                    category_stats = model_data["categories"][category]
                    comparison_data.append({
                        'Model': model_display_names.get(model_name, model_name),  # Use clean model name
                        'Category': category_display_names.get(category, category),  # Use clean category name
                        'Raw Category': category,  # Keep raw category for sorting
                        'Average Cosine Similarity': category_stats['avg_cosine'],
                        'Line 0 Exact Match Rate': category_stats['line0_exact_match_rate'],
                        'Total Samples': category_stats['total_comparisons']
                    })
    
    # Create DataFrame
    df_comparison = pd.DataFrame(comparison_data)
    
    # Create a plot for each metric
    for metric_key, metric_label in metrics:
        plt.figure(figsize=(16, 10))
        
        # Set font sizes - increased for better readability
        plt.rcParams.update({
            'font.size': 20,
            'axes.titlesize': 28,
            'axes.labelsize': 26,
            'xtick.labelsize': 24,
            'ytick.labelsize': 24,
            'legend.fontsize': 24
        })
        
        # Convert metric key to DataFrame column name
        if metric_key == 'avg_cosine':
            y_col = 'Average Cosine Similarity'
        elif metric_key == 'line0_exact_match_rate':
            y_col = 'Line 0 Exact Match Rate'
        
        # Ensure categories are displayed in the original order
        category_order = [category_display_names.get(cat, cat) for cat in selected_categories]
        
        # Create the bar plot with clean category names
        ax = sns.barplot(data=df_comparison, x='Category', y=y_col, hue='Model', order=category_order)
        
        # Set the title and labels with increased font sizes
        ax.set_title(f'{metric_label} by Category Across Languages', fontsize=32, pad=25)
        ax.set_xlabel('Category', fontsize=28)
        ax.set_ylabel(metric_label, fontsize=28)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right', fontsize=24)
        plt.yticks(fontsize=24)
        
        # Only add legend for the cosine similarity plot
        if metric_key == 'avg_cosine':
            legend = plt.legend(title='Model', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=24)
            legend.get_title().set_fontsize(26)
        else:
            # Remove legend for the line0_exact_match_rate plot
            ax.get_legend().remove()
        
        # Format y-axis for percentage metrics
        if 'Rate' in metric_label:
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}%'))
        
        plt.tight_layout()
        
        # Generate a safe filename
        safe_metric = metric_key.replace('_', '-')
        plt.savefig(f'{plots_dir}/specific_category_comparison_{safe_metric}.png', bbox_inches='tight', dpi=300)
        plt.close()
        
        # Create an additional plot for line0_exact_match_rate WITH legend
        if metric_key == 'line0_exact_match_rate':
            # Use a wider figure to accommodate the legend
            plt.figure(figsize=(20, 10))
            
            # Apply smaller font settings for this specific plot
            plt.rcParams.update({
                'font.size': 16,
                'axes.titlesize': 22,
                'axes.labelsize': 20,
                'xtick.labelsize': 18,
                'ytick.labelsize': 18,
                'legend.fontsize': 18
            })
            
            # Create the plot again
            ax = sns.barplot(data=df_comparison, x='Category', y=y_col, hue='Model', order=category_order)
            
            # Set the title and labels with more conservative font sizes
            ax.set_title(f'{metric_label} by Category Across Languages', fontsize=24, pad=30)
            ax.set_xlabel('Category', fontsize=20)
            ax.set_ylabel(metric_label, fontsize=20, labelpad=15)
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right', fontsize=18)
            plt.yticks(fontsize=18)
            
            # Add legend for this version
            legend = plt.legend(title='Model', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=18)
            legend.get_title().set_fontsize(20)
            
            # Format y-axis for percentage metrics
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}%'))
            
            # Adjust the subplot parameters directly for more control
            plt.subplots_adjust(top=0.85, left=0.15)
            
            # Save with a different filename to indicate it has a legend
            plt.savefig(f'{plots_dir}/specific_category_comparison_{safe_metric}_with_legend.png', bbox_inches='tight', dpi=300)
            plt.close()
    
    print("Created specific category comparison plots across languages")

def run_comparison(benchmark_base="../benchmark", completions_base="../completions", 
                  results_file="model_benchmark_comparison_results.json", plots_dir="plots", debug=False):
    """Run the comparison pipeline and save results."""
    # Load and compare completions
    if debug:
        results, test_cases = load_and_compare_completions(completions_base, benchmark_base, debug=True)
        # Print only cosine similarity for debug mode
        for model_name, cases in test_cases.items():
            print(f"\n## MODEL: {model_name}")
            # Sort by cosine similarity (ascending)
            sorted_cases = sorted(cases, key=lambda x: x['cosine_similarity'])
            for i, case in enumerate(sorted_cases[:10]):
                print(f"\n{i+1}. Test ID: {case['test_id']}")
                print(f"   Language: {case['language']}, Category: {case['category']}")
                print(f"   Cosine Similarity: {case['cosine_similarity']}")
                print(f"   Prompt: {case['prompt'][:100]}..." if len(case['prompt']) > 100 else f"   Prompt: {case['prompt']}")
                print(f"   Golden completion: {case['golden_completion'][:100]}..." if len(case['golden_completion']) > 100 else f"   Golden completion: {case['golden_completion']}")
                print(f"   Model completion: {case['model_completion'][:100]}..." if len(case['model_completion']) > 100 else f"   Model completion: {case['model_completion']}")
        return
    
    # Standard flow (generate plots and JSON)
    results = load_and_compare_completions(completions_base, benchmark_base)
    
    # Format results 
    formatted_results = format_results(results)
    
    # Check if we have any results
    if not formatted_results:
        print("No comparison results found. Check that the paths to benchmark and completions are correct.")
        return
    
    # Save results to JSON file
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_results, f, indent=2)
    print(f"\nResults have been saved to {results_file}")
    
    # Create only specific category comparison plots
    create_specific_category_comparisons(formatted_results, plots_dir)
    print(f"\nSpecific category comparison plots have been saved to the '{plots_dir}' directory")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evaluate code completions against benchmarks.')
    parser.add_argument('--completions', default="../completions", 
                        help='Path to the completions directory (default: ../completions)')
    parser.add_argument('--benchmark', default="../benchmark",
                        help='Path to the benchmark directory (default: ../benchmark)')
    parser.add_argument('--results', default="model_benchmark_comparison_results.json",
                        help='Path for the output results JSON file (default: model_benchmark_comparison_results.json)')
    parser.add_argument('--plots', default="plots",
                        help='Directory to save visualization plots (default: plots)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode to print most dissimilar test cases instead of generating plots and JSON')
    
    args = parser.parse_args()
    
    benchmark_base = args.benchmark
    completions_base = args.completions
    results_file = args.results
    plots_dir = args.plots
    debug = args.debug
    
    print(f"Using benchmark path: {benchmark_base}")
    print(f"Using completions path: {completions_base}")
    
    if not debug:
        print(f"Results will be saved to: {results_file}")
        print(f"Plots will be saved to: {plots_dir}")
    else:
        print("Debug mode enabled: printing most dissimilar test cases")
    
    run_comparison(benchmark_base, completions_base, results_file, plots_dir, debug)
