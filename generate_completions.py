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
parser.add_argument('--num_completions', type=int, default=1, 
                    help='Number of completions to generate per test case (default: 1)')
parser.add_argument('--output_dir', type=str, default='completions',
                    help='Output directory for completions (default: completions)')
parser.add_argument('--temperature', type=float, default=0.0,
                    help='Temperature for model generation (default: 0.0)')
args = parser.parse_args()

# Number of completions to generate per test case
NUM_COMPLETIONS = args.num_completions  # Set from command-line arguments
# Output directory for completions
OUTPUT_DIR = args.output_dir  # Set from command-line arguments
# Temperature for model generation
TEMPERATURE = args.temperature  # Set from command-line arguments

print(f"Generating {NUM_COMPLETIONS} completion(s) per test case")
print(f"Using output directory: {OUTPUT_DIR}")
print(f"Using temperature: {TEMPERATURE}")

# Hardcoded Azure OpenAI Endpoint and API Key
ENDPOINT = "https://github-research-aoai-eastus2.openai.azure.com/"

O1MINI_ENDPOINT = "https://deepprompteastus.openai.azure.com/"  # Remove the deployment path
O1MINI_DEPLOYMENT = "deepprompt-o1-mini-2024-09-12-global"  # Add deployment name as separate variable
O1MINI_MODEL = "o1-mini"
O1MINI_API_VERSION = "2025-01-01-preview"  # Add API version

# Comment out the API key for o1-mini since we'll use token authentication
# O1MINI_API_KEY = os.getenv("O1MINI_API_KEY")  # Comment this line

# Update the O1PREVIEW_ENDPOINT to use the base URL without the deployment path
O1PREVIEW_ENDPOINT = "https://deepprompteastus.openai.azure.com/"
O1PREVIEW_DEPLOYMENT = "deepprompt-o1-preview"  # Add deployment name as separate variable
O1PREVIEW_API_VERSION = "2025-01-01-preview"  # Add API version

# Comment out the API key for o1-preview since we'll use token authentication
# O1PREVIEW_API_KEY = os.getenv("O1PREVIEW_API_KEY")

# o3-mini endpoint and deployment details
O3MINI_ENDPOINT = "https://deepprompteastus.openai.azure.com"  # Remove the deployment path from endpoint
O3MINI_DEPLOYMENT = "deepprompt-o3-mini-2025-01-31"  # The deployment name to use in API calls
O3MINI_API_VERSION = "2024-12-01-preview"

# Add Claude API configuration
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Add Claude endpoints and model names
CLAUDE_35_MODEL = "claude-3-5-sonnet-20240620"
CLAUDE_37_MODEL = "claude-3-7-sonnet-20250219"

# Define model types
MODEL_TYPE_AZURE_OPENAI = "azure_openai"
MODEL_TYPE_O1MINI = "o1mini"
MODEL_TYPE_O1PREVIEW = "o1preview"
MODEL_TYPE_O3MINI = "o3mini"
MODEL_TYPE_CLAUDE_35 = "claude_35_sonnet"
MODEL_TYPE_CLAUDE_37 = "claude_37_sonnet"

# Add GPT-4o mini endpoint and model details
GPT4OMINI_ENDPOINT = "https://deepprompteastus.openai.azure.com/"
GPT4OMINI_DEPLOYMENT = "deepprompt-gpt-4o-mini-2024-07-18"
GPT4OMINI_MODEL = "gpt-4o-mini"
GPT4OMINI_API_VERSION = "2025-01-01-preview"

# Add model type for GPT-4o mini
MODEL_TYPE_GPT4OMINI = "gpt4o_mini"

# Add API key environment variable
GPT4OMINI_API_KEY = os.getenv("GPT4OMINI_API_KEY")

# Add GPT-3.5 Turbo endpoint and model details
GPT35TURBO_ENDPOINT = "https://deeppromptnorthcentralus.openai.azure.com/"
GPT35TURBO_DEPLOYMENT = "deepprompt-gpt-35-turbo-0125"
GPT35TURBO_MODEL = "gpt-35-turbo"
GPT35TURBO_API_VERSION = "2024-12-01-preview"

# Add model type for GPT-3.5 Turbo
MODEL_TYPE_GPT35TURBO = "gpt35_turbo"

# Add API key environment variable
# GPT35TURBO_API_KEY = os.getenv("GPT35TURBO_API_KEY")

# Add DeepSeek R1 endpoint and model details
DEEPSEEK_R1_ENDPOINT = "https://DeepSeek-R1-xrkdn.eastus.models.ai.azure.com"
DEEPSEEK_R1_MODEL = "DeepSeek-R1"

# Add model type for DeepSeek R1
MODEL_TYPE_DEEPSEEK_R1 = "deepseek_r1"

# Add API key environment variable
DEEPSEEK_R1_API_KEY = os.getenv("DEEPSEEK_R1_API_KEY")

# Add GPT-4.5 endpoint and model details
GPT45_ENDPOINT = "https://DeepPromptEastUS2.openai.azure.com/"
GPT45_DEPLOYMENT = "gpt-4.5-preview"
GPT45_MODEL = "gpt-4.5-preview"
GPT45_API_VERSION = "2024-12-01-preview"

# Add model type for GPT-4.5
MODEL_TYPE_GPT45 = "gpt45_preview"

# Add API key environment variable
GPT45_API_KEY = os.getenv("GPT45_API_KEY")

# Add Ministral-3B endpoint and model details
MINISTRAL_ENDPOINT = "https://Ministral-3B-udnwz.eastus.models.ai.azure.com"
MINISTRAL_MODEL = "Ministral-3B"

# Add model type for Ministral-3B
MODEL_TYPE_MINISTRAL = "ministral_3b"

# Add API key environment variable
MINISTRAL_API_KEY = os.getenv("MINISTRAL_API_KEY")

# Add DeepSeek V3 endpoint and model details
DEEPSEEK_V3_ENDPOINT = "https://DeepSeek-V3-0324-emzev.eastus.models.ai.azure.com"
DEEPSEEK_V3_MODEL = "DeepSeek-V3-0324"

# Add model type for DeepSeek V3
MODEL_TYPE_DEEPSEEK_V3 = "deepseek_v3"

# Add API key environment variable
DEEPSEEK_V3_API_KEY = os.getenv("DEEPSEEK_V3_API_KEY")

# Add GPT-3.5 Turbo Completions (Instruct) endpoint and model details
GPT35TURBO_COMPLETIONS_ENDPOINT = "https://deeppromptnorthcentralus.openai.azure.com/"
GPT35TURBO_COMPLETIONS_DEPLOYMENT = "deepprompt-gpt-35-turbo-0125"
GPT35TURBO_COMPLETIONS_API_VERSION = "2023-09-15-preview"

# Add model type for GPT-3.5 Turbo Completions
MODEL_TYPE_GPT35TURBO_COMPLETIONS = "gpt35_turbo_completions"

