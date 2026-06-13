import json
import numpy as np
from pathlib import Path

def compute_aggregate_epss_exposure(epss_scores: list[float]) -> float:
    if not epss_scores: return 0.0
    return float(1.0 - np.prod([1.0 - float(e) for e in epss_scores]))

def calculate_cvss_base_score_vectorized(impact: float, exploitability_array: np.ndarray, scope_changed: bool) -> np.ndarray:
    if impact <= 0: return np.zeros_like(exploitability_array)
    if not scope_changed:
        scores = np.minimum(impact + exploitability_array, 10.0)
    else:
        scores = np.minimum(1.08 * (impact + exploitability_array), 10.0)
    scores_int = np.round(scores * 100000).astype(int)
    return np.where(scores_int % 10000 == 0, np.round(scores, 1), np.ceil(np.round(scores, 9) * 10.0) / 10.0)

def identify_family(img_name: str) -> str:
    name_lower = img_name.lower()
    if "alpine" in name_lower: return "Alpine (Minimal)"
    elif "slim-bookworm" in name_lower: return "Debian Slim (Bookworm)"
    elif "slim-bullseye" in name_lower: return "Debian Slim (Bullseye)"
    elif "bookworm" in name_lower: return "Full Debian (Bookworm)"
    elif "bullseye" in name_lower: return "Full Debian (Bullseye)"
    return "Other"

def main():
    data_dir = Path("aggregated_summary")
    npz_path = data_dir / "environmental_simulation_arrays.npz"
    profile_path = data_dir / "environmental_cve_profiles.json"

    if not npz_path.exists() or not profile_path.exists():
        print("❌ Erro: Execute a simulação principal primeiro para gerar os arquivos basolares.")
        return

    sim_data = np.load(npz_path)
    with open(profile_path, "r", encoding="utf-8") as f:
        cve_dataset = json.load(f)

    # =========================================================
    # PARTE 1: GERAÇÃO DA TABELA DE MARCOS DE CONVERGÊNCIA
    # =========================================================
    print("📈 Calculando marcos numéricos de convergência...")
    target_images = [
        "3.9-bullseye", "3.11-bookworm", "3.9-slim-bullseye", "3.11-slim-bookworm", "3.11-alpine3.22"
    ]
    milestones = [1000, 5000, 10000, 25000, 50000]
    convergence_data = {}

    for img in target_images:
        if img in sim_data.files:
            arr = sim_data[img]
            convergence_data[img] = [float(np.mean(arr[:m])) for m in milestones]

    tex_conv_path = data_dir / "table_convergence_milestones.tex"
    with open(tex_conv_path, "w", encoding="utf-8") as f:
        f.write("\\begin{table}[htbp]\n\\centering\\footnotesize\n")
        f.write("\\caption{Monte Carlo Convergence Stability and Running Mean Milestones.}\n")
        f.write("\\label{tab:monte_carlo_convergence_milestones}\n")
        f.write("\\begin{tabular}{lccccc}\n\\toprule\n")
        f.write("\\textbf{Image Baseline} & \\textbf{$M=1,000$} & \\textbf{$M=5,000$} & \\textbf{$M=10,000$} & \\textbf{$M=25,000$} & \\textbf{$M=50,000$} \\\\\n\\midrule\n")
        for img, vals in convergence_data.items():
            f.write(f"\\texttt{{ {img} }} & {vals[0]:.4f} & {vals[1]:.4f} & {vals[2]:.4f} & {vals[3]:.4f} & {vals[4]:.4f} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

    # =========================================================
    # PARTE 2: GERAÇÃO DA TABELA DE SENSIBILIDADE LAMBDA
    # =========================================================
    print("🎲 Calculando sensibilidade paramétrica do Lambda...")
    lambda_vals = [0.1, 0.5, 1.0]
    n_samples = 50000
    rng = np.random.default_rng(seed=42)
    sensitivity_results = {img: [] for img in cve_dataset.keys()}

    for lam in lambda_vals:
        for img_name, cves in cve_dataset.items():
            if not cves:
                sensitivity_results[img_name].append(0.0)
                continue
            epss_list = [cve["epss"] for cve in cves]
            ai = compute_aggregate_epss_exposure(epss_list)
            risk_accum = np.zeros(n_samples)
            
            for cve in cves:
                iv, xv, sv, ev = cve["impact_subscore"], cve["exploitability_subscore"], cve["scope_changed"], cve["epss"]
                hi = (lam * ai * 3.9) / 2.0
                lower, upper = max(0.0, xv - hi), min(3.9, xv + hi)
                expl_samples = np.full(n_samples, lower) if lower == upper else rng.triangular(lower, xv, upper, size=n_samples)
                risk_accum += (ev * calculate_cvss_base_score_vectorized(iv, expl_samples, sv))
                
            sensitivity_results[img_name].append(float(np.mean(risk_accum)))

    sorted_images = sorted(sensitivity_results.keys(), key=lambda k: sensitivity_results[k][2], reverse=True)
    
    tex_sens_path = data_dir / "table_lambda_sensitivity.tex"
    with open(tex_sens_path, "w", encoding="utf-8") as f:
        f.write("\\begin{table*}[htbp]\n\\centering\\footnotesize\n")
        f.write("\\caption{Sensitivity Analysis and Ordinal Stability Across Lambda Scales.}\n")
        f.write("\\label{tab:lambda_sensitivity_milestones}\n")
        f.write("\\begin{tabular}{lccc}\n\\toprule\n")
        f.write("\\textbf{Base Image Configuration} & \\textbf{Risk Phenotype ($\\\\lambda=0.1$)} & \\textbf{Risk Phenotype ($\\\\lambda=0.5$)} & \\textbf{Risk Phenotype ($\\\\lambda=1.0$)} \\\\\n\\midrule\n")
        
        current_family = ""
        for img in sorted_images:
            res = sensitivity_results[img]
            fam = identify_family(img)
            if fam != current_family:
                current_family = fam
                f.write(f"\\midrule\n\\multicolumn{{4}}{{l}}{{\\textbf{{{current_family}}}}} \\\\\n")
            f.write(f"\\texttt{{{img}}} & {res[0]:.4f} & {res[1]:.4f} & {res[2]:.4f} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table*}\n")

    print(f"✅ Tabelas prontas salvas em '{data_dir}/'!")

if __name__ == "__main__":
    main()