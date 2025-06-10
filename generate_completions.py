import json
import os
from openai import AzureOpenAI
import dotenv
# Add imports for Azure AI Inference SDK
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import openai
import requests
import anthropic
import glob
from collections import defaultdict
import re
import argparse  # Import for command-line argument parsing

# Import Azure identity for token-based authentication
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

dotenv.load_dotenv()

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Generate completions for code benchmarks')
parser.add_argument('--output_dir', type=str, default='completions',
                    help='Output directory for completions (default: completions)')
parser.add_argument('--temperature', type=float, default=0.0,
                    help='Temperature for model generation (default: 0.0)')
args = parser.parse_args()

# Output directory for completions
OUTPUT_DIR = args.output_dir  # Set from command-line arguments
# Temperature for model generation
TEMPERATURE = args.temperature  # Set from command-line arguments
# Fixed number of completions (always 1)
NUM_COMPLETIONS = 1

print(f"Using output directory: {OUTPUT_DIR}")
print(f"Using temperature: {TEMPERATURE}")

# Hardcoded Azure OpenAI Endpoint and API Key
ENDPOINT = "[ANONYMIZED-ENDPOINT-1]"

# o3-mini endpoint and deployment details
O3MINI_ENDPOINT = "[ANONYMIZED-ENDPOINT-2]"  # Remove the deployment path from endpoint
O3MINI_DEPLOYMENT = "[ANONYMIZED-DEPLOYMENT-3]"  # The deployment name to use in API calls
O3MINI_API_VERSION = "2024-12-01-preview"

# Add Claude API configuration
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Add Claude endpoints and model names
CLAUDE_35_MODEL = "claude-3-5-sonnet-20240620"
CLAUDE_37_MODEL = "claude-3-7-sonnet-20250219"

# Define model types
MODEL_TYPE_O3MINI = "o3mini"
MODEL_TYPE_CLAUDE_35 = "claude_35_sonnet"
MODEL_TYPE_CLAUDE_37 = "claude_37_sonnet"

# Add GPT-4o mini endpoint and model details
GPT4OMINI_ENDPOINT = "[ANONYMIZED-ENDPOINT-2]"
GPT4OMINI_DEPLOYMENT = "[ANONYMIZED-DEPLOYMENT-4]"
GPT4OMINI_MODEL = "gpt-4o-mini"
GPT4OMINI_API_VERSION = "2025-01-01-preview"

# Add model type for GPT-4o mini
MODEL_TYPE_GPT4OMINI = "gpt4o_mini"

# Add API key environment variable
GPT4OMINI_API_KEY = os.getenv("GPT4OMINI_API_KEY")

# Add DeepSeek R1 endpoint and model details
DEEPSEEK_R1_ENDPOINT = "[ANONYMIZED-ENDPOINT-3]"
DEEPSEEK_R1_MODEL = "DeepSeek-R1"

# Add model type for DeepSeek R1
MODEL_TYPE_DEEPSEEK_R1 = "deepseek_r1"

# Add API key environment variable
DEEPSEEK_R1_API_KEY = os.getenv("DEEPSEEK_R1_API_KEY")

# Add Ministral-3B endpoint and model details
MINISTRAL_ENDPOINT = "[ANONYMIZED-ENDPOINT-5]"
MINISTRAL_MODEL = "Ministral-3B"

# Add model type for Ministral-3B
MODEL_TYPE_MINISTRAL = "ministral_3b"

# Add API key environment variable
MINISTRAL_API_KEY = os.getenv("MINISTRAL_API_KEY")

# Add DeepSeek V3 endpoint and model details
DEEPSEEK_V3_ENDPOINT = "[ANONYMIZED-ENDPOINT-6]"
DEEPSEEK_V3_MODEL = "DeepSeek-V3-0324"

# Add model type for DeepSeek V3
MODEL_TYPE_DEEPSEEK_V3 = "deepseek_v3"

# Add API key environment variable
DEEPSEEK_V3_API_KEY = os.getenv("DEEPSEEK_V3_API_KEY")

