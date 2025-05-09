import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Input data from the table
models = [
    "o1-mini", "o1-preview", "o3-mini", "Claude 3.5 Sonnet", "Claude 3.7 Sonnet",
    "GPT-4o mini", "GPT-3.5 Turbo", "GPT-4.5 preview", "Ministral-3B", 
    "DeepSeek-V3", "GPT-4.1 mini", "GPT-4.1 nano", "GPT-4o", "GPT-4o Copilot", "DeepSeek-R1"
]

languages = ["Py", "JS", "TS", "Java", "C++", "C#"]

# Create DataFrames for each metric
cosine_data = pd.DataFrame({
    "Py": [0.76, 0.86, 0.64, 0.69, 0.64, 0.63, 0.69, 0.70, 0.51, 0.70, 0.71, 0.58, 0.68, 0.64, 0.67],
    "JS": [0.75, 0.82, 0.60, 0.60, 0.60, 0.58, 0.55, 0.65, 0.38, 0.63, 0.65, 0.52, 0.63, 0.61, 0.60],
    "TS": [0.62, 1.0, 0.55, 0.55, 0.51, 0.51, 0.45, 0.61, 0.35, 0.58, 0.57, 0.49, 0.56, 0.51, 0.55],
    "Java": [0.84, 0.92, 0.74, 0.78, 0.70, 0.70, 0.70, 0.79, 0.50, 0.76, 0.77, 0.66, 0.76, 0.75, 0.69],
    "C++": [0.99, 0.9, 0.78, 0.78, 0.69, 0.70, 0.61, 0.79, 0.42, 0.75, 0.75, 0.64, 0.75, 0.71, 0.73],
    "C#": [0.72, 0.93, 0.67, 0.69, 0.66, 0.66, 0.62, 0.71, 0.51, 0.68, 0.70, 0.60, 0.69, 0.67, 0.65]
}, index=models)

line0_exact_match_data = pd.DataFrame({
    "Py": [50.0, 71.43, 45.13, 49.38, 44.51, 42.81, 52.53, 52.53, 29.38, 49.37, 52.08, 34.91, 48.44, 45.31, 44.65],
    "JS": [75.0, 60.0, 39.18, 42.71, 44.82, 40.0, 47.75, 47.75, 18.67, 44.11, 47.65, 31.03, 47.83, 44.67, 40.67],
    "TS": [10.0, 100.0, 32.1, 37.71, 35.03, 30.64, 41.52, 41.52, 14.67, 40.2, 40.74, 28.57, 37.67, 32.67, 34.0],
    "Java": [80.0, 80.0, 56.15, 60.61, 55.18, 54.33, 61.72, 61.72, 27.67, 61.54, 58.51, 45.48, 62.54, 60.67, 53.2],
    "C++": [88.89, 73.33, 61.89, 61.36, 54.88, 56.33, 66.08, 66.08, 22.67, 59.0, 60.63, 48.49, 61.67, 57.0, 54.33],
    "C#": [63.64, 57.14, 41.6, 49.0, 47.83, 42.67, 48.82, 48.82, 25.33, 44.67, 49.11, 34.45, 51.0, 48.0, 43.0]
}, index=models)

# Function to calculate language preference index
def calculate_language_preference(model_data):
    # Calculate how much a model performs better/worse in each language compared to its average
    model_avg = model_data.mean(axis=1)
    normalized = pd.DataFrame()
    
    for col in model_data.columns:
        normalized[col] = model_data[col] / model_avg
    
    return normalized

# Function to find outliers (models with strong preferences for specific languages)
def find_language_outliers(normalized_data, threshold=0.2):
    outliers = {}
    
    for model in normalized_data.index:
        model_preferences = normalized_data.loc[model]
        
        # Find languages where the model performs significantly better or worse
        strong_preferences = {}
        for lang in model_preferences.index:
            pref_score = model_preferences[lang] - 1.0  # Difference from neutral (1.0)
            
            if abs(pref_score) >= threshold:
                strong_preferences[lang] = round(pref_score, 2)
        
        if strong_preferences:
            outliers[model] = strong_preferences
    
    return outliers

