# DevBench: A Realistic, Developer-Informed Benchmark for Code Generation Models

[![arXiv](https://img.shields.io/badge/arXiv-2601.11895-b31b1b.svg)](https://arxiv.org/abs/2601.11895)

A telemetry-driven benchmark with 1,800 code completion tasks across six programming languages and six task categories. See the [paper](https://arxiv.org/abs/2601.11895) for full details on benchmark design, evaluation methodology, and results.

## Repository Structure

```
devbench/
├── benchmark/                  # 1,800 tasks (6 languages x 6 categories x 50 tasks)
│   └── {language}/{category}/
│       ├── {category}.jsonl
│       └── {category}_formatted.txt
├── completions/                # Pre-generated model completions (9 models x 5 per task)
│   └── {language}/{category}/
│       └── {category}-{model}.jsonl
├── judge_completions/          # LLM judge scores (Gemini 2.5 Flash)
│   └── judge_results.json
├── prompts/                    # Generation prompt templates (one per language)
├── evaluation/                 # Evaluation scripts
│   ├── execute_benchmark.py    #   Run completions against assertions
│   ├── compute_pass_at_1.py    #   Compute Pass@1 from saved completions
│   ├── evaluate_similarity.py  #   Cosine similarity + Line 0 Exact Match
│   ├── llm_judge.py            #   LLM judge (Gemini 2.5 Flash via Vertex AI)
│   └── calculate_complexity.py #   Benchmark complexity statistics
└── analysis/                   # Paper figure and table generation
    ├── generate_figures.py
    └── compute_category_correlations.py
```

## Benchmark Format

Each task is a JSON line in `benchmark/{language}/{category}/{category}.jsonl`:

```json
{
  "id": "1",
  "testsource": "devbench-api-usage",
  "language": "python",
  "prefix": "# Code before the cursor (visible to model)\n...",
  "golden_completion": "    # The correct completion\n...",
  "suffix": "# Code after the cursor (visible to model)\n...",
  "assertions": "# Hidden assertions (NOT visible to model)\n..."
}
```

The model sees `prefix + #TODO: Your Code Here + suffix`. The `assertions` are appended during execution but never shown to the model.

## Installation

**Platform:** Linux or macOS. Windows users should use [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).

### Option A: Docker (recommended)

```bash
docker build -t devbench .
docker run devbench                                                    # Pass@1
docker run devbench python evaluation/evaluate_similarity.py           # similarity
```

### Option B: Local setup

```bash
pip install -r requirements.txt
```

Language runtimes are auto-detected on `PATH`. Override with environment variables if needed:

| Language | Runtime | Min Version | Env var override |
|---|---|---|---|
| Python | python | 3.10+ | (current interpreter) |
| JavaScript | node | 18.0+ | `NODE_PATH` |
| TypeScript | node + tsc | 18.0+ | `NODE_PATH` |
| Java | javac, java | 11+ | `JAVAC_PATH`, `JAVA_PATH` |
| C++ | g++ or clang++ | C++17 | (auto-detected) |
| C# | dotnet | 6.0+ | (auto-detected) |

API keys (`.env` file) are only needed for generating new completions or running the LLM judge.

## Usage

```bash
# Compute Pass@1 from included completions
cd evaluation && python compute_pass_at_1.py

# Similarity metrics (cosine similarity + Line 0 exact match)
cd evaluation && python evaluate_similarity.py

# Benchmark complexity statistics
cd evaluation && python calculate_complexity.py

# Reproduce paper figures from judge scores
cd analysis && python generate_figures.py

# LLM judge (requires Vertex AI credentials)
cd evaluation && python llm_judge.py test
```

## Generation Parameters

All model completions included in this repository were generated with: temperature=0.2 (where supported; reasoning models use default settings), top-p=1.0, max output length=800 tokens, n=5 samples per task. Models are evaluated in a zero-shot, code-only setting using the fill-in-the-middle prompt defined in `evaluation/execute_benchmark.py`.

## Security

Benchmark execution runs LLM-generated code. Use a sandboxed environment with minimal permissions.

## Citation

```bibtex
@misc{devbench2026,
  author       = {Kumarappan, Adarsh and Golnari, Pareesa Ameneh and Wen, Wen and Liu, Xiaoyu and Ryan, Gabriel and Sun, Yuting and Fu, Shengyu and Nallipogu, Elsie},
  title        = {{DevBench}: A Realistic, Developer-Informed Benchmark for Code Generation Models},
  year         = {2026},
  eprint       = {2601.11895},
  archivePrefix = {arXiv},
  primaryClass = {cs.LG},
  url          = {https://arxiv.org/abs/2601.11895}
}
```

## License

MIT License - Copyright (c) Microsoft Corporation. See [LICENSE](LICENSE) for details.