# Add GPT-4.1 mini endpoint and model details
GPT41MINI_ENDPOINT = "[ANONYMIZED-ENDPOINT-8]"
GPT41MINI_DEPLOYMENT = "gpt-4.1-mini"
GPT41MINI_MODEL = "gpt-4.1-mini"
GPT41MINI_API_VERSION = "2025-01-01-preview"

# Add model type for GPT-4.1 mini
MODEL_TYPE_GPT41MINI = "gpt41_mini"

# Add GPT-4.1 nano endpoint and model details
GPT41NANO_ENDPOINT = "[ANONYMIZED-ENDPOINT-8]"
GPT41NANO_DEPLOYMENT = "gpt-4.1-nano"
GPT41NANO_MODEL = "gpt-4.1-nano"
GPT41NANO_API_VERSION = "2025-01-01-preview"

# Add model type for GPT-4.1 nano
MODEL_TYPE_GPT41NANO = "gpt41_nano"

# Add GPT-4o endpoint and model details
GPT4O_ENDPOINT = "[ANONYMIZED-ENDPOINT-9]"
GPT4O_DEPLOYMENT = "[ANONYMIZED-DEPLOYMENT-6]"
GPT4O_MODEL = "gpt-4o"
GPT4O_API_VERSION = "2025-01-01-preview"

# Add model type for GPT-4o
MODEL_TYPE_GPT4O = "gpt4o"

# Add API key environment variable
GPT4O_API_KEY = os.getenv("GPT4O_API_KEY")

# Add to DEPLOYMENTS list
DEPLOYMENTS = [
    {"name": "o3-mini", "type": MODEL_TYPE_O3MINI},
    {"name": "claude-3-5-sonnet", "type": MODEL_TYPE_CLAUDE_35},
    {"name": "claude-3-7-sonnet", "type": MODEL_TYPE_CLAUDE_37},
    {"name": "gpt-4o-mini", "type": MODEL_TYPE_GPT4OMINI},
    {"name": "DeepSeek-R1", "type": MODEL_TYPE_DEEPSEEK_R1},
    {"name": "Ministral-3B", "type": MODEL_TYPE_MINISTRAL},
    {"name": "DeepSeek-V3-0324", "type": MODEL_TYPE_DEEPSEEK_V3},
    {"name": "gpt-4.1-mini", "type": MODEL_TYPE_GPT41MINI},
    {"name": "gpt-4.1-nano", "type": MODEL_TYPE_GPT41NANO},
    {"name": "gpt-4o", "type": MODEL_TYPE_GPT4O},
]

# Split input dirs into categories
common_dirs = [
    "low_context",
    "api_usage",
    "pattern_matching",
    "code_purpose_understanding",
    "syntax_completion",
    "code2NL_NL2code",
]

# Split input files into categories
common_files = [
    "low_context",
    "api_usage",
    "pattern_matching",
    "code_purpose_understanding",
    "syntax_completion",
    "code2NL_NL2code",
]

languages = [
    "python",
    "c_sharp",
    "cpp",
    "java",
    "javascript",
    "typescript",
]


API_KEY = os.getenv("COMPLETIONS_API_KEY")
O3MINI_API_KEY = os.getenv("O3MINI_API_KEY")  # Add API key for o3-mini

# Initialize GPT-4.1 mini client with Azure AD authentication
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)

# Initialize Azure OpenAI Client
client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
    api_version="2024-12-01-preview",
)

# Initialize o3-mini client (using standard AzureOpenAI client)
o3mini_client = AzureOpenAI(
    api_version=O3MINI_API_VERSION,
    azure_endpoint=O3MINI_ENDPOINT,
    # api_key=O3MINI_API_KEY,
    azure_ad_token_provider=token_provider,
)

# Initialize Claude client
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# Initialize GPT-4o mini client
gpt4omini_client = AzureOpenAI(
    api_version=GPT4OMINI_API_VERSION,
    azure_endpoint=GPT4OMINI_ENDPOINT,
    # api_key=GPT4OMINI_API_KEY,
    azure_ad_token_provider=token_provider,
)

# Initialize DeepSeek R1 client
deepseek_r1_client = ChatCompletionsClient(
    endpoint=DEEPSEEK_R1_ENDPOINT,
    credential=AzureKeyCredential(DEEPSEEK_R1_API_KEY),
)

