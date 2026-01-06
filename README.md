# DevBench

A comprehensive framework for generating, evaluating, and comparing code completions across multiple programming languages and AI models on our synthetic, telemetry-driven benchmark.

## Overview

DevBench provides tools for:
- Generating standardized code benchmark test cases across multiple programming languages
- Running code completions through various AI models
- Evaluating model performance using multiple metrics
- Analyzing and comparing results across models and languages
- Measuring code complexity metrics of benchmark cases

The benchmark supports execution-based evaluation across multiple programming languages:
- **Python** - Direct script execution with assertion checking, automatic pip install for missing packages
- **JavaScript** - Node.js execution with automatic npm dependency installation  
- **TypeScript** - Transpiled to JavaScript with TypeScript compiler, automatic npm install for missing packages
- **Java** - Compiled with javac or Gradle (automatic selection based on dependencies)
- **C++** - Compiled with g++/clang++ with automatic library detection and linking
- **C#** - Built and executed with .NET SDK, automatic NuGet package detection and installation

## Repository Structure

- `benchmark/` - Generated benchmark test cases organized by language and category
- `completions/` - Model-generated code completions for the benchmark test cases
- `prompts/` - Prompt templates for generating benchmark test cases
- `completion_evaluations/` - Evaluation scripts for analyzing model performance
- `complexities/` - Scripts for measuring code complexity metrics
- `execute_benchmark.py` - Script for executing benchmark tests and evaluating model completions
- `generate_completions.py` - Script for generating model completions

## Setup

### Requirements

- Python 3.10+
- Conda environment (recommended)
- API keys for various language models
- Azure CLI for authentication (if using Azure AI Foundry endpoints)

### Language-Specific Version Requirements

| Language | Tool | Minimum Version | Tested Version |
|----------|------|-----------------|----------------|
| Python | python | 3.10+ | 3.10, 3.11 |
| JavaScript | Node.js | 18.0+ | 18.x, 20.x, 22.x |
| TypeScript | Node.js + tsc | 18.0+ | TypeScript 5.x |
| Java | JDK | 8+ | OpenJDK 11, 17 |
| C++ | g++/clang++ | C++11+ | g++ 11.x, clang 14.x |
| C# | .NET SDK | 6.0+ | .NET 6.0, 7.0, 8.0 |

### Installation

1. Clone this repository
2. Create and activate a conda environment:
   ```bash
   conda create -n devbench python=3.10
   conda activate devbench
   ```
3. Install requirements:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Install Azure CLI following the [official documentation](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)
5. Authenticate with Azure:
   ```bash
   az login
   ```
6. Set your subscription:
   ```bash
   az account set --subscription <your-subscription-id>
   ```

### Environment Variables Setup

The code requires API keys and configuration for various language models and services. Create a `.env` file in the root directory with the following variables:

```
# Azure OpenAI Endpoints
ENDPOINT_URL="your_endpoint_url"
DEPLOYMENT_NAME="your_deployment_name"

# Model-Specific API Keys and Endpoints
GPT4O_API_KEY="your_gpt4o_api_key"
GPT41_API_KEY="your_gpt41_api_key"  # GPT-4.1
GPT41MINI_API_KEY="your_gpt41mini_api_key"  # GPT-4.1-mini
GPT41NANO_API_KEY="your_gpt41nano_api_key"  # GPT-4.1-nano
CLAUDE_API_KEY="your_claude_api_key"  # Claude 3.7 Sonnet and Claude 4 Sonnet
DEEPSEEK_V3_API_KEY="your_deepseek_v3_api_key"  # DeepSeek-V3
DEEPSEEK_V31_API_KEY="your_deepseek_v31_api_key"  # DeepSeek-V3.1
MINISTRAL_API_KEY="your_ministral_api_key"  # Ministral-3B
O3MINI_API_KEY="your_o3mini_api_key"  # o3-mini (for LLM judge)
O3MINI_ENDPOINT="your_o3mini_endpoint"  # o3-mini endpoint
O3MINI_DEPLOYMENT="your_o3mini_deployment"  # o3-mini deployment name

# General Completions API Key
COMPLETIONS_API_KEY="your_completions_api_key"

# API Keys for Test Case Execution (used within generated test code)
# These are needed only if your benchmark test cases use external APIs
AWS_ACCESS_KEY_ID="your_aws_access_key"  # For AWS API tests
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
AWS_REGION="your_aws_region"
S3_BUCKET_NAME="your_s3_bucket"
GITHUB_TOKEN="your_github_token"  # For GitHub API tests
OPENAI_API_KEY="your_openai_api_key"  # For OpenAI API tests
```

