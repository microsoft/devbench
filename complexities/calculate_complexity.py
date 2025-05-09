import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
import re
import tokenize
from io import StringIO
import numpy as np
from collections import Counter
import ast

def calculate_ast_depth_python(code_string):
    """Calculate AST depth for Python code."""
    try:
        tree = ast.parse(code_string)
        return get_ast_depth(tree)
    except SyntaxError:
        return estimate_code_depth(code_string)

def get_ast_depth(node):
    """Recursively calculate the depth of an AST node."""
    if not isinstance(node, ast.AST):
        return 0
    
    max_child_depth = 0
    for child in ast.iter_child_nodes(node):
        child_depth = get_ast_depth(child)
        max_child_depth = max(max_child_depth, child_depth)
    
    return max_child_depth + 1

def estimate_code_depth(code_string):
    """Estimate code depth for non-Python code using indentation and brackets."""
    try:
        # Calculate depth based on indentation
        lines = code_string.split('\n')
        indent_depth = 0
        max_indent_depth = 0
        bracket_depth = 0
        max_bracket_depth = 0
        
        # Track different types of brackets
        brackets = {
            '{': '}',
            '(': ')',
            '[': ']'
        }
        bracket_stack = []
        
        for line in lines:
            # Calculate indentation depth
            stripped_line = line.lstrip()
            if stripped_line:  # Skip empty lines
                current_indent = len(line) - len(stripped_line)
                indent_depth = current_indent // 4  # Assuming 4 spaces per indent level
                max_indent_depth = max(max_indent_depth, indent_depth)
            
            # Calculate bracket depth
            for char in line:
                if char in brackets:
                    bracket_stack.append(char)
                    bracket_depth += 1
                    max_bracket_depth = max(max_bracket_depth, bracket_depth)
                elif char in brackets.values():
                    if bracket_stack and brackets[bracket_stack[-1]] == char:
                        bracket_stack.pop()
                        bracket_depth -= 1
        
        # Combine both metrics, giving more weight to bracket depth
        return max(max_indent_depth, max_bracket_depth)
    
    except Exception:
        return 0

def calculate_shannon_entropy(tokens):
    """Calculate Shannon entropy of token distribution."""
    if not tokens:
        return 0.0
    
    # Count frequency of each token
    token_counts = Counter(tokens)
    total_tokens = sum(token_counts.values())
    
    # Calculate probabilities
    probabilities = [count / total_tokens for count in token_counts.values()]
    
    # Calculate Shannon entropy
    entropy = -sum(p * np.log2(p) for p in probabilities)
    return entropy

def calculate_unique_token_ratio(tokens):
    """Calculate the ratio of unique tokens to total tokens."""
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)

def get_tokens_list(code_string):
    """Get list of tokens from code string."""
    try:
        # Try Python's tokenizer first
        code_io = StringIO(code_string)
        try:
            tokens = []
            for token in tokenize.generate_tokens(code_io.readline):
                if token.type not in [tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.ENCODING]:
                    tokens.append(token.string)
            return tokens
        except tokenize.TokenError:
            # Fallback to regex for non-Python code
            return re.findall(r'[a-zA-Z_]\w*|[(){}\[\]<>]=?|[-+*/%=]|"[^"]*"|\'[^\']*\'|\S+', code_string)
    except Exception:
        # Final fallback
        return re.findall(r'[a-zA-Z_]\w*|[(){}\[\]<>]=?|[-+*/%=]|"[^"]*"|\'[^\']*\'|\S+', code_string)

def count_tokens(code_string):
    """Count the number of tokens in a code string."""
    return len(get_tokens_list(code_string))

