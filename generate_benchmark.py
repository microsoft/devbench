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
import math

dotenv.load_dotenv()

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

def main():
    # Using GPT-4o to generate the benchmark test cases
    endpoint = os.getenv("ENDPOINT_URL", "[ANONYMIZED-ENDPOINT-1]")  
    deployment = os.getenv("DEPLOYMENT_NAME", "[ANONYMIZED-DEPLOYMENT-1]")  

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
    parser = argparse.ArgumentParser(description='Generate benchmark test cases')
    parser.add_argument('--generate', action='store_true', help='Generate benchmark test cases')
    parser.add_argument('--completions', type=int, default=10, help='Number of completions to generate')
    parser.add_argument('--language', type=str, default='python', choices=['python', 'javascript', 'c_sharp', 'cpp', 'typescript', 'java'],
                        help='Programming language for benchmark generation')
    parser.add_argument('--output', type=str, help='Custom output file path for generated benchmarks')
    parser.add_argument('--prompt-type', type=str, default='api_usage',
                        help='Type of prompt to use (e.g., api_usage, code_purpose_understanding)')

    args = parser.parse_args()

    if not args.generate:
        print("Error: --generate flag is required to run this script.")
        print("Usage: python generate_benchmark.py --generate [--language python] [--completions 10] [--prompt-type api_usage]")
        print("\nFor executing benchmark tests, use execute_benchmark.py instead.")
        parser.print_help()
        return

    # Generation code
    valid_completions = 0
    total_completions = args.completions
    LANGUAGE = args.language.lower()

    # Determine prompt module based on language
    prompt_module = None
    if LANGUAGE == 'python':
        prompt_module = python_prompts
    elif LANGUAGE == 'javascript':
        prompt_module = javascript_prompts
    elif LANGUAGE == 'c_sharp':
        prompt_module = c_sharp_prompts
    elif LANGUAGE == 'cpp':
        prompt_module = cpp_prompts
    elif LANGUAGE == 'typescript':
        prompt_module = typescript_prompts
    elif LANGUAGE == 'java':
        prompt_module = java_prompts
    else:
        print(f"Unsupported language: {LANGUAGE}")
        return

    # Get the correct prompts based on prompt type
    prompt_type = args.prompt_type.upper()
    try:
        SYSTEM_PROMPT = getattr(prompt_module, f"{prompt_type}_SYSTEM_PROMPT")
        USER_PROMPT = getattr(prompt_module, f"{prompt_type}_USER_PROMPT")
    except AttributeError:
        print(f"Prompt type '{args.prompt_type}' not found for language '{LANGUAGE}'")
        print("Available prompt types for this language:")
        for attr in dir(prompt_module):
            if attr.endswith("_SYSTEM_PROMPT"):
                print(f"  - {attr.replace('_SYSTEM_PROMPT', '').lower()}")
        return

    # Set output file path
    if args.output:
        output_file = args.output
    else:
        # Create default path: benchmark/{language}/{prompt_type}/{prompt_type}.jsonl
        prompt_type_dir = args.prompt_type.lower()
        os.makedirs(f"benchmark/{LANGUAGE}/{prompt_type_dir}", exist_ok=True)
        output_file = f"benchmark/{LANGUAGE}/{prompt_type_dir}/{prompt_type_dir}.jsonl"

    print(f"Generating {total_completions} benchmark test cases for {LANGUAGE} using {args.prompt_type} prompts")
    print(f"Output will be saved to: {output_file}")

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