# Add API key environment variable (using the same key as chat version if you want)
# GPT35TURBO_COMPLETIONS_API_KEY = os.getenv("GPT35TURBO_API_KEY")

# Add GPT-4.1 mini endpoint and model details
GPT41MINI_ENDPOINT = "https://ai-copilotevals.openai.azure.com/"
GPT41MINI_DEPLOYMENT = "gpt-4.1-mini"
GPT41MINI_MODEL = "gpt-4.1-mini"
GPT41MINI_API_VERSION = "2025-01-01-preview"

# Add model type for GPT-4.1 mini
MODEL_TYPE_GPT41MINI = "gpt41_mini"

# Add GPT-4.1 nano endpoint and model details
GPT41NANO_ENDPOINT = "https://ai-copilotevals.openai.azure.com/"
GPT41NANO_DEPLOYMENT = "gpt-4.1-nano"
GPT41NANO_MODEL = "gpt-4.1-nano"
GPT41NANO_API_VERSION = "2025-01-01-preview"

# Add model type for GPT-4.1 nano
MODEL_TYPE_GPT41NANO = "gpt41_nano"

# Add GPT-4o endpoint and model details
GPT4O_ENDPOINT = "https://deeppromptswedencentral.openai.azure.com/"
GPT4O_DEPLOYMENT = "deepprompt-gpt-4o-2024-05-13"
GPT4O_MODEL = "gpt-4o"
GPT4O_API_VERSION = "2025-01-01-preview"

# Add model type for GPT-4o
MODEL_TYPE_GPT4O = "gpt4o"

# Add API key environment variable
GPT4O_API_KEY = os.getenv("GPT4O_API_KEY")

# Add midtrain_devdiv4 endpoint and model details
MIDTRAIN_DEVDIV4_ENDPOINT = "https://copilot-ppe-centralus.openai.azure.com/"
MIDTRAIN_DEVDIV4_DEPLOYMENT = "chat-v7"
MIDTRAIN_DEVDIV4_MODEL = "midtrain_devdiv4_200B_sft39_api7_16_o3grader_v6_8"
MIDTRAIN_DEVDIV4_API_VERSION = "2024-08-01-preview"

# Add model type for midtrain_devdiv4
MODEL_TYPE_MIDTRAIN_DEVDIV4 = "midtrain_devdiv4"

# Add API key 
MIDTRAIN_DEVDIV4_API_KEY = "c01759dcf9f0464ca7f7ce22599c4939"

# Add midtrain_devdiv4 v4 endpoint and model details
MIDTRAIN_DEVDIV4_V4_ENDPOINT = "https://copilot-ppe-centralus.openai.azure.com/"
MIDTRAIN_DEVDIV4_V4_DEPLOYMENT = "chat-v4"
MIDTRAIN_DEVDIV4_V4_MODEL = "midtrain_devdivv4_200B_sft39_api7_v2_mixRLCES0311balancedV2_constraintV6parsing_10"
MIDTRAIN_DEVDIV4_V4_API_VERSION = "2024-08-01-preview"

# Add model type for midtrain_devdiv4 v4
MODEL_TYPE_MIDTRAIN_DEVDIV4_V4 = "midtrain_devdiv4_v4"

