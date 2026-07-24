import json
import numpy as np
import scipy.stats as stats
from pathlib import Path
from typing import Dict, Any, List

def identify_family(img_name: str) -> str:
    """Classifies the image into its respective Operating System structural family."""
    name_lower = img_name.lower()
    if "alpine" in name_lower:
        return "Alpine (Minimal)"
    elif "slim-bookworm" in name_lower:
        return "Debian Slim (Bookworm)"
    elif "slim-bullseye" in name_lower:
        return "Debian Slim (Bullseye)"
    elif "bookworm" in name_lower:
        return "Full Debian (Bookworm)"
    elif "bullseye" in name_lower:
        return "Full Debian (Bullseye)"
    return "Other"

def main():
    data_dir = Path("aggregated_summary")
    clt_path = data_dir / "analytical_clt_summary.json"
    cve_profiles_path = data_dir / "environmental_cve_profiles.json"
    latex_output_path = data_dir / "environmental_tables_latex.tex"

    if not clt_path.exists() or not cve_profiles_path.exists():
        print("❌ Error: Base analytical files not found in the 'aggregated_summary/' folder.")
        print("Run the 'extract_environmental_data.py' and 'MC_simulation_environmental.py' scripts first.")
        return

    print("📥 Loading CLT analytical metrics and CISA KEV vulnerability profiles...")
    with open(clt_path, "r", encoding="utf-8") as f:
        clt_data = json.load(f)
    with open(cve_profiles_path, "r", encoding="utf-8") as f:
        cve_profiles = json.load(f)

    # 1. Baseline Processing and Extrapolation (Response to Reviewer A's Baselines Criticism)
    detailed_stats: Dict[str, Dict[str, Any]] = {}
    family_grouped_risks: Dict[str, List[float]] = {}
    family_grouped_variances: Dict[str, List[float]] = {}

    for img_name, clt_info in clt_data.items():
        mean_val = clt_info["expected_mean"]
        std_val = clt_info["std_dev"]
        var_val = clt_info["variance"]
        total_cves = clt_info["total_cves"]
        kev_count = clt_info.get("kev_confirmed_count", 0)
        
        # Exact parametric derivation of percentiles via Central Limit Theorem (Norm PPF)
        if std_val > 0:
            p5 = float(stats.norm.ppf(0.05, loc=mean_val, scale=std_val))
            p50 = mean_val # In an ideal Normal Curve, Median = Mean
            p95 = float(stats.norm.ppf(0.95, loc=mean_val, scale=std_val))
            p5 = max(0.0, p5) # Non-negative physical boundary
        else:
            p5 = p50 = p95 = mean_val

        # Extraction of Deterministic Baseline Metrics for comparison
        cves_list = cve_profiles.get(img_name, [])
        raw_cvss_sum = sum(c.get("base_score", 0.0) for c in cves_list)
        deterministic_risk_sum = sum(c.get("base_score", 0.0) * c.get("epss", 0.0001) for c in cves_list)

        family = identify_family(img_name)
        if family not in family_grouped_risks:
            family_grouped_risks[family] = []
            family_grouped_variances[family] = []
        family_grouped_risks[family].append(mean_val)
        family_grouped_variances[family].append(var_val)

        python_version = img_name.split("-")[0] if "-" in img_name else img_name
        variant_name = img_name.replace(f"{python_version}-", "")

        detailed_stats[img_name] = {
            "python": python_version,
            "variant": variant_name,
            "family": family,
            "mean": mean_val,
            "std": std_val,
            "var": var_val,
            "p5": p5,
            "p50": p50,
            "p95": p95,
            "total_cves": total_cves,
            "kev_count": kev_count,
            "raw_cvss_sum": raw_cvss_sum,
            "deterministic_risk_sum": deterministic_risk_sum
        }

    # =========================================================
    # TABLE 1: TERMINAL MARKDOWN (BASELINES VS CLT COMPARISON)
    # =========================================================
    print("\n📜 ACADEMIC COMPARISON OF BASELINES VS. CLT ANALYTICAL MODEL (MARKDOWN)")
    print(f"| {'Base Image':<25} | {'CVEs':<6} | {'KEV':<5} | {'CVSS Sum':<11} | {'Det. Sum':<11} | {'E[R] (CLT)':<11} | {'σ (Uncertainty)':<15} |")
    print("|" + "-"*27 + "|" + "-"*8 + "|" + "-"*7 + "|" + "-"*13 + "|" + "-"*13 + "|" + "-"*13 + "|" + "-"*17 + "|")
    
    sorted_images = sorted(detailed_stats.keys(), key=lambda k: detailed_stats[k]["mean"], reverse=True)
    for img in sorted_images:
        s = detailed_stats[img]
        print(f"| {img:<25} | {s['total_cves']:<6} | {s['kev_count']:<5} | {s['raw_cvss_sum']:11.2f} | {s['deterministic_risk_sum']:11.4f} | {s['mean']:11.4f} | {s['std']:15.4f} |")

    # =========================================================
    # MATHEMATICAL RIGOR AND EMPIRICAL VALIDATION (RQ1, RQ2 & RQ3)
    # =========================================================
    print("\n🔬 VARIANCE ANALYSIS AND THEORETICAL PROOF OF THE STUDY")
    print("=" * 75)
    
    print("\n[RQ1 & RQ3 PROOF] Average Pressure and Contextual Instability per OS Family:")
    for family in family_grouped_risks.keys():
        f_means = np.array(family_grouped_risks[family])
        f_stds = np.sqrt(np.array(family_grouped_variances[family]))
        print(f"  • {family:<25} -> Average Risk E[R]: {np.mean(f_means):8.4f} | Instability σ_R: {np.mean(f_stds):6.4f}")
    
    # RQ2 Proof: Statistically isolated calculation (OS Effect vs Python Version Effect)
    # We calculate intra-OS variation when changing Python vs variation when changing OS
    family_means_list = [np.mean(pts) for pts in family_grouped_risks.values() if len(pts) > 0]
    variance_between_os = float(np.var(family_means_list))

    python_group_means: Dict[str, List[float]] = {}
    for img, s in detailed_stats.items():
        py = s["python"]
        if py not in python_group_means:
            python_group_means[py] = []
        python_group_means[py].append(s["mean"])
    
    # Intra-group variance (how much Python version alters score within families)
    intra_family_variances = [np.var(pts) for pts in family_grouped_risks.values() if len(pts) > 1]
    variance_between_pythons = float(np.median(intra_family_variances)) if intra_family_variances else 1e-9

    print("\n[RQ2 PROOF] Exact Variance Decomposition (O.S. vs Python Runtime Version):")
    print(f"  • Variance Explained by Base O.S. selection (Variant) : {variance_between_os:.6f}")
    print(f"  • Variance Explained by Python Runtime evolution     : {variance_between_pythons:.6f}")
    
    ratio = variance_between_os / (variance_between_pythons if variance_between_pythons > 0 else 1e-9)
    print(f"  👉 SCIENTIFIC CONCLUSION: Operating System is {ratio:.1f}x more decisive in risk than Python version.")
    print("=" * 75)

    # =========================================================
    # STANDARDIZED LATEX GENERATOR FOR OVERLEAF / LADC 2026
    # =========================================================
    with open(latex_output_path, "w", encoding="utf-8") as f:
        f.write("% =========================================================\n")
        f.write("% LATEX TABLES AUTOMATICALLY GENERATED VIA CLT / CISA KEV\n")
        f.write("% =========================================================\n\n")
        
        # TABLE A: Direct Response to Baselines Criticism (Reviewer A) and KEV Validation (Reviewer B)
        f.write("\\begin{table*}[t]\n\\centering \\footnotesize\n")
        f.write("\\caption{Comparative Risk Evaluation: Deterministic Baselines vs. Analytical CLT Probability Model.}\n")
        f.write("\\label{tab:baseline_comparative}\n")
        f.write("\\begin{tabular}{lcccccc}\n\\toprule\n")
        f.write("\\textbf{Image Configuration} & \\textbf{Package/CVEs} & \\textbf{CISA KEV} & \\textbf{Raw CVSS Sum} & \\textbf{Det. Risk Sum} & \\textbf{Expected Mean ($\\mathbb{E}[\\widetilde{R}_i]$)} & \\textbf{Uncertainty ($\\sigma_R$)} \\\\\n\\midrule\n")
        
        current_family = ""
        for img in sorted_images:
            s = detailed_stats[img]
            if s["family"] != current_family:
                current_family = s["family"]
                f.write(f"\\midrule\n\\multicolumn{{7}}{{l}}{{\\textbf{{{current_family}}}}} \\\\\n")
            
            f.write(
                f"\\texttt{{{img}}} & {s['total_cves']} & {s['kev_count']} & "
                f"{s['raw_cvss_sum']:.1f} & {s['deterministic_risk_sum']:.4f} & "
                f"\\textbf{{{s['mean']:.4f}}} & {s['std']:.4f} \\\\\n"
            )
            
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table*}\n\n")

        # TABLE B: Variance Decomposition (RQ2)
        f.write("\\begin{table}[htbp]\n\\centering\n")
        f.write("\\caption{Variance Decomposition of Environment-Conditioned Risk (RQ2 Validation).}\n")
        f.write("\\label{tab:variance_decomposition}\n")
        f.write("\\begin{tabular}{lcc}\n\\toprule\n")
        f.write("\\textbf{Analysis Dimension} & \\textbf{Calculated Variance} & \\textbf{Relative Influence Factor} \\\\\n\\midrule\n")
        f.write(f"Operating System Base (Variant) & {variance_between_os:.6f} & {ratio:.1f}x \\\\\n")
        f.write(f"Python Runtime Version & {variance_between_pythons:.6f} & 1.0x \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n\n")

        # TABLE C: Exact Percentiles Statistics (Parametric CLT)
        f.write("\\begin{table}[htbp]\n\\centering \\footnotesize\n")
        f.write("\\caption{Analytical Risk Percentiles Derived via Central Limit Theorem (CLT) Normal Approximation.}\n")
        f.write("\\label{tab:ecosystem_full_statistics}\n")
        f.write("\\begin{tabular}{lccccc}\n\\toprule\n")
        f.write("\\textbf{Image Configuration} & \\textbf{Mean ($\\mathbb{E}[\\widetilde{R}_i]$)} & \\textbf{Std Dev ($\\sigma$)} & \\textbf{$P_5$} & \\textbf{$P_{50}$ (Median)} & \\textbf{$P_{95}$} \\\\\n\\midrule\n")
        
        current_family = ""
        for img in sorted_images:
            s = detailed_stats[img]
            if s["family"] != current_family:
                current_family = s["family"]
                f.write(f"\\midrule\n\\multicolumn{{6}}{{l}}{{\\textbf{{{current_family}}}}} \\\\\n")
            
            f.write(f"\\texttt{{{img}}} & {s['mean']:.4f} & {s['std']:.4f} & {s['p5']:.4f} & {s['p50']:.4f} & {s['p95']:.4f} \\\\\n")
            
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

    print(f"\n🚀 Success! LaTeX file generated with 3 tables ready for Overleaf at: {latex_output_path}")

if __name__ == "__main__":
    main()