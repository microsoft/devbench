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

def get_min_Levenshtein(golden, completion, min_length):
    """Get minimum Levenshtein distance considering substrings."""
    if not golden or not completion:
        return len(golden) + len(completion)  # Maximum distance if either is empty
        
    dist_min = Levenshtein.distance(golden, completion)
    for i in range(min_length, len(golden)):
        gstring = golden[:i]
        dist_i = Levenshtein.distance(gstring, completion)
        dist_min = min(dist_i, dist_min)
    return dist_min

def calculate_proximity_match(golden_completion, model_completion):
    """Calculate if there's a proximity match between completions."""
    # 1. Get the cleansed text of the completion and the ground truth
    fl_golden = get_fully_cleansed_first_line(golden_completion)
    fl_model = get_fully_cleansed_first_line(model_completion)

    # 2. Split to words
    fl_golden_words = re.split(r'[ ]', fl_golden) if fl_golden else []
    fl_model_words = re.split(r'[ ]', fl_model) if fl_model else []

    # 3. Compare each two words:
    min_length = 3
    distances = []
    for gword in fl_golden_words:
        for cword in fl_model_words:
            # Ignore the words that are too short
            if len(cword) < min_length or len(gword) < min_length:
                continue
            distance = get_min_Levenshtein(golden=gword, completion=cword, min_length=min_length)
            norm_dist = distance / max(len(cword), 1)
            distances.append(norm_dist)
    
    # 4. Check if there is a close distance
    # Th=0.5 means less effort is required to make the two words similar than rewriting one from scratch
    is_low_distance = any((distance <= 0.5) for distance in distances) if distances else False
    
    return int(is_low_distance)

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

def calculate_edit_similarity(text1, text2):
    """Calculate edit similarity (normalized Levenshtein distance)."""
    if text1 == text2:
        return 1.0
    
    if not text1 or not text2:
        return 0.0
    
    # Calculate Levenshtein distance
    lev_dist = levenshtein_distance(text1, text2)
    
    # Normalize by the length of the longer string to get a similarity score between 0 and 1
    max_len = max(len(text1), len(text2))
    if max_len == 0:
        return 1.0  # Both strings are empty
    
    # Convert distance to similarity (1 - normalized_distance)
    return 1.0 - (lev_dist / max_len)