# Initialize Ministral-3B client
ministral_client = ChatCompletionsClient(
    endpoint=MINISTRAL_ENDPOINT,
    credential=AzureKeyCredential(MINISTRAL_API_KEY),
)

# Initialize DeepSeek V3 client
deepseek_v3_client = ChatCompletionsClient(
    endpoint=DEEPSEEK_V3_ENDPOINT,
    credential=AzureKeyCredential(DEEPSEEK_V3_API_KEY),
)

gpt41mini_client = AzureOpenAI(
    azure_endpoint=GPT41MINI_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version=GPT41MINI_API_VERSION,
)

# Initialize GPT-4.1 nano client (using same authentication as GPT-4.1 mini)
gpt41nano_client = AzureOpenAI(
    azure_endpoint=GPT41NANO_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version=GPT41NANO_API_VERSION,
)

# Initialize GPT-4o client
gpt4o_client = AzureOpenAI(
    api_version=GPT4O_API_VERSION,
    azure_endpoint=GPT4O_ENDPOINT,
    azure_ad_token_provider=token_provider,
    # api_key=GPT4O_API_KEY,
)

def get_prompt_template(prefix, suffix):
    """
    Returns the message-based prompt template for code completion
    
    Args:
        prefix: The code prefix
        suffix: The code suffix
    
    Returns:
        List of message objects for the chat API
    """
    return [
        {
            "role": "system",
            "content": """
            You are a code completion assistant. 
            You are given a code function and you need to generate a code snippet \
            to replace the `#TODO: You Code Here` part that is functionally correct. 
            You only output the necessary code to replace the `#TODO: You Code Here` part, without any additional explanation, comments, MODIFICATION or DUPLICATION to the existing code.

            # Output Format

            - Output only the code snippet that replaces the `#TODO: You Code Here`.
            - Do not include any other parts of the existing code or additional text.

            # Example 1

            **User Input:**

            ```python
            def calculate_circle_area(radius):
                pi = 3.14
                #TODO: You Code Here
                return area
            ```

            **Assistant Output:**

            ```python
                area = pi * radius * radius
            ```

            # Example 2

            **User Input:**

            ```python
            def calculate_circle_area(radius):
                pi = #TODO: You Code Here
                return area
            ```

            **Assistant Output:**

            ```python
                    3.14
                area = pi * radius * radius
            ```

            # Example 3

            **User Input:**

            ```python
            def calculate_circle_area(radius):
                pi = 3.14
                ar#TODO: You Code Here
                return area
            ```

            **Assistant Output:**

            ```python
                ea = pi * radius * radius
            ```

            I REPEAT, you only output the necessary code to replace the `TODO` code part, \
            WITHOUT any additional explanation, comments, MODIFICATION or DUPLICATION to the existing code. \
            Make sure **not to duplicate** existing lines such as `return area`.
            """.strip(),
        },
        {
            "role": "user",
            "content": f"```python\n{prefix}#TODO: You Code Here{suffix}\n```",
        },
    ]

def display_test_case(json_str: str, deployment: str) -> None:
    """
    Parse and display a test case JSONL entry in a readable format.
    
    Args:
        json_str: The JSON string containing the test case
        deployment: The model deployment name
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
        
        # Single completion case
        print(f"\nLLM COMPLETION {deployment}:")
        print("-" * 40)
        print(test_case[deployment])
        
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

def process_jsonl_file(input_file: str, output_file: str, deployment: str) -> None:
    """
    Process each line in a JSONL file and write formatted test cases to a text file.
    
    Args:
        input_file: Path to input JSONL file
        output_file: Path to output text file
        deployment: The model deployment name
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
                    display_test_case(line, deployment)
                    
                    # Get captured output and write to file
                    output = output_buffer.getvalue()
                    f_out.write(output)
                    
                except Exception as e:
                    f_out.write(f"Error processing test case: {str(e)}\n")
                
                finally:
                    # Restore original stdout
                    sys.stdout = original_stdout
                    output_buffer.close()

