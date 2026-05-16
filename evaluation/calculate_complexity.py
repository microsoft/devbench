"""Compute benchmark complexity statistics: LOC, tokens, cyclomatic complexity, entropy.

Walks the benchmark/ directory structure and computes per-language and overall
complexity metrics for all tasks.  Outputs a summary table to stdout.

Usage:
    python calculate_complexity.py
"""

import os
import json
import re
import ast
import tokenize
from io import StringIO
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# AST / depth helpers
# ---------------------------------------------------------------------------

def get_ast_depth(node):
    """Recursively compute the depth of a Python AST node."""
    if not isinstance(node, ast.AST):
        return 0
    return 1 + max((get_ast_depth(c) for c in ast.iter_child_nodes(node)), default=0)


def calculate_ast_depth_python(code_string):
    """Return AST depth for Python code, falling back to heuristic."""
    try:
        return get_ast_depth(ast.parse(code_string))
    except SyntaxError:
        return estimate_code_depth(code_string)


def estimate_code_depth(code_string):
    """Estimate nesting depth for non-Python code using indentation and brackets."""
    try:
        lines = code_string.split('\n')
        max_indent = 0
        bracket_depth = 0
        max_bracket = 0
        openers = {'{': '}', '(': ')', '[': ']'}
        stack = []

        for line in lines:
            stripped = line.lstrip()
            if stripped:
                indent = (len(line) - len(stripped)) // 4
                max_indent = max(max_indent, indent)
            for ch in line:
                if ch in openers:
                    stack.append(ch)
                    bracket_depth += 1
                    max_bracket = max(max_bracket, bracket_depth)
                elif ch in openers.values():
                    if stack and openers[stack[-1]] == ch:
                        stack.pop()
                        bracket_depth -= 1

        return max(max_indent, max_bracket)
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def get_tokens_list(code_string):
    """Tokenise *code_string* and return a list of token strings."""
    try:
        tokens = []
        for tok in tokenize.generate_tokens(StringIO(code_string).readline):
            if tok.type not in (tokenize.COMMENT, tokenize.NL,
                                tokenize.NEWLINE, tokenize.ENCODING):
                tokens.append(tok.string)
        return tokens
    except tokenize.TokenError:
        pass
    except Exception:
        pass
    # Fallback regex tokeniser (for non-Python)
    return re.findall(
        r'[a-zA-Z_]\w*|[(){}\[\]<>]=?|[-+*/%=]|"[^"]*"|\'[^\']*\'|\S+',
        code_string,
    )


def count_tokens(code_string):
    """Return the number of tokens in *code_string*."""
    return len(get_tokens_list(code_string))


def calculate_shannon_entropy(tokens):
    """Compute Shannon entropy (bits) of the token distribution."""
    if not tokens:
        return 0.0
    counts = Counter(tokens)
    total = sum(counts.values())
    probs = [c / total for c in counts.values()]
    return -sum(p * np.log2(p) for p in probs)


def calculate_unique_token_ratio(tokens):
    """Fraction of unique tokens relative to total."""
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


# ---------------------------------------------------------------------------
# Cyclomatic complexity
# ---------------------------------------------------------------------------