# Determine which metric direction is better (higher is better)
cosine_normalized = calculate_language_preference(cosine_data)
line0_exact_match_normalized = calculate_language_preference(line0_exact_match_data)

# Find outliers
cosine_outliers = find_language_outliers(cosine_normalized, 0.15)
line0_exact_match_outliers = find_language_outliers(line0_exact_match_normalized, 0.1)

# Create heat maps to visualize language preferences across models
plt.figure(figsize=(12, 10))

# For cosine similarity (higher is better)
plt.subplot(1, 2, 1)
sns.heatmap(cosine_normalized, cmap="RdYlGn", center=1, annot=True, fmt=".2f", cbar_kws={'label': 'Relative Performance'})
plt.title("Cosine Similarity Language Preference\n(Relative to Model Average)")

# For line 0 exact match rate (higher is better)
plt.subplot(1, 2, 2)
sns.heatmap(line0_exact_match_normalized, cmap="RdYlGn", center=1, annot=True, fmt=".2f", cbar_kws={'label': 'Relative Performance'})
plt.title("Line 0 Exact Match Rate Language Preference\n(Relative to Model Average)")

plt.tight_layout()
plt.savefig("language_preference_heatmaps.png", dpi=300, bbox_inches='tight')

# Create a function to display the outliers
def display_outliers(outliers, metric_name):
    print(f"\n=== {metric_name} Outliers ===")
    for model, preferences in outliers.items():
        print(f"\n{model}:")
        
        strengths = {lang: score for lang, score in preferences.items() if score > 0}
        weaknesses = {lang: score for lang, score in preferences.items() if score < 0}
        
        if strengths:
            print("  Strengths:", ", ".join([f"{lang} (+{score*100:.0f}%)" for lang, score in sorted(strengths.items(), key=lambda x: -x[1])]))
        
        if weaknesses:
            print("  Weaknesses:", ", ".join([f"{lang} ({score*100:.0f}%)" for lang, score in sorted(weaknesses.items(), key=lambda x: x[1])]))

# Display the results
print("=== LANGUAGE PREFERENCE ANALYSIS ===")
print("This analysis shows which languages each model performs relatively better or worse at.")
print("Scores indicate how much better/worse a model performs in a language compared to its average.")

display_outliers(cosine_outliers, "Cosine Similarity")
display_outliers(line0_exact_match_outliers, "Line 0 Exact Match Rate")

# Find models with the largest variance in language performance
def variance_analysis(normalized_data, metric_name):
    variances = normalized_data.var(axis=1).sort_values(ascending=False)
    
    print(f"\n=== Models with Most Varied {metric_name} Performance Across Languages ===")
    for model, var in variances.items():
        if var > 0.01:  # Only show models with significant variance
            best_lang = normalized_data.loc[model].idxmax()
            worst_lang = normalized_data.loc[model].idxmin()
            best_val = normalized_data.loc[model, best_lang]
            worst_val = normalized_data.loc[model, worst_lang]
            
            print(f"{model}: Variance = {var:.4f}, Best: {best_lang} (+{(best_val-1)*100:.1f}%), Worst: {worst_lang} ({(worst_val-1)*100:.1f}%)")

# Run variance analysis
variance_analysis(cosine_normalized, "Cosine Similarity")
variance_analysis(line0_exact_match_normalized, "Line 0 Exact Match Rate")

# Find languages that models consistently struggle with or excel at
def language_difficulty_analysis(normalized_data, metric_name):
    lang_means = normalized_data.mean().sort_values()
    
    print(f"\n=== Language Difficulty Analysis for {metric_name} ===")
    print("Languages ranked from most difficult to easiest (based on average normalized performance):")
    
    for lang, mean_val in lang_means.items():
        print(f"{lang}: {mean_val:.2f} ({(mean_val-1)*100:.1f}% from neutral)")

# Run language difficulty analysis
language_difficulty_analysis(cosine_normalized, "Cosine Similarity")
language_difficulty_analysis(line0_exact_match_normalized, "Line 0 Exact Match Rate")

