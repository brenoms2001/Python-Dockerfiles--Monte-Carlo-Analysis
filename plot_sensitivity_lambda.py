import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Importing the aggregate exposure function
from cvss_environmental_math import compute_aggregate_epss_exposure

def calculate_cvss_base_score_vectorized(impact: float, exploitability_array: np.ndarray, scope_changed: bool) -> np.ndarray:
    """Vectorized official CVSS v3.1 equation with integrated RoundUp1."""
    if impact <= 0:
        return np.zeros_like(exploitability_array)
    if not scope_changed:
        scores = np.minimum(impact + exploitability_array, 10.0)
    else:
        scores = np.minimum(1.08 * (impact + exploitability_array), 10.0)
    scores_int = np.round(scores * 100000).astype(int)
    return np.where(scores_int % 10000 == 0, np.round(scores, 1), np.ceil(np.round(scores, 9) * 10.0) / 10.0)

def identify_family(img_name: str) -> str:
    """Maps color and grouping by OS structural family."""
    name_lower = img_name.lower()
    if "alpine" in name_lower: return "Alpine (Minimal)"
    elif "slim-bookworm" in name_lower: return "Debian Slim (Bookworm)"
    elif "slim-bullseye" in name_lower: return "Debian Slim (Bullseye)"
    elif "bookworm" in name_lower: return "Full Debian (Bookworm)"
    elif "bullseye" in name_lower: return "Full Debian (Bullseye)"
    return "Other"

def main():
    # 1. Path configuration and loading
    data_dir = Path("aggregated_summary")
    output_dir = Path("Plots_Environmental")
    output_dir.mkdir(exist_ok=True)

    profile_path = data_dir / "environmental_cve_profiles.json"
    if not profile_path.exists():
        print("❌ Error: environmental_cve_profiles.json not found.")
        return

    with open(profile_path, "r", encoding="utf-8") as f:
        cve_dataset = json.load(f)

    # Test parameters and fixed seed for reproducibility
    lambda_vals = [0.1, 0.5, 1.0]
    n_samples = 50000
    rng = np.random.default_rng(seed=42)

    # Structure to store calculated means: {image: [mean_λ_0.1, mean_λ_0.5, mean_λ_1.0]}
    sensitivity_results = {img: [] for img in cve_dataset.keys()}

    print("🎲 Executing Sensitivity Analysis by perturbing the Lambda parameter...")

    # 2. Simulation loop per Lambda level
    for lam in lambda_vals:
        print(f"  • Batch simulation for Lambda = {lam:.1f}")
        for img_name, cves in cve_dataset.items():
            if not cves:
                sensitivity_results[img_name].append(0.0)
                continue

            epss_list = [cve["epss"] for cve in cves]
            ai = compute_aggregate_epss_exposure(epss_list)
            image_risk_accumulated = np.zeros(n_samples)

            for cve in cves:
                iv = cve["impact_subscore"]
                xv = cve["exploitability_subscore"]
                sv = cve["scope_changed"]
                ev = cve["epss"]

                # Dynamic calculation of boundaries injecting current Lambda
                hi = (lam * ai * 3.9) / 2.0
                lower = max(0.0, xv - hi)
                upper = min(3.9, xv + hi)

                if lower == upper:
                    expl_samples = np.full(n_samples, lower)
                else:
                    expl_samples = rng.triangular(lower, xv, upper, size=n_samples)

                simulated_base_scores = calculate_cvss_base_score_vectorized(iv, expl_samples, sv)
                image_risk_accumulated += (ev * simulated_base_scores)

            sensitivity_results[img_name].append(float(np.mean(image_risk_accumulated)))

    # =========================================================
    # RANKING ORDINAL STABILITY COMPARATIVE TABLE IN TERMINAL
    # =========================================================
    print("\n📊 RANKING ORDINAL STABILITY TABLE")
    print(f"| {'Image Configuration':<25} | {'Risk (λ=0.1)':<14} | {'Risk (λ=0.5)':<14} | {'Risk (λ=1.0)':<14} |")
    print("|" + "-"*27 + "|" + "-"*16 + "|" + "-"*16 + "|" + "-"*16 + "|")
    
    # Sorts based on default λ=1.0 result descending
    sorted_images = sorted(sensitivity_results.keys(), key=lambda k: sensitivity_results[k][2], reverse=True)
    for img in sorted_images:
        res = sensitivity_results[img]
        print(f"| {img:<25} | {res[0]:14.4f} | {res[1]:14.4f} | {res[2]:14.4f} |")

    # =========================================================
    # SCIENTIFIC CHART GENERATION (SLOPE / SENSITIVITY CHART)
    # =========================================================
    print("\n📈 Rendering parallel sensitivity chart...")
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    family_colors = {
        "Alpine (Minimal)": "#1f77b4",
        "Debian Slim (Bookworm)": "#2ca02c",
        "Debian Slim (Bullseye)": "#9467bd",
        "Full Debian (Bookworm)": "#ff7f0e",
        "Full Debian (Bullseye)": "#d62728"
    }

    # Plots one line for each configuration
    legend_tracker = set()
    for img in sorted_images:
        family = identify_family(img)
        label_to_use = family if family not in legend_tracker else ""
        legend_tracker.add(family)
        
        ax.plot(
            ["0.1", "0.5", "1.0"], 
            sensitivity_results[img], 
            marker='o', 
            markersize=5,
            linewidth=1.5, 
            color=family_colors[family], 
            alpha=0.7,
            label=label_to_use
        )

    ax.set_title("Sensitivity Analysis and Ordinal Ranking Robustness")
    ax.set_xlabel(r"Uncertainty Scaling Factor ($\lambda$)")
    ax.set_ylabel(r"Expected Exposure Risk Score ($\mathbb{E}[\widetilde{R}_i]$)")
    ax.legend(title="Structural OS Families", loc="upper left")
    
    plt.tight_layout()
    output_path = output_dir / "lambda_sensitivity_analysis.png"
    plt.savefig(output_path, dpi=300)
    plt.close()

    # =========================================================
    # LATEX TABLE GENERATOR FOR OVERLEAF
    # =========================================================
    latex_path = data_dir / "sensitivity_table_latex.tex"
    with open(latex_path, "w", encoding="utf-8") as f:
        f.write("\\begin{table}[htbp]\n\\centering \\footnotesize\n")
        f.write("\\caption{Sensitivity Analysis and Ordinal Stability Across Lambda Scales.}\n")
        f.write("\\label{tab:lambda_sensitivity}\n")
        f.write("\\begin{tabular}{lccc}\n\\toprule\n")
        f.write("\\textbf{Base Image Configuration} & \\textbf{Risk ($\\\\lambda=0.1$)} & \\textbf{Risk ($\\\\lambda=0.5$)} & \\textbf{Risk ($\\\\lambda=1.0$)} \\\\\n\\midrule\n")
        
        current_family = ""
        for img in sorted_images:
            res = sensitivity_results[img]
            fam = identify_family(img)
            if fam != current_family:
                current_family = fam
                f.write(f"\\midrule\n\\multicolumn{{4}}{{l}}{{\\textbf{{{current_family}}}}} \\\\\n")
            f.write(f"\\texttt{{{img}}} & {res[0]:.4f} & {res[1]:.4f} & {res[2]:.4f} \\\\\n")
            
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

    print(f"✅ Analysis completed! Image saved to: {output_path}")
    print(f"📄 LaTeX code generated for Overleaf at: {latex_path}")

if __name__ == "__main__":
    main()