"""LLM Judge using Gemini 2.5 Flash via Vertex AI Batch API.

Judges all model completions against the benchmark using the same prompt
template from the paper.  Supports submitting batch requests, polling for
completion, collecting results, and computing per-model / per-language /
per-category score summaries with bootstrap confidence intervals.

Usage:
    python llm_judge.py test              # verify API connectivity
    python llm_judge.py submit [MODEL]    # submit batch requests
    python llm_judge.py poll              # poll batch job status
    python llm_judge.py collect           # collect results and print summary
    python llm_judge.py count             # count requests without submitting
    python llm_judge.py summarize FILE    # summarize a collected results JSON
"""

import json
import os
import sys
import re
import time
import glob
import argparse
from pathlib import Path
from collections import defaultdict

import numpy as np
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JUDGE_MODEL = "gemini-2.5-flash"
MAX_OUTPUT_TOKENS = 2048

# The 9 paper models
PAPER_MODELS = [
    'gpt-5.5', 'gpt-5.4-mini', 'gpt-5.4-nano',
    'claude-opus-4-7', 'claude-sonnet-4-6',
    'deepseek-v4-pro', 'llama-4-maverick', 'mistral-medium-3.5',
    'qwen3.6-27b',
]

MODELS_TO_JUDGE = list(PAPER_MODELS)

LANGUAGES = ['python', 'javascript', 'typescript', 'java', 'cpp', 'c_sharp']
CATEGORIES = [
    'api_usage', 'code2NL_NL2code', 'code_purpose_understanding',
    'low_context', 'pattern_matching', 'syntax_completion',
]

JUDGE_PROMPT_TEMPLATE = """You are a highly experienced software judge tasked with evaluating the quality of a model-generated code completion. For a given code prefix and suffix, your job is to evaluate a completion based on the criteria below and determine the overall final score (0-10). Assign a score (0-5) for each category. Please solely focus on the completion quality.

    # Evaluation Criteria:
    1. Relevance to Prefix and Suffix (0-5): Does the code completion connect semantically meaningfully to both the prefix and suffix?
    2. Helpfulness (0-5): Does the completion provide non-trivial assistance, adding meaningful content that reduces the user's effort in writing code?

    Based on the evaluation, provide your answer following format:
    Final Sum Score for Completion: <score>
    Detailed Reasoning:
    <your reasoning here>

    # Begin:
    Prefix:
    ```
    {prefix}
    ```

    Model Completion:
    ```
    {completion}
    ```

    Suffix:
    ```
    {suffix}
    ```
    """

# State file written by ``submit`` and read by ``poll`` / ``collect``
STATE_FILE = "gemini_judge_state.json"
RESULTS_FILE = "gemini_judge_results.json"


# ---------------------------------------------------------------------------
# Score extraction
# ---------------------------------------------------------------------------

def extract_score(response_text):
    """Parse the numeric score from a judge response."""
    try:
        m = re.search(
            r'Final\s+Sum\s+Score\s+for\s+Completion:?\s*(?:\*\*)?([0-9.]+)(?:\*\*)?',
            response_text, re.IGNORECASE,
        )
        if m:
            return float(m.group(1))
        for pat in [r'Final\s+Score:?\s*(?:\*\*)?([0-9.]+)',
                     r'Score:?\s*(?:\*\*)?([0-9.]+)']:
            m = re.search(pat, response_text, re.IGNORECASE)
            if m:
                return float(m.group(1))
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals
# ---------------------------------------------------------------------------

def bootstrap_ci(scores, n_bootstrap=10000, confidence=0.95):
    """Compute bootstrap confidence interval for the mean of *scores*.

    Parameters
    ----------
    scores : list[float]
        Raw score values.
    n_bootstrap : int
        Number of resamples.
    confidence : float
        Confidence level (e.g. 0.95 for 95% CI).

    Returns
    -------
    (lower, upper) : tuple[float, float]
    """
    n = len(scores)
    if n == 0:
        return (0.0, 0.0)
    arr = np.array(scores)
    means = [np.mean(np.random.choice(arr, n, replace=True)) for _ in range(n_bootstrap)]
    lo = np.percentile(means, (1 - confidence) / 2 * 100)
    hi = np.percentile(means, (1 + confidence) / 2 * 100)
    return float(lo), float(hi)


# ---------------------------------------------------------------------------
# Batch request building
# ---------------------------------------------------------------------------