# Add to DEPLOYMENTS list
DEPLOYMENTS = [
    # {"name": "4omini_sft39_spm_fix2_5", "type": MODEL_TYPE_AZURE_OPENAI},
    # {"name": "o1-mini", "type": MODEL_TYPE_O1MINI},
    # {"name": "o1-preview", "type": MODEL_TYPE_O1PREVIEW},
    # {"name": "o3-mini", "type": MODEL_TYPE_O3MINI},
    # {"name": "claude-3-5-sonnet", "type": MODEL_TYPE_CLAUDE_35},
    # {"name": "claude-3-7-sonnet", "type": MODEL_TYPE_CLAUDE_37},
    # {"name": "gpt-4o-mini", "type": MODEL_TYPE_GPT4OMINI},
    # {"name": "gpt-35-turbo-completions", "type": MODEL_TYPE_GPT35TURBO_COMPLETIONS},
    # {"name": "DeepSeek-R1", "type": MODEL_TYPE_DEEPSEEK_R1},
    # {"name": "gpt-4.5-preview", "type": MODEL_TYPE_GPT45},
    # {"name": "Ministral-3B", "type": MODEL_TYPE_MINISTRAL},
    # {"name": "DeepSeek-V3-0324", "type": MODEL_TYPE_DEEPSEEK_V3},
    # {"name": "gpt-4.1-mini", "type": MODEL_TYPE_GPT41MINI},
    # {"name": "gpt-4.1-nano", "type": MODEL_TYPE_GPT41NANO},
    {"name": "gpt-4o", "type": MODEL_TYPE_GPT4O},
    # {"name": MIDTRAIN_DEVDIV4_MODEL, "type": MODEL_TYPE_MIDTRAIN_DEVDIV4},
    # {"name": MIDTRAIN_DEVDIV4_V4_MODEL, "type": MODEL_TYPE_MIDTRAIN_DEVDIV4_V4},
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
O1MINI_API_KEY = os.getenv("O1MINI_API_KEY")  # Add API key for o1-mini
O1PREVIEW_API_KEY = os.getenv("O1PREVIEW_API_KEY")  # Add API key for o1-preview
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

# Initialize o1-mini client
o1mini_client = AzureOpenAI(
    azure_endpoint=O1MINI_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version=O1MINI_API_VERSION,
)

# Update the o1-preview client initialization to use AzureOpenAI with token-based auth
o1preview_client = AzureOpenAI(
    azure_endpoint=O1PREVIEW_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version=O1PREVIEW_API_VERSION,
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

# Initialize GPT-3.5 Turbo client
gpt35turbo_client = AzureOpenAI(
    api_version=GPT35TURBO_API_VERSION,
    azure_endpoint=GPT35TURBO_ENDPOINT,
    azure_ad_token_provider=token_provider,
)

# Initialize DeepSeek R1 client
deepseek_r1_client = ChatCompletionsClient(
    endpoint=DEEPSEEK_R1_ENDPOINT,
    credential=AzureKeyCredential(DEEPSEEK_R1_API_KEY),
)

# Initialize GPT-4.5 client
gpt45_client = AzureOpenAI(
    api_version=GPT45_API_VERSION,
    azure_endpoint=GPT45_ENDPOINT,
    api_key=GPT45_API_KEY,
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

# Initialize midtrain_devdiv4 client
midtrain_devdiv4_client = AzureOpenAI(
    api_version=MIDTRAIN_DEVDIV4_API_VERSION,
    azure_endpoint=MIDTRAIN_DEVDIV4_ENDPOINT,
    api_key=MIDTRAIN_DEVDIV4_API_KEY,
)

# Initialize midtrain_devdiv4 v4 client (using same API key as v7)
midtrain_devdiv4_v4_client = AzureOpenAI(
    api_version=MIDTRAIN_DEVDIV4_V4_API_VERSION,
    azure_endpoint=MIDTRAIN_DEVDIV4_V4_ENDPOINT,
    api_key=MIDTRAIN_DEVDIV4_API_KEY,
)

# Replace the existing SPM_PROMPT_TEMPLATE with a function that returns the new template
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

# Keep the original template for backward compatibility with the completions API
SPM_PROMPT_TEMPLATE = """Please complete the code in the middle given the prefix code snippet and suffix code snippet.
Please respond without any formatting:
<code in the middle>

Suffix: {suffix}

Prefix: {prefix}

Code in the middle:"""

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
        
        # Check for multiple completions
        if NUM_COMPLETIONS > 1:
            for i in range(NUM_COMPLETIONS):
                field_name = f"{deployment}_completion_{i+1}"
                if field_name in test_case:
                    print(f"\nLLM COMPLETION {deployment} #{i+1}:")
                    print("-" * 40)
                    print(test_case[field_name])
        else:
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
    if deployment_type == MODEL_TYPE_O1MINI:
        client = o1mini_client
        model_name = O1MINI_DEPLOYMENT
        use_chat_api = True
    elif deployment_type == MODEL_TYPE_O1PREVIEW:
        client = o1preview_client
        model_name = O1PREVIEW_DEPLOYMENT
        use_chat_api = True
    elif deployment_type == MODEL_TYPE_DEEPSEEK_R1:
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
            # For AzureOpenAI client (o1-preview and o1-mini)
            # Convert system message to user message for models that don't support system role
            if deployment_type in [MODEL_TYPE_O1PREVIEW, MODEL_TYPE_O1MINI]:
                modified_messages = []
                system_content = ""
                
                # Extract system content and convert to a prefix for the user message
                for msg in messages:
                    if msg["role"] == "system":
                        system_content = msg["content"]
                    else:
                        # If there was a system message, prepend it to the user message
                        if system_content and msg["role"] == "user":
                            modified_messages.append({
                                "role": "user",
                                "content": f"{system_content}\n\n{msg['content']}"
                            })
                        else:
                            modified_messages.append(msg)
                
                messages = modified_messages if modified_messages else messages
                
                # Use max_completion_tokens instead of max_tokens
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_completion_tokens=800,
                    stream=False
                )
            else:
                # For other models that use the chat API but accept max_tokens
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
            if deployment_type in [MODEL_TYPE_O1MINI, MODEL_TYPE_DEEPSEEK_R1, MODEL_TYPE_DEEPSEEK_V3]:
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


# Function to call GPT-3.5 Turbo using Completions API with suffix mode
def call_gpt35turbo_completions(prefix, suffix, deployment_info):
    """
    Call GPT-3.5 Turbo using the Completions API with suffix mode enabled.
    
    Args:
        prefix: The code prefix
        suffix: The code suffix
        deployment_info: Dictionary containing model name and type
    
    Returns:
        Model completion as string
    """
    try:
        # Create AzureOpenAI client with token-based auth
        client = AzureOpenAI(
            azure_endpoint=GPT35TURBO_COMPLETIONS_ENDPOINT,
            azure_ad_token_provider=token_provider,
            api_version=GPT35TURBO_COMPLETIONS_API_VERSION,
        )
        
        # For completions API we still need to use the prefix/suffix format
        modified_prompt = f"{prefix}#TODO: You Code Here"
        
        # Use client to make the API call with suffix mode
        response = client.completions.create(
            model=GPT35TURBO_COMPLETIONS_DEPLOYMENT,
            prompt=modified_prompt,
            suffix=suffix,
            temperature=TEMPERATURE,
            max_tokens=800,
            stop="<|endoftext|>",
        )
        
        return response.choices[0].text.strip()
            
    except Exception as e:
        print(f"Error calling GPT-3.5 Turbo Completions endpoint: {str(e)}")
        return f"Error: API request failed - {str(e)}"

# Updated function to route to appropriate API based on model type
def call_endpoint(prefix, suffix, deployment_info):
    # Extract deployment name and type
    deployment_name = deployment_info["name"]
    deployment_type = deployment_info["type"]
    
    # Call appropriate endpoint based on model type
    if deployment_type in [MODEL_TYPE_O1MINI, MODEL_TYPE_O1PREVIEW, MODEL_TYPE_DEEPSEEK_R1, MODEL_TYPE_DEEPSEEK_V3, MODEL_TYPE_MINISTRAL]:
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
    elif deployment_type in [MODEL_TYPE_GPT4OMINI, MODEL_TYPE_GPT35TURBO, MODEL_TYPE_GPT45, MODEL_TYPE_GPT4O]:
        try:
            # Use new message format for chat models
            messages = get_prompt_template(prefix, suffix)
            
            # Different parameter name for tokens depending on the model
            if deployment_type == MODEL_TYPE_GPT45:
                token_param = {"max_completion_tokens": 800}
                client_to_use = gpt45_client
                model_deployment = GPT45_DEPLOYMENT
            elif deployment_type == MODEL_TYPE_GPT4OMINI:
                token_param = {"max_tokens": 800}
                client_to_use = gpt4omini_client
                model_deployment = GPT4OMINI_DEPLOYMENT
            elif deployment_type == MODEL_TYPE_GPT4O:
                token_param = {"max_tokens": 800}
                client_to_use = gpt4o_client
                model_deployment = GPT4O_DEPLOYMENT
            else:  # GPT35TURBO
                token_param = {"max_tokens": 800}
                client_to_use = gpt35turbo_client
                model_deployment = GPT35TURBO_DEPLOYMENT
            
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
    elif deployment_type == MODEL_TYPE_GPT35TURBO_COMPLETIONS:
        return call_gpt35turbo_completions(prefix, suffix, deployment_info)
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
    elif deployment_type == MODEL_TYPE_MIDTRAIN_DEVDIV4:
        try:
            # Use new message format for chat models
            messages = get_prompt_template(prefix, suffix)
            
            # Send request to midtrain_devdiv4
            completion = midtrain_devdiv4_client.chat.completions.create(
                model=MIDTRAIN_DEVDIV4_DEPLOYMENT,
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
    elif deployment_type == MODEL_TYPE_MIDTRAIN_DEVDIV4_V4:
        try:
            # Use new message format for chat models
            messages = get_prompt_template(prefix, suffix)
            
            # Send request to midtrain_devdiv4 v4
            completion = midtrain_devdiv4_v4_client.chat.completions.create(
                model=MIDTRAIN_DEVDIV4_V4_DEPLOYMENT,
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

                # Generate multiple completions if requested
                for i in range(NUM_COMPLETIONS):
                    # Call the endpoint and get completion
                    completion = call_endpoint(prefix, suffix, deployment_info)
                    
                    # Clean any markdown formatting from the completion
                    completion = clean_markdown_formatting(completion)
                    
                    # Store result in field with deployment name and completion number if multiple completions
                    if NUM_COMPLETIONS > 1:
                        field_name = f"{deployment_name}_completion_{i+1}"
                    else:
                        field_name = deployment_name
                        
                    data[field_name] = completion

                # Write updated entry back to the output file
                json.dump(data, outfile)
                outfile.write("\n")  # Ensure each JSON object is on a new line

                # Print output for debugging
                print(f"Processed entry with model {deployment_name} - generated {NUM_COMPLETIONS} completion(s)")

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
    
    # Determine file pattern suffix based on number of completions
    file_pattern_suffix = f"_x{NUM_COMPLETIONS}.jsonl" if NUM_COMPLETIONS > 1 else ".jsonl"
    
    # Dictionary to store error counts per file
    error_counts = defaultdict(int)
    # Dictionary to track total processed lines per file
    total_lines = defaultdict(int)
    # Dictionary to track models with errors
    model_error_counts = defaultdict(int)
    
    # Walk through the output directory
    for file_path in glob.glob(f"{OUTPUT_DIR}/**/*{file_pattern_suffix}", recursive=True):
        # Skip formatted text files
        if "_formatted" in file_path:
            continue
            
        # Extract deployment name more carefully from filename
        base_filename = os.path.basename(file_path)
        # Format is typically like: "code_purpose_understanding-o1-mini.jsonl" or "code_purpose_understanding-o1-mini_x3.jsonl"
        # We need to find the model name part after the first hyphen
        if '-' in base_filename:
            # Get everything after the first hyphen but before the .jsonl or _x3.jsonl extension
            if "_x" in base_filename:
                deployment_name = base_filename.split('-', 1)[1].split('_x')[0]
            else:
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
                        # Handle both single completion and multiple completions
                        error_found = False
                        
                        if NUM_COMPLETIONS > 1:
                            # Check each completion when multiple are present
                            for i in range(NUM_COMPLETIONS):
                                field_name = f"{deployment_name}_completion_{i+1}"
                                if field_name in data and isinstance(data[field_name], str) and "Error: API request failed" in data[field_name]:
                                    error_counts[file_path] += 1
                                    model_error_counts[deployment_name] += 1
                                    error_found = True
                                    break
                        else:
                            # Check single completion
                            if deployment_name in data and isinstance(data[deployment_name], str) and "Error: API request failed" in data[deployment_name]:
                                error_counts[file_path] += 1
                                model_error_counts[deployment_name] += 1
                                error_found = True
                                
                        # Print first error found for debugging
                        if error_found and error_counts[file_path] == 1:
                            field_name = f"{deployment_name}_completion_1" if NUM_COMPLETIONS > 1 else deployment_name
                            print(f"Found error in {file_path}, line {line_num}:")
                            print(f"Error message: {data[field_name][:500]}...")  # Print first 500 chars
                            
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

def regenerate_failed_completions():
    """
    Regenerate completions for entries that failed with API errors.
    Identifies failures and tries to regenerate them, printing the new JSONL.
    """
    print("\n" + "="*80)
    print("REGENERATING FAILED COMPLETIONS")
    print("="*80)
    
    # Determine file pattern suffix based on number of completions
    file_pattern_suffix = f"_x{NUM_COMPLETIONS}.jsonl" if NUM_COMPLETIONS > 1 else ".jsonl"
    
    # Store failed completions as (file_path, line_number) tuples
    failed_completions = []
    
    # Walk through the output directory to find failures
    for file_path in glob.glob(f"{OUTPUT_DIR}/**/*{file_pattern_suffix}", recursive=True):
        # Skip formatted text files
        if "_formatted" in file_path:
            continue
            
        # Extract deployment info
        base_filename = os.path.basename(file_path)
        if '-' in base_filename:
            # Extract deployment name (handling both single and multiple completion cases)
            if "_x" in base_filename:
                deployment_name = base_filename.split('-', 1)[1].split('_x')[0]
            else:
                deployment_name = base_filename.split('-', 1)[1].replace('.jsonl', '')
            
            # Find matching deployment info
            deployment_info = None
            for dep in DEPLOYMENTS:
                if dep["name"] == deployment_name:
                    deployment_info = dep
                    break
                    
            if not deployment_info:
                print(f"Warning: No deployment info found for {deployment_name}")
                continue
        else:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # Parse the JSON line
                        data = json.loads(line.strip())
                        
                        # Check for errors in completions
                        for i in range(NUM_COMPLETIONS):
                            field_name = f"{deployment_name}_completion_{i+1}" if NUM_COMPLETIONS > 1 else deployment_name
                            
                            if field_name in data and isinstance(data[field_name], str) and "Error: API request failed" in data[field_name]:
                                # Add to the failed completions list with completion number
                                failed_completions.append((file_path, line_num, data, deployment_info, i+1 if NUM_COMPLETIONS > 1 else 0))
                            
                    except json.JSONDecodeError:
                        print(f"Warning: Invalid JSON at line {line_num} in {file_path}")
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
    
    # Process each failed completion
    print(f"\nFound {len(failed_completions)} failed completions to regenerate.")
    
    for file_path, line_num, data, deployment_info, completion_num in failed_completions:
        deployment_name = deployment_info["name"]
        field_name = f"{deployment_name}_completion_{completion_num}" if NUM_COMPLETIONS > 1 else deployment_name
        
        print(f"\n{'-' * 40}")
        print(f"Regenerating: {file_path}, line {line_num}")
        print(f"Model: {deployment_name}" + (f", Completion #{completion_num}" if NUM_COMPLETIONS > 1 else ""))
        
        # Extract prefix and suffix
        prefix = data.get("prefix", "")
        suffix = data.get("suffix", "")
            
        # Add special handling for DeepSeek-R1
        if deployment_name == "DeepSeek-R1":
            max_attempts = 3
        else:
            max_attempts = 1
            
        for attempt in range(max_attempts):
            try:
                # Call the endpoint and get completion with longer timeout
                print(f"Calling model API... (Attempt {attempt+1}/{max_attempts})")
                completion = call_endpoint(prefix, suffix, deployment_info)
                
                if "Error: API request failed" in completion:
                    if attempt < max_attempts - 1:
                        print("Failed, retrying after delay...")
                        import time
                        time.sleep((attempt + 1) * 10)  # Increasing delay
                        continue
                    else:
                        print("All retry attempts failed")
                        break
                        
                # Update the data with the new completion
                data[field_name] = completion
                print("Successfully regenerated")
                break
                
            except Exception as e:
                print(f"Error on attempt {attempt+1}: {str(e)}")
                if attempt < max_attempts - 1:
                    import time
                    time.sleep((attempt + 1) * 10)
    
    print("\n" + "="*80)

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
    
    # Determine file pattern suffix for current number of completions
    file_pattern_suffix = f"_x{NUM_COMPLETIONS}.jsonl" if NUM_COMPLETIONS > 1 else ".jsonl"
    
    # Walk through the output directory to find JSONL files matching the current pattern
    for file_path in glob.glob(f"{OUTPUT_DIR}/**/*{file_pattern_suffix}", recursive=True):
        # Skip files that already have _formatted in the name
        if "_formatted" in file_path:
            continue
            
        total_files += 1
        
        # Extract deployment name from filename
        base_filename = os.path.basename(file_path)
        if '-' in base_filename:
            # Extract deployment name (handling both single and multiple completion cases)
            if "_x" in base_filename:
                deployment_name = base_filename.split('-', 1)[1].split('_x')[0]
            else:
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

def regenerate_deepseek_failures():
    """
    Specifically regenerate only the failed DeepSeek-R1 completions and apply the
    <think></think> tag removal logic to their outputs.
    """
    print("\n" + "="*80)
    print("REGENERATING FAILED DEEPSEEK-R1 COMPLETIONS")
    print("="*80)
    
    # Determine file pattern suffix based on number of completions
    file_pattern_suffix = f"_x{NUM_COMPLETIONS}.jsonl" if NUM_COMPLETIONS > 1 else ".jsonl"
    
    # Find deployment info for DeepSeek-R1
    deepseek_deployment = None
    for dep in DEPLOYMENTS:
        if dep["name"] == "DeepSeek-R1":
            deepseek_deployment = dep
            break
    
    if not deepseek_deployment:
        print("Error: DeepSeek-R1 deployment not found in DEPLOYMENTS list.")
        return
    
    # Store failed completions as (file_path, line_number, data, completion_num) tuples
    failed_completions = []
    
    # Find all the DeepSeek failures
    for file_path in glob.glob(f"{OUTPUT_DIR}/**/*-DeepSeek-R1{file_pattern_suffix}", recursive=True):
        if "_formatted" in file_path:
            continue
            
        print(f"Checking {file_path} for failures...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = list(f)
                for line_num, line in enumerate(lines, 1):
                    try:
                        data = json.loads(line.strip())
                        
                        # Check for failures in each completion
                        for i in range(NUM_COMPLETIONS):
                            field_name = f"DeepSeek-R1_completion_{i+1}" if NUM_COMPLETIONS > 1 else "DeepSeek-R1"
                            
                            if field_name in data and isinstance(data[field_name], str) and "Error: API request failed" in data[field_name]:
                                failed_completions.append((file_path, line_num, data, i+1 if NUM_COMPLETIONS > 1 else 0))
                                
                    except json.JSONDecodeError:
                        print(f"Warning: Invalid JSON at line {line_num} in {file_path}")
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
    
    print(f"\nFound {len(failed_completions)} DeepSeek-R1 failures to regenerate.")
    
    # Process each file's failures
    current_file = None
    file_lines = []
    updates_by_file = {}
    
    for file_path, line_num, data, completion_num in failed_completions:
        if current_file != file_path:
            # Save any previous file changes before moving to a new file
            if current_file and file_lines:
                updates_by_file[current_file] = file_lines
            
            # Move to new file
            current_file = file_path
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_lines = list(f)
            except Exception as e:
                print(f"Error reading {file_path}: {str(e)}")
                file_lines = []
                continue
        
        field_name = f"DeepSeek-R1_completion_{completion_num}" if NUM_COMPLETIONS > 1 else "DeepSeek-R1"
        completion_info = f", Completion #{completion_num}" if NUM_COMPLETIONS > 1 else ""
        
        print(f"Regenerating completion for {file_path}, line {line_num}{completion_info}")
        
        # Extract prefix and suffix
        prefix = data.get("prefix", "")
        suffix = data.get("suffix", "")
        
        # Try multiple times with exponential backoff
        max_attempts = 3
        success = False
        
        for attempt in range(max_attempts):
            try:
                print(f"Attempt {attempt+1}/{max_attempts}...")
                
                # Call DeepSeek-R1 with longer timeout
                user_message = get_prompt_template(prefix, suffix)
                messages = []
                for msg in user_message:
                    messages.append(SystemMessage(content=msg["content"]))
                
                response = deepseek_r1_client.complete(
                    messages=messages,
                    model=DEEPSEEK_R1_MODEL,
                    stream=False,
                    timeout=600  # 10 minutes timeout
                )
                
                # Extract and clean the response
                response_content = response.choices[0].message.content
                
                # Remove content inside <think> tags
                response_content = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()
                
                # Update the data and the line in the file
                data[field_name] = response_content
                file_lines[line_num-1] = json.dumps(data) + "\n"
                success = True
                print("Successfully regenerated completion")
                break
                
            except Exception as e:
                print(f"Error on attempt {attempt+1}: {str(e)}")
                if attempt < max_attempts - 1:
                    delay = (attempt + 1) * 15  # Longer delay between attempts
                    print(f"Retrying in {delay} seconds...")
                    import time
                    time.sleep(delay)
        
        if not success:
            print(f"Failed to regenerate completion after {max_attempts} attempts")
    
    # Save all updated files
    for file_path, lines in updates_by_file.items():
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"Updated {file_path}")
        except Exception as e:
            print(f"Error saving {file_path}: {str(e)}")
    
    print("\n" + "="*80)

def clean_all_deepseek_completions():
    """
    Process all existing DeepSeek-R1 completion files to remove content inside <think> tags.
    This function finds all DeepSeek-R1 JSONL files and cleans existing completions that
    may contain <think> tags from previous runs.
    """
    print("\n" + "="*80)
    print("CLEANING ALL DEEPSEEK-R1 COMPLETIONS - REMOVING <THINK> TAGS")
    print("="*80)
    
    # Determine file pattern suffix based on number of completions
    file_pattern_suffix = f"_x{NUM_COMPLETIONS}.jsonl" if NUM_COMPLETIONS > 1 else ".jsonl"
    
    # Find all DeepSeek-R1 JSONL files
    deepseek_files = glob.glob(f"{OUTPUT_DIR}/**/*-DeepSeek-R1{file_pattern_suffix}", recursive=True)
    print(f"Found {len(deepseek_files)} DeepSeek-R1 completion files")
    
    files_updated = 0
    entries_updated = 0
    
    for file_path in deepseek_files:
        # Skip formatted text files
        if "_formatted" in file_path:
            continue
            
        print(f"Processing {file_path}...")
        file_modified = False
        
        try:
            # Read all lines from the file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = list(f)
            
            # Process each line
            for i, line in enumerate(lines):
                try:
                    # Parse the JSON
                    data = json.loads(line.strip())
                    
                    # Check for multiple completions and clean each one
                    for j in range(NUM_COMPLETIONS):
                        field_name = f"DeepSeek-R1_completion_{j+1}" if NUM_COMPLETIONS > 1 else "DeepSeek-R1"
                        
                        # Check if it contains DeepSeek-R1 data
                        if field_name in data and isinstance(data[field_name], str):
                            # Get the original content
                            original_content = data[field_name]
                            
                            # Remove content inside <think> tags
                            cleaned_content = re.sub(r'<think>.*?</think>', '', original_content, flags=re.DOTALL).strip()
                            
                            # If the content changed, update it
                            if cleaned_content != original_content:
                                data[field_name] = cleaned_content
                                lines[i] = json.dumps(data) + "\n"
                                file_modified = True
                                entries_updated += 1
                            
                except json.JSONDecodeError:
                    print(f"Warning: Invalid JSON at line {i+1} in {file_path}")
                except Exception as e:
                    print(f"Error processing line {i+1} in {file_path}: {str(e)}")
            
            # Write the updated lines back to the file if any changes were made
            if file_modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                files_updated += 1
                print(f"Updated {file_path}")
            else:
                print(f"No <think> tags found in {file_path}")
                
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
    
    # Print summary
    print("\nCleaning Summary:")
    print(f"Total DeepSeek-R1 files found: {len(deepseek_files)}")
    print(f"Files updated: {files_updated}")
    print(f"Total entries cleaned: {entries_updated}")
    print("="*80)

def process_typescript_syntax_completion_line_by_line():
    """
    Process the TypeScript syntax completion file for DeepSeek-R1 completions one line at a time.
    Updates the file after each successful completion to ensure progress is saved.
    """
    print("\n" + "="*80)
    print("PROCESSING TYPESCRIPT SYNTAX COMPLETION FILE LINE BY LINE FOR DEEPSEEK-R1")
    print("="*80)
    
    # Determine file pattern suffix based on number of completions
    file_pattern_suffix = f"_x{NUM_COMPLETIONS}" if NUM_COMPLETIONS > 1 else ""
    
    # File path for the TypeScript syntax completion file
    file_path = f"{OUTPUT_DIR}/typescript/syntax_completion/syntax_completion-DeepSeek-R1{file_pattern_suffix}.jsonl"
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return
    
    # Get DeepSeek-R1 deployment info
    deepseek_deployment = None
    for dep in DEPLOYMENTS:
        if dep["name"] == "DeepSeek-R1":
            deepseek_deployment = dep
            break
    
    if not deepseek_deployment:
        print("Error: DeepSeek-R1 deployment not found in DEPLOYMENTS list.")
        return
    
    # Read all lines from the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = list(f)
        print(f"Successfully read {len(lines)} lines from {file_path}")
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return
    
    # Access the global variable
    global DEEPSEEK_R1_ENDPOINT
    global deepseek_r1_client
    
    # Store the original endpoint
    original_endpoint = DEEPSEEK_R1_ENDPOINT
    
    # Process each line one by one
    for line_num, line in enumerate(lines, 1):
        print(f"\nProcessing line {line_num}/{len(lines)}")
        
        try:
            # Parse the JSON line
            data = json.loads(line.strip())
            
            # Check each completion for errors
            for completion_num in range(1, NUM_COMPLETIONS + 1):
                field_name = f"DeepSeek-R1_completion_{completion_num}" if NUM_COMPLETIONS > 1 else "DeepSeek-R1"
                
                # Check if this entry has an error
                if field_name in data and isinstance(data[field_name], str) and "Error: API request failed" in data[field_name]:
                    print(f"Line {line_num}, Completion #{completion_num if NUM_COMPLETIONS > 1 else ''} has an error, attempting to fix...")
                    
                    # Extract prefix and suffix
                    prefix = data.get("prefix", "")
                    suffix = data.get("suffix", "")
                    
                    # Try multiple times with exponential backoff
                    max_attempts = 5  # Increase max attempts for reliability
                    success = False
                    
                    try:
                        # Temporarily modify the endpoint to lowercase
                        DEEPSEEK_R1_ENDPOINT = original_endpoint.lower()
                        
                        # Reinitialize the client with the lowercase endpoint
                        deepseek_r1_client = ChatCompletionsClient(
                            endpoint=DEEPSEEK_R1_ENDPOINT,
                            credential=AzureKeyCredential(DEEPSEEK_R1_API_KEY),
                        )
                        
                        for attempt in range(max_attempts):
                            try:
                                print(f"Attempt {attempt+1}/{max_attempts}...")
                                
                                # Call DeepSeek-R1 with longer timeout
                                user_message = get_prompt_template(prefix, suffix)
                                messages = []
                                for msg in user_message:
                                    messages.append(SystemMessage(content=msg["content"]))
                                
                                response = deepseek_r1_client.complete(
                                    messages=messages,
                                    model=DEEPSEEK_R1_MODEL,
                                    stream=False,
                                    timeout=600  # 10 minutes timeout, very generous
                                )
                                
                                # Extract and clean the response
                                response_content = response.choices[0].message.content
                                
                                # Remove content inside <think> tags
                                response_content = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()
                                
                                # Update the data
                                data[field_name] = response_content
                                
                                # Write the updated line back to the file
                                lines[line_num-1] = json.dumps(data) + "\n"
                                
                                # Save the file after each successful update
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.writelines(lines)
                                
                                success = True
                                print(f"Line {line_num}, Completion #{completion_num if NUM_COMPLETIONS > 1 else ''} successfully updated and file saved")
                                break
                                
                            except Exception as e:
                                print(f"Error on attempt {attempt+1}: {str(e)}")
                                if attempt < max_attempts - 1:
                                    delay = (attempt + 1) * 30  # Longer delay between attempts
                                    print(f"Retrying in {delay} seconds...")
                                    import time
                                    time.sleep(delay)
                    finally:
                        # Restore the original endpoint
                        DEEPSEEK_R1_ENDPOINT = original_endpoint
                        
                        # Reinitialize the client with the original endpoint
                        deepseek_r1_client = ChatCompletionsClient(
                            endpoint=DEEPSEEK_R1_ENDPOINT,
                            credential=AzureKeyCredential(DEEPSEEK_R1_API_KEY),
                        )
                    
                    if not success:
                        print(f"Failed to process line {line_num}, Completion #{completion_num if NUM_COMPLETIONS > 1 else ''} after {max_attempts} attempts")
                else:
                    print(f"Line {line_num}, Completion #{completion_num if NUM_COMPLETIONS > 1 else ''} already has a valid completion, skipping")
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON at line {line_num}")
        except Exception as e:
            print(f"Error processing line {line_num}: {str(e)}")
    
    print("\n" + "="*80)
    print("TYPESCRIPT SYNTAX COMPLETION PROCESSING COMPLETE")
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

def regenerate_and_save_failed_completions():
    """
    Regenerate completions that failed with API errors and save them back to the files.
    Uses the same error detection logic as validate_completions().
    """
    print("\n" + "="*80)
    print("REGENERATING AND SAVING FAILED COMPLETIONS")
    print("="*80)
    
    # Determine file pattern suffix based on number of completions
    file_pattern_suffix = f"_x{NUM_COMPLETIONS}.jsonl" if NUM_COMPLETIONS > 1 else ".jsonl"
    
    # Track statistics
    total_failures = 0
    successful_regenerations = 0
    failed_regenerations = 0
    files_updated = 0
    
    # Process each deployment separately to use the right client
    for deployment_info in DEPLOYMENTS:
        deployment_name = deployment_info["name"]
        deployment_type = deployment_info["type"]
        
        print(f"\nChecking for {deployment_name} failures...")
        
        # Find all files for this deployment
        deployment_files = glob.glob(f"{OUTPUT_DIR}/**/*-{deployment_name}{file_pattern_suffix}", recursive=True)
        
        if not deployment_files:
            print(f"No files found for {deployment_name}")
            continue
            
        print(f"Found {len(deployment_files)} files for {deployment_name}")
        
        # Process each file
        for file_path in deployment_files:
            # Skip formatted text files
            if "_formatted" in file_path:
                continue
                
            # Read the entire file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = list(f)
                
                file_modified = False
                
                # Process each line
                for line_idx, line in enumerate(lines):
                    try:
                        data = json.loads(line.strip())
                        
                        # Check each completion for API request failures
                        for comp_idx in range(NUM_COMPLETIONS):
                            field_name = f"{deployment_name}_completion_{comp_idx+1}" if NUM_COMPLETIONS > 1 else deployment_name
                            
                            # Match exactly what validate_completions() checks for
                            if field_name in data and isinstance(data[field_name], str) and "Error: API request failed" in data[field_name]:
                                total_failures += 1
                                print(f"\nRegenerating: {file_path}, line {line_idx+1}, field {field_name}")
                                print(f"Error message: {data[field_name][:100]}...")  # Print first 100 chars
                                
                                # Extract prefix and suffix
                                prefix = data.get("prefix", "")
                                suffix = data.get("suffix", "")
                                
                                # Determine max attempts based on model
                                max_attempts = 3 if deployment_name == "DeepSeek-R1" else 2
                                
                                # Try to regenerate
                                for attempt in range(max_attempts):
                                    try:
                                        print(f"Attempt {attempt+1}/{max_attempts}...")
                                        
                                        # Call the endpoint with appropriate timeout
                                        completion = call_endpoint(prefix, suffix, deployment_info)
                                        
                                        # Check if still an error
                                        if "Error: API request failed" in completion:
                                            if attempt < max_attempts - 1:
                                                print("Failed, retrying after delay...")
                                                import time
                                                time.sleep((attempt + 1) * 10)
                                                continue
                                            else:
                                                print(f"All {max_attempts} attempts failed")
                                                failed_regenerations += 1
                                                break
                                        
                                        # Model-specific post-processing (e.g., for DeepSeek-R1)
                                        if deployment_name == "DeepSeek-R1":
                                            completion = re.sub(r'<think>.*?</think>', '', completion, flags=re.DOTALL).strip()
                                        
                                        # Clean any markdown formatting
                                        completion = clean_markdown_formatting(completion)
                                        
                                        # Update the data
                                        data[field_name] = completion
                                        lines[line_idx] = json.dumps(data) + "\n"
                                        file_modified = True
                                        successful_regenerations += 1
                                        print("Successfully regenerated")
                                        break
                                        
                                    except Exception as e:
                                        print(f"Error on attempt {attempt+1}: {str(e)}")
                                        if attempt < max_attempts - 1:
                                            import time
                                            time.sleep((attempt + 1) * 10)
                                        else:
                                            failed_regenerations += 1
                    
                    except json.JSONDecodeError:
                        print(f"Warning: Invalid JSON at line {line_idx+1} in {file_path}")
                
                # Write the updated file if modified
                if file_modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    files_updated += 1
                    print(f"Updated file: {file_path}")
            
            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
    
    # Print summary
    print("\nRegeneration Summary:")
    print(f"Total failures identified: {total_failures}")
    print(f"Successfully regenerated: {successful_regenerations}")
    print(f"Failed to regenerate: {failed_regenerations}")
    print(f"Files updated: {files_updated}")
    print("="*80)
    
    # # Regenerate formatted text files for updated JSONLs
    # if files_updated > 0:
    #     print("\nRegenerating formatted text files for updated JSON files...")
    #     generate_all_formatted_text_files()

def detect_and_generate_missing_files():
    """
    Detect missing files across different completion configurations and generate them.
    This function:
    1. Determines expected files based on models, languages, and test types
    2. Checks which files actually exist
    3. Identifies and generates missing files
    """
    print("\n" + "="*80)
    print("DETECTING AND GENERATING MISSING FILES")
    print("="*80)
    
    # Models to check
    all_models = [
        {"name": "4omini_sft39_spm_fix2_5", "type": MODEL_TYPE_AZURE_OPENAI},
        {"name": "o1-mini", "type": MODEL_TYPE_O1MINI},
        {"name": "o1-preview", "type": MODEL_TYPE_O1PREVIEW},
        {"name": "o3-mini", "type": MODEL_TYPE_O3MINI},
        {"name": "claude-3-5-sonnet", "type": MODEL_TYPE_CLAUDE_35},
        {"name": "claude-3-7-sonnet", "type": MODEL_TYPE_CLAUDE_37},
        {"name": "gpt-4o-mini", "type": MODEL_TYPE_GPT4OMINI},
        {"name": "gpt-35-turbo-completions", "type": MODEL_TYPE_GPT35TURBO_COMPLETIONS},
        {"name": "DeepSeek-R1", "type": MODEL_TYPE_DEEPSEEK_R1},
        {"name": "gpt-4.5-preview", "type": MODEL_TYPE_GPT45},
        {"name": "Ministral-3B", "type": MODEL_TYPE_MINISTRAL},
        {"name": "DeepSeek-V3-0324", "type": MODEL_TYPE_DEEPSEEK_V3},
        {"name": "gpt-4.1-mini", "type": MODEL_TYPE_GPT41MINI},
        {"name": "gpt-4.1-nano", "type": MODEL_TYPE_GPT41NANO},
        {"name": "gpt-4o", "type": MODEL_TYPE_GPT4O},
    ]
    
    # File suffix based on number of completions
    completion_suffix = f"_x{NUM_COMPLETIONS}" if NUM_COMPLETIONS > 1 else ""
    file_pattern_suffix = f"{completion_suffix}.jsonl"
    
    # Find all existing files first and put them in a set for fast lookup
    existing_files_dict = {}
    for file_path in glob.glob(f"{OUTPUT_DIR}/**/*{file_pattern_suffix}", recursive=True):
        if "_formatted" in file_path:
            continue
        
        # Extract key components from the path
        base_name = os.path.basename(file_path)
        
        # Store path by its basename (model specific filename)
        existing_files_dict[base_name.lower()] = file_path
    
    expected_files = []
    missing_files = []
    
    # Build expected files and check against existing files
    for language in languages:
        # Process common directories
        for i, curr_dir in enumerate(common_dirs):
            curr_file = common_files[i]
            
            for model_info in all_models:
                model_name = model_info["name"]
                
                # Construct expected filename
                expected_filename = f"{curr_file}-{model_name}{completion_suffix}.jsonl"
                expected_path = os.path.join(OUTPUT_DIR, language, curr_dir, expected_filename)
                expected_files.append((expected_path, model_info))
                
                # Check if file exists (case insensitive)
                if expected_filename.lower() not in existing_files_dict:
                    missing_files.append((expected_path, model_info))
    
    # Report statistics
    print(f"\nTotal expected files: {len(expected_files)}")
    print(f"Existing files found: {len(existing_files_dict)}")
    print(f"Missing files: {len(missing_files)}")
    
    # Group and report missing files by model
    missing_by_model = defaultdict(list)
    for file_path, model_info in missing_files:
        missing_by_model[model_info["name"]].append(file_path)
    
    print("\nMissing files by model:")
    for model_name, files in missing_by_model.items():
        print(f"{model_name}: {len(files)} files")
        # Print the first few missing files for this model to help debug
        for i, file_path in enumerate(files[:3]):
            print(f"  - {os.path.basename(file_path)}")
            if i >= 2 and len(files) > 3:
                print(f"  - ... and {len(files)-3} more")
                break
    
    # Generate missing files if needed
    if missing_files:
        print("\nWould you like to generate the missing files? (y/n)")
        # Uncomment the code below to enable file generation
        
        # response = input().strip().lower()
        # if response == 'y':
        #     print("\nGenerating missing files...")
        #     for file_path, model_info in missing_files:
        #         # Extract language and directories from file path
        #         path_parts = os.path.normpath(file_path).split(os.path.sep)
        #         try:
        #             language_idx = path_parts.index(OUTPUT_DIR) + 1
        #             language = path_parts[language_idx]
        #         except (ValueError, IndexError):
        #             print(f"Could not determine language from path: {file_path}")
        #             continue
        #         
        #         # Get directory and file
        #         is_python_only = any(pd in path_parts for pd in [p.split('/')[0] for p in python_only_dirs])
        #         
        #         if is_python_only:
        #             for i, pd in enumerate(python_only_dirs):
        #                 if pd.split('/')[0] in path_parts:
        #                     curr_dir = pd
        #                     curr_file = python_only_files[i]
        #                     break
        #         else:
        #             for i, cd in enumerate(common_dirs):
        #                 if cd in path_parts:
        #                     curr_dir = cd
        #                     curr_file = common_files[i]
        #                     break
        #         
        #         # Get input file path
        #         input_jsonl = f"benchmark/{language}/{curr_dir}/{curr_file}.jsonl"
        #         
        #         # Create output directory
        #         os.makedirs(os.path.dirname(file_path), exist_ok=True)
        #         
        #         try:
        #             print(f"Generating: {file_path}")
        #             process_jsonl(input_jsonl, file_path, model_info)
        #             
        #             # Generate formatted text file
        #             output_txt_file = file_path.replace('.jsonl', '_formatted.txt')
        #             process_jsonl_file(file_path, output_txt_file, model_info["name"])
        #             
        #             print(f"Successfully generated: {file_path}")
        #         except Exception as e:
        #             print(f"Failed to generate {file_path}: {str(e)}")
    
    print("="*80)

def generate_missing_deepseek_files():
    """
    Generate only the missing DeepSeek-R1 files for TypeScript and JavaScript
    with 3 completions per test case.
    """
    print("\n" + "="*80)
    print("GENERATING MISSING DEEPSEEK-R1 FILES FOR JAVASCRIPT AND TYPESCRIPT")
    print("="*80)
    
    # Number of completions we're generating
    num_completions = 3
    
    # Output directory
    output_dir = "completions"
    
    # DeepSeek-R1 deployment info
    deepseek_deployment = {"name": "DeepSeek-R1", "type": MODEL_TYPE_DEEPSEEK_R1}
    
    # Missing file configurations (language, test_type)
    missing_files = [
        ("javascript", "code2NL_NL2code"),
        # ("javascript", "syntax_completion"),
        ("typescript", "api_usage"),
        ("typescript", "code_purpose_understanding"),
        ("typescript", "code2NL_NL2code"),
        ("typescript", "low_context"),
        ("typescript", "pattern_matching"),
        ("typescript", "syntax_completion")
    ]
    
    # Process each missing file
    for language, test_type in missing_files:
        # Construct input and output paths
        input_jsonl = f"benchmark/{language}/{test_type}/{test_type}.jsonl"
        output_jsonl = f"{output_dir}/{language}/{test_type}/{test_type}-{deepseek_deployment['name']}_x{num_completions}.jsonl"
        
        # Create output directory
        os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
        
        print(f"\nGenerating: {output_jsonl}")
        try:
            # Process the file with DeepSeek-R1 deployment
            process_jsonl(input_jsonl, output_jsonl, deepseek_deployment)
            
            # Generate formatted text file
            output_txt_file = output_jsonl.replace('.jsonl', '_formatted.txt')
            process_jsonl_file(output_jsonl, output_txt_file, deepseek_deployment['name'])
            
            print(f"Successfully generated: {output_jsonl}")
        except Exception as e:
            print(f"Error generating {output_jsonl}: {str(e)}")
    
    print("\nMissing file generation complete!")
    print("="*80)


def main():
    print(f"\nRunning with {NUM_COMPLETIONS} completion(s) per test case")
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
                
                # Adjust output filename based on number of completions
                if NUM_COMPLETIONS > 1:
                    output_jsonl = f"{OUTPUT_DIR}/{language}/{curr_dir}/{curr_file}-{deployment_name}_x{NUM_COMPLETIONS}.jsonl"
                else:
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

    # # Call validate_completions after processing all files
    # validate_completions()

    # # Regenerate and save failed completions
    # regenerate_and_save_failed_completions()

    # # Finally, generate formatted text files for all JSONL files
    # generate_all_formatted_text_files()

    # # Detect and generate missing files
    # detect_and_generate_missing_files()
    
    # # Generate the missing files
    # generate_missing_deepseek_files()

if __name__ == "__main__":
    main()
    # process_typescript_syntax_completion_line_by_line()
    # clean_all_deepseek_completions()

# Example usage:
# python generate_completions.py --output_dir new_completions
# python generate_completions.py --temperature 0.2 --output_dir new_completions_02_1
# python generate_completions.py --temperature 0.8 --output_dir new_completions_08_1
# python generate_completions.py --temperature 0.2 --output_dir new_completions_02_3 --num_completions 3
# python generate_completions.py --temperature 0.8 --output_dir new_completions_08_3 --num_completions 3
# python generate_completions.py --temperature 0.2 --output_dir new_completions_02_5 --num_completions 5
# python generate_completions.py --temperature 0.8 --output_dir new_completions_08_5 --num_completions 5

# python generate_completions.py --temperature 0.2 --output_dir new_completions_02_1_v5_v7