def load_jsonl_data(file_path):
    """Load data from a JSONL file."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON line in {file_path}")
    return data

class CyclomaticComplexityVisitor(ast.NodeVisitor):
    """AST visitor to calculate cyclomatic complexity for Python code."""
    def __init__(self):
        self.complexity = 1  # Base complexity is 1

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
        # Count boolean operators (and, or) as decision points
        if isinstance(node.op, (ast.And, ast.Or)):
            self.complexity += len(node.values) - 1
        self.generic_visit(node)

def calculate_cyclomatic_complexity_python(code_string):
    """Calculate cyclomatic complexity for Python code using AST."""
    try:
        tree = ast.parse(code_string)
        visitor = CyclomaticComplexityVisitor()
        visitor.visit(tree)
        return visitor.complexity
    except SyntaxError:
        return estimate_cyclomatic_complexity(code_string)

def estimate_cyclomatic_complexity(code_string):
    """Estimate cyclomatic complexity for non-Python code using pattern matching."""
    try:
        complexity = 1  # Base complexity

        # Define patterns for control flow statements and boolean operators
        patterns = [
            r'\bif\b',                    # if statements
            r'\belse\s+if\b|\belif\b',    # else if statements
            r'\bfor\b',                   # for loops
            r'\bwhile\b',                 # while loops
            r'\bcase\b',                  # switch cases
            r'\bcatch\b',                 # try-catch blocks
            r'\?',                        # ternary operators
            r'\&\&|\|\|',                 # boolean operators
            r'\bbreak\b',                 # break statements
            r'\bcontinue\b',              # continue statements
            r'\breturn\b'                 # return statements (when not at end of block)
        ]

        # Count occurrences of each pattern
        for pattern in patterns:
            complexity += len(re.findall(pattern, code_string))

        return complexity

    except Exception:
        return 1

def calculate_max_indentation(code_string):
    """Calculate the maximum indentation level in the code."""
    try:
        lines = code_string.split('\n')
        max_indent = 0
        current_indent = 0
        
        # Common indentation patterns
        tab_size = 4  # Assuming 4 spaces per indent level
        
        for line in lines:
            if line.strip():  # Skip empty lines
                # Count leading spaces/tabs
                indent_spaces = len(line) - len(line.lstrip())
                
                # Handle tabs (convert to equivalent spaces)
                line_start = line[:indent_spaces]
                tab_count = line_start.count('\t')
                space_count = line_start.count(' ')
                
                # Calculate total indentation level
                total_spaces = tab_count * tab_size + space_count
                current_indent = total_spaces // tab_size
                
                max_indent = max(max_indent, current_indent)
        
        return max_indent
    
    except Exception:
        return 0

def calculate_nested_blocks(code_string):
    """Calculate statistics about nested blocks in the code."""
    try:
        lines = code_string.split('\n')
        nesting_levels = []
        current_indent = 0
        bracket_depth = 0
        
        # Track different types of brackets
        brackets = {
            '{': '}',
            '(': ')',
            '[': ']'
        }
        bracket_stack = []
        tab_size = 4  # Assuming 4 spaces per indent level
        
        for line in lines:
            if line.strip():  # Skip empty lines
                # Calculate indentation level
                indent_spaces = len(line) - len(line.lstrip())
                line_start = line[:indent_spaces]
                tab_count = line_start.count('\t')
                space_count = line_start.count(' ')
                total_spaces = tab_count * tab_size + space_count
                current_indent = total_spaces // tab_size
                
                # Calculate bracket depth for this line
                for char in line:
                    if char in brackets:
                        bracket_stack.append(char)
                        bracket_depth += 1
                    elif char in brackets.values():
                        if bracket_stack and brackets[bracket_stack[-1]] == char:
                            bracket_stack.pop()
                            bracket_depth -= 1
                
                # Use the maximum of indentation and bracket depth as the nesting level
                nesting_level = max(current_indent, bracket_depth)
                nesting_levels.append(nesting_level)
        
        if not nesting_levels:
            return 0.0
        
        # Calculate average nesting level
        return sum(nesting_levels) / len(nesting_levels)
    
    except Exception:
        return 0.0

def calculate_loc_metrics(code_string):
    """Calculate various Lines of Code (LOC) metrics."""
    try:
        lines = code_string.split('\n')
        total_lines = len(lines)
        
        # Count non-empty lines
        non_empty_lines = sum(1 for line in lines if line.strip())
        
        # Count comment lines for different languages
        comment_patterns = {
            'single': [r'^\s*#', r'^\s*//', r'^\s*--'],  # Python, JS/Java/C#/C++, SQL
            'multi_start': [r'^\s*/\*', r'^\s*<!--'],    # C-style, XML/HTML
            'multi_end': [r'\*/', r'-->']                # C-style, XML/HTML
        }
        
        comment_lines = 0
        in_multiline_comment = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # Skip empty lines
            if not stripped_line:
                continue
            
            # Check if we're in a multiline comment
            if in_multiline_comment:
                comment_lines += 1
                # Check for end of multiline comment
                for end_pattern in comment_patterns['multi_end']:
                    if re.search(end_pattern, stripped_line):
                        in_multiline_comment = False
                        break
                continue
            
            # Check for start of multiline comment
            for start_pattern in comment_patterns['multi_start']:
                if re.search(start_pattern, stripped_line):
                    in_multiline_comment = True
                    comment_lines += 1
                    # Check if multiline comment ends on same line
                    for end_pattern in comment_patterns['multi_end']:
                        if re.search(end_pattern, stripped_line):
                            in_multiline_comment = False
                            break
                    break
            
            # Check for single-line comments if not in multiline comment
            if not in_multiline_comment:
                for pattern in comment_patterns['single']:
                    if re.search(pattern, stripped_line):
                        comment_lines += 1
                        break
        
        # Calculate code lines (non-empty, non-comment lines)
        code_lines = non_empty_lines - comment_lines
        
        return {
            'total_lines': total_lines,
            'non_empty_lines': non_empty_lines,
            'comment_lines': comment_lines,
            'code_lines': code_lines,
            'comment_ratio': comment_lines / non_empty_lines if non_empty_lines > 0 else 0
        }
    
    except Exception:
        return {
            'total_lines': 0,
            'non_empty_lines': 0,
            'comment_lines': 0,
            'code_lines': 0,
            'comment_ratio': 0
        }

def calculate_api_usage_diversity(code_string):
    """Calculate API usage diversity metrics from code."""
    try:
        # Common patterns for API/function calls across languages
        patterns = {
            'function_calls': r'\b\w+\s*\([^)]*\)',  # Basic function calls
            'method_calls': r'\b\w+\.\w+\s*\([^)]*\)',  # Method calls
            'static_calls': r'\b\w+\.\w+\.\w+\s*\([^)]*\)',  # Static/namespaced calls
            'imports': r'(?:import|from|require|using|include)\s+[\w\s,\.]+',  # Import statements
            'new_objects': r'new\s+\w+',  # Object instantiation
        }
        
        api_calls = set()
        total_calls = 0
        
        for pattern_type, pattern in patterns.items():
            matches = re.findall(pattern, code_string)
            # Extract the function/method names without parameters
            for match in matches:
                if pattern_type == 'imports':
                    # Clean up import statements to get just the module names
                    cleaned = re.sub(r'(?:import|from|require|using|include)\s+', '', match)
                    modules = [m.strip() for m in cleaned.split(',')]
                    api_calls.update(modules)
                else:
                    # Extract the function/method name
                    name = re.search(r'\b\w+\s*\(', match)
                    if name:
                        api_calls.add(name.group().strip('('))
                total_calls += len(matches)
        
        return {
            'unique_apis': len(api_calls),
            'total_api_calls': total_calls,
            'api_diversity_ratio': len(api_calls) / total_calls if total_calls > 0 else 0
        }
    
    except Exception:
        return {
            'unique_apis': 0,
            'total_api_calls': 0,
            'api_diversity_ratio': 0
        }

def count_tests_in_assertions(assertions_string, language):
    """Count the number of test assertions in the assertions string based on language."""
    if not assertions_string:
        return 0
    
    # Debug: print sample of assertions string and language
    print(f"\nDEBUG - Language: {language}")
    sample = assertions_string[:100] + "..." if len(assertions_string) > 100 else assertions_string
    print(f"Sample assertions string: {sample}")
    
    # Different patterns for test assertions based on language and prompt conventions
    patterns = {
        "python": [
            r'\bassert\s+', # Assert statements
            r'\.assert\w+\(', # unittest assertions
            r'@pytest\.mark\.', # pytest decorators
            r'self\.fail\(', # unittest failures
            r'pytest\.raises\(', # pytest exception tests
            r'self\.assert', # unittest assertions
            r'assertTrue', r'assertEquals', r'assertFalse', # Common assertion methods
            r'@Test', # Test annotations
        ],
        "javascript": [
            r'\bexpect\(', # Jest/Jasmine expectations
            r'\.toBe\(', r'\.toEqual\(', r'\.toMatch\(', # Common Jest matchers
            r'\btest\(', r'\bit\(', # Jest/Mocha test blocks
            r'\bassert\.', # Node.js assert
            r'\.should\.', # Chai assertions
            r'describe\(', # Test suite declarations
            r'assert\(', # Basic assertions
        ],
        "typescript": [
            r'\bexpect\(', # Jest/Jasmine expectations
            r'\.toBe\(', r'\.toEqual\(', r'\.toMatch\(', # Common Jest matchers
            r'\btest\(', r'\bit\(', # Jest/Mocha test blocks
            r'\bassert\.', # ts-assert
            r'\.should\.', # Chai assertions
            r'describe\(', # Test suite declarations
            r'assert\(', # Basic assertions
        ],
        "java": [
            r'Assert\.', # JUnit assertions
            r'assert\w+\(', # JUnit/TestNG assertions
            r'@Test', # JUnit/TestNG test annotations
            r'\.assertEquals\(', r'\.assertTrue\(', r'\.assertFalse\(', # Common assertion methods
            r'org\.junit', # JUnit imports
            r'assertEquals', r'assertTrue', r'assertFalse', # Common assertion methods without class qualifier
        ],
        "c_sharp": [
            r'Debug\.Assert\(', # C# Debug.Assert as specified in the prompts
            r'Assert\.', # NUnit/MSTest assertions
            r'\[Test\]', r'\[Fact\]', # Common test attributes
            r'\.Should\.', # FluentAssertions
            r'\.Equals\(', r'\.AreEqual\(', # Common assertion methods
            r'Debug\.Assert', # The specific assertion method mentioned in C# prompts
            r'Microsoft\.VisualStudio\.TestTools', # MSTest namespace
            r'\.IsTrue\(', r'\.IsFalse\(', # Common assertion methods
        ],
        "cpp": [
            r'ASSERT_', r'EXPECT_', # Google Test macros
            r'CHECK_', r'REQUIRE_', # Catch2 macros
            r'TEST\(', r'TEST_CASE\(', # Test case definitions
            r'assert\(', # Standard C assert
            r'BOOST_TEST', r'BOOST_CHECK', # Boost.Test
            r'#include <gtest/', # Google Test includes
            r'#include <catch2/', # Catch2 includes
        ]
    }
    
    # Use the appropriate patterns for the language
    language_patterns = patterns.get(language, patterns["python"])
    
    # Count the occurrences of each pattern
    test_count = 0
    print(f"Checking patterns for {language}:")
    for pattern in language_patterns:
        matches = re.findall(pattern, assertions_string)
        if matches:
            print(f"  Pattern '{pattern}' found {len(matches)} matches: {matches[:2]}")
        test_count += len(matches)
    
    result = max(1, test_count) if test_count > 0 else 0  # Return at least 1 if any tests were found, otherwise 0
    print(f"Total test count for {language}: {result}")
    return result

def analyze_benchmark_data(metrics=None):
    """
    Analyze complexity metrics in benchmark data.
    
    Parameters:
        metrics (dict): Dictionary of metrics to compute and visualize.
                       Set a metric to True to enable it, False to disable it.
                       If None, only the essential metrics will be enabled.
    """
    # Set default metrics - only essential ones enabled by default
    default_metrics = {
        'prefix_length': True,     # Essential
        'prefix_char_length': True,  # New metric for character count
        'token_count': True,       # Essential
        'ast_depth': True,         # Essential
        'cyclomatic': True,        # Essential
        'unique_apis': True,       # Essential
        
        # Optional metrics - disabled by default
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
        
        # New metrics requested by user
        'golden_length': True,          # Lines in golden completion
        'golden_token_count': True,     # Tokens in golden completion
        'total_length': True,           # Total lines (prefix + golden + suffix + assertions)
        'total_token_count': True,      # Total tokens (prefix + golden + suffix + assertions)
        'test_count': True,             # Number of tests per test case
    }
    
    # Use provided metrics if any, otherwise use defaults
    if metrics is None:
        metrics = default_metrics
    else:
        # Update defaults with provided metrics
        for key, value in metrics.items():
            if key in default_metrics:
                default_metrics[key] = value
        metrics = default_metrics
        
    # Find benchmark directory
    benchmark_dir = Path("../benchmark")
    if not benchmark_dir.exists():
        print(f"Benchmark directory not found at {benchmark_dir}")
        return
    
    # Data structure to hold results
    results = {
        "python": {},
        "javascript": {},
        "c_sharp": {},
        "cpp": {},
        "typescript": {},
        "java": {}
    }
    
    # Initialize metric arrays based on enabled metrics
    for language in results:
        for metric_name, enabled in metrics.items():
            if enabled:
                results[language][metric_name] = []
    
    # Walk through benchmark directory
    for root, dirs, files in os.walk(benchmark_dir):
        for file in files:
            if file.endswith(".jsonl") and not file.endswith("_formatted.jsonl"):
                file_path = os.path.join(root, file)
                
                # Determine language from path
                language = None
                for lang in results.keys():
                    if lang in file_path.lower():
                        language = lang
                        break
                
                if language:
                    try:
                        data = load_jsonl_data(file_path)
                        for item in data:
                            if "prefix" in item:
                                prefix = item["prefix"]
                                golden = item.get("golden_completion", "")  # Get golden completion if available
                                suffix = item.get("suffix", "")  # Get suffix if available
                                assertions = item.get("assertions", "")  # Get assertions if available
                                
                                # Calculate combined total code
                                total_code = prefix + golden + suffix + assertions
                                
                                # Calculate only enabled metrics
                                metrics_data = {}
                                
                                # Prefix length - essential
                                if metrics['prefix_length']:
                                    metrics_data['prefix_length'] = len(prefix.split("\n"))
                                
                                # Prefix character length
                                if metrics['prefix_char_length']:
                                    metrics_data['prefix_char_length'] = len(prefix)
                                
                                # Golden completion length
                                if metrics['golden_length']:
                                    metrics_data['golden_length'] = len(golden.split("\n")) if golden else 0
                                
                                # Total length
                                if metrics['total_length']:
                                    metrics_data['total_length'] = len(total_code.split("\n"))
                                
                                # Token count for prefix
                                if metrics['token_count']:
                                    tokens_list = get_tokens_list(prefix)
                                    metrics_data['token_count'] = len(tokens_list)
                                    
                                    # Token entropy - optional
                                    if metrics['token_entropy']:
                                        metrics_data['token_entropy'] = calculate_shannon_entropy(tokens_list)
                                    
                                    # Unique token ratio - optional
                                    if metrics['unique_token_ratio']:
                                        metrics_data['unique_token_ratio'] = calculate_unique_token_ratio(tokens_list)
                                
                                # Token count for golden completion
                                if metrics['golden_token_count']:
                                    golden_tokens = get_tokens_list(golden) if golden else []
                                    metrics_data['golden_token_count'] = len(golden_tokens)
                                
                                # Token count for total
                                if metrics['total_token_count']:
                                    total_tokens = get_tokens_list(total_code)
                                    metrics_data['total_token_count'] = len(total_tokens)
                                
                                # Count tests in assertions
                                if metrics['test_count']:
                                    # Check each field for assertions
                                    prefix_count = count_tests_in_assertions(prefix, language)
                                    suffix_count = count_tests_in_assertions(suffix, language)
                                    assertions_count = count_tests_in_assertions(assertions, language)
                                    
                                    # Sum up all tests found across all fields
                                    metrics_data['test_count'] = prefix_count + suffix_count + assertions_count
                                    print(f"Final test count for {language}: {metrics_data['test_count']} (prefix: {prefix_count}, suffix: {suffix_count}, assertions: {assertions_count})")
                                
                                # AST depth - essential
                                if metrics['ast_depth']:
                                    if language == "python":
                                        metrics_data['ast_depth'] = calculate_ast_depth_python(prefix)
                                    else:
                                        metrics_data['ast_depth'] = estimate_code_depth(prefix)
                                
                                # Cyclomatic complexity - essential
                                if metrics['cyclomatic']:
                                    if language == "python":
                                        metrics_data['cyclomatic'] = calculate_cyclomatic_complexity_python(prefix)
                                    else:
                                        metrics_data['cyclomatic'] = estimate_cyclomatic_complexity(prefix)
                                
                                # Maximum indentation - optional
                                if metrics['max_indent']:
                                    metrics_data['max_indent'] = calculate_max_indentation(prefix)
                                
                                # Average nesting - optional
                                if metrics['avg_nesting']:
                                    metrics_data['avg_nesting'] = calculate_nested_blocks(prefix)
                                
                                # LOC metrics - optional
                                if any(metrics[m] for m in ['total_lines', 'non_empty_lines', 'comment_lines', 'code_lines', 'comment_ratio']):
                                    loc_metrics = calculate_loc_metrics(prefix)
                                    
                                    if metrics['total_lines']:
                                        metrics_data['total_lines'] = loc_metrics['total_lines']
                                    if metrics['non_empty_lines']:
                                        metrics_data['non_empty_lines'] = loc_metrics['non_empty_lines']
                                    if metrics['comment_lines']:
                                        metrics_data['comment_lines'] = loc_metrics['comment_lines']
                                    if metrics['code_lines']:
                                        metrics_data['code_lines'] = loc_metrics['code_lines']
                                    if metrics['comment_ratio']:
                                        metrics_data['comment_ratio'] = loc_metrics['comment_ratio']
                                
                                # API usage metrics
                                if any(metrics[m] for m in ['unique_apis', 'total_api_calls', 'api_diversity_ratio']):
                                    api_metrics = calculate_api_usage_diversity(prefix)
                                    
                                    if metrics['unique_apis']:
                                        metrics_data['unique_apis'] = api_metrics['unique_apis']
                                    if metrics['total_api_calls']:
                                        metrics_data['total_api_calls'] = api_metrics['total_api_calls']
                                    if metrics['api_diversity_ratio']:
                                        metrics_data['api_diversity_ratio'] = api_metrics['api_diversity_ratio']
                                
                                # Store computed metrics
                                for metric_name, value in metrics_data.items():
                                    results[language][metric_name].append(value)
                    except Exception as e:
                        print(f"Error processing {file_path}: {str(e)}")
    
    # Create DataFrames for visualization
    dataframes = {}
    
    # Create dataframes only for enabled metrics
    for metric_name, enabled in metrics.items():
        if enabled:
            metric_data = []
            for language, data in results.items():
                if metric_name in data:
                    for value in data[metric_name]:
                        metric_data.append({"Language": language, metric_name: value})
            
            if metric_data:
                dataframes[metric_name] = pd.DataFrame(metric_data)
    
    # Generate statistics for enabled metrics
    print("\n===== SUMMARY OF METRICS =====")
    
    # Store averages for final summary
    averages = {}
    
    for metric_name, df in dataframes.items():
        if df is not None and not df.empty:
            print(f"\n{metric_name.replace('_', ' ').title()} Statistics:")
            stats = df.groupby("Language")[metric_name].describe()
            print(stats)
            
            # Calculate and display average across all languages
            overall_mean = df[metric_name].mean()
            print(f"\nAverage {metric_name.replace('_', ' ').title()} across all languages: {overall_mean:.2f}")
            
            # Store average for final summary
            averages[metric_name] = overall_mean
    
    print(f"\nTotal number of test cases analyzed: {len(next(iter(dataframes.values())))}")
    
    # Print compact summary of all averages
    print("\n===== COMPACT SUMMARY =====")
    for metric_name, avg_value in averages.items():
        print(f"Average {metric_name.replace('_', ' ').title()}: {avg_value:.2f}")
    
    # No plots will be generated

if __name__ == "__main__":
    # Disable plot generation and only print selected metrics
    metrics = {
        'prefix_length': True,          # Lines in prefix
        'prefix_char_length': False,     # Characters in prefix
        'token_count': True,            # Tokens in prefix
        'ast_depth': False,             # AST depth
        'cyclomatic': True,             # Cyclomatic complexity
        'unique_apis': False,           # Unique APIs
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
        'golden_length': True,          # Lines in golden completion
        'golden_token_count': True,     # Tokens in golden completion
        'total_length': True,           # Total lines (prefix + golden + suffix + assertions)
        'total_token_count': True,      # Total tokens (prefix + golden + suffix + assertions)
        'test_count': False,            # Number of tests per test case
    }
    
    # Create DataFrames for visualization but don't generate plots
    dataframes = {}
    
    # Analyze benchmark data with modified metrics
    analyze_benchmark_data(metrics)