Replace the placeholder values with your actual API keys and credentials. You may not need all of these keys depending on which models you're using for evaluations.

**Security Note:** The benchmark execution scripts pass environment variables to subprocess calls, allowing test code to access API keys if needed (e.g., for tests that make GitHub API calls or AWS API calls). This is done via `env=os.environ.copy()` in subprocess calls. Ensure you run the benchmark in a secure, isolated environment.

### Prerequisites for Test Execution

To execute benchmark tests with `execute_benchmark.py`, you need the following language-specific tools installed:

#### Required Language Tools:
- **Python**: Python 3.10+ (already required for the framework)
- **JavaScript/TypeScript**: Node.js and npm
  - TypeScript will be installed automatically via npm when needed
- **Java**: JDK 8+ with `javac` and `java` commands available
  - Gradle will be downloaded automatically for complex test cases
- **C++**: A C++ compiler (`g++`, `clang++`, or `c++`)
  - Additional libraries may be needed (OpenSSL, Boost, etc.) - see C++ configuration below
- **C#**: .NET SDK 6.0+ with `dotnet` command available

Ensure these tools are in your system PATH or configure the paths as described below.

### System Configuration for Test Execution

When running test case execution with `execute_benchmark.py`, you may need to configure some system-specific paths:

#### Node.js/JavaScript/TypeScript Configuration

The script contains a placeholder `[NODE-BIN-PATH]` for Node.js binary paths. If `node`, `npm`, and `npx` are already in your system PATH, no changes are needed. Otherwise, replace `[NODE-BIN-PATH]` with your Node.js installation path.

**Lines to modify in `execute_benchmark.py`:**
- Line ~700: `nvm_bin_path = "[NODE-BIN-PATH]"` (JavaScript runner)
- Line ~890: `nvm_bin_path = "[NODE-BIN-PATH]"` (TypeScript runner)

**Examples:**
- macOS with nvm: `/Users/yourname/.nvm/versions/node/v22.17.0/bin`
- Linux with nvm: `/home/yourname/.nvm/versions/node/v22.17.0/bin`
- System installation: `/usr/local/bin` or leave as `[NODE-BIN-PATH]` to use system PATH

#### C++ Compilation Configuration

For C++ tests that require external libraries, you may need to:

1. **Install Required Libraries:**
   ```bash
   # macOS with Homebrew
   brew install openssl boost opencv eigen armadillo nlohmann-json
   
   # Ubuntu/Debian
   sudo apt-get install libssl-dev libboost-all-dev libopencv-dev libeigen3-dev libarmadillo-dev nlohmann-json3-dev
   
   # Fedora/RHEL
   sudo dnf install openssl-devel boost-devel opencv-devel eigen3-devel armadillo-devel json-devel
   ```

2. **Configure Include and Library Paths** (if needed):

   **Lines to modify in `execute_benchmark.py`:**
   - Line ~1290: `common_include_paths = []  # [CPP-INCLUDE-PATHS]`
   - Line ~1304: `common_lib_paths = []  # [CPP-LIB-PATHS]`
   
   **Examples for macOS with Homebrew:**
   ```python
   common_include_paths = ['/opt/homebrew/include', '/opt/homebrew/opt/openssl/include']
   common_lib_paths = ['/opt/homebrew/lib', '/opt/homebrew/opt/openssl/lib']
   ```
   
   **Examples for Linux:**
   ```python
   common_include_paths = ['/usr/include', '/usr/include/openssl']
   common_lib_paths = ['/usr/lib', '/usr/lib/x86_64-linux-gnu']
   ```

**Necessary C++ Libraries:**
- OpenSSL (crypto, SSL)
- Boost (system, filesystem)
- OpenCV (computer vision)
- Eigen (linear algebra)
- Armadillo (scientific computing)
- nlohmann/json (JSON parsing)
- pthread (threading)

### Important Note on Script Adaptation

