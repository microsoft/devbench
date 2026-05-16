"""Compute Average Cosine Similarity and Line 0 Exact Match Rate for DevBench completions.

Walks the benchmark/ and completions/ directories, compares model completions against
golden completions, and reports per-model, per-category, and per-language metrics.

Usage:
    python evaluate_similarity.py [--completions DIR] [--benchmark DIR] [--results FILE] [--debug]
"""

import os
import json
import argparse
import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# The 9 paper models
PAPER_MODELS = [
    'gpt-5.5', 'gpt-5.4-mini', 'gpt-5.4-nano',
    'claude-opus-4-7', 'claude-sonnet-4-6',
    'deepseek-v4-pro', 'llama-4-maverick', 'mistral-medium-3.5',
    'qwen3.6-27b',
]

LANGUAGES = ['python', 'javascript', 'typescript', 'java', 'cpp', 'c_sharp']
CATEGORIES = [
    'api_usage', 'code2NL_NL2code', 'code_purpose_understanding',
    'low_context', 'pattern_matching', 'syntax_completion',
]


# ---------------------------------------------------------------------------
# Text cleaning helpers
# ---------------------------------------------------------------------------

def strip_trivial_characters(text):
    """Strip trailing semicolons, commas, and whitespace."""
    if not text:
        return ""
    return text.strip().rstrip(";").rstrip(",")


def index_of_first_non_space_char(text):
    """Return the index of the first non-whitespace character."""
    if not text:
        return 0
    for i, char in enumerate(text):
        if char not in (' ', '\n', '\t'):
            return i
    return len(text)


def remove_special_chars_fn(completion):
    """Remove special tokens like <|endoftext|>."""
    if not completion:
        return ""
    for spec in ['<|endoftext|>']:
        completion = completion.replace(spec, '')
    return completion


def get_fully_cleansed_first_line(text):
    """Extract and clean the first non-blank line of *text*."""
    if not text:
        return ""
    try:
        fl = text[index_of_first_non_space_char(text):].split('\n')[0].strip()
        return remove_special_chars_fn(strip_trivial_characters(fl))
    except Exception as e:
        print(f"Error in get_fully_cleansed_first_line: {e}")
        return ""


# ---------------------------------------------------------------------------
# Similarity computation
# ---------------------------------------------------------------------------