def build_batch_requests():
    """Walk ``../completions/`` and build Gemini batch request payloads.

    Returns (requests, request_meta) where each element in *requests* is a
    dict suitable for ``client.batches.create(src=...)`` and *request_meta*
    holds the provenance information for each request.
    """
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    requests = []
    meta = []

    for model_short in MODELS_TO_JUDGE:
        for lang in LANGUAGES:
            for cat in CATEGORIES:
                comp_path = os.path.join(base, 'completions', lang, cat,
                                         f'{cat}-{model_short}.jsonl')
                if not os.path.exists(comp_path):
                    continue

                with open(comp_path) as f:
                    records = [json.loads(l) for l in f]

                for rec in records:
                    tid = rec['id']
                    prefix = rec.get('prefix', '')
                    suffix = rec.get('suffix', '')
                    completions = rec.get(f'{model_short}_completions', [])

                    for ci, completion in enumerate(completions):
                        prompt = JUDGE_PROMPT_TEMPLATE.format(
                            prefix=prefix, completion=completion, suffix=suffix,
                        )
                        requests.append({
                            'contents': [{'parts': [{'text': prompt}], 'role': 'user'}],
                        })
                        meta.append({
                            'model': model_short,
                            'lang': lang,
                            'cat': cat,
                            'tid': tid,
                            'comp_idx': ci,
                        })

    return requests, meta


# ---------------------------------------------------------------------------
# Batch submission / polling / collection
# ---------------------------------------------------------------------------

def submit_batch(requests, meta):
    """Submit Gemini batch job(s) and save state to *STATE_FILE*."""
    from google import genai

    client = genai.Client(vertexai=True, project=os.environ.get('GOOGLE_CLOUD_PROJECT', ''),
                          location='us-central1')

    print(f"Total requests: {len(requests)}")
    batch_size = 10000
    jobs = []

    for i in range(0, len(requests), batch_size):
        chunk = requests[i:i + batch_size]
        print(f"  Submitting chunk {i // batch_size + 1} ({len(chunk)} requests)...")
        try:
            job = client.batches.create(
                model=JUDGE_MODEL,
                src=chunk,
                config={'display_name': f'devbench-judge-chunk-{i // batch_size}'},
            )
            print(f"  Batch job: {job.name}")
            jobs.append({'name': job.name, 'start_idx': i, 'count': len(chunk)})
        except Exception as e:
            print(f"  ERROR: {e}")
            return None

    state = {'batch_jobs': jobs, 'meta': meta, 'total_requests': len(requests)}
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)
    print(f"State saved to {STATE_FILE}")
    return jobs


def poll_batches():
    """Poll until all batch jobs reach a terminal state."""
    from google import genai

    client = genai.Client(vertexai=True, project=os.environ.get('GOOGLE_CLOUD_PROJECT', ''),
                          location='us-central1')

    with open(STATE_FILE) as f:
        state = json.load(f)

    while True:
        all_done = True
        for job in state['batch_jobs']:
            b = client.batches.get(name=job['name'])
            status = f"  {job['name']}: {b.state}"
            if hasattr(b, 'completed_request_count'):
                status += f" ({b.completed_request_count}/{job['count']})"
            print(status, flush=True)
            if b.state not in ('JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED',
                               'JOB_STATE_CANCELLED'):
                all_done = False
        if all_done:
            print("All batch jobs complete!")
            break
        print("  Waiting 60s...", flush=True)
        time.sleep(60)


def collect_results():
    """Collect scored responses and write to *RESULTS_FILE*."""
    from google import genai

    client = genai.Client(vertexai=True, project=os.environ.get('GOOGLE_CLOUD_PROJECT', ''),
                          location='us-central1')

    with open(STATE_FILE) as f:
        state = json.load(f)

    meta = state['meta']
    all_scores = []
    idx = 0

    for job in state['batch_jobs']:
        b = client.batches.get(name=job['name'])
        if b.state != 'JOB_STATE_SUCCEEDED':
            print(f"  WARNING: {job['name']} state={b.state}, skipping")
            idx += job['count']
            continue
        for ir in b.dest.inlined_responses:
            text = ""
            try:
                text = ir.response.candidates[0].content.parts[0].text
            except Exception:
                pass
            score = extract_score(text)
            m = meta[idx]
            all_scores.append({
                'model': m['model'], 'lang': m['lang'], 'cat': m['cat'],
                'tid': m['tid'], 'comp_idx': m['comp_idx'],
                'score': score, 'full_response': text,
            })
            idx += 1

    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_scores, f, indent=2)
    print(f"Collected {len(all_scores)} results -> {RESULTS_FILE}")

    _print_summary(all_scores)


# ---------------------------------------------------------------------------
# Summary / aggregation
# ---------------------------------------------------------------------------