# Consolidated function to call Azure AI Inference models
def call_inference_model(prefix, suffix, deployment_info):
    """
    Call any model using the Azure AI Inference SDK.
    
    Args:
        prefix: The code prefix
        suffix: The code suffix
        deployment_info: Dictionary containing model name and type
    
    Returns:
        Model completion as string
    """
    deployment_type = deployment_info["type"]
    deployment_name = deployment_info["name"]
    
    # Select appropriate client and model based on deployment type
    if deployment_type == MODEL_TYPE_DEEPSEEK_R1:
        client = deepseek_r1_client
        model_name = DEEPSEEK_R1_MODEL
        use_chat_api = False
    elif deployment_type == MODEL_TYPE_DEEPSEEK_V3:
        client = deepseek_v3_client
        model_name = DEEPSEEK_V3_MODEL
        use_chat_api = False
    elif deployment_type == MODEL_TYPE_MINISTRAL:
        client = ministral_client
        model_name = MINISTRAL_MODEL
        use_chat_api = False
    else:
        return "Error: Unknown inference model type"
    
    try:
        # Get messages using the new format
        messages = get_prompt_template(prefix, suffix)
        
        if use_chat_api:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=800,
                temperature=TEMPERATURE,
                stream=False
            )
            
            return completion.choices[0].message.content
        else:
            # For ChatCompletionsClient (other models)
            # Convert to SDK format
            sdk_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    sdk_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    sdk_messages.append(UserMessage(content=msg["content"]))
            
            # Model-specific API calls
            if deployment_type in [MODEL_TYPE_DEEPSEEK_R1, MODEL_TYPE_DEEPSEEK_V3]:
                max_retries = 3 if deployment_type in [MODEL_TYPE_DEEPSEEK_R1, MODEL_TYPE_DEEPSEEK_V3] else 1
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        timeout = 600 if deployment_type in [MODEL_TYPE_DEEPSEEK_R1, MODEL_TYPE_DEEPSEEK_V3] else 300
                        
                        response = client.complete(
                            messages=sdk_messages,
                            model=model_name,
                            stream=False,
                            timeout=timeout
                        )
                        break
                    except Exception as retry_error:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"Attempt {retry_count} failed for {deployment_name}. Retrying in {retry_count * 5} seconds...")
                            import time
                            time.sleep(retry_count * 5)
                        else:
                            raise retry_error
            elif deployment_type == MODEL_TYPE_MINISTRAL:
                response = client.complete(
                    messages=sdk_messages,
                    max_tokens=800,
                    temperature=TEMPERATURE,
                    top_p=1.0,
                    model=model_name,
                    stream=False
                )
            
            response_content = response.choices[0].message.content
            
            if deployment_type == MODEL_TYPE_DEEPSEEK_R1:
                response_content = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()
                
            return response_content

    except Exception as e:
        print(f"Error calling {deployment_name} endpoint: {str(e)}")
        return f"Error: API request failed - {str(e)}"