The scripts `generate_completions.py` and `llm_judge.py` were used for our specific experimental setup, which primarily uses Azure AI Foundry to access various language models. If you're using different methods to access these models, you'll need to modify these scripts accordingly:

- `generate_completions.py`: This script contains anonymized endpoints (e.g., `[ANONYMIZED-ENDPOINT-1]`) and deployment names (e.g., `[ANONYMIZED-DEPLOYMENT-1]`). You will need to replace these with your own valid endpoints and deployment names for each model service you're using.
- `llm_judge.py`: This script also uses anonymized endpoints (e.g., `[ANONYMIZED-ENDPOINT-2]`) and deployment names (e.g., `[ANONYMIZED-DEPLOYMENT-3]`) for the o3-mini model used as a judge. You will need to replace these with your own valid endpoints and deployment names.

These scripts should be considered templates that demonstrate the methodology rather than plug-and-play solutions. You'll need to:
1. Replace all anonymized endpoints and deployment names with your actual values
2. Adapt the model access methods, API calls, and authentication to match your specific infrastructure
3. Ensure you have the proper API keys and credentials for each model you intend to use

### ⚠️ Security Warning: Executing LLM-Generated Code

**IMPORTANT**: Both the benchmark and model completions evaluation processes involve executing code generated by large language models. This code is **untrusted** and could potentially:

- Contain security vulnerabilities
- Access sensitive data
- Perform unintended or harmful operations
- Execute malicious logic

**Recommended Safety Measures**:
- Run all code execution in a containerized environment (Docker, etc.)
- Use environments with minimal permissions and no access to sensitive systems
- Do not run evaluations on production systems or with production credentials
- Inspect generated code before execution when possible
- Use sandbox environments with network and file system isolation

By using this benchmark system, you accept responsibility for any risks associated with executing AI-generated code. The authors of this project are not responsible for any damage or data loss that may result.

## Usage Guide

### Executing Benchmark Tests

Use `execute_benchmark.py` to run benchmark tests. There are two modes:

#### 1. Testing against Golden Completions

This mode tests the benchmark cases against their golden (correct) completions:

```bash
# Execute all Python benchmark test cases
python execute_benchmark.py --execute --verbose

# Execute specific language
python execute_benchmark.py --execute --language javascript --verbose

# Execute specific categories
python execute_benchmark.py --execute --categories api_usage,code_purpose_understanding --verbose

# Execute a specific test case
python execute_benchmark.py --execute --id <test_id> --verbose
```

Parameters:
- `--execute`: Flag to execute test cases (required)
- `--language`: Programming language (`python`, `javascript`, `c_sharp`, `cpp`, `typescript`, `java`, `all`)
- `--verbose`: Print detailed information during execution
- `--categories`: Comma-separated list of test categories to execute
- `--id`: Run a specific test case with the given ID
- `--report`: Path to output file for detailed test results

**Note:** Each test case execution has a 30-second timeout for Python/JavaScript/TypeScript/C++/C#, and 60 seconds for Java/Gradle builds to prevent hanging on infinite loops or blocking operations.

#### 2. Evaluating Model Completions

This mode evaluates the model-generated completions against the benchmark tests:

```bash
# Evaluate with pass@1 (single completion per test)
python execute_benchmark.py --execute --model-eval --verbose

# Evaluate with pass@k metrics (requires n≥k completions)
python execute_benchmark.py --execute --model-eval --pass-at-k 1 --verbose
python execute_benchmark.py --execute --model-eval --pass-at-k 5 --verbose

# Evaluate specific categories and models
python execute_benchmark.py --execute --model-eval --categories api_usage --models gpt-4o,claude-3-7-sonnet --verbose

# Evaluate all languages
python execute_benchmark.py --execute --model-eval --language all --pass-at-k 1 --verbose

# Output results to JSON file
python execute_benchmark.py --execute --model-eval --verbose --json-output benchmark_results.json
```

Parameters:
- `--execute`: Flag to execute test cases (required)
- `--model-eval`: Flag to evaluate model-generated completions
- `--pass-at-k`: Evaluate pass@k where k is the number of samples to consider (default: 1)
  - Requires generating n≥k completions with `generate_completions.py`
  - Uses formula: pass@k := E[1 - C(n-c, k) / C(n, k)]
