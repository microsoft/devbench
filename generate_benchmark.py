# Note: Before using this code, log in to Azure using the Azure CLI and set the subscription to the one you want to use.

import os
import base64
from openai import AzureOpenAI  
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import dotenv
from typing import Dict, List, Tuple, Set
import re
import ast
import subprocess
import sys
import importlib
import pkg_resources
from prompts import python_prompts, javascript_prompts, c_sharp_prompts, cpp_prompts, typescript_prompts, java_prompts
from tree_sitter_languages import get_parser
import json
import argparse
import time

dotenv.load_dotenv()

def execute_python_test_cases(jsonl_files: List[str], verbose=True, report_file=None) -> Dict:
    """
    Execute Python test cases from the benchmark JSONL files.
    
    Args:
        jsonl_files: List of JSONL file paths to process
        verbose: Whether to print detailed information during execution
        report_file: Path to file for saving detailed test results
        
    Returns:
        Dict: Summary of execution results
    """
    results = {
        "total_cases": 0,
        "successful_cases": 0,
        "failed_cases": 0,
        "failures": []
    }
    
    # Open report file if specified
    report_fp = None
    if report_file:
        try:
            report_fp = open(report_file, 'w', encoding='utf-8')
            report_fp.write("PYTHON BENCHMARK TEST RESULTS\n")
            report_fp.write("=" * 80 + "\n\n")
        except Exception as e:
            print(f"Error opening report file: {e}")
            report_fp = None
    
    try:
        for jsonl_file in jsonl_files:
            if verbose:
                print(f"\nProcessing {jsonl_file}...")
            
            if report_fp:
                report_fp.write(f"\nFILE: {jsonl_file}\n")
                report_fp.write("-" * 80 + "\n")
            
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        try:
                            test_case = json.loads(line)
                            results["total_cases"] += 1
                            
                            # Debug test case details
                            if verbose:
                                print(f"Running test case #{i} (ID: {test_case['id']})...")
                            
                            # Get test case components
                            prefix = test_case["prefix"]
                            golden_completion = test_case["golden_completion"]
                            suffix = test_case["suffix"]
                            assertions = test_case.get("assertions", "")
                            
                            # Write test case info to report
                            if report_fp:
                                report_fp.write(f"\nTEST CASE #{i} (ID: {test_case['id']})\n")
                                report_fp.write(f"  Source: {test_case.get('testsource', 'Unknown')}\n\n")
                            
                            # Execute the test case
                            success, error_msg = run_python_test_case(
                                prefix, golden_completion, suffix, assertions, verbose
                            )
                            
                            if success:
                                results["successful_cases"] += 1
                                if verbose:
                                    print(f"Test case #{i} (ID: {test_case['id']}) passed ✓")
                                if report_fp:
                                    report_fp.write("  RESULT: PASS\n\n")
                            else:
                                results["failed_cases"] += 1
                                results["failures"].append({
                                    "file": jsonl_file,
                                    "test_id": test_case['id'],
                                    "error": error_msg
                                })
                                if verbose:
                                    print(f"Test case #{i} (ID: {test_case['id']}) failed")
                                    print(f"  Error: {error_msg}")
                                if report_fp:
                                    report_fp.write("  RESULT: FAIL\n")
                                    report_fp.write(f"  ERROR: {error_msg}\n\n")
                                    
                                    # Include the test case code in the report for debugging
                                    report_fp.write("  PREFIX CODE:\n")
                                    report_fp.write("  " + prefix.replace("\n", "\n  ") + "\n\n")
                                    report_fp.write("  GOLDEN COMPLETION:\n")
                                    report_fp.write("  " + golden_completion.replace("\n", "\n  ") + "\n\n")
                                    report_fp.write("  SUFFIX CODE:\n")
                                    report_fp.write("  " + suffix.replace("\n", "\n  ") + "\n\n")
                                    report_fp.write("  ASSERTIONS:\n")
                                    report_fp.write("  " + assertions.replace("\n", "\n  ") + "\n\n")
                        
                        except Exception as e:
                            results["failed_cases"] += 1
                            results["failures"].append({
                                "file": jsonl_file,
                                "test_id": f"{i}",
                                "error": str(e)
                            })
                            if verbose:
                                print(f"Error processing test case #{i}: {str(e)}")
                            if report_fp:
                                report_fp.write(f"\nTEST CASE #{i}\n")
                                report_fp.write("  RESULT: ERROR\n")
                                report_fp.write(f"  ERROR: {str(e)}\n\n")
            except Exception as e:
                print(f"Error processing file {jsonl_file}: {str(e)}")
                if report_fp:
                    report_fp.write(f"\nERROR processing file: {str(e)}\n\n")
    
    finally:
        # Write summary to report file
        if report_fp:
            try:
                report_fp.write("\n" + "="*80 + "\n")
                report_fp.write("EXECUTION SUMMARY\n")
                report_fp.write("="*80 + "\n")
                report_fp.write(f"Total test cases: {results['total_cases']}\n")
                report_fp.write(f"Successful test cases: {results['successful_cases']}\n")
                report_fp.write(f"Failed test cases: {results['failed_cases']}\n\n")
                
                if results["failures"]:
                    report_fp.write("Failed test cases:\n")
                    for i, failure in enumerate(results["failures"], 1):
                        report_fp.write(f"  {i}. {failure['file']} - Test ID: {failure['test_id']}\n")
                        report_fp.write(f"     Error: {failure['error']}\n\n")
            except Exception as e:
                print(f"Error writing summary to report file: {e}")
            
            # Close report file
            try:
                report_fp.close()
                if verbose:
                    print(f"\nDetailed test results saved to {report_file}")
            except Exception as e:
                print(f"Error closing report file: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    print(f"Total test cases: {results['total_cases']}")
    print(f"Successful test cases: {results['successful_cases']}")
    print(f"Failed test cases: {results['failed_cases']}")
    
    if results["failures"]:
        print("\nFailed test cases:")
        for i, failure in enumerate(results["failures"][:10], 1):  # Show first 10 failures
            print(f"  {i}. {failure['file']} - Test ID: {failure['test_id']}")
            print(f"     Error: {failure['error']}")
        
        if len(results["failures"]) > 10:
            print(f"  ... and {len(results['failures']) - 10} more failures")
    
    return results

def run_python_test_case(prefix: str, golden_completion: str, suffix: str, 
                         assertions: str = "", verbose=True, timeout=30) -> Tuple[bool, str]:
    """
    Run a Python test case by creating a temporary file and executing it.
    
    Args:
        prefix: Prefix code
        golden_completion: Golden completion code
        suffix: Suffix code
        assertions: Assertion code
        verbose: Whether to print detailed information
        timeout: Maximum execution time in seconds before killing the process
        
    Returns:
        Tuple containing success flag and error message if any
    """
    # Add matplotlib non-interactive mode to prevent plt.show() from blocking
    matplotlib_header = """
# Added automatically to prevent matplotlib from blocking
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
# Override plt.show to prevent blocking
original_show = plt.show
def non_blocking_show(*args, **kwargs):
    plt.savefig('temp_plot.png')  # Save plot to file instead of displaying
    plt.close()
plt.show = non_blocking_show
"""
    
    # Add code to load API keys from environment
    env_vars_header = """
# Added automatically to provide access to environment variables
import os
"""

    # Create environment variables access code
    # Only pass variables that appear to be API keys or tokens
    env_vars_code = []
    for key, value in os.environ.items():
        if any(pattern in key.lower() for pattern in ["api", "key", "token", "secret", "password", "auth"]):
            env_vars_code.append(f"os.environ['{key}'] = {repr(value)}")
    
    env_setup = "\n".join(env_vars_code)
    
    # Combine all code sections
    combined_code = f"""{matplotlib_header}
{env_vars_header}
{env_setup}

{prefix}
{golden_completion}
{suffix}

# Run assertions
{assertions}
"""
    
    # Create a temporary python file to execute
    temp_file = "temp_test_execution.py"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(combined_code)
        
        # Run the code with the current environment variables and a timeout
        try:
            process = subprocess.run(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                env=os.environ.copy(),  # Pass the current environment variables to the subprocess
                timeout=timeout  # Add timeout parameter
            )
            
            if process.returncode != 0:
                error = process.stderr.strip()
                # Check if it's an import error
                if "ImportError" in error or "ModuleNotFoundError" in error:
                    # Extract the missing module name
                    match = re.search(r"No module named '([^']+)'", error)
                    if match:
                        module_name = match.group(1).split('.')[0]
                        if verbose:
                            print(f"  Missing dependency: {module_name}, attempting to install...")
                        
                        # Try to install the module
                        install_process = subprocess.run(
                            [sys.executable, "-m", "pip", "install", module_name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            check=False
                        )
                        
                        if install_process.returncode == 0:
                            if verbose:
                                print(f"  Successfully installed {module_name}, retrying test case...")
                            
                            # Retry running the test
                            return run_python_test_case(prefix, golden_completion, suffix, assertions, verbose, timeout)
                        else:
                            return False, f"Failed to install dependency {module_name}: {install_process.stderr.strip()}"
                
                return False, f"Execution failed: {error}"
            
            return True, ""
            
        except subprocess.TimeoutExpired:
            # Handle timeout case
            if verbose:
                print(f"  Test case execution timed out after {timeout} seconds")
            return False, f"Execution timed out after {timeout} seconds"
            
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        # Clean up temporary files - with retry logic for Windows
        for attempt in range(5):
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                break
            except PermissionError:
                # If file is still in use, wait briefly and retry
                time.sleep(0.5)
                if attempt == 4:  # Last attempt
                    print(f"Warning: Could not remove temporary file {temp_file}")
                    
        if os.path.exists('temp_plot.png'):
            try:
                os.remove('temp_plot.png')
            except:
                print("Warning: Could not remove temporary plot file")

def display_test_case(json_str: str) -> None:
    """
    Parse and display a test case JSONL entry in a readable format.
    
    Args:
        json_str: The JSON string containing the test case
    """
    import json
    
    # Remove markdown code block markers if present
    json_str = json_str.replace("```json", "").replace("```", "").strip()
    
    try:
        test_case = json.loads(json_str)
        
        print("=" * 80)
        print(f"Test Case ID: {test_case['id']}")
        print(f"Source: {test_case['testsource']}")
        print(f"Language: {test_case['language']}")
        print("=" * 80)
        
        print("\nPREFIX CODE:")
        print("-" * 40)
        print(test_case['prefix'])
        
        print("\nGOLDEN COMPLETION:")
        print("-" * 40)
        print(test_case['golden_completion'])
        
        print("\nSUFFIX CODE:")
        print("-" * 40)
        print(test_case['suffix'])
        
        print("\nJUSTIFICATION:")
        print("-" * 40)
        print(test_case['LLM_justification'])
        
        print("\nASSERTIONS:")
        print("-" * 40)
        print(test_case['assertions'])
        print("=" * 80)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except KeyError as e:
        print(f"Missing required field in JSON: {e}")

def validate_test_case(json_str: str, language="python") -> dict:
    """
    Validate a test case JSONL entry by testing the combined code execution.
    
    Args:
        json_str: The JSON string containing the test case
        language: The programming language of the test case
        
    Returns:
        dict: Validation results for the complete test case
    """
    import json
    import ast
    
    result = {
        "syntax_valid": False,
    }
    
    # Remove markdown code block markers if present
    json_str = json_str.replace("```json", "").replace("```", "").strip()
    
    try:

        try:
            display_test_case(json_str)
        except Exception as debug_e:
            print(f"DEBUG error: {str(debug_e)}")

        test_case = json.loads(json_str)
        
        # Combine all code sections
        combined_code = f"""
{test_case['prefix']}

{test_case['golden_completion']}

{test_case['suffix']}

{test_case['assertions']}
"""
        
        if language.lower() == "python":
            try:
                ast.parse(combined_code)
                result["syntax_valid"] = True
            except SyntaxError as e:
                print(f"Syntax error in combined code: {str(e)}")
                return result
        else:
            parser = get_parser(language.lower())

            processed_code = combined_code.encode("utf-8", errors="ignore").decode("utf-8")
            tree = parser.parse(bytes(processed_code, "utf-8"))
            if tree.root_node.has_error:
                print(f"Syntax error in combined code")

                error_nodes = []
                
                def collect_error_nodes(node):
                    if node.has_error:
                        error_nodes.append(node)
                    for child in node.children:
                        collect_error_nodes(child)
                
                collect_error_nodes(tree.root_node)
                
                # Print first 3 error nodes
                for i, node in enumerate(error_nodes[:3]):
                    print(f"Error node {i}: {node.type} at line {node.start_point[0]+1}")

                return result
            else:
                result["syntax_valid"] = True
            
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    
    return result

def display_validation_results(json_str: str, language="python") -> None:
    """
    Display test case validation results in a clear format.
    """
    results = validate_test_case(json_str, language)
    
    print("\nVALIDATION RESULTS:")
    print("=" * 40)
    print(f"Syntax Valid: {results['syntax_valid']}")

    print("=" * 40)

def process_jsonl_file(input_file: str, output_file: str) -> None:
    """
    Process each line in a JSONL file and write formatted test cases to a text file.
    
    Args:
        input_file: Path to input JSONL file
        output_file: Path to output text file
    """
    with open(input_file, 'r', encoding='utf-8') as f_in:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line_number, line in enumerate(f_in, 1):
                # Write separator for each test case
                f_out.write(f"\n{'='*80}\n")
                f_out.write(f"Test Case #{line_number}\n")
                f_out.write(f"{'='*80}\n\n")
                
                # Redirect stdout to capture output from display functions
                from io import StringIO
                import sys
                
                # Create string buffer to capture output
                output_buffer = StringIO()
                # Save original stdout
                original_stdout = sys.stdout
                # Redirect stdout to buffer
                sys.stdout = output_buffer
                
                try:
                    # Call display functions
                    display_test_case(line)
                    
                    # Get captured output and write to file
                    output = output_buffer.getvalue()
                    f_out.write(output)
                    
                except Exception as e:
                    f_out.write(f"Error processing test case: {str(e)}\n")
                
                finally:
                    # Restore original stdout
                    sys.stdout = original_stdout
                    output_buffer.close()

def find_jsonl_files(directory):
    """
    Find all JSONL files in the specified directory (excluding _formatted.jsonl files).
    
    Args:
        directory: Path to the directory to search
        
    Returns:
        List of JSONL file paths
    """
    jsonl_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.jsonl') and not file.endswith('_formatted.jsonl'):
                jsonl_files.append(os.path.join(root, file))
    return jsonl_files

def execute_model_completions(benchmark_jsonl_files: List[str], models_dir="completions/python", 
                             verbose=True, report_file=None, models_filter=None, json_output_file=None) -> Dict:
    """
    Execute Python test cases using model completions instead of golden completions.
    
    Args:
        benchmark_jsonl_files: List of benchmark JSONL file paths to process
        models_dir: Directory containing model completions
        verbose: Whether to print detailed information during execution
        report_file: Path to file for saving detailed test results
        models_filter: List of model names to filter by (if None, all models are used)
        json_output_file: Path to JSON file for saving detailed results
        
    Returns:
        Dict: Summary of execution results by model
    """
    results = {
        "total_cases": 0,
        "models": {},
        "categories": {}  # Track test cases by category
    }
    
    # Track detailed per-test-case results for JSON output
    detailed_results = {
        "total_cases": 0,
        "models": {},
        "categories": {}  # Track detailed category results
    }
    
    # Open report file if specified
    report_fp = None
    if report_file:
        try:
            report_fp = open(report_file, 'w', encoding='utf-8')
            report_fp.write("MODEL COMPLETIONS BENCHMARK TEST RESULTS\n")
            report_fp.write("=" * 80 + "\n\n")
        except Exception as e:
            print(f"Error opening report file: {e}")
            report_fp = None
    
    try:
        # Fix model filtering to be consistent
        if models_filter:
            # Convert to lowercase for case-insensitive matching
            models_filter = [model.lower() for model in models_filter]
        
        for benchmark_file in benchmark_jsonl_files:
            if verbose:
                print(f"\nProcessing benchmark file: {benchmark_file}...")
            
            if report_fp:
                report_fp.write(f"\nBENCHMARK FILE: {benchmark_file}\n")
                report_fp.write("-" * 80 + "\n")
            
            # Extract category from benchmark path, handling nested directories
            path_parts = benchmark_file.split(os.sep)
            category = None
            for i, part in enumerate(path_parts):
                if part.endswith('.jsonl'):
                    # Use immediate parent directory as category
                    category = path_parts[i-1]
                    
                    # Handle nested categories if needed
                    if i >= 2:
                        # Check if we need to use a hierarchical category path
                        parent_dir = path_parts[i-2]
                        if parent_dir not in ["python", "javascript", "cpp", "java", "c_sharp", "typescript"]:
                            # Use hierarchical category path
                            category = f"{parent_dir}/{category}"
                    break
            
            if not category:
                if verbose:
                    print(f"Could not determine category from {benchmark_file}, skipping...")
                continue
            
            # Initialize category tracking in results if not already present
            if category not in results["categories"]:
                results["categories"][category] = {
                    "total_cases": 0,
                    "models": {}
                }
                detailed_results["categories"][category] = {
                    "total_cases": 0,
                    "models": {}
                }
            
            # For api_usage/api_usage.jsonl, we want to find api_usage/api_usage-*.jsonl
            base_name = os.path.basename(benchmark_file).replace('.jsonl', '')
            completion_dir = os.path.join(models_dir, *category.split('/'))
            os.makedirs(completion_dir, exist_ok=True)
            
            # Find all model completion files for this category
            model_files = {}
            for file in os.listdir(completion_dir):
                if file.startswith(f"{base_name}-") and file.endswith('.jsonl'):
                    # Extract model name from file name
                    model_name = file.replace(f"{base_name}-", "").replace(".jsonl", "")
                    
                    # Skip if models_filter is provided and this model doesn't match any filter
                    if models_filter and not any(model_filter in model_name.lower() for model_filter in models_filter):
                        if verbose:
                            print(f"  Skipping model {model_name} - not in requested models list")
                        continue
                    
                    model_files[model_name] = os.path.join(completion_dir, file)
                    
                    # Initialize model results if not already present
                    if model_name not in results["models"]:
                        results["models"][model_name] = {
                            "successful_cases": 0,
                            "failed_cases": 0,
                            "timeout_cases": 0,
                            "failures": []
                        }
                        detailed_results["models"][model_name] = {
                            "test_cases": [],
                            "summary": {}
                        }
                    
                    # Initialize model results for this category
                    if model_name not in results["categories"][category]["models"]:
                        results["categories"][category]["models"][model_name] = {
                            "successful_cases": 0,
                            "failed_cases": 0,
                            "timeout_cases": 0
                        }
                        detailed_results["categories"][category]["models"][model_name] = {
                            "test_cases": []
                        }
            
            if not model_files:
                if verbose:
                    print(f"No model completion files found for {base_name} in {completion_dir}, skipping...")
                continue
            
            if verbose:
                print(f"Found {len(model_files)} model completion files for {base_name}:")
                for model, path in model_files.items():
                    print(f"  - {model}: {path}")
            
            # Load benchmark test cases
            benchmark_tests = []
            try:
                with open(benchmark_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        benchmark_tests.append(json.loads(line))
                
                if verbose:
                    print(f"Loaded {len(benchmark_tests)} benchmark test cases from {benchmark_file}")
            except Exception as e:
                print(f"Error loading benchmark test cases from {benchmark_file}: {str(e)}")
                continue
            
            # Update total cases count for this category
            results["categories"][category]["total_cases"] += len(benchmark_tests)
            detailed_results["categories"][category]["total_cases"] += len(benchmark_tests)
            
            # Collect all model completions first for debugging comparison
            all_model_completions = {}
            for model_name, model_file in model_files.items():
                try:
                    with open(model_file, 'r', encoding='utf-8') as f:
                        model_completions = []
                        for line in f:
                            json_data = json.loads(line)
                            # Extract completion using the model name as the key
                            completion = json_data.get(model_name, "")
                            model_completions.append({"completion": completion})
                    all_model_completions[model_name] = model_completions
                    if verbose:
                        print(f"Loaded {len(model_completions)} completions from {model_file}")
                except Exception as e:
                    print(f"Error loading completions from {model_file}: {str(e)}")
            
            # Check if completions are actually different (debugging code can remain the same)
            if verbose and len(all_model_completions) > 1:
                print("\nCOMPARING MODEL COMPLETIONS (SAMPLE):")
                # Take the first few test cases as samples
                if benchmark_tests and all(model_name in all_model_completions and all_model_completions[model_name] for model_name in model_files):
                    for idx in range(min(3, len(benchmark_tests))):  # Check first 3 test cases
                        print(f"\nTEST CASE #{idx+1} (ID: {benchmark_tests[idx]['id']}) COMPLETION COMPARISON:")
                        completions_are_same = True
                        first_completion = None
                        
                        for i, model_name in enumerate(model_files):
                            if idx < len(all_model_completions[model_name]):
                                current_completion = all_model_completions[model_name][idx].get("completion", "")
                                if i == 0:
                                    first_completion = current_completion
                                    print(f"  {model_name} (first 80 chars): {first_completion[:80]}")
                                else:
                                    if current_completion != first_completion:
                                        completions_are_same = False
                                    print(f"  {model_name} (first 80 chars): {current_completion[:80]}")
                                    if current_completion == first_completion:
                                        print("  WARNING: Same as first model")
                        
                        if completions_are_same:
                            print("  WARNING: ALL MODELS HAVE IDENTICAL COMPLETIONS FOR THIS TEST CASE!")
                        else:
                            print("  Models have different completions for this test case.")
            
            # Now load each model's completions and run the tests
            for model_name, model_completions in all_model_completions.items():
                if verbose:
                    print(f"\nEvaluating model: {model_name}")
                
                if report_fp:
                    report_fp.write(f"\nMODEL: {model_name}\n")
                    report_fp.write("-" * 40 + "\n")
                
                if len(model_completions) != len(benchmark_tests):
                    print(f"WARNING: Number of completions ({len(model_completions)}) does not match benchmark tests ({len(benchmark_tests)})")
                
                # Run tests for each benchmark case with the corresponding model completion
                for i, (benchmark, completion) in enumerate(zip(benchmark_tests, model_completions), 1):
                    results["total_cases"] += 1
                    detailed_results["total_cases"] += 1
                    
                    if verbose:
                        print(f"Running test case #{i} (ID: {benchmark['id']}) with model {model_name}...")
                    
                    # Get test case components from benchmark
                    prefix = benchmark["prefix"]
                    
                    # Use model's completion instead of golden completion
                    model_completion = completion.get("completion", "")
                    
                    # DEBUG: Print model completion
                    if verbose:
                        print(f"Model {model_name} completion (truncated to 100 chars):")
                        print(f"  {model_completion[:100]}" + ("..." if len(model_completion) > 100 else ""))
                    
                    suffix = benchmark["suffix"]
                    assertions = benchmark.get("assertions", "")
                    
                    # Write test case info to report
                    if report_fp:
                        report_fp.write(f"\nTEST CASE #{i} (ID: {benchmark['id']})\n")
                        report_fp.write(f"  Source: {benchmark.get('testsource', 'Unknown')}\n\n")
                    
                    # Execute the test case with the model's completion
                    success, error_msg = run_python_test_case(
                        prefix, model_completion, suffix, assertions, verbose, timeout=30
                    )
                    
                    # Check if timeout occurred
                    is_timeout = "timed out" in error_msg.lower()
                    
                    # Create detailed test case result entry
                    test_case_result = {
                        "test_id": benchmark['id'],
                        "file": benchmark_file,
                        "category": category,
                        "success": success,
                        "error": error_msg if not success else None,
                        "is_timeout": is_timeout if not success else False
                    }
                    detailed_results["models"][model_name]["test_cases"].append(test_case_result)
                    detailed_results["categories"][category]["models"][model_name]["test_cases"].append(test_case_result)
                    
                    if success:
                        # Update global model success stats
                        results["models"][model_name]["successful_cases"] += 1
                        
                        # Update category-specific success stats
                        results["categories"][category]["models"][model_name]["successful_cases"] += 1
                        
                        if verbose:
                            print(f"Test case #{i} (ID: {benchmark['id']}) passed with model {model_name}")
                        if report_fp:
                            report_fp.write("  RESULT: PASS\n\n")
                    else:
                        # Update global model failure stats
                        results["models"][model_name]["failed_cases"] += 1
                        if is_timeout:
                            results["models"][model_name]["timeout_cases"] += 1
                        
                        # Update category-specific failure stats
                        results["categories"][category]["models"][model_name]["failed_cases"] += 1
                        if is_timeout:
                            results["categories"][category]["models"][model_name]["timeout_cases"] += 1
                        
                        results["models"][model_name]["failures"].append({
                            "file": benchmark_file,
                            "category": category,
                            "test_id": benchmark['id'],
                            "error": error_msg,
                            "is_timeout": is_timeout
                        })
                        
                        if verbose:
                            print(f"Test case #{i} (ID: {benchmark['id']}) failed with model {model_name}")
                            print(f"  Error: {error_msg}")
                            if is_timeout:
                                print("  REASON: TIMEOUT OCCURRED")
                        
                        if report_fp:
                            report_fp.write("  RESULT: FAIL\n")
                            report_fp.write(f"  ERROR: {error_msg}\n\n")
                            
                            # Include the test case code in the report for debugging
                            report_fp.write("  PREFIX CODE:\n")
                            report_fp.write("  " + prefix.replace("\n", "\n  ") + "\n\n")
                            report_fp.write("  MODEL COMPLETION:\n")
                            report_fp.write("  " + model_completion.replace("\n", "\n  ") + "\n\n")
                            report_fp.write("  SUFFIX CODE:\n")
                            report_fp.write("  " + suffix.replace("\n", "\n  ") + "\n\n")
                            report_fp.write("  ASSERTIONS:\n")
                            report_fp.write("  " + assertions.replace("\n", "\n  ") + "\n\n")
                
                # Write model summary to report
                if report_fp:
                    report_fp.write(f"\nSUMMARY FOR MODEL: {model_name}\n")
                    report_fp.write("-" * 40 + "\n")
                    total = results["models"][model_name]["successful_cases"] + results["models"][model_name]["failed_cases"]
                    success_rate = results["models"][model_name]["successful_cases"] / total * 100 if total > 0 else 0
                    report_fp.write(f"Success rate: {success_rate:.2f}%\n")
                    report_fp.write(f"Successful test cases: {results['models'][model_name]['successful_cases']}\n")
                    report_fp.write(f"Failed test cases: {results['models'][model_name]['failed_cases']}\n")
                    timeout_pct = results["models"][model_name]["timeout_cases"] / max(results["models"][model_name]["failed_cases"], 1) * 100 if results["models"][model_name]["failed_cases"] > 0 else 0
                    report_fp.write(f"Timeout failures: {results['models'][model_name]['timeout_cases']} ({timeout_pct:.1f}% of failures)\n\n")
    
    finally:
        # Write overall summary to report file
        if report_fp:
            try:
                report_fp.write("\n" + "="*80 + "\n")
                report_fp.write("OVERALL EXECUTION SUMMARY\n")
                report_fp.write("="*80 + "\n")
                report_fp.write(f"Total test cases: {results['total_cases']}\n\n")
                
                report_fp.write("RESULTS BY MODEL:\n")
                for model_name, model_results in results["models"].items():
                    total = model_results["successful_cases"] + model_results["failed_cases"]
                    success_rate = model_results["successful_cases"] / total * 100 if total > 0 else 0
                    report_fp.write(f"{model_name}:\n")
                    report_fp.write(f"  Success rate: {success_rate:.2f}%\n")
                    report_fp.write(f"  Successful test cases: {model_results['successful_cases']}\n")
                    report_fp.write(f"  Failed test cases: {model_results['failed_cases']}\n")
                    report_fp.write(f"  Timeout failures: {model_results['timeout_cases']} ({model_results['timeout_cases']/max(model_results['failed_cases'], 1)*100:.1f}% of failures)\n\n")
                
                # Add category breakdown for each model
                report_fp.write("\nRESULTS BY CATEGORY:\n")
                for category, category_results in results["categories"].items():
                    report_fp.write(f"\nCategory: {category}\n")
                    report_fp.write("-" * 50 + "\n")
                    report_fp.write(f"Total test cases: {category_results['total_cases']}\n\n")
                    
                    # Sort models by success rate in this category
                    category_model_rates = []
                    for model_name, model_category_results in category_results["models"].items():
                        total = model_category_results["successful_cases"] + model_category_results["failed_cases"]
                        if total > 0:
                            success_rate = model_category_results["successful_cases"] / total * 100
                            category_model_rates.append((model_name, success_rate, model_category_results))
                    
                    # Sort by success rate in descending order
                    category_model_rates.sort(key=lambda x: x[1], reverse=True)
                    
                    for model_name, success_rate, model_category_results in category_model_rates:
                        total = model_category_results["successful_cases"] + model_category_results["failed_cases"]
                        timeout_pct = model_category_results["timeout_cases"] / max(model_category_results["failed_cases"], 1) * 100 if model_category_results["failed_cases"] > 0 else 0
                        
                        report_fp.write(f"  {model_name}:\n")
                        report_fp.write(f"    Success rate: {success_rate:.2f}%\n")
                        report_fp.write(f"    Successful test cases: {model_category_results['successful_cases']}/{total}\n")
                        report_fp.write(f"    Timeout failures: {model_category_results['timeout_cases']} ({timeout_pct:.1f}% of failures)\n")
                
                report_fp.write("\nFAILURES BY MODEL:\n")
                for model_name, model_results in results["models"].items():
                    if model_results["failures"]:
                        report_fp.write(f"{model_name}:\n")
                        for i, failure in enumerate(model_results["failures"], 1):
                            report_fp.write(f"  {i}. Category: {failure['category']} - Test ID: {failure['test_id']}\n")
                            report_fp.write(f"     Error: {failure['error']}\n\n")
            except Exception as e:
                print(f"Error writing summary to report file: {e}")
            
            # Close report file
            try:
                report_fp.close()
                if verbose:
                    print(f"\nDetailed test results saved to {report_file}")
            except Exception as e:
                print(f"Error closing report file: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    print(f"Total test cases: {results['total_cases']}")
    print("\nRESULTS BY MODEL:")
    
    # Sort models by success rate
    model_success_rates = []
    for model_name, model_results in results["models"].items():
        total = model_results["successful_cases"] + model_results["failed_cases"]
        success_rate = model_results["successful_cases"] / total * 100 if total > 0 else 0
        model_success_rates.append((model_name, success_rate, model_results))
    
    # Sort by success rate in descending order
    model_success_rates.sort(key=lambda x: x[1], reverse=True)
    
    for model_name, success_rate, model_results in model_success_rates:
        print(f"{model_name}:")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Successful test cases: {model_results['successful_cases']}")
        print(f"  Failed test cases: {model_results['failed_cases']}")
        print(f"  Timeout failures: {model_results['timeout_cases']} ({model_results['timeout_cases']/max(model_results['failed_cases'], 1)*100:.1f}% of failures)")
    
    # Print category breakdown
    print("\nRESULTS BY CATEGORY:")
    
    # Sort categories by name for consistent output
    sorted_categories = sorted(results["categories"].keys())
    
    for category in sorted_categories:
        category_results = results["categories"][category]
        print(f"\nCategory: {category}")
        print("-" * 50)
        print(f"Total test cases: {category_results['total_cases']}")
        
        # Sort models by success rate in this category
        category_model_rates = []
        for model_name, model_category_results in category_results["models"].items():
            total = model_category_results["successful_cases"] + model_category_results["failed_cases"]
            if total > 0:
                success_rate = model_category_results["successful_cases"] / total * 100
                category_model_rates.append((model_name, success_rate, model_category_results))
        
        # Sort by success rate in descending order
        category_model_rates.sort(key=lambda x: x[1], reverse=True)
        
        for model_name, success_rate, model_category_results in category_model_rates:
            total = model_category_results["successful_cases"] + model_category_results["failed_cases"]
            timeout_pct = model_category_results["timeout_cases"] / max(model_category_results["failed_cases"], 1) * 100 if model_category_results["failed_cases"] > 0 else 0
            
            print(f"  {model_name}:")
            print(f"    Success rate: {success_rate:.2f}%")
            print(f"    Successful test cases: {model_category_results['successful_cases']}/{total}")
            print(f"    Timeout failures: {model_category_results['timeout_cases']} ({timeout_pct:.1f}% of failures)")
    
    # Write results to JSON file if specified
    if json_output_file:
        try:
            # Prepare final JSON output with calculated metrics
            json_output = {
                "total_cases": detailed_results["total_cases"],
                "models": {},
                "categories": {}
            }
            
            # Add overall model summaries
            for model_name, model_results in results["models"].items():
                total = model_results["successful_cases"] + model_results["failed_cases"]
                success_rate = model_results["successful_cases"] / total * 100 if total > 0 else 0
                timeout_pct = model_results["timeout_cases"] / max(model_results["failed_cases"], 1) * 100 if model_results["failed_cases"] > 0 else 0
                
                json_output["models"][model_name] = {
                    "success_rate": round(success_rate, 2),
                    "successful_cases": model_results["successful_cases"],
                    "failed_cases": model_results["failed_cases"],
                    "timeout_cases": model_results["timeout_cases"],
                    "timeout_percentage": round(timeout_pct, 1),
                    "test_cases": detailed_results["models"][model_name]["test_cases"]
                }
            
            # Add category breakdowns
            for category, category_results in results["categories"].items():
                json_output["categories"][category] = {
                    "total_cases": category_results["total_cases"],
                    "models": {}
                }
                
                for model_name, model_category_results in category_results["models"].items():
                    total = model_category_results["successful_cases"] + model_category_results["failed_cases"]
                    if total > 0:
                        success_rate = model_category_results["successful_cases"] / total * 100
                        timeout_pct = model_category_results["timeout_cases"] / max(model_category_results["failed_cases"], 1) * 100 if model_category_results["failed_cases"] > 0 else 0
                        
                        json_output["categories"][category]["models"][model_name] = {
                            "success_rate": round(success_rate, 2),
                            "successful_cases": model_category_results["successful_cases"],
                            "failed_cases": model_category_results["failed_cases"],
                            "total_cases": total,
                            "timeout_cases": model_category_results["timeout_cases"],
                            "timeout_percentage": round(timeout_pct, 1),
                            "test_cases": detailed_results["categories"][category]["models"][model_name]["test_cases"]
                        }
            
            with open(json_output_file, 'w', encoding='utf-8') as json_fp:
                json.dump(json_output, json_fp, indent=2)
                
            if verbose:
                print(f"\nJSON results saved to {json_output_file}")
                
        except Exception as e:
            print(f"Error writing results to JSON file: {e}")
    
    return results

def main():
    endpoint = os.getenv("ENDPOINT_URL", "https://deeppromptnorthcentralus.openai.azure.com/")  
    deployment = os.getenv("DEPLOYMENT_NAME", "deepprompt-gpt-4o-2024-05-13")  

    # Initialize Azure OpenAI Service client with Entra ID authentication
    token_provider = get_bearer_token_provider(  
        DefaultAzureCredential(),  
        "https://cognitiveservices.azure.com/.default"
    )  
    
    client = AzureOpenAI(  
        azure_endpoint=endpoint,  
        azure_ad_token_provider=token_provider,  
        api_version="2024-05-01-preview",  
    )
    
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Generate or execute benchmark test cases')
    parser.add_argument('--benchmark-dir', type=str, default='benchmark/', help='Directory containing benchmark files')
    parser.add_argument('--execute', action='store_true', help='Execute test cases')
    parser.add_argument('--verbose', action='store_true', help='Print detailed information during execution')
    parser.add_argument('--categories', type=str, help='Comma-separated list of test categories to execute (e.g., api_usage,code_purpose_understanding)')
    parser.add_argument('--report', default="benchmark_report.txt", type=str, help='Path to output file for detailed test results')
    parser.add_argument('--id', type=str, help='Run a specific test case with the given ID')
    parser.add_argument('--model-eval', action='store_true', help='Evaluate model completions against benchmark test cases')
    parser.add_argument('--models', type=str, help='Comma-separated list of model names to evaluate (e.g., 4o_mini,gpt_3.5_turbo)')
    parser.add_argument('--json-output', type=str, help='Path to output JSON file for detailed test results')
    parser.add_argument('--models-dir', type=str, default='completions/python', 
                       help='Directory containing model completions (default: completions/python)')
    
    args = parser.parse_args()
    
    if args.execute:
        # Print information about API keys when executing test cases
        if args.categories and "api_usage" in args.categories:
            print("\nNOTE: API Usage test cases may require API keys. Add your API keys to a .env file")
            print("in the root directory with the format API_KEY=your_api_key. These will be")
            print("available to the test cases during execution.\n")
        
        # Find all Python JSONL files in the benchmark directory
        jsonl_files = find_jsonl_files("benchmark/python")
        print(f"Found {len(jsonl_files)} JSONL files for execution.")
        
        # Filter files by category if specified
        if args.categories:
            categories = args.categories.split(',')
            filtered_files = []
            
            for file in jsonl_files:
                if any(category in file for category in categories):
                    filtered_files.append(file)
            
            if not filtered_files:
                print(f"No files matching the categories: {args.categories}")
                return
            
            print(f"Found {len(filtered_files)} files matching the categories: {args.categories}")
            jsonl_files = filtered_files
        
        # If a specific test ID is provided, filter for just that test case
        if args.id:
            print(f"Looking for test case with ID: {args.id}")
            # We'll collect the test case here if found
            found_test_case = None
            found_file_path = None
            
            # Search through all relevant files for the specified test ID
            for jsonl_file in jsonl_files:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            test_case = json.loads(line)
                            if str(test_case.get('id')) == str(args.id):
                                found_test_case = test_case
                                found_file_path = jsonl_file
                                print(f"Found test case with ID {args.id} in file {jsonl_file}")
                                break
                        except json.JSONDecodeError:
                            print(f"Warning: Invalid JSON at line {line_num} in {jsonl_file}")
                
                if found_test_case:
                    break
            
            if not found_test_case:
                print(f"No test case found with ID: {args.id}")
                return
            
            # Set up a temporary JSONL file with just the one test case
            temp_jsonl = "temp_single_test.jsonl"
            with open(temp_jsonl, 'w', encoding='utf-8') as f:
                f.write(json.dumps(found_test_case) + '\n')
            
            try:
                # Execute just this single test case
                results = execute_python_test_cases(
                    [temp_jsonl], 
                    verbose=args.verbose,
                    report_file=args.report
                )
                
                # Print source file information
                print(f"\nTest case ID {args.id} from file: {found_file_path}")
                
                return
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_jsonl):
                    os.remove(temp_jsonl)
        
        # If model evaluation is requested
        if args.model_eval:
            print("Evaluating model completions against benchmark test cases...")
            # Filter models if specified
            models_filter = args.models.split(',') if args.models else None
            
            execute_model_completions(
                jsonl_files,
                models_dir=args.models_dir,
                verbose=args.verbose,
                report_file=args.report,
                models_filter=models_filter,
                json_output_file=args.json_output
            )
            return
        
        # Otherwise, execute golden completions as before
        execute_python_test_cases(
            jsonl_files, 
            verbose=args.verbose,
            report_file=args.report
        )
        return
    
    valid_completions = 0
    total_completions = 0
    LANGUAGE = "python"
    output_file = f"benchmark/{LANGUAGE}/api_usage/api_usage.jsonl"
    SYSTEM_PROMPT = python_prompts.API_USAGE_SYSTEM_PROMPT
    USER_PROMPT = python_prompts.API_USAGE_USER_PROMPT

    while valid_completions < total_completions:
        try:
            # Prompt the AI with a message
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": USER_PROMPT
                }
            ]

            completion = client.chat.completions.create(  
                model=deployment,  
                messages=messages,
                max_tokens=4000,  
                temperature=0.7,  
                top_p=0.95,  
                frequency_penalty=0,  
                presence_penalty=0,
                stop=None,  
                stream=False  
            )

            response_content = completion.choices[0].message.content
            results = validate_test_case(response_content, LANGUAGE)

            if results["syntax_valid"]:
                # Append to JSONL file
                with open(output_file, 'a') as f:
                    cleaned_response = response_content.replace("```json", "").replace("```", "").strip()
                    json_obj = json.loads(cleaned_response)
                    json_line = json.dumps(json_obj)

                    f.write(json_line + '\n')
                
                valid_completions += 1
                print(f"Valid completion {valid_completions}/{total_completions} saved")
                
                # Display the test case and validation results
                print("\nTest Case Details:")
                display_test_case(response_content)
                display_validation_results(response_content, LANGUAGE)
            else:
                print("Invalid syntax - retrying...")

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            continue
    
    print(f"\nCompleted! {valid_completions} valid completions have been saved to {output_file}")

    # Process the generated JSONL file
    output_txt_file = output_file.replace('.jsonl', '_formatted.txt')
    print(f"\nGenerating formatted output in {output_txt_file}...")
    process_jsonl_file(output_file, output_txt_file)
    print("Formatting complete!")

if __name__ == "__main__":
    main()

# Example usage:
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --categories api_usage --verbose
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --models gpt-4o-mini,gpt-35-turbo,DeepSeek-R1,gpt-4.5-preview,Ministral-3B
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --models gpt-35-turbo-completions
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --json-output benchmark_results_pass_1.json
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --models-dir completions/python
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --models-dir new_completions_oai_41_mini/python
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --models-dir new_completions_oai_41_nano/python
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --models-dir new_completions_02_1_v4_v7/python

# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --models-dir new_completions_02_1/python
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --models-dir new_completions_02_1/python --models DeepSeek-R1
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --models-dir new_completions_02_3/python
# python generate_benchmark.py --execute --model-eval --benchmark-dir benchmark/python --verbose --models-dir new_completions_02_5/python
