#!/usr/bin/env python3
"""Generate paper figures: Figure 2 (model comparison bar chart with CIs),
Figures 3-4 (per-model language x category heatmaps).

Reads judge_results.json and produces:
  - figures/model_comparison_plot.png  (Figure 2: bar chart with 95% CIs)
  - figures/heatmap_part1.png          (Figure 3: top-5 model heatmaps)
  - figures/heatmap_part2.png          (Figure 4: bottom-4 model heatmaps)

Usage:
  cd analysis
  python generate_figures.py
"""

import json
import os
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# --- paths (relative to this script's directory) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JUDGE_DATA = os.path.join(SCRIPT_DIR, '..', 'judge_completions', 'judge_results.json')
FIGURES_DIR = os.path.join(SCRIPT_DIR, 'figures')

# --- 9 paper models ---
MODELS_9 = {
    'gpt-5.5', 'gpt-5.4-mini', 'gpt-5.4-nano',
    'claude-opus-4-7', 'claude-sonnet-4-6',
    'deepseek-v4-pro', 'llama-4-maverick',
    'mistral-medium-3.5', 'qwen3.6-27b',
}

DISPLAY = {
    'gpt-5.5': 'GPT-5.5',
    'gpt-5.4-mini': 'GPT-5.4 Mini',
    'gpt-5.4-nano': 'GPT-5.4 Nano',
    'claude-opus-4-7': 'Claude Opus 4.7',
    'claude-sonnet-4-6': 'Claude Sonnet 4.6',
    'deepseek-v4-pro': 'DeepSeek V4 Pro',
    'llama-4-maverick': 'Llama 4 Maverick',
    'mistral-medium-3.5': 'Mistral Med. 3.5',
    'qwen3.6-27b': 'Qwen3.6-27B',
}

LANGS_ORDER = ['python', 'javascript', 'typescript', 'java', 'cpp', 'c_sharp']
LANG_LABELS = ['Python', 'Javascript', 'Typescript', 'Java', 'Cpp', 'C_sharp']
CATS_ORDER = [
    'api_usage', 'code2NL_NL2code', 'code_purpose_understanding',
    'low_context', 'pattern_matching', 'syntax_completion',
]
CAT_LABELS = [
    'API Usage', 'Code2NL/NL2Code', 'Code Purpose',
    'Low Context', 'Pattern Matching', 'Syntax Completion',
]

N_BOOTSTRAP = 10000
SEED = 42


def load_data():
    """Load judge_results.json and aggregate scores.

    Format: {metadata: {...}, results: {model -> lang -> cat -> {task_id: {scores, mean}}}}
    """
    with open(JUDGE_DATA) as f:
        raw = json.load(f)

    data_root = raw.get('results', raw)

    scores = defaultdict(list)
    by_lang = defaultdict(lambda: defaultdict(list))
    by_cat = defaultdict(lambda: defaultdict(list))
    flat_data = []

    for model, langs in data_root.items():
        if model not in MODELS_9:
            continue
        for lang, cats in langs.items():
            for cat, tasks in cats.items():
                for tid, task_data in tasks.items():
                    s = task_data['mean'] if isinstance(task_data, dict) else task_data
                    if s is None:
                        continue
                    scores[model].append(s)
                    by_lang[model][lang].append(s)
                    by_cat[model][cat].append(s)
                    flat_data.append({
                        'model': model, 'lang': lang,
                        'cat': cat, 'score': s,
                    })

    return scores, by_lang, by_cat, flat_data


def bootstrap_ci(values, seed=SEED):
    """Return (lo, hi) for a 95% bootstrap confidence interval."""
    np.random.seed(seed)
    boot = [
        np.mean(np.random.choice(values, len(values), replace=True))
        for _ in range(N_BOOTSTRAP)
    ]
    return np.percentile(boot, 2.5), np.percentile(boot, 97.5)