# Create a composite ranking of languages by difficulty
print("\n=== Composite Language Difficulty Ranking ===")
composite_ranking = (
    cosine_normalized.mean() + 
    line0_exact_match_normalized.mean()
) / 2

for lang, score in composite_ranking.sort_values().items():
    print(f"{lang}: {score:.2f} ({(score-1)*100:.1f}% from neutral)")

# Create a bar chart showing performance of selected interesting models across languages
def plot_model_performance_across_languages(data, model_list, metric_name):
    plt.figure(figsize=(12, 6))
    
    # Create a subset with just the selected models
    subset = data.loc[model_list]
    
    # Prepare the plot
    ax = subset.T.plot(kind='bar', figsize=(12, 6))
    plt.title(f"{metric_name} across Languages for Selected Models")
    plt.xlabel("Language")
    plt.ylabel(metric_name)
    plt.legend(title="Model")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(f"selected_models_{metric_name.lower().replace(' ', '_')}.png", dpi=300, bbox_inches='tight')

# Choose some interesting models to compare
interesting_models = ["o1-preview", "o3-mini", "Claude 3.7 Sonnet", "GPT-4o", "Ministral-3B"]

# Plot their performance across languages for each metric
plot_model_performance_across_languages(cosine_data, interesting_models, "Cosine Similarity")
plot_model_performance_across_languages(line0_exact_match_data, interesting_models, "Line 0 Exact Match Rate (%)")

print("\nAnalysis complete. Output files have been saved.")

# Add this function to identify best/worst models for each language
def analyze_language_performance(cosine_df, line0_exact_match_df, top_n=3):
    """
    Determine the best and worst performing models for each language
    based on cosine similarity and line 0 exact match metrics.
    
    Args:
        cosine_df: DataFrame with cosine similarity data
        line0_exact_match_df: DataFrame with line 0 exact match rate data
        top_n: Number of top/bottom models to report
        
    Returns:
        None (prints results)
    """
    print(f"\n=== Top {top_n} and Bottom {top_n} Models for Each Language ===")
    
    # Create a composite score for each model in each language
    # We normalize each metric first to put them on similar scales
    
    # Create empty DataFrame for composite scores
    composite_scores = pd.DataFrame(index=cosine_df.index, columns=cosine_df.columns)
    
    for language in languages:
        # Normalize each metric for the current language (0-1 scale)
        cosine_min, cosine_max = cosine_df[language].min(), cosine_df[language].max()
        line0_exact_match_min, line0_exact_match_max = line0_exact_match_df[language].min(), line0_exact_match_df[language].max()
        
        # Calculate normalized scores (higher is better for all metrics after normalization)
        cosine_norm = (cosine_df[language] - cosine_min) / (cosine_max - cosine_min)
        line0_exact_match_norm = (line0_exact_match_df[language] - line0_exact_match_min) / (line0_exact_match_max - line0_exact_match_min)
        
        # Compute composite score with equal weight to each metric
        composite_scores[language] = (cosine_norm + line0_exact_match_norm) / 2
    
    # Now analyze each language
    for language in languages:
        print(f"\n## {language}")
        
        # Sort models by their composite score for this language
        language_ranking = composite_scores[language].sort_values(ascending=False)
        
        # Get top and bottom performers
        top_models = language_ranking.head(top_n)
        bottom_models = language_ranking.tail(top_n)
        
        # Print top performers with their raw metric scores
        print(f"Top {top_n} models:")
        for model in top_models.index:
            print(f"  {model}:")
            print(f"    Composite Score: {composite_scores.loc[model, language]:.3f}")
            print(f"    Cosine Similarity: {cosine_df.loc[model, language]:.3f}")
            print(f"    Line 0 Exact Match Rate: {line0_exact_match_df.loc[model, language]:.2f}%")
        
        # Print bottom performers with their raw metric scores
        print(f"\nBottom {top_n} models:")
        for model in bottom_models.index:
            print(f"  {model}:")
            print(f"    Composite Score: {composite_scores.loc[model, language]:.3f}")
            print(f"    Cosine Similarity: {cosine_df.loc[model, language]:.3f}")
            print(f"    Line 0 Exact Match Rate: {line0_exact_match_df.loc[model, language]:.2f}%")
    
    return composite_scores