def calculate_first_line_edit_similarity(text1, text2):
    """Calculate edit similarity (normalized Levenshtein distance) between first lines only."""
    # Get cleaned first lines
    first_line1 = get_fully_cleansed_first_line(text1)
    first_line2 = get_fully_cleansed_first_line(text2)
    
    if first_line1 == first_line2:
        return 1.0
    
    if not first_line1 or not first_line2:
        return 0.0
    
    # Calculate Levenshtein distance between first lines
    lev_dist = levenshtein_distance(first_line1, first_line2)
    
    # Normalize by the length of the longer first line
    max_len = max(len(first_line1), len(first_line2))
    if max_len == 0:
        return 1.0  # Both first lines are empty
    
    # Convert distance to similarity (1 - normalized_distance)
    return 1.0 - (lev_dist / max_len)

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
        'levenshtein_distances': [],
        'avg_levenshtein': 0,
        'edit_similarities': [],
        'avg_edit_similarity': 0,
        'first_line_edit_similarities': [],
        'avg_first_line_edit_similarity': 0,
        'cosine_similarities': [],
        'avg_cosine': 0,
        'proximity_matches': 0,
        'categories': defaultdict(lambda: {
            'total': 0,
            'line0_exact_matches': 0,
            'levenshtein_distances': [],
            'avg_levenshtein': 0,
            'edit_similarities': [],
            'avg_edit_similarity': 0,
            'first_line_edit_similarities': [],
            'avg_first_line_edit_similarity': 0,
            'cosine_similarities': [],
            'avg_cosine': 0,
            'proximity_matches': 0
        }),
        'languages': defaultdict(lambda: {
            'total': 0,
            'line0_exact_matches': 0,
            'levenshtein_distances': [],
            'avg_levenshtein': 0,
            'edit_similarities': [],
            'avg_edit_similarity': 0,
            'first_line_edit_similarities': [],
            'avg_first_line_edit_similarity': 0,
            'cosine_similarities': [],
            'avg_cosine': 0,
            'proximity_matches': 0
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
                                
                                # Levenshtein distance for first line
                                lev_dist = levenshtein_distance(model_line0, golden_line0)
                                results[model_name]['levenshtein_distances'].append(lev_dist)
                                results[model_name]['categories'][category]['levenshtein_distances'].append(lev_dist)
                                results[model_name]['languages'][language]['levenshtein_distances'].append(lev_dist)
                                
                                # Edit similarity for first line
                                edit_sim = calculate_edit_similarity(model_line0, golden_line0)
                                results[model_name]['edit_similarities'].append(edit_sim)
                                results[model_name]['categories'][category]['edit_similarities'].append(edit_sim)
                                results[model_name]['languages'][language]['edit_similarities'].append(edit_sim)
                                
                                # First line edit similarity
                                first_line_edit_sim = calculate_first_line_edit_similarity(model_completion, golden_completion)
                                results[model_name]['first_line_edit_similarities'].append(first_line_edit_sim)
                                results[model_name]['categories'][category]['first_line_edit_similarities'].append(first_line_edit_sim)
                                results[model_name]['languages'][language]['first_line_edit_similarities'].append(first_line_edit_sim)
                                
                                # Cosine similarity for first line
                                cosine_sim = calculate_cosine_similarity(model_line0, golden_line0)
                                results[model_name]['cosine_similarities'].append(cosine_sim)
                                results[model_name]['categories'][category]['cosine_similarities'].append(cosine_sim)
                                results[model_name]['languages'][language]['cosine_similarities'].append(cosine_sim)
                                
                                # Calculate proximity match for first line
                                prox_match = calculate_proximity_match(golden_completion, model_completion)
                                if prox_match:
                                    results[model_name]['proximity_matches'] += 1
                                    results[model_name]['categories'][category]['proximity_matches'] += 1
                                    results[model_name]['languages'][language]['proximity_matches'] += 1
                                
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
                                        'edit_similarity': edit_sim,
                                        'first_line_edit_similarity': first_line_edit_sim,
                                        'cosine_similarity': cosine_sim,
                                        'levenshtein_distance': lev_dist,
                                        'proximity_match': bool(prox_match)
                                    })
                            
                        except json.JSONDecodeError:
                            print(f"Error parsing JSON in file: {file_path}")
                            continue
    
    # Calculate average metrics for each model
    for model_name in results:
        # Overall averages
        distances = results[model_name]['levenshtein_distances']
        results[model_name]['avg_levenshtein'] = sum(distances) / len(distances) if distances else 0
        
        edit_sims = results[model_name]['edit_similarities']
        results[model_name]['avg_edit_similarity'] = sum(edit_sims) / len(edit_sims) if edit_sims else 0
        
        first_line_edit_sims = results[model_name]['first_line_edit_similarities']
        results[model_name]['avg_first_line_edit_similarity'] = sum(first_line_edit_sims) / len(first_line_edit_sims) if first_line_edit_sims else 0
        
        cosine_sims = results[model_name]['cosine_similarities']
        results[model_name]['avg_cosine'] = sum(cosine_sims) / len(cosine_sims) if cosine_sims else 0
        
        # Category averages
        for category in results[model_name]['categories']:
            cat_distances = results[model_name]['categories'][category]['levenshtein_distances']
            results[model_name]['categories'][category]['avg_levenshtein'] = sum(cat_distances) / len(cat_distances) if cat_distances else 0
            
            cat_edit_sims = results[model_name]['categories'][category]['edit_similarities']
            results[model_name]['categories'][category]['avg_edit_similarity'] = sum(cat_edit_sims) / len(cat_edit_sims) if cat_edit_sims else 0
            
            cat_first_line_edit_sims = results[model_name]['categories'][category]['first_line_edit_similarities']
            results[model_name]['categories'][category]['avg_first_line_edit_similarity'] = sum(cat_first_line_edit_sims) / len(cat_first_line_edit_sims) if cat_first_line_edit_sims else 0
            
            cat_cosine_sims = results[model_name]['categories'][category]['cosine_similarities']
            results[model_name]['categories'][category]['avg_cosine'] = sum(cat_cosine_sims) / len(cat_cosine_sims) if cat_cosine_sims else 0
        
        # Language averages
        for language in results[model_name]['languages']:
            lang_distances = results[model_name]['languages'][language]['levenshtein_distances']
            results[model_name]['languages'][language]['avg_levenshtein'] = sum(lang_distances) / len(lang_distances) if lang_distances else 0
            
            lang_edit_sims = results[model_name]['languages'][language]['edit_similarities']
            results[model_name]['languages'][language]['avg_edit_similarity'] = sum(lang_edit_sims) / len(lang_edit_sims) if lang_edit_sims else 0
            
            lang_first_line_edit_sims = results[model_name]['languages'][language]['first_line_edit_similarities']
            results[model_name]['languages'][language]['avg_first_line_edit_similarity'] = sum(lang_first_line_edit_sims) / len(lang_first_line_edit_sims) if lang_first_line_edit_sims else 0
            
            lang_cosine_sims = results[model_name]['languages'][language]['cosine_similarities']
            results[model_name]['languages'][language]['avg_cosine'] = sum(lang_cosine_sims) / len(lang_cosine_sims) if lang_cosine_sims else 0
    
    if debug:
        return results, test_cases
    return results