# Function to call Claude models
def call_claude(prefix, suffix, deployment_info):
    """
    Call Claude API using Anthropic client.
    
    Args:
        prefix: The code prefix
        suffix: The code suffix
        deployment_info: Dictionary containing model name and type
    
    Returns:
        Model completion as string
    """
    try:
        model_type = deployment_info["type"]
        if model_type == MODEL_TYPE_CLAUDE_35:
            model = CLAUDE_35_MODEL
        elif model_type == MODEL_TYPE_CLAUDE_37:
            model = CLAUDE_37_MODEL
        else:
            return "Error: Unknown Claude model type"
            
        # Get messages using the template
        template_messages = get_prompt_template(prefix, suffix)
        
        # Extract system message and user messages
        system_content = ""
        user_messages = []
        
        for msg in template_messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            elif msg["role"] == "user":
                user_messages.append({"role": "user", "content": msg["content"]})
        
        # Call Claude API with system as top-level parameter
        response = claude_client.messages.create(
            model=model,
            max_tokens=800,
            temperature=TEMPERATURE,
            system=system_content,
            messages=user_messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        print(f"Error calling Claude endpoint: {str(e)}")
        return f"Error: API request failed - {str(e)}"


# Updated function to route to appropriate API based on model type
def call_endpoint(prefix, suffix, deployment_info):
    # Extract deployment name and type
    deployment_name = deployment_info["name"]
    deployment_type = deployment_info["type"]
    
    # Call appropriate endpoint based on model type
    if deployment_type in [MODEL_TYPE_DEEPSEEK_R1, MODEL_TYPE_DEEPSEEK_V3, MODEL_TYPE_MINISTRAL]:
        return call_inference_model(prefix, suffix, deployment_info)
    elif deployment_type == MODEL_TYPE_O3MINI:
        try:
            # Use new message format
            messages = get_prompt_template(prefix, suffix)
            
            # Send request to o3-mini
            completion = o3mini_client.chat.completions.create(
                model=O3MINI_DEPLOYMENT,
                messages=messages,
                stream=False
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling o3-mini endpoint: {str(e)}")
            return f"Error: API request failed - {str(e)}"
    elif deployment_type in [MODEL_TYPE_CLAUDE_35, MODEL_TYPE_CLAUDE_37]:
        return call_claude(prefix, suffix, deployment_info)
    elif deployment_type in [MODEL_TYPE_GPT4OMINI, MODEL_TYPE_GPT4O]:
        try:
            # Use new message format for chat models
            messages = get_prompt_template(prefix, suffix)
            
            # Different parameter name for tokens depending on the model
            if deployment_type == MODEL_TYPE_GPT4OMINI:
                token_param = {"max_tokens": 800}
                client_to_use = gpt4omini_client
                model_deployment = GPT4OMINI_DEPLOYMENT
            elif deployment_type == MODEL_TYPE_GPT4O:
                token_param = {"max_tokens": 800}
                client_to_use = gpt4o_client
                model_deployment = GPT4O_DEPLOYMENT
            
            # Send request
            completion = client_to_use.chat.completions.create(
                model=model_deployment,
                messages=messages,
                temperature=TEMPERATURE,
                top_p=1.0,
                stream=False,
                **token_param
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling {deployment_name} endpoint: {str(e)}")
            return f"Error: API request failed - {str(e)}"
    elif deployment_type == MODEL_TYPE_GPT41MINI:
        try:
            # Use new message format for chat models
            messages = get_prompt_template(prefix, suffix)
            
            # Send request to GPT-4.1 mini
            completion = gpt41mini_client.chat.completions.create(
                model=GPT41MINI_DEPLOYMENT,
                messages=messages,
                max_tokens=800,
                temperature=TEMPERATURE,
                top_p=1.0,
                frequency_penalty=0,  
                presence_penalty=0,
                stream=False
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling {deployment_name} endpoint: {str(e)}")
            return f"Error: API request failed - {str(e)}"
    elif deployment_type == MODEL_TYPE_GPT41NANO:
        try:
            # Use new message format for chat models
            messages = get_prompt_template(prefix, suffix)
            
            # Send request to GPT-4.1 nano
            completion = gpt41nano_client.chat.completions.create(
                model=GPT41NANO_DEPLOYMENT,
                messages=messages,
                max_tokens=800,
                temperature=TEMPERATURE,
                top_p=1.0,
                frequency_penalty=0,  
                presence_penalty=0,
                stream=False
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling {deployment_name} endpoint: {str(e)}")
            return f"Error: API request failed - {str(e)}"
    else:  # Default to Azure OpenAI
        try:
            # Use new message format but adjust for Azure OpenAI content format
            messages = get_prompt_template(prefix, suffix)
            
            # Convert to Azure OpenAI format
            chat_prompt = []
            for msg in messages:
                if msg["role"] == "system":
                    chat_prompt.append({
                        "role": "system",
                        "content": [{"type": "text", "text": msg["content"]}]
                    })
                else:
                    chat_prompt.append({
                        "role": "user",
                        "content": [{"type": "text", "text": msg["content"]}]
                    })
            
            # Send request to Azure OpenAI
            completion = client.chat.completions.create(
                model=deployment_name,
                messages=chat_prompt,
                max_completion_tokens=800,
                temperature=TEMPERATURE,
                top_p=1,
                frequency_penalty=0.2,
                presence_penalty=0.2,
                stop=None,
                stream=False
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling endpoint: {str(e)}")
            return "Error: API request failed"

# Function to process JSONL file for a single deployment
def process_jsonl(input_file, output_file, deployment_info):
    deployment_name = deployment_info["name"]
    
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            try:
                # Parse JSON line
                data = json.loads(line.strip())

                # Extract prefix and suffix
                prefix = data.get("prefix", "")
                suffix = data.get("suffix", "")

                # Call the endpoint and get completion
                completion = call_endpoint(prefix, suffix, deployment_info)
                
                # Clean any markdown formatting from the completion
                completion = clean_markdown_formatting(completion)
                
                # Store result in field with deployment name
                data[deployment_name] = completion

                # Write updated entry back to the output file
                json.dump(data, outfile)
                outfile.write("\n")  # Ensure each JSON object is on a new line

                # Print output for debugging
                print(f"Processed entry with model {deployment_name}")

            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON line: {e}")

def validate_completions():
    """
    Validate the generated completions by checking for API request failures.
    Iterates through all JSONL files in the output directory and counts
    error occurrences per file.
    """
    print("\n" + "="*80)
    print("VALIDATING COMPLETIONS - CHECKING FOR API ERRORS")
    print("="*80)
    
    # File pattern for JSONL files
    file_pattern = "*.jsonl"
    
    # Dictionary to store error counts per file
    error_counts = defaultdict(int)
    # Dictionary to track total processed lines per file
    total_lines = defaultdict(int)
    # Dictionary to track models with errors
    model_error_counts = defaultdict(int)
    
    # Walk through the output directory
    for file_path in glob.glob(f"{OUTPUT_DIR}/**/{file_pattern}", recursive=True):
        # Skip formatted text files
        if "_formatted" in file_path:
            continue
            
        # Extract deployment name more carefully from filename
        base_filename = os.path.basename(file_path)
        # We need to find the model name part after the first hyphen
        if '-' in base_filename:
            # Get everything after the first hyphen but before the .jsonl extension
            deployment_name = base_filename.split('-', 1)[1].replace('.jsonl', '')
        else:
            # Fallback if filename doesn't contain expected format
            print(f"Warning: Couldn't extract deployment name from {file_path}")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # Parse the JSON line
                        data = json.loads(line.strip())
                        total_lines[file_path] += 1
                        
                        # Check if the completion contains an error message (as substring)
                        error_found = False
                        
                        # Check completion
                        if deployment_name in data and isinstance(data[deployment_name], str) and "Error: API request failed" in data[deployment_name]:
                            error_counts[file_path] += 1
                            model_error_counts[deployment_name] += 1
                            error_found = True
                                
                        # Print first error found for debugging
                        if error_found and error_counts[file_path] == 1:
                            print(f"Found error in {file_path}, line {line_num}:")
                            print(f"Error message: {data[deployment_name][:500]}...")  # Print first 500 chars
                            
                    except json.JSONDecodeError:
                        print(f"Warning: Invalid JSON at line {line_num} in {file_path}")
                    except Exception as e:
                        print(f"Error processing line {line_num} in {file_path}: {str(e)}")
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
    
    # Print the validation results
    print("\nValidation Results:")
    print("-" * 40)
    
    if not error_counts:
        print("No API errors found in any completion files.")
    else:
        print("Files with API errors:")
        for file_path, count in sorted(error_counts.items()):
            total = total_lines[file_path]
            error_percentage = (count / total) * 100 if total > 0 else 0
            print(f"{file_path}: {count}/{total} lines contain errors ({error_percentage:.2f}%)")
        
        print("\nErrors by model:")
        for model_name, count in sorted(model_error_counts.items()):
            print(f"{model_name}: {count} errors")
    
    # Calculate overall statistics
    total_error_count = sum(error_counts.values())
    total_line_count = sum(total_lines.values())
    overall_error_rate = (total_error_count / total_line_count) * 100 if total_line_count > 0 else 0
    
    print("\nOverall Statistics:")
    print(f"Total files processed: {len(total_lines)}")
    print(f"Total lines processed: {total_line_count}")
    print(f"Total errors found: {total_error_count} ({overall_error_rate:.2f}%)")
    print("="*80)

def generate_all_formatted_text_files():
    """
    Generate formatted text files for all JSONL files in the output directory.
    This runs as a separate operation at the end of processing to ensure all
    files have corresponding formatted versions, even if they already exist.
    """
    print("\n" + "="*80)
    print("GENERATING FORMATTED TEXT FILES FOR ALL COMPLETIONS")
    print("="*80)
    
    # Track counts for reporting
    total_files = 0
    successful_files = 0
    
    # Walk through the output directory to find JSONL files
    for file_path in glob.glob(f"{OUTPUT_DIR}/**/*.jsonl", recursive=True):
        # Skip files that already have _formatted in the name
        if "_formatted" in file_path:
            continue
            
        total_files += 1
        
        # Extract deployment name from filename
        base_filename = os.path.basename(file_path)
        if '-' in base_filename:
            # Extract deployment name
            deployment_name = base_filename.split('-', 1)[1].replace('.jsonl', '')
        else:
            print(f"Warning: Couldn't extract deployment name from {file_path}")
            continue
            
        # Generate the formatted text file path
        output_txt_file = file_path.replace('.jsonl', '_formatted.txt')
        
        try:
            print(f"Generating formatted output for {file_path}")
            process_jsonl_file(file_path, output_txt_file, deployment_name)
            successful_files += 1
        except Exception as e:
            print(f"Error generating formatted text for {file_path}: {str(e)}")
    
    # Print summary
    print("\nFormatting Summary:")
    print(f"Total JSONL files processed: {total_files}")
    print(f"Successful formatting: {successful_files}")
    print(f"Failed formatting: {total_files - successful_files}")
    print("="*80)

def clean_markdown_formatting(text):
    """
    Remove markdown code block formatting from text while preserving indentation and whitespace.
    
    Args:
        text: The text to clean
    
    Returns:
        Cleaned text with markdown code blocks removed but indentation preserved
    """
    # Check if the text starts with a code block marker
    if text.lstrip().startswith("```"):
        # Extract the content inside the code block
        lines = text.split('\n')
        # Find the first line with code block marker
        start_index = -1
        for i, line in enumerate(lines):
            if line.lstrip().startswith("```"):
                start_index = i
                break
        
        if start_index >= 0:
            # Find the ending code block marker
            end_index = -1
            for i in range(start_index + 1, len(lines)):
                if lines[i].rstrip() == "```":
                    end_index = i
                    break
            
            if end_index > start_index:
                # Extract the content between markers
                code_content = lines[start_index+1:end_index]
                return '\n'.join(code_content)
    
    # If no code block markers found or couldn't parse properly, 
    # return the original text to avoid data loss
    return text

def main():
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Process each deployment separately
    for deployment_info in DEPLOYMENTS:
        deployment_name = deployment_info["name"]
        
        for language in languages:            
            # Process common directories for all languages
            for i in range(len(common_dirs)):
                curr_dir = common_dirs[i]
                curr_file = common_files[i]
                input_jsonl = f"benchmark/{language}/{curr_dir}/{curr_file}.jsonl"
                
                # Set output filename
                output_jsonl = f"{OUTPUT_DIR}/{language}/{curr_dir}/{curr_file}-{deployment_name}.jsonl"

                # Create output directory if it doesn't exist
                os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
                
                # Process with the current deployment
                process_jsonl(input_jsonl, output_jsonl, deployment_info)
                print(f"Processing completed for {deployment_name} ({language}/{curr_dir}). JSONL saved to {output_jsonl}.")

                # Generate formatted text output
                output_txt_file = output_jsonl.replace('.jsonl', '_formatted.txt')
                print(f"\nGenerating formatted output in {output_txt_file}...")
                process_jsonl_file(output_jsonl, output_txt_file, deployment_name)
                print("Formatting complete!")

    # Call validate_completions after processing all files
    validate_completions()

    # Finally, generate formatted text files for all JSONL files
    generate_all_formatted_text_files()

if __name__ == "__main__":
    main()