class CyclomaticComplexityVisitor(ast.NodeVisitor):
    """Count decision points to estimate cyclomatic complexity (Python)."""

    def __init__(self):
        self.complexity = 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Break(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Continue(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        if isinstance(node.op, (ast.And, ast.Or)):
            self.complexity += len(node.values) - 1
        self.generic_visit(node)


def calculate_cyclomatic_complexity_python(code_string):
    """Cyclomatic complexity via AST for Python code."""
    try:
        tree = ast.parse(code_string)
        v = CyclomaticComplexityVisitor()
        v.visit(tree)
        return v.complexity
    except SyntaxError:
        return estimate_cyclomatic_complexity(code_string)


def estimate_cyclomatic_complexity(code_string):
    """Heuristic cyclomatic complexity for non-Python code via regex."""
    try:
        complexity = 1
        patterns = [
            r'\bif\b', r'\belse\s+if\b|\belif\b', r'\bfor\b', r'\bwhile\b',
            r'\bcase\b', r'\bcatch\b', r'\?', r'\&\&|\|\|',
            r'\bbreak\b', r'\bcontinue\b', r'\breturn\b',
        ]
        for pat in patterns:
            complexity += len(re.findall(pat, code_string))
        return complexity
    except Exception:
        return 1


# ---------------------------------------------------------------------------
# LOC metrics
# ---------------------------------------------------------------------------

def calculate_loc_metrics(code_string):
    """Return dict with total_lines, non_empty_lines, comment_lines, code_lines, comment_ratio."""
    try:
        lines = code_string.split('\n')
        total = len(lines)
        non_empty = sum(1 for l in lines if l.strip())

        comment_patterns_single = [r'^\s*#', r'^\s*//', r'^\s*--']
        comment_patterns_start = [r'^\s*/\*', r'^\s*<!--']
        comment_patterns_end = [r'\*/', r'-->']

        comment_count = 0
        in_multi = False

        for line in lines:
            s = line.strip()
            if not s:
                continue
            if in_multi:
                comment_count += 1
                if any(re.search(p, s) for p in comment_patterns_end):
                    in_multi = False
                continue
            if any(re.search(p, s) for p in comment_patterns_start):
                in_multi = True
                comment_count += 1
                if any(re.search(p, s) for p in comment_patterns_end):
                    in_multi = False
                continue
            if any(re.search(p, s) for p in comment_patterns_single):
                comment_count += 1

        code_lines = non_empty - comment_count
        return {
            'total_lines': total,
            'non_empty_lines': non_empty,
            'comment_lines': comment_count,
            'code_lines': code_lines,
            'comment_ratio': comment_count / non_empty if non_empty else 0,
        }
    except Exception:
        return {'total_lines': 0, 'non_empty_lines': 0, 'comment_lines': 0,
                'code_lines': 0, 'comment_ratio': 0}


# ---------------------------------------------------------------------------
# Indentation / nesting
# ---------------------------------------------------------------------------

def calculate_max_indentation(code_string):
    """Maximum indentation level (in units of 4-space tabs)."""
    try:
        max_indent = 0
        for line in code_string.split('\n'):
            if line.strip():
                raw = line[:len(line) - len(line.lstrip())]
                spaces = raw.count('\t') * 4 + raw.count(' ')
                max_indent = max(max_indent, spaces // 4)
        return max_indent
    except Exception:
        return 0


def calculate_nested_blocks(code_string):
    """Average nesting level across non-empty lines."""
    try:
        lines = code_string.split('\n')
        levels = []
        bracket_depth = 0
        openers = {'{': '}', '(': ')', '[': ']'}
        stack = []

        for line in lines:
            if not line.strip():
                continue
            raw = line[:len(line) - len(line.lstrip())]
            indent = (raw.count('\t') * 4 + raw.count(' ')) // 4
            for ch in line:
                if ch in openers:
                    stack.append(ch)
                    bracket_depth += 1
                elif ch in openers.values():
                    if stack and openers[stack[-1]] == ch:
                        stack.pop()
                        bracket_depth -= 1
            levels.append(max(indent, bracket_depth))

        return sum(levels) / len(levels) if levels else 0.0
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# API usage diversity
# ---------------------------------------------------------------------------

def calculate_api_usage_diversity(code_string):
    """Count unique APIs, total calls, and diversity ratio."""
    try:
        patterns = {
            'function_calls': r'\b\w+\s*\([^)]*\)',
            'method_calls': r'\b\w+\.\w+\s*\([^)]*\)',
            'static_calls': r'\b\w+\.\w+\.\w+\s*\([^)]*\)',
            'imports': r'(?:import|from|require|using|include)\s+[\w\s,\.]+',
            'new_objects': r'new\s+\w+',
        }
        apis = set()
        total = 0
        for ptype, pat in patterns.items():
            matches = re.findall(pat, code_string)
            if ptype == 'imports':
                for m in matches:
                    cleaned = re.sub(r'(?:import|from|require|using|include)\s+', '', m)
                    apis.update(c.strip() for c in cleaned.split(','))
            else:
                for m in matches:
                    name = re.search(r'\b\w+\s*\(', m)
                    if name:
                        apis.add(name.group().strip('('))
            total += len(matches)
        return {
            'unique_apis': len(apis),
            'total_api_calls': total,
            'api_diversity_ratio': len(apis) / total if total else 0,
        }
    except Exception:
        return {'unique_apis': 0, 'total_api_calls': 0, 'api_diversity_ratio': 0}


# ---------------------------------------------------------------------------
# Test-count heuristic
# ---------------------------------------------------------------------------

def count_tests_in_assertions(assertions_string, language):
    """Estimate the number of test assertions in *assertions_string*."""
    if not assertions_string:
        return 0

    patterns_map = {
        "python": [r'\bassert\s+', r'\.assert\w+\(', r'pytest\.raises\('],
        "javascript": [r'\bexpect\(', r'\bassert\.', r'assert\('],
        "typescript": [r'\bexpect\(', r'\bassert\.', r'assert\('],
        "java": [r'Assert\.', r'assert\w+\(', r'@Test'],
        "c_sharp": [r'Debug\.Assert\(', r'Assert\.', r'\[Test\]', r'\[Fact\]'],
        "cpp": [r'ASSERT_', r'EXPECT_', r'assert\('],
    }

    pats = patterns_map.get(language, patterns_map["python"])
    total = sum(len(re.findall(p, assertions_string)) for p in pats)
    return max(1, total) if total > 0 else 0


# ---------------------------------------------------------------------------
# JSONL loader
# ---------------------------------------------------------------------------

def load_jsonl_data(file_path):
    """Load lines from a JSONL file into a list of dicts."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                pass
    return data


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_benchmark_data(metrics=None):
    """Compute complexity metrics and print per-language statistics.

    Parameters
    ----------
    metrics : dict, optional
        Mapping of metric name -> bool.  Only enabled (True) metrics are
        computed.  Defaults to a sensible set.
    """
    default_metrics = {
        'prefix_length': True,
        'prefix_char_length': False,
        'token_count': True,
        'ast_depth': True,
        'cyclomatic': True,
        'unique_apis': False,
        'token_entropy': False,
        'unique_token_ratio': False,
        'max_indent': False,
        'avg_nesting': False,
        'total_lines': False,
        'non_empty_lines': False,
        'comment_lines': False,
        'code_lines': False,
        'comment_ratio': False,
        'total_api_calls': False,
        'api_diversity_ratio': False,
        'golden_length': True,
        'golden_token_count': True,
        'total_length': True,
        'total_token_count': True,
        'test_count': False,
    }
    if metrics is not None:
        for k, v in metrics.items():
            if k in default_metrics:
                default_metrics[k] = v
    metrics = default_metrics

    benchmark_dir = Path("../benchmark")
    if not benchmark_dir.exists():
        print(f"Benchmark directory not found at {benchmark_dir}")
        return

    all_languages = ["python", "javascript", "c_sharp", "cpp", "typescript", "java"]
    results = {lang: {} for lang in all_languages}

    for lang in results:
        for name, enabled in metrics.items():
            if enabled:
                results[lang][name] = []

    for root, _dirs, files in os.walk(benchmark_dir):
        for fname in files:
            if not fname.endswith(".jsonl") or fname.endswith("_formatted.jsonl"):
                continue
            fpath = os.path.join(root, fname)

            language = None
            for lang in all_languages:
                if lang in fpath.lower():
                    language = lang
                    break
            if language is None:
                continue

            try:
                data = load_jsonl_data(fpath)
            except Exception as e:
                print(f"Error reading {fpath}: {e}")
                continue

            for item in data:
                prefix = item.get("prefix", "")
                golden = item.get("golden_completion", "")
                suffix = item.get("suffix", "")
                assertions = item.get("assertions", "")
                total_code = prefix + golden + suffix + assertions

                md = {}

                if metrics['prefix_length']:
                    md['prefix_length'] = len(prefix.split("\n"))
                if metrics['prefix_char_length']:
                    md['prefix_char_length'] = len(prefix)
                if metrics['golden_length']:
                    md['golden_length'] = len(golden.split("\n")) if golden else 0
                if metrics['total_length']:
                    md['total_length'] = len(total_code.split("\n"))

                if metrics['token_count']:
                    toks = get_tokens_list(prefix)
                    md['token_count'] = len(toks)
                    if metrics['token_entropy']:
                        md['token_entropy'] = calculate_shannon_entropy(toks)
                    if metrics['unique_token_ratio']:
                        md['unique_token_ratio'] = calculate_unique_token_ratio(toks)

                if metrics['golden_token_count']:
                    md['golden_token_count'] = len(get_tokens_list(golden)) if golden else 0
                if metrics['total_token_count']:
                    md['total_token_count'] = len(get_tokens_list(total_code))

                if metrics['test_count']:
                    md['test_count'] = (
                        count_tests_in_assertions(prefix, language)
                        + count_tests_in_assertions(suffix, language)
                        + count_tests_in_assertions(assertions, language)
                    )

                if metrics['ast_depth']:
                    if language == "python":
                        md['ast_depth'] = calculate_ast_depth_python(prefix)
                    else:
                        md['ast_depth'] = estimate_code_depth(prefix)

                if metrics['cyclomatic']:
                    if language == "python":
                        md['cyclomatic'] = calculate_cyclomatic_complexity_python(prefix)
                    else:
                        md['cyclomatic'] = estimate_cyclomatic_complexity(prefix)

                if metrics['max_indent']:
                    md['max_indent'] = calculate_max_indentation(prefix)
                if metrics['avg_nesting']:
                    md['avg_nesting'] = calculate_nested_blocks(prefix)

                if any(metrics[m] for m in ('total_lines', 'non_empty_lines',
                                            'comment_lines', 'code_lines', 'comment_ratio')):
                    loc = calculate_loc_metrics(prefix)
                    for k in ('total_lines', 'non_empty_lines', 'comment_lines',
                              'code_lines', 'comment_ratio'):
                        if metrics[k]:
                            md[k] = loc[k]

                if any(metrics[m] for m in ('unique_apis', 'total_api_calls', 'api_diversity_ratio')):
                    api = calculate_api_usage_diversity(prefix)
                    for k in ('unique_apis', 'total_api_calls', 'api_diversity_ratio'):
                        if metrics[k]:
                            md[k] = api[k]

                for name, val in md.items():
                    results[language][name].append(val)

    # Build DataFrames and print stats
    dataframes = {}
    for name, enabled in metrics.items():
        if not enabled:
            continue
        rows = []
        for lang, data in results.items():
            if name in data:
                for v in data[name]:
                    rows.append({"Language": lang, name: v})
        if rows:
            dataframes[name] = pd.DataFrame(rows)

    print("\n===== SUMMARY OF METRICS =====")
    averages = {}
    for name, df in dataframes.items():
        if df.empty:
            continue
        print(f"\n{name.replace('_', ' ').title()} Statistics:")
        print(df.groupby("Language")[name].describe())
        overall = df[name].mean()
        averages[name] = overall
        print(f"\nOverall average: {overall:.2f}")

    total_tasks = len(next(iter(dataframes.values()))) if dataframes else 0
    print(f"\nTotal tasks analysed: {total_tasks}")

    print("\n===== COMPACT SUMMARY =====")
    for name, avg in averages.items():
        print(f"  {name.replace('_', ' ').title()}: {avg:.2f}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    analyze_benchmark_data({
        'prefix_length': True,
        'prefix_char_length': False,
        'token_count': True,
        'ast_depth': False,
        'cyclomatic': True,
        'unique_apis': False,
        'token_entropy': False,
        'unique_token_ratio': False,
        'max_indent': False,
        'avg_nesting': False,
        'total_lines': False,
        'non_empty_lines': False,
        'comment_lines': False,
        'code_lines': False,
        'comment_ratio': False,
        'total_api_calls': False,
        'api_diversity_ratio': False,
        'golden_length': True,
        'golden_token_count': True,
        'total_length': True,
        'total_token_count': True,
        'test_count': False,
    })