def format_results(results):
    """Format results into a JSON-friendly dictionary with computed statistics."""
    formatted_results = {}
    
    for model_name, model_data in results.items():
        formatted_results[model_name] = {
            "overall": {
                "total_comparisons": model_data['total'],
                "line0_exact_matches": model_data['line0_exact_matches'],
                "line0_exact_match_rate": round((model_data['line0_exact_matches'] / model_data['total'] * 100) if model_data['total'] > 0 else 0, 2),
                "proximity_matches": model_data['proximity_matches'],
                "proximity_match_rate": round((model_data['proximity_matches'] / model_data['total'] * 100) if model_data['total'] > 0 else 0, 2),
                "avg_levenshtein": round(model_data['avg_levenshtein'], 2),
                "avg_edit_similarity": round(model_data['avg_edit_similarity'], 2),
                "avg_first_line_edit_similarity": round(model_data['avg_first_line_edit_similarity'], 2),
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
                    "proximity_matches": category_data['proximity_matches'],
                    "proximity_match_rate": round((category_data['proximity_matches'] / category_data['total'] * 100) if category_data['total'] > 0 else 0, 2),
                    "avg_levenshtein": round(category_data['avg_levenshtein'], 2),
                    "avg_edit_similarity": round(category_data['avg_edit_similarity'], 2),
                    "avg_first_line_edit_similarity": round(category_data['avg_first_line_edit_similarity'], 2),
                    "avg_cosine": round(category_data['avg_cosine'], 2)
                }
        
        # Format language data with the new metric
        for language, language_data in model_data['languages'].items():
            if language_data['total'] > 0:
                formatted_results[model_name]["languages"][language] = {
                    "total_comparisons": language_data['total'],
                    "line0_exact_matches": language_data['line0_exact_matches'],
                    "line0_exact_match_rate": round((language_data['line0_exact_matches'] / language_data['total'] * 100) if language_data['total'] > 0 else 0, 2),
                    "proximity_matches": language_data['proximity_matches'],
                    "proximity_match_rate": round((language_data['proximity_matches'] / language_data['total'] * 100) if language_data['total'] > 0 else 0, 2),
                    "avg_levenshtein": round(language_data['avg_levenshtein'], 2),
                    "avg_edit_similarity": round(language_data['avg_edit_similarity'], 2),
                    "avg_first_line_edit_similarity": round(language_data['avg_first_line_edit_similarity'], 2),
                    "avg_cosine": round(language_data['avg_cosine'], 2)
                }
    
    return formatted_results

def create_visualizations(formatted_results, plots_dir="plots"):
    """Create and save visualizations of the comparison results."""
    # Set style
    sns.set_palette("husl")
    plt.rcParams['figure.autolayout'] = True
    
    # Create directory for plots if it doesn't exist
    os.makedirs(plots_dir, exist_ok=True)
    
    # Collect data for overall comparison
    overall_data = []
    
    for model_name, model_data in formatted_results.items():
        overall_data.append({
            'Model': model_name,
            'Line 0 Exact Match Rate': model_data['overall']['line0_exact_match_rate'],
            'Proximity Match Rate': model_data['overall']['proximity_match_rate'],
            'Avg Edit Similarity': model_data['overall']['avg_edit_similarity'],
            'Avg First Line Edit Similarity': model_data['overall']['avg_first_line_edit_similarity'],
            'Avg Cosine Similarity': model_data['overall']['avg_cosine']
        })
    
    # Check if we have any data to plot
    if overall_data:
        df_overall = pd.DataFrame(overall_data)
        
        # 1. Overall comparison across models (all metrics except Levenshtein)
        fig, axes = plt.subplots(5, 1, figsize=(14, 25))
        
        # Line 0 Exact match rate plot
        ax0 = sns.barplot(data=df_overall, x='Model', y='Line 0 Exact Match Rate', ax=axes[0])
        axes[0].set_title('Line 0 Exact Match Rate by Model', pad=20)
        # Fix tick labels
        axes[0].set_xticks(range(len(df_overall)))
        axes[0].set_xticklabels(df_overall['Model'], rotation=45, ha='right')
        axes[0].set_ylabel('Line 0 Exact Match Rate (%)')
        for i in axes[0].containers:
            axes[0].bar_label(i, fmt='%.1f%%')
        
        # Proximity match rate plot
        sns.barplot(data=df_overall, x='Model', y='Proximity Match Rate', ax=axes[1])
        axes[1].set_title('Proximity Match Rate by Model', pad=20)
        axes[1].set_xticks(range(len(df_overall)))
        axes[1].set_xticklabels(df_overall['Model'], rotation=45, ha='right')
        axes[1].set_ylabel('Proximity Match Rate (%)')
        for i in axes[1].containers:
            axes[1].bar_label(i, fmt='%.1f%%')
        
        # Edit similarity plot
        sns.barplot(data=df_overall, x='Model', y='Avg Edit Similarity', ax=axes[2])
        axes[2].set_title('Average Edit Similarity by Model', pad=20)
        axes[2].set_xticks(range(len(df_overall)))
        axes[2].set_xticklabels(df_overall['Model'], rotation=45, ha='right')
        axes[2].set_ylabel('Average Edit Similarity')
        for i in axes[2].containers:
            axes[2].bar_label(i, fmt='%.2f')
        
        # First Line Edit similarity plot
        sns.barplot(data=df_overall, x='Model', y='Avg First Line Edit Similarity', ax=axes[3])
        axes[3].set_title('Average First Line Edit Similarity by Model', pad=20)
        axes[3].set_xticks(range(len(df_overall)))
        axes[3].set_xticklabels(df_overall['Model'], rotation=45, ha='right')
        axes[3].set_ylabel('Average First Line Edit Similarity')
        for i in axes[3].containers:
            axes[3].bar_label(i, fmt='%.2f')
        
        # Cosine similarity plot
        sns.barplot(data=df_overall, x='Model', y='Avg Cosine Similarity', ax=axes[4])
        axes[4].set_title('Average Cosine Similarity by Model', pad=20)
        axes[4].set_xticks(range(len(df_overall)))
        axes[4].set_xticklabels(df_overall['Model'], rotation=45, ha='right')
        axes[4].set_ylabel('Average Cosine Similarity')
        for i in axes[4].containers:
            axes[4].bar_label(i, fmt='%.2f')
        
        plt.tight_layout()
        plt.savefig(f'{plots_dir}/overall_model_comparison.png', bbox_inches='tight', dpi=300)
        plt.close()
    else:
        print("No overall data to plot.")
    
    # 2. Category comparison for each model
    for model_name, model_data in formatted_results.items():
        categories_data = []
        
        for category, category_stats in model_data['categories'].items():
            categories_data.append({
                'Category': category,
                'Line 0 Exact Match Rate': category_stats['line0_exact_match_rate'],
                'Proximity Match Rate': category_stats['proximity_match_rate'],
                'Avg Edit Similarity': category_stats['avg_edit_similarity'],
                'Avg First Line Edit Similarity': category_stats['avg_first_line_edit_similarity'],
                'Avg Cosine Similarity': category_stats['avg_cosine'],
                'Total Samples': category_stats['total_comparisons']
            })
        
        if categories_data:
            df_categories = pd.DataFrame(categories_data)
            
            # Create figure with five subplots (removed Levenshtein)
            fig, axes = plt.subplots(4, 1, figsize=(14, 20))
            
            # Line 0 Exact match rate by category
            sns.barplot(data=df_categories, x='Category', y='Line 0 Exact Match Rate', ax=axes[0])
            axes[0].set_title(f'Line 0 Exact Match Rate by Category - {model_name}', pad=20)
            axes[0].set_xticks(range(len(df_categories)))
            axes[0].set_xticklabels(df_categories['Category'], rotation=45, ha='right')
            axes[0].set_ylabel('Line 0 Exact Match Rate (%)')
            for i in axes[0].containers:
                axes[0].bar_label(i, fmt='%.1f%%')
            
            # Proximity match rate by category
            sns.barplot(data=df_categories, x='Category', y='Proximity Match Rate', ax=axes[1])
            axes[1].set_title(f'Proximity Match Rate by Category - {model_name}', pad=20)
            axes[1].set_xticks(range(len(df_categories)))
            axes[1].set_xticklabels(df_categories['Category'], rotation=45, ha='right')
            axes[1].set_ylabel('Proximity Match Rate (%)')
            for i in axes[1].containers:
                axes[1].bar_label(i, fmt='%.1f%%')
            
            # Average Edit similarity by category
            sns.barplot(data=df_categories, x='Category', y='Avg Edit Similarity', ax=axes[2])
            axes[2].set_title(f'Average Edit Similarity by Category - {model_name}', pad=20)
            axes[2].set_xticks(range(len(df_categories)))
            axes[2].set_xticklabels(df_categories['Category'], rotation=45, ha='right')
            axes[2].set_ylabel('Average Edit Similarity')
            for i in axes[2].containers:
                axes[2].bar_label(i, fmt='%.2f')
            
            # Average First Line Edit similarity by category
            sns.barplot(data=df_categories, x='Category', y='Avg First Line Edit Similarity', ax=axes[3])
            axes[3].set_title(f'Average First Line Edit Similarity by Category - {model_name}', pad=20)
            axes[3].set_xticks(range(len(df_categories)))
            axes[3].set_xticklabels(df_categories['Category'], rotation=45, ha='right')
            axes[3].set_ylabel('Average First Line Edit Similarity')
            for i in axes[3].containers:
                axes[3].bar_label(i, fmt='%.2f')
            
            # Sample size by category
            sns.barplot(data=df_categories, x='Category', y='Total Samples', ax=axes[3])
            axes[3].set_title(f'Sample Size by Category - {model_name}', pad=20)
            axes[3].set_xticks(range(len(df_categories)))
            axes[3].set_xticklabels(df_categories['Category'], rotation=45, ha='right')
            axes[3].set_ylabel('Number of Samples')
            for i in axes[3].containers:
                axes[3].bar_label(i)
            
            plt.tight_layout()
            plt.savefig(f'{plots_dir}/{model_name}_categories.png', bbox_inches='tight', dpi=300)
            plt.close()
        else:
            print(f"No category data to plot for model: {model_name}")
    
    # 3. Language comparison for each model
    for model_name, model_data in formatted_results.items():
        languages_data = []
        
        for language, language_stats in model_data['languages'].items():
            languages_data.append({
                'Language': language,
                'Line 0 Exact Match Rate': language_stats['line0_exact_match_rate'],
                'Proximity Match Rate': language_stats['proximity_match_rate'],
                'Avg Edit Similarity': language_stats['avg_edit_similarity'],
                'Avg First Line Edit Similarity': language_stats['avg_first_line_edit_similarity'],
                'Avg Cosine Similarity': language_stats['avg_cosine'],
                'Total Samples': language_stats['total_comparisons']
            })
        
        if languages_data:
            df_languages = pd.DataFrame(languages_data)
            
            # Create figure with five subplots
            fig, axes = plt.subplots(4, 1, figsize=(14, 20))
            
            # Line 0 Exact match rate by language
            sns.barplot(data=df_languages, x='Language', y='Line 0 Exact Match Rate', ax=axes[0])
            axes[0].set_title(f'Line 0 Exact Match Rate by Language - {model_name}', pad=20)
            axes[0].set_xticks(range(len(df_languages)))
            axes[0].set_xticklabels(df_languages['Language'], rotation=45, ha='right')
            axes[0].set_ylabel('Line 0 Exact Match Rate (%)')
            for i in axes[0].containers:
                axes[0].bar_label(i, fmt='%.1f%%')
            
            # Proximity match rate by language
            sns.barplot(data=df_languages, x='Language', y='Proximity Match Rate', ax=axes[1])
            axes[1].set_title(f'Proximity Match Rate by Language - {model_name}', pad=20)
            axes[1].set_xticks(range(len(df_languages)))
            axes[1].set_xticklabels(df_languages['Language'], rotation=45, ha='right')
            axes[1].set_ylabel('Proximity Match Rate (%)')
            for i in axes[1].containers:
                axes[1].bar_label(i, fmt='%.1f%%')
            
            # Average Edit similarity by language
            sns.barplot(data=df_languages, x='Language', y='Avg Edit Similarity', ax=axes[2])
            axes[2].set_title(f'Average Edit Similarity by Language - {model_name}', pad=20)
            axes[2].set_xticks(range(len(df_languages)))
            axes[2].set_xticklabels(df_languages['Language'], rotation=45, ha='right')
            axes[2].set_ylabel('Average Edit Similarity')
            for i in axes[2].containers:
                axes[2].bar_label(i, fmt='%.2f')
            
            # Average First Line Edit similarity by language
            sns.barplot(data=df_languages, x='Language', y='Avg First Line Edit Similarity', ax=axes[3])
            axes[3].set_title(f'Average First Line Edit Similarity by Language - {model_name}', pad=20)
            axes[3].set_xticks(range(len(df_languages)))
            axes[3].set_xticklabels(df_languages['Language'], rotation=45, ha='right')
            axes[3].set_ylabel('Average First Line Edit Similarity')
            for i in axes[3].containers:
                axes[3].bar_label(i, fmt='%.2f')
            
            # Sample size by language
            sns.barplot(data=df_languages, x='Language', y='Total Samples', ax=axes[3])
            axes[3].set_title(f'Sample Size by Language - {model_name}', pad=20)
            axes[3].set_xticks(range(len(df_languages)))
            axes[3].set_xticklabels(df_languages['Language'], rotation=45, ha='right')
            axes[3].set_ylabel('Number of Samples')
            for i in axes[3].containers:
                axes[3].bar_label(i)
            
            plt.tight_layout()
            plt.savefig(f'{plots_dir}/{model_name}_languages.png', bbox_inches='tight', dpi=300)
            plt.close()
        else:
            print(f"No language data to plot for model: {model_name}")
            
    # 4. Create comparison plots for each category across models
    # Group by category first
    category_model_data = defaultdict(list)
    
    for model_name, model_data in formatted_results.items():
        for category, category_stats in model_data['categories'].items():
            category_model_data[category].append({
                'Model': model_name,
                'Line 0 Exact Match Rate': category_stats['line0_exact_match_rate'],
                'Proximity Match Rate': category_stats['proximity_match_rate'],
                'Avg Edit Similarity': category_stats['avg_edit_similarity'],
                'Avg First Line Edit Similarity': category_stats['avg_first_line_edit_similarity'],
                'Avg Cosine Similarity': category_stats['avg_cosine']
            })
    
    # Create plots for each category
    for category, model_data_list in category_model_data.items():
        if len(model_data_list) > 1:  # Only plot if we have multiple models
            df_category = pd.DataFrame(model_data_list)
            
            fig, axes = plt.subplots(4, 1, figsize=(14, 20))
            
            # Line 0 Exact match rate
            sns.barplot(data=df_category, x='Model', y='Line 0 Exact Match Rate', ax=axes[0])
            axes[0].set_title(f'Line 0 Exact Match Rate - {category}', pad=20)
            axes[0].set_xticks(range(len(df_category)))
            axes[0].set_xticklabels(df_category['Model'], rotation=45, ha='right')
            axes[0].set_ylabel('Line 0 Exact Match Rate (%)')
            for i in axes[0].containers:
                axes[0].bar_label(i, fmt='%.1f%%')
            
            # Proximity match rate
            sns.barplot(data=df_category, x='Model', y='Proximity Match Rate', ax=axes[1])
            axes[1].set_title(f'Proximity Match Rate - {category}', pad=20)
            axes[1].set_xticks(range(len(df_category)))
            axes[1].set_xticklabels(df_category['Model'], rotation=45, ha='right')
            axes[1].set_ylabel('Proximity Match Rate (%)')
            for i in axes[1].containers:
                axes[1].bar_label(i, fmt='%.1f%%')
            
            # Edit similarity
            sns.barplot(data=df_category, x='Model', y='Avg Edit Similarity', ax=axes[2])
            axes[2].set_title(f'Average Edit Similarity - {category}', pad=20)
            axes[2].set_xticks(range(len(df_category)))
            axes[2].set_xticklabels(df_category['Model'], rotation=45, ha='right')
            axes[2].set_ylabel('Average Edit Similarity')
            for i in axes[2].containers:
                axes[2].bar_label(i, fmt='%.2f')
            
            # First Line Edit similarity
            sns.barplot(data=df_category, x='Model', y='Avg First Line Edit Similarity', ax=axes[3])
            axes[3].set_title(f'Average First Line Edit Similarity - {category}', pad=20)
            axes[3].set_xticks(range(len(df_category)))
            axes[3].set_xticklabels(df_category['Model'], rotation=45, ha='right')
            axes[3].set_ylabel('Average First Line Edit Similarity')
            for i in axes[3].containers:
                axes[3].bar_label(i, fmt='%.2f')
            
            plt.tight_layout()
            
            # Make category name safe for filenames
            safe_category = category.replace('/', '_')
            plt.savefig(f'{plots_dir}/category_{safe_category}_comparison.png', bbox_inches='tight', dpi=300)
            plt.close()
        else:
            print(f"Not enough models ({len(model_data_list)}) to compare for category: {category}")
    
    # 5. Create comparison plots for each language across models
    # Group by language first
    language_model_data = defaultdict(list)
    
    for model_name, model_data in formatted_results.items():
        for language, language_stats in model_data['languages'].items():
            language_model_data[language].append({
                'Model': model_name,
                'Line 0 Exact Match Rate': language_stats['line0_exact_match_rate'],
                'Proximity Match Rate': language_stats['proximity_match_rate'],
                'Avg Edit Similarity': language_stats['avg_edit_similarity'],
                'Avg First Line Edit Similarity': language_stats['avg_first_line_edit_similarity'],
                'Avg Cosine Similarity': language_stats['avg_cosine']
            })
    
    # Create plots for each language
    for language, model_data_list in language_model_data.items():
        if len(model_data_list) > 1:  # Only plot if we have multiple models
            df_language = pd.DataFrame(model_data_list)
            
            fig, axes = plt.subplots(4, 1, figsize=(14, 20))
            
            # Line 0 Exact match rate
            sns.barplot(data=df_language, x='Model', y='Line 0 Exact Match Rate', ax=axes[0])
            axes[0].set_title(f'Line 0 Exact Match Rate - {language}', pad=20)
            axes[0].set_xticks(range(len(df_language)))
            axes[0].set_xticklabels(df_language['Model'], rotation=45, ha='right')
            axes[0].set_ylabel('Line 0 Exact Match Rate (%)')
            for i in axes[0].containers:
                axes[0].bar_label(i, fmt='%.1f%%')
            
            # Proximity match rate
            sns.barplot(data=df_language, x='Model', y='Proximity Match Rate', ax=axes[1])
            axes[1].set_title(f'Proximity Match Rate - {language}', pad=20)
            axes[1].set_xticks(range(len(df_language)))
            axes[1].set_xticklabels(df_language['Model'], rotation=45, ha='right')
            axes[1].set_ylabel('Proximity Match Rate (%)')
            for i in axes[1].containers:
                axes[1].bar_label(i, fmt='%.1f%%')
            
            # Edit similarity
            sns.barplot(data=df_language, x='Model', y='Avg Edit Similarity', ax=axes[2])
            axes[2].set_title(f'Average Edit Similarity - {language}', pad=20)
            axes[2].set_xticks(range(len(df_language)))
            axes[2].set_xticklabels(df_language['Model'], rotation=45, ha='right')
            axes[2].set_ylabel('Average Edit Similarity')
            for i in axes[2].containers:
                axes[2].bar_label(i, fmt='%.2f')
            
            # First Line Edit similarity
            sns.barplot(data=df_language, x='Model', y='Avg First Line Edit Similarity', ax=axes[3])
            axes[3].set_title(f'Average First Line Edit Similarity - {language}', pad=20)
            axes[3].set_xticks(range(len(df_language)))
            axes[3].set_xticklabels(df_language['Model'], rotation=45, ha='right')
            axes[3].set_ylabel('Average First Line Edit Similarity')
            for i in axes[3].containers:
                axes[3].bar_label(i, fmt='%.2f')
            
            plt.tight_layout()
            plt.savefig(f'{plots_dir}/language_{language}_comparison.png', bbox_inches='tight', dpi=300)
            plt.close()
        else:
            print(f"Not enough models ({len(model_data_list)}) to compare for language: {language}")

def create_model_comparison_by_category_plots(formatted_results, plots_dir="plots"):
    """
    Create plots for comparing specific models across categories for all metrics.
    Each plot has categories on x-axis, a metric on y-axis, with bars for each selected model.
    """
    # Set style
    sns.set_palette("husl")
    plt.rcParams['figure.autolayout'] = True
    
    # Create directory for plots if it doesn't exist
    os.makedirs(plots_dir, exist_ok=True)
    
    # Selected models to compare
    selected_models = ['4omini_sft39_spm_fix2_5', 'claude-3-7-sonnet', 'gpt-4o', 'o3-mini']
    
    # Metrics to plot
    metrics = [
        ('line0_exact_match_rate', 'Line 0 Exact Match Rate (%)'),
        ('proximity_match_rate', 'Proximity Match Rate (%)'),
        ('avg_levenshtein', 'Average Levenshtein Distance'),
        ('avg_edit_similarity', 'Average Edit Similarity'),
        ('avg_first_line_edit_similarity', 'Average First Line Edit Similarity'),
        ('avg_cosine', 'Average Cosine Similarity')
    ]
    
    # Collect data for all categories across the selected models
    category_data = []
    
    # Get all unique categories from all models
    all_categories = set()
    for model_name, model_data in formatted_results.items():
        if model_name in selected_models:
            for category in model_data["categories"].keys():
                all_categories.add(category)
    
    # Collect data for each model and category
    for model_name, model_data in formatted_results.items():
        if model_name in selected_models:
            for category in all_categories:
                if category in model_data["categories"]:
                    category_data.append({
                        'Model': model_name,
                        'Category': category,
                        'Line 0 Exact Match Rate': model_data["categories"][category]['line0_exact_match_rate'],
                        'Proximity Match Rate': model_data["categories"][category]['proximity_match_rate'],
                        'Average Levenshtein Distance': model_data["categories"][category]['avg_levenshtein'],
                        'Average Edit Similarity': model_data["categories"][category]['avg_edit_similarity'],
                        'Average First Line Edit Similarity': model_data["categories"][category]['avg_first_line_edit_similarity'],
                        'Average Cosine Similarity': model_data["categories"][category]['avg_cosine']
                    })
    
    # Create DataFrame
    df_categories = pd.DataFrame(category_data)
    
    # Create a plot for each metric
    for metric_key, metric_label in metrics:
        plt.figure(figsize=(16, 10))
        
        # Convert metric key to DataFrame column name
        if metric_key == 'line0_exact_match_rate':
            y_col = 'Line 0 Exact Match Rate'
        elif metric_key == 'proximity_match_rate':
            y_col = 'Proximity Match Rate'
        elif metric_key == 'avg_levenshtein':
            y_col = 'Average Levenshtein Distance'
        elif metric_key == 'avg_edit_similarity':
            y_col = 'Average Edit Similarity'
        elif metric_key == 'avg_first_line_edit_similarity':
            y_col = 'Average First Line Edit Similarity'
        elif metric_key == 'avg_cosine':
            y_col = 'Average Cosine Similarity'
        
        # Create the bar plot
        ax = sns.barplot(data=df_categories, x='Category', y=y_col, hue='Model')
        
        # Set the title and labels
        ax.set_title(f'{metric_label} by Category Across Selected Models', pad=20)
        ax.set_xlabel('Category')
        ax.set_ylabel(metric_label)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Add legend
        plt.legend(title='Model', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Format y-axis for percentage metrics
        if 'Rate' in metric_label:
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}%'))
        
        plt.tight_layout()
        
        # Generate a safe filename
        safe_metric = metric_key.replace('_', '-')
        plt.savefig(f'{plots_dir}/category_comparison_{safe_metric}.png', bbox_inches='tight', dpi=300)
        plt.close()
    
    print("Created model comparison by category plots")

def create_specific_category_comparisons(formatted_results, plots_dir="plots"):
    """
    Create specific graphs comparing key categories across all languages for selected models.
    
    This creates four graphs (one for each metric: cosine similarity, avg levenshtein distance,
    proximity match rate, and line 0 exact match rate) showing how different models perform 
    across 6 specific categories, with data aggregated across all languages.
    """
    # Set style
    sns.set_palette("husl")
    plt.rcParams['figure.autolayout'] = True
    
    # Create directory for plots if it doesn't exist
    os.makedirs(plots_dir, exist_ok=True)
    
    # Specific models to compare with clean display names mapping
    selected_models = ['claude-3-7-sonnet', 'gpt-4o', 'o3-mini', 'DeepSeek-V3-0324']
    model_display_names = {
        'claude-3-7-sonnet': 'Claude 3.7 Sonnet',
        'gpt-4o': 'GPT-4o',
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
    
    # Metrics to plot (now including first line edit similarity)
    metrics = [
        ('avg_cosine', 'Average Cosine Similarity'),
        ('avg_levenshtein', 'Average Levenshtein Distance'),
        ('avg_first_line_edit_similarity', 'Average Line 0 Edit Similarity'),
        ('proximity_match_rate', 'Proximity Match Rate (%)'),
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
                        'Average Levenshtein Distance': category_stats['avg_levenshtein'],
                        'Average Line 0 Edit Similarity': category_stats['avg_first_line_edit_similarity'],
                        'Proximity Match Rate': category_stats['proximity_match_rate'],
                        'Line 0 Exact Match Rate': category_stats['line0_exact_match_rate'],
                        'Total Samples': category_stats['total_comparisons']
                    })
    
    # Create DataFrame
    df_comparison = pd.DataFrame(comparison_data)
    
    # Create a plot for each metric
    for metric_key, metric_label in metrics:
        plt.figure(figsize=(16, 10))
        
        # Set font sizes
        plt.rcParams.update({
            'font.size': 12,
            'axes.titlesize': 16,
            'axes.labelsize': 14,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
            'legend.fontsize': 12
        })
        
        # Convert metric key to DataFrame column name
        if metric_key == 'avg_cosine':
            y_col = 'Average Cosine Similarity'
        elif metric_key == 'avg_levenshtein':
            y_col = 'Average Levenshtein Distance'
        elif metric_key == 'avg_first_line_edit_similarity':
            y_col = 'Average Line 0 Edit Similarity'
        elif metric_key == 'proximity_match_rate':
            y_col = 'Proximity Match Rate'
        elif metric_key == 'line0_exact_match_rate':
            y_col = 'Line 0 Exact Match Rate'
        
        # Ensure categories are displayed in the original order
        category_order = [category_display_names.get(cat, cat) for cat in selected_categories]
        
        # Create the bar plot with clean category names
        ax = sns.barplot(data=df_comparison, x='Category', y=y_col, hue='Model', order=category_order)
        
        # Set the title and labels with increased font sizes
        ax.set_title(f'{metric_label} by Category Across Languages', fontsize=18, pad=20)
        ax.set_xlabel('Category', fontsize=16)
        ax.set_ylabel(metric_label, fontsize=16)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right', fontsize=14)
        plt.yticks(fontsize=14)
        
        # Add legend with increased font size
        legend = plt.legend(title='Model', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=14)
        legend.get_title().set_fontsize(16)
        
        # Format y-axis for percentage metrics
        if 'Rate' in metric_label:
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}%'))
        
        plt.tight_layout()
        
        # Generate a safe filename
        safe_metric = metric_key.replace('_', '-')
        plt.savefig(f'{plots_dir}/specific_category_comparison_{safe_metric}.png', bbox_inches='tight', dpi=300)
        plt.close()
    
    print("Created specific category comparison plots across languages")