def calculate_cosine_similarity(text1, text2):
    """Calculate cosine similarity between two text snippets.

    Falls back from word-level to character n-gram to Jaccard set similarity
    when tokenisation produces an empty vocabulary.
    """
    if text1 == text2:
        return 1.0
    if not text1 or not text2:
        return 0.0

    try:
        vectorizer = CountVectorizer(analyzer='word', token_pattern=r'\b\w+\b')
        try:
            vectors = vectorizer.fit_transform([text1, text2])
            if vectors.shape[1] > 0:
                return cosine_similarity(vectors)[0, 1]
        except ValueError:
            pass

        # Fallback: character 1-3 grams
        vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 3))
        vectors = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(vectors)[0, 1]

    except Exception:
        # Last resort: Jaccard on character sets
        common = set(text1) & set(text2)
        union = set(text1) | set(text2)
        return len(common) / len(union) if union else 0.0


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_benchmark_files(benchmark_dir):
    """Load golden completions keyed by ``language/category`` then task id."""
    benchmark_data = {}

    for root, _dirs, files in os.walk(benchmark_dir):
        for fname in files:
            if not fname.endswith('.jsonl'):
                continue
            norm = root.replace('\\', '/')
            parts = norm.split('/')
            try:
                idx = parts.index('benchmark')
            except ValueError:
                continue
            if idx + 2 >= len(parts):
                continue
            language = parts[idx + 1]
            category = parts[idx + 2]
            key = f"{language}/{category}"
            benchmark_data[key] = {}

            with open(os.path.join(root, fname), 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        rec = json.loads(line.strip())
                        tid = rec.get('id')
                        if tid:
                            benchmark_data[key][tid] = rec
                    except json.JSONDecodeError:
                        continue

    return benchmark_data


# ---------------------------------------------------------------------------
# Core comparison
# ---------------------------------------------------------------------------

_NON_MODEL_FIELDS = {
    'id', 'testsource', 'language', 'prefix', 'suffix',
    'golden_completion', 'LLM_justification', 'assertions',
}


def load_and_compare_completions(completions_dir, benchmark_dir, debug=False):
    """Compare every model completion against the golden completion.

    Returns a nested dict: model -> {total, line0_exact_matches,
    cosine_similarities, avg_cosine, categories, languages}.
    """
    benchmark_data = load_benchmark_files(benchmark_dir)

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
        }),
    })

    test_cases = defaultdict(list) if debug else None

    for root, _dirs, files in os.walk(completions_dir):
        for fname in files:
            if not fname.endswith('.jsonl') or fname.endswith('_formatted.jsonl'):
                continue

            fpath = os.path.join(root, fname)
            norm = fpath.replace('\\', '/')
            parts = norm.split('/')

            comp_idx = -1
            for i, p in enumerate(parts):
                if 'completions' in p:
                    comp_idx = i
                    break
            if comp_idx < 0 or comp_idx + 2 >= len(parts):
                continue

            language = parts[comp_idx + 1]
            category = parts[comp_idx + 2]
            bkey = f"{language}/{category}"

            if bkey not in benchmark_data:
                continue

            print(f"Processing {fpath}")

            with open(fpath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue

                    tid = data.get('id')
                    if not tid or tid not in benchmark_data[bkey]:
                        continue

                    golden = benchmark_data[bkey][tid].get('golden_completion', '')
                    models_processed = set()

                    for field, _val in data.items():
                        if field in _NON_MODEL_FIELDS:
                            continue

                        model_name = None
                        if field.endswith('_completions'):
                            model_name = field[:-12]
                        elif field.endswith('_completion_0'):
                            mn = field[:-13]
                            if mn not in models_processed:
                                model_name = mn
                        elif '_completion_' in field:
                            continue

                        if not model_name or model_name in models_processed:
                            continue
                        models_processed.add(model_name)

                        # Collect completions
                        completions = []
                        if f'{model_name}_completions' in data and isinstance(data[f'{model_name}_completions'], list):
                            completions = data[f'{model_name}_completions']
                        elif f'{model_name}_completion_0' in data:
                            i = 0
                            while f'{model_name}_completion_{i}' in data:
                                completions.append(data[f'{model_name}_completion_{i}'])
                                i += 1
                        elif model_name in data:
                            completions = [data[model_name]]
                        if not completions:
                            continue

                        results[model_name]['total'] += 1
                        results[model_name]['categories'][category]['total'] += 1
                        results[model_name]['languages'][language]['total'] += 1

                        cosine_sims = []
                        any_line0 = False

                        for comp in completions:
                            if not comp:
                                cosine_sims.append(0.0)
                                continue
                            m_line0 = comp.strip().split('\n')[0].strip()
                            g_line0 = golden.strip().split('\n')[0].strip()
                            if m_line0 == g_line0:
                                any_line0 = True
                            cosine_sims.append(calculate_cosine_similarity(m_line0, g_line0))

                        if any_line0:
                            results[model_name]['line0_exact_matches'] += 1
                            results[model_name]['categories'][category]['line0_exact_matches'] += 1
                            results[model_name]['languages'][language]['line0_exact_matches'] += 1

                        avg_cs = sum(cosine_sims) / len(cosine_sims) if cosine_sims else 0.0
                        results[model_name]['cosine_similarities'].append(avg_cs)
                        results[model_name]['categories'][category]['cosine_similarities'].append(avg_cs)
                        results[model_name]['languages'][language]['cosine_similarities'].append(avg_cs)

                        if debug:
                            test_cases[model_name].append({
                                'test_id': tid,
                                'language': language,
                                'category': category,
                                'golden_completion': golden,
                                'model_completions': completions,
                                'individual_cosine_similarities': cosine_sims,
                                'avg_cosine_similarity': avg_cs,
                            })

    # Compute averages
    for model_name in results:
        cs = results[model_name]['cosine_similarities']
        results[model_name]['avg_cosine'] = sum(cs) / len(cs) if cs else 0
        for cat in results[model_name]['categories']:
            ccs = results[model_name]['categories'][cat]['cosine_similarities']
            results[model_name]['categories'][cat]['avg_cosine'] = sum(ccs) / len(ccs) if ccs else 0
        for lang in results[model_name]['languages']:
            lcs = results[model_name]['languages'][lang]['cosine_similarities']
            results[model_name]['languages'][lang]['avg_cosine'] = sum(lcs) / len(lcs) if lcs else 0

    if debug:
        return results, test_cases
    return results


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_results(results):
    """Turn the raw results dict into a JSON-friendly summary."""
    formatted = {}

    for model_name, mdata in results.items():
        if mdata['total'] == 0:
            continue

        fmt = {
            "overall": {
                "total_comparisons": mdata['total'],
                "line0_exact_matches": mdata['line0_exact_matches'],
                "line0_exact_match_rate": round(
                    mdata['line0_exact_matches'] / mdata['total'] * 100
                    if mdata['total'] > 0 else 0, 2),
                "avg_cosine": round(mdata['avg_cosine'], 2),
            },
            "categories": {},
            "languages": {},
        }

        for cat, cd in mdata['categories'].items():
            if cd['total'] > 0:
                fmt["categories"][cat] = {
                    "total_comparisons": cd['total'],
                    "line0_exact_matches": cd['line0_exact_matches'],
                    "line0_exact_match_rate": round(
                        cd['line0_exact_matches'] / cd['total'] * 100, 2),
                    "avg_cosine": round(cd['avg_cosine'], 2),
                }

        for lang, ld in mdata['languages'].items():
            if ld['total'] > 0:
                fmt["languages"][lang] = {
                    "total_comparisons": ld['total'],
                    "line0_exact_matches": ld['line0_exact_matches'],
                    "line0_exact_match_rate": round(
                        ld['line0_exact_matches'] / ld['total'] * 100, 2),
                    "avg_cosine": round(ld['avg_cosine'], 2),
                }

        formatted[model_name] = fmt

    return formatted


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_comparison(benchmark_base="../benchmark", completions_base="../completions",
                   results_file="similarity_results.json", debug=False):
    """Run the full comparison pipeline."""
    if debug:
        results, cases = load_and_compare_completions(completions_base, benchmark_base, debug=True)
        for model_name, items in cases.items():
            print(f"\n## MODEL: {model_name}")
            for i, c in enumerate(sorted(items, key=lambda x: x['avg_cosine_similarity'])[:10]):
                print(f"\n{i+1}. ID={c['test_id']}  lang={c['language']}  cat={c['category']}")
                print(f"   avg_cosine={c['avg_cosine_similarity']:.4f}")
        return

    results = load_and_compare_completions(completions_base, benchmark_base)
    formatted = format_results(results)

    if not formatted:
        print("No results found. Check benchmark and completions paths.")
        return

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(formatted, f, indent=2)
    print(f"Results saved to {results_file}")

    # Print summary table
    print("\n" + "=" * 80)
    print(f"{'Model':<25} {'Cosine':>8} {'Line0 EM%':>10} {'N':>6}")
    print("-" * 80)
    for model in sorted(formatted, key=lambda m: -formatted[m]['overall']['avg_cosine']):
        o = formatted[model]['overall']
        print(f"{model:<25} {o['avg_cosine']:>8.2f} {o['line0_exact_match_rate']:>9.1f}% {o['total_comparisons']:>6}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Evaluate code completions: cosine similarity and Line 0 exact match.')
    parser.add_argument('--completions', default="../completions",
                        help='Path to completions directory (default: ../completions)')
    parser.add_argument('--benchmark', default="../benchmark",
                        help='Path to benchmark directory (default: ../benchmark)')
    parser.add_argument('--results', default="similarity_results.json",
                        help='Output JSON file (default: similarity_results.json)')
    parser.add_argument('--debug', action='store_true',
                        help='Print 10 most dissimilar cases per model instead of full run')

    args = parser.parse_args()
    print(f"Benchmark: {args.benchmark}")
    print(f"Completions: {args.completions}")

    run_comparison(args.benchmark, args.completions, args.results, args.debug)