def _print_summary(all_scores):
    """Print per-model average scores to stdout."""
    valid = [s for s in all_scores if s['score'] is not None]
    print(f"\nValid scores: {len(valid)}/{len(all_scores)}")

    by_model = defaultdict(list)
    for s in valid:
        by_model[s['model']].append(s['score'])

    print("\n" + "=" * 72)
    print(f"{'Model':<25} {'Avg':>6} {'95% CI':>18} {'N':>6}")
    print("-" * 72)
    for model in sorted(by_model, key=lambda m: -np.mean(by_model[m])):
        scores = by_model[model]
        avg = np.mean(scores)
        lo, hi = bootstrap_ci(scores)
        print(f"{model:<25} {avg:>6.2f} [{lo:>6.2f}, {hi:>6.2f}] {len(scores):>6}")
    print("=" * 72)

    # Per-model per-language breakdown
    by_model_lang = defaultdict(lambda: defaultdict(list))
    for s in valid:
        by_model_lang[s['model']][s['lang']].append(s['score'])

    print("\nPer-language breakdown:")
    for model in sorted(by_model_lang):
        print(f"\n  {model}:")
        for lang in sorted(by_model_lang[model]):
            sc = by_model_lang[model][lang]
            lo, hi = bootstrap_ci(sc)
            print(f"    {lang:<14} {np.mean(sc):>6.2f}  CI [{lo:.2f}, {hi:.2f}]  (n={len(sc)})")

    # Per-model per-category breakdown
    by_model_cat = defaultdict(lambda: defaultdict(list))
    for s in valid:
        by_model_cat[s['model']][s['cat']].append(s['score'])

    print("\nPer-category breakdown:")
    for model in sorted(by_model_cat):
        print(f"\n  {model}:")
        for cat in sorted(by_model_cat[model]):
            sc = by_model_cat[model][cat]
            lo, hi = bootstrap_ci(sc)
            print(f"    {cat:<30} {np.mean(sc):>6.2f}  CI [{lo:.2f}, {hi:.2f}]  (n={len(sc)})")


def summarize_from_file(path):
    """Load a previously-collected results JSON and print the summary."""
    with open(path) as f:
        all_scores = json.load(f)
    _print_summary(all_scores)


# ---------------------------------------------------------------------------
# Test helper
# ---------------------------------------------------------------------------

def test_single():
    """Fire a single request to verify API connectivity."""
    from google import genai

    client = genai.Client(vertexai=True, project=os.environ.get('GOOGLE_CLOUD_PROJECT', ''),
                          location='us-central1')
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        prefix="def add(a, b):\n",
        completion="    return a + b",
        suffix="\n\nresult = add(1, 2)\nassert result == 3",
    )
    print(f"Testing single request to {JUDGE_MODEL}...")
    resp = client.models.generate_content(
        model=JUDGE_MODEL,
        contents=[{'role': 'user', 'parts': [{'text': prompt}]}],
        config={'max_output_tokens': MAX_OUTPUT_TOKENS,
                'thinking_config': {'thinking_budget': -1}},
    )
    text = resp.text or ""
    score = extract_score(text)
    print(f"Response: {text[:300]}")
    print(f"Score: {score}")
    return score is not None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python llm_judge.py [test|submit|poll|collect|count|summarize]")
        sys.exit(1)

    cmd = sys.argv[1]

    # Optional model filter
    model_filter = sys.argv[2] if len(sys.argv) > 2 and cmd != 'summarize' else None
    if model_filter:
        global MODELS_TO_JUDGE
        MODELS_TO_JUDGE = [model_filter]
        print(f"Filtering to model: {model_filter}")

    if cmd == 'test':
        ok = test_single()
        print(f"\nTest {'PASSED' if ok else 'FAILED'}")

    elif cmd == 'submit':
        reqs, meta = build_batch_requests()
        if not reqs:
            print("No requests to submit!")
            return
        submit_batch(reqs, meta)

    elif cmd == 'poll':
        poll_batches()

    elif cmd == 'collect':
        collect_results()

    elif cmd == 'count':
        reqs, meta = build_batch_requests()
        print(f"Total requests: {len(reqs)}")
        by_model = {}
        for m in meta:
            by_model[m['model']] = by_model.get(m['model'], 0) + 1
        for model, count in sorted(by_model.items()):
            print(f"  {model}: {count}")

    elif cmd == 'summarize':
        if len(sys.argv) < 3:
            path = RESULTS_FILE
        else:
            path = sys.argv[2]
        summarize_from_file(path)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()