def print_most_dissimilar_cases(test_cases, top_n=10, similarity_metric='edit_similarity'):
    """Print the most dissimilar test cases based on the specified similarity metric."""
    print(f"\n===== MOST DISSIMILAR TEST CASES (using {similarity_metric}) =====\n")
    
    for model_name, cases in test_cases.items():
        print(f"\n## MODEL: {model_name}")
        
        # Filter Python cases
        python_cases = [case for case in cases if case['language'].lower() == 'python']
        other_cases = [case for case in cases if case['language'].lower() != 'python']
        
        # Sort Python cases by similarity (ascending) or distance (descending)
        if similarity_metric in ['edit_similarity', 'cosine_similarity', 'first_line_edit_similarity']:
            sorted_python_cases = sorted(python_cases, key=lambda x: x[similarity_metric])
            sorted_other_cases = sorted(other_cases, key=lambda x: x[similarity_metric])
        elif similarity_metric == 'levenshtein_distance':
            sorted_python_cases = sorted(python_cases, key=lambda x: x[similarity_metric], reverse=True)
            sorted_other_cases = sorted(other_cases, key=lambda x: x[similarity_metric], reverse=True)
        else:
            print(f"Unknown similarity metric: {similarity_metric}")
            continue
        
        # Print Python cases
        print(f"\n### PYTHON (Top {top_n} most dissimilar)")
        if sorted_python_cases:
            for i, case in enumerate(sorted_python_cases[:top_n]):
                print(f"\n{i+1}. Test ID: {case['test_id']}")
                print(f"   Category: {case['category']}")
                print(f"   {similarity_metric}: {case[similarity_metric]}")
                print(f"   Prompt: {case['prompt'][:100]}..." if len(case['prompt']) > 100 else f"   Prompt: {case['prompt']}")
                print(f"   Golden completion: {case['golden_completion'][:100]}..." if len(case['golden_completion']) > 100 else f"   Golden completion: {case['golden_completion']}")
                print(f"   Model completion: {case['model_completion'][:100]}..." if len(case['model_completion']) > 100 else f"   Model completion: {case['model_completion']}")
        else:
            print("   No Python test cases found.")
        
        # Print other language cases
        print(f"\n### OTHER LANGUAGES (Top {top_n} most dissimilar)")
        if sorted_other_cases:
            for i, case in enumerate(sorted_other_cases[:top_n]):
                print(f"\n{i+1}. Test ID: {case['test_id']}")
                print(f"   Language: {case['language']}, Category: {case['category']}")
                print(f"   {similarity_metric}: {case[similarity_metric]}")
                print(f"   Prompt: {case['prompt'][:100]}..." if len(case['prompt']) > 100 else f"   Prompt: {case['prompt']}")
                print(f"   Golden completion: {case['golden_completion'][:100]}..." if len(case['golden_completion']) > 100 else f"   Golden completion: {case['golden_completion']}")
                print(f"   Model completion: {case['model_completion'][:100]}..." if len(case['model_completion']) > 100 else f"   Model completion: {case['model_completion']}")
        else:
            print("   No other language test cases found.")

def run_comparison(benchmark_base="../benchmark", completions_base="../completions", 
                  results_file="model_benchmark_comparison_results.json", plots_dir="plots", debug=False):
    """Run the comparison pipeline and save results."""
    # Load and compare completions
    if debug:
        results, test_cases = load_and_compare_completions(completions_base, benchmark_base, debug=True)
        print_most_dissimilar_cases(test_cases, top_n=10, similarity_metric='edit_similarity')
        print("\n")
        print_most_dissimilar_cases(test_cases, top_n=10, similarity_metric='cosine_similarity')
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
    
    # Create visualizations
    create_visualizations(formatted_results, plots_dir)
    print(f"\nVisualizations have been saved to the '{plots_dir}' directory")
    
    # Create model comparison by category plots
    create_model_comparison_by_category_plots(formatted_results, plots_dir)
    print(f"\nModel comparison by category plots have been saved to the '{plots_dir}' directory")
    
    # Create specific category comparison plots
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
