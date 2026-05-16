#!/usr/bin/env python3
"""Compute pairwise Spearman correlations of Pass@1 across task categories
(Table 9) and PCA analysis.

Uses per-model-per-language-per-category Pass@1 data
(9 models x 6 languages = 54 observations).
Output: correlation matrix + PCA explained variance for the paper's
category relationship analysis.

Usage:
  cd analysis
  python compute_category_correlations.py
"""

import json
import os
import numpy as np
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from collections import defaultdict

# --- paths (relative to this script's directory) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PASS_AT_1_FILE = os.path.join(SCRIPT_DIR, '..', 'evaluation', 'pass_at_1_results.json')

# --- 9 paper models ---
MODELS_9 = [
    'gpt-5.5', 'gpt-5.4-mini', 'gpt-5.4-nano',
    'claude-opus-4-7', 'claude-sonnet-4-6',
    'deepseek-v4-pro', 'llama-4-maverick',
    'mistral-medium-3.5', 'qwen3.6-27b',
]

CATS = [
    'api_usage', 'code2NL_NL2code', 'code_purpose_understanding',
    'low_context', 'pattern_matching', 'syntax_completion',
]
CAT_SHORT = ['API', 'Code2NL', 'Purpose', 'Low Ctx', 'Pattern', 'Syntax']
CAT_DISPLAY = ['API Usage', 'Code2NL', 'Purpose', 'Low Context', 'Pattern', 'Syntax']
LANGS = ['python', 'javascript', 'typescript', 'java', 'cpp', 'c_sharp']


def load_matrix():
    """Build an (N_models * N_langs) x N_cats matrix of Pass@1 scores."""
    with open(PASS_AT_1_FILE) as f:
        data = json.load(f)

    matrix = []
    row_labels = []

    for m in MODELS_9:
        if m not in data.get('models', {}):
            print(f'WARNING: {m} not found in data, skipping')
            continue
        tc = data['models'][m]['test_cases']
        if not tc:
            print(f'WARNING: {m} has empty test_cases, skipping')
            continue

        scores = defaultdict(lambda: defaultdict(list))
        for t in tc:
            scores[t['language']][t['category']].append(t['pass_at_k_score'])

        for lang in LANGS:
            row = []
            for cat in CATS:
                if scores[lang][cat]:
                    row.append(np.mean(scores[lang][cat]) * 100)
                else:
                    row.append(0)
            matrix.append(row)
            row_labels.append(f'{m}/{lang}')

    return np.array(matrix), row_labels


def print_correlation_matrix(corr, p_vals):
    """Print lower-triangular correlation matrix."""
    print('=== PAIRWISE SPEARMAN CORRELATIONS ===')
    print(f'{"":>10}', '  '.join(f'{s:>8}' for s in CAT_SHORT))
    for i, name in enumerate(CAT_SHORT):
        row = f'{name:>10}'
        for j in range(6):
            if j <= i:
                row += f'  {corr[i][j]:>8.2f}'
            else:
                row += f'  {"":>8}'
        print(row)

    upper = [corr[i][j] for i in range(6) for j in range(i + 1, 6)]
    print(f'\nMean pairwise rho: {np.mean(upper):.2f}')
    print(f'Min pairwise rho:  {min(upper):.2f}')
    print(f'Max pairwise rho:  {max(upper):.2f}')
    print()

    for i in range(6):
        for j in range(i + 1, 6):
            p = p_vals[i][j]
            sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
            print(f'  {CAT_SHORT[i]:>8} vs {CAT_SHORT[j]:<8}: '
                  f'rho={corr[i][j]:.2f}  p={p:.4f} {sig}')


def print_pca(matrix):
    """Run PCA and print explained variance."""
    print('\n=== PCA ===')
    scaler = StandardScaler()
    X = scaler.fit_transform(matrix)
    pca = PCA()
    pca.fit(X)
    print('Explained variance ratios:',
          [f'{v:.3f}' for v in pca.explained_variance_ratio_])
    print(f'First 2 components: {sum(pca.explained_variance_ratio_[:2]) * 100:.1f}%')
    print(f'First 3 components: {sum(pca.explained_variance_ratio_[:3]) * 100:.1f}%')


def print_latex_table(corr):
    """Print LaTeX source for the correlation table."""
    print('\n=== LATEX TABLE ===')
    print(r'\begin{table}[h]')
    print(r'\caption{Pairwise Spearman correlations of Pass@1 across categories '
          r'($n = 54$ model--language pairs).}')
    print(r'\label{tab:category-correlations}')
    print(r'\centering')
    print(r'\small')
    print(r'\begin{tabular}{lcccccc}')
    print(r'\toprule')
    print(r' & API & Code2NL & Purpose & Low Ctx & Pattern & Syntax \\')
    print(r'\midrule')
    for i, name in enumerate(CAT_DISPLAY):
        row = f'{name}'
        for j in range(6):
            if j < i:
                row += f' & {corr[i][j]:.2f}'
            elif j == i:
                row += ' & 1.00'
            else:
                row += ' &'
        row += r' \\'
        print(row)
    print(r'\bottomrule')
    print(r'\end{tabular}')
    print(r'\end{table}')


def main():
    matrix, row_labels = load_matrix()
    n_models = len(matrix) // len(LANGS)
    print(f'Matrix shape: {matrix.shape} ({n_models} models x {len(LANGS)} languages)')
    print()

    # Pairwise Spearman correlations
    corr = np.zeros((6, 6))
    p_vals = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            rho, p = stats.spearmanr(matrix[:, i], matrix[:, j])
            corr[i][j] = rho
            p_vals[i][j] = p

    print_correlation_matrix(corr, p_vals)
    print_pca(matrix)
    print_latex_table(corr)


if __name__ == '__main__':
    main()