# Add a function to visualize the best model for each language
def visualize_best_models_by_language(composite_scores):
    """Create a bar chart showing the best model for each language"""
    plt.figure(figsize=(12, 6))
    
    # Find the best model for each language
    best_models = {}
    for language in languages:
        best_model = composite_scores[language].idxmax()
        best_score = composite_scores.loc[best_model, language]
        best_models[language] = (best_model, best_score)
    
    # Create data for the plot
    langs = []
    model_names = []
    scores = []
    colors = plt.cm.tab20(np.linspace(0, 1, len(best_models)))
    
    for i, (lang, (model, score)) in enumerate(best_models.items()):
        langs.append(lang)
        model_names.append(model)
        scores.append(score)
    
    # Create the bar chart
    bars = plt.bar(langs, scores, color=colors)
    
    # Annotate bars with model names
    for i, bar in enumerate(bars):
        plt.text(
            bar.get_x() + bar.get_width()/2, 
            bar.get_height() + 0.01, 
            model_names[i], 
            ha='center', 
            va='bottom',
            rotation=45,
            fontsize=9
        )
    
    plt.title("Best Performing Model for Each Language")
    plt.xlabel("Programming Language")
    plt.ylabel("Composite Performance Score")
    plt.ylim(top=1.1)  # Add space for model name labels
    plt.tight_layout()
    
    plt.savefig("best_models_by_language.png", dpi=300, bbox_inches='tight')

# Add a radar chart to compare top models across all languages
def create_model_radar_chart(cosine_df, line0_exact_match_df, selected_models):
    """Create a radar chart comparing selected models across all languages"""
    # Number of languages (variables)
    num_vars = len(languages)
    
    # Compute angles for the radar chart
    angles = np.linspace(0, 2*np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Close the loop
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    
    # Add language labels
    plt.xticks(angles[:-1], languages, size=12)
    
    # Add composite scores for each selected model
    composite_scores = pd.DataFrame(index=cosine_df.index, columns=cosine_df.columns)
    
    for language in languages:
        # Normalize each metric (0-1 scale)
        cosine_norm = (cosine_df[language] - cosine_df[language].min()) / (cosine_df[language].max() - cosine_df[language].min())
        line0_exact_match_norm = (line0_exact_match_df[language] - line0_exact_match_df[language].min()) / (line0_exact_match_df[language].max() - line0_exact_match_df[language].min())
        
        # Compute composite score 
        composite_scores[language] = (cosine_norm + line0_exact_match_norm) / 2
    
    # Plot each model
    for i, model in enumerate(selected_models):
        model_values = composite_scores.loc[model].values.tolist()
        model_values += model_values[:1]  # Close the loop
        
        ax.plot(angles, model_values, linewidth=2, label=model)
        ax.fill(angles, model_values, alpha=0.1)
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.title("Model Performance Across Languages", size=15, y=1.1)
    plt.tight_layout()
    
    plt.savefig("model_radar_chart.png", dpi=300, bbox_inches='tight')

# Run the new analyses after the existing code
print("\n" + "=" * 50)
print("ADDITIONAL ANALYSES: BEST AND WORST MODELS BY LANGUAGE")
print("=" * 50)

# Determine best and worst models for each language
composite_scores = analyze_language_performance(cosine_data, line0_exact_match_data, top_n=3)

# Create visualization of best model for each language
visualize_best_models_by_language(composite_scores)

# Create radar chart comparing top-performing models across languages
top_models = ["o1-preview", "GPT-4.5 preview", "o1-mini", "DeepSeek-V3", "GPT-4o"]
create_model_radar_chart(cosine_data, line0_exact_match_data, top_models)

print("\nAdditional visualizations saved: best_models_by_language.png and model_radar_chart.png")