def generate_figure2(scores):
    """Bar chart with 95% CIs (Figure 2)."""
    order = sorted(scores.keys(), key=lambda m: -np.mean(scores[m]))

    means, lows, highs, labels = [], [], [], []
    for m in order:
        s = scores[m]
        mean = np.mean(s)
        lo, hi = bootstrap_ci(s)
        means.append(mean)
        lows.append(mean - lo)
        highs.append(hi - mean)
        labels.append(DISPLAY[m])

    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(order))
    ax.errorbar(x, means, yerr=[lows, highs], fmt='o', capsize=5, capthick=1.5,
                markersize=8, color='#1f4e79', ecolor='#1f4e79', elinewidth=1.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)
    ax.set_ylabel('Average Score', fontsize=11)
    ax.set_xlabel('Model', fontsize=11)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.5))
    ax.set_ylim(5.0, 10.0)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()

    os.makedirs(FIGURES_DIR, exist_ok=True)
    out = os.path.join(FIGURES_DIR, 'model_comparison_plot.png')
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'Figure 2 saved: {out}')


def _make_heatmap(models_subset, flat_data, out_path, show_cbar=True):
    """Helper: create a stacked heatmap for a subset of models."""
    n = len(models_subset)
    fig, axes = plt.subplots(n, 1, figsize=(8, 3.0 * n))
    if n == 1:
        axes = [axes]

    for idx, m in enumerate(models_subset):
        ax = axes[idx]
        matrix = np.zeros((len(CATS_ORDER), len(LANGS_ORDER)))
        for ci, cat in enumerate(CATS_ORDER):
            for li, lang in enumerate(LANGS_ORDER):
                subset = [e['score'] for e in flat_data
                          if e['model'] == m and e['lang'] == lang
                          and e['cat'] == cat and e['score'] is not None]
                matrix[ci][li] = np.mean(subset) if subset else 0

        sns.heatmap(matrix, ax=ax, annot=True, fmt='.2f', cmap='YlOrRd_r',
                    xticklabels=LANG_LABELS, yticklabels=CAT_LABELS,
                    vmin=3, vmax=10, annot_kws={'size': 7},
                    cbar=idx == 0 and show_cbar)
        ax.set_title(DISPLAY[m], fontsize=11, fontweight='bold')
        ax.tick_params(labelsize=7)

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out_path}')


def generate_figure3(scores, flat_data):
    """Per-model heatmaps split into two pages (Figures 3 & 4)."""
    order = sorted(scores.keys(), key=lambda m: -np.mean(scores[m]))
    split = 5

    _make_heatmap(order[:split], flat_data,
                  os.path.join(FIGURES_DIR, 'heatmap_part1.png'))
    _make_heatmap(order[split:], flat_data,
                  os.path.join(FIGURES_DIR, 'heatmap_part2.png'))


def print_table7(by_lang):
    """Print Table 7 data (LLM-Judge by Language with 95% CIs)."""
    order = ['deepseek-v4-pro', 'gpt-5.5', 'claude-opus-4-7', 'gpt-5.4-nano',
             'gpt-5.4-mini', 'claude-sonnet-4-6', 'qwen3.6-27b',
             'llama-4-maverick', 'mistral-medium-3.5']
    langs = ['cpp', 'c_sharp', 'java', 'javascript', 'python', 'typescript']

    print('\n=== Table 7: LLM-Judge by Language with 95% CIs ===')
    for m in order:
        if m not in by_lang:
            continue
        row = f'{DISPLAY[m]:<22}'
        for lang in langs:
            s = by_lang[m][lang]
            if s:
                mean = np.mean(s)
                lo, hi = bootstrap_ci(s)
                row += f' & {mean:.2f} ({lo:.2f}-{hi:.2f})'
            else:
                row += ' & --'
        row += ' \\\\'
        print(row)


if __name__ == '__main__':
    print('Loading judge data...')
    scores, by_lang, by_cat, flat_data = load_data()

    print(f'Models: {sorted(scores.keys())}')
    for m in sorted(scores.keys(), key=lambda m: -np.mean(scores[m])):
        print(f'  {DISPLAY[m]}: {np.mean(scores[m]):.2f} (n={len(scores[m])})')

    generate_figure2(scores)
    generate_figure3(scores, flat_data)
    print_table7(by_lang)
    print('\nDone.')