- `--language`: Programming language for evaluation (`python`, `javascript`, `c_sharp`, `cpp`, `typescript`, `java`, `all`)
- `--verbose`: Print detailed information during execution
- `--categories`: Comma-separated list of test categories to evaluate
- `--models`: Comma-separated list of model names to evaluate
- `--json-output`: Path to JSON file for saving detailed results
- `--models-dir`: Directory containing model completions (default: completions/{language})
- `--report`: Path to output file for detailed test results

### Generating Model Completions

Use `generate_completions.py` to generate completions for benchmark test cases using different models.

**Supported Models (9 models):**
- GPT-4o (`gpt-4o`)
- GPT-4.1 (`gpt-4.1`)
- GPT-4.1-mini (`gpt-4.1-mini`)
- GPT-4.1-nano (`gpt-4.1-nano`)
- Claude 3.7 Sonnet (`claude-3-7-sonnet`)
- Claude 4 Sonnet (`claude-4-sonnet`)
- DeepSeek-V3 (`DeepSeek-V3-0324`)
- DeepSeek-V3.1 (`DeepSeek-V3.1`)
- Ministral-3B (`Ministral-3B`)

**Usage:**

```bash
# Generate single completion per test case (n=1, for traditional evaluation)
python generate_completions.py

# Generate multiple completions per test case (n=5, for pass@k evaluation)
python generate_completions.py --num_completions 5 --temperature 0.2

# Generate with custom output directory
python generate_completions.py --output_dir new_completions --num_completions 5
```

Parameters:
- `--output_dir`: Output directory for completions (default: completions)
- `--temperature`: Temperature for model generation (default: 0.0)
- `--num_completions`: Number of completions to generate per test case (default: 1)
  - Use n=1 for traditional pass/fail evaluation
  - Use n=5 or higher for pass@k evaluation metrics

**Features:**
- Automatically validates completions for API errors after generation
- Supports all 6 programming languages (Python, JavaScript, TypeScript, Java, C++, C#)
- Processes all 6 benchmark categories (api_usage, code2NL_NL2code, etc.)
- Skips already-generated files to allow resuming interrupted runs

### Evaluating Model Completions

Use `evaluate_completions.py` to compare generated completions against benchmarks:

```bash
# Evaluate completions with default settings
python evaluate_completions.py

# Custom evaluation with different paths
python evaluate_completions.py --completions ../new_completions --benchmark ../benchmark
```

Parameters:
- `--completions`: Path to the completions directory
- `--benchmark`: Path to the benchmark directory
- `--results`: Path for the output results JSON file
- `--plots`: Directory to save visualization plots
- `--debug`: Enable debug mode to print most dissimilar test cases

### Using LLM Judge for Completion Evaluation

Use `completion_evaluations/llm_judge.py` to evaluate model completions using a language model (o3-mini) as a judge:

```bash
cd completion_evaluations

# Evaluate all model completions
python llm_judge.py

# Evaluate specific models (space-separated)
python llm_judge.py --specific_models gpt-4o claude-3-7-sonnet DeepSeek-V3-0324

# Filter evaluations to specific languages (space-separated)
python llm_judge.py --language python javascript

# Limit number of evaluations (for testing)
python llm_judge.py --limit 10 --max_evaluations 100

# Generate only a summary from existing evaluations
python llm_judge.py --summary_only --plot --heatmap
```

Parameters:
- `--completions_dir`: Directory containing completion files (default: ../completions)
- `--output_dir`: Directory to save evaluation results (default: llm_judge_results)
- `--limit`: Optional limit on the number of files to process per model
- `--max_evaluations`: Optional limit on the total number of evaluations to run
- `--max_file_evaluations`: Optional limit on the number of evaluations per file
- `--summary_only`: Only generate summary without running evaluations
- `--specific_models`: List of specific models to evaluate
- `--language`: List of specific languages to evaluate
- `--plot`: Generate a comparison plot of model scores with confidence intervals
- `--heatmap`: Generate language-category heatmaps for models

### Analyzing Code Complexity

Use `complexities/calculate_complexity.py` to analyze complexity metrics of benchmark cases:

```bash
cd complexities
python calculate_complexity.py
```

This script calculates various code complexity metrics including:
- Line count
- Token count
- Cyclomatic complexity
