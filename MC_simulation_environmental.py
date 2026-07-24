import json
import numpy as np
from pathlib import Path
from typing import Dict, Any
import scipy.stats as stats

# Importing pure mathematical modules
from cvss_environmental_math import compute_aggregate_epss_exposure, compute_uncertainty_bounds

def calculate_deterministic_cvss(impact: float, exploitability: float, scope_changed: bool) -> float:
    """
    Calculates strict point CVSS v3.1 score for a pair of impact and exploitability subscores.
    Used to determine the exact physical boundaries (a, c, b) of triangular severity.
    """
    if impact <= 0 or exploitability <= 0:
        return 0.0
    
    raw_score = (impact + exploitability) if not scope_changed else 1.08 * (impact + exploitability)
    score = min(raw_score, 10.0)
    
    # Strict implementation of CVSS v3.1 RoundUp1
    score_int = int(round(score * 100000))
    if score_int % 10000 == 0:
        return round(score, 1)
    else:
        return round(np.ceil(round(score, 9) * 10.0) / 10.0, 1)

def compute_analytical_triangular_moments(a: np.ndarray, c: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculates exact Expectation (Mean) and Variance for a vector of triangular distributions
    using the closed-form formulas from the Thesis Appendix:
      μ = (a + b + c) / 3
      σ² = (a² + b² + c² - ab - ac - bc) / 18
    """
    mean_c = (a + b + c) / 3.0
    variance_c = (a**2 + b**2 + c**2 - a*b - a*c - b*c) / 18.0
    return mean_c, variance_c

def main():
    # 1. Loads enriched dataset with Threat Intelligence (FIRST EPSS + CISA KEV)
    profile_path = Path("aggregated_summary/environmental_cve_profiles.json")
    if not profile_path.exists():
        print("❌ Error: File environmental_cve_profiles.json not found. Run the extractor first.")
        return
        
    with open(profile_path, "r", encoding="utf-8") as f:
        cve_dataset = json.load(f)

    # Dictionaries to store analytical statistical moments per environment
    image_expected_means: Dict[str, float] = {}
    image_expected_variances: Dict[str, float] = {}
    image_metadata_summary: Dict[str, Dict[str, Any]] = {}
    
    # Backward compatibility dictionary to feed density plots (.npz)
    clt_normal_distributions: Dict[str, np.ndarray] = {}
    n_compat_samples = 50000
    rng = np.random.default_rng(seed=42) # Fixed seed for identical static plots

    print("📊 Starting Stochastic Analytical Model via Central Limit Theorem (CLT)...")

    # 2. Vector processing over each environment of the ecosystem
    for img_name, cves in cve_dataset.items():
        if not cves:
            # Robust handling for fully clean images (e.g., Alpine without vulnerabilities)
            image_expected_means[img_name] = 0.0
            image_expected_variances[img_name] = 0.0
            image_metadata_summary[img_name] = {"ai": 0.0, "total_cves": 0, "kev_count": 0}
            clt_normal_distributions[img_name] = np.zeros(n_compat_samples)
            print(f"  🟢 {img_name.ljust(25)}: Ai = 0.0000 | 0 CVEs (μ_R: 0.0000 | σ²_R: 0.0000)")
            continue

        # Step A: Aggregate Exposure (Ai) and KEV count
        epss_list = [cve["epss"] for cve in cves]
        ai = compute_aggregate_epss_exposure(epss_list)
        kev_count = sum(1 for cve in cves if cve.get("in_cisa_kev", False))
        image_metadata_summary[img_name] = {"ai": ai, "total_cves": len(cves), "kev_count": kev_count}

        # Arrays for algebraic vectorization via NumPy
        a_vec = np.zeros(len(cves))
        c_vec = np.zeros(len(cves))
        b_vec = np.zeros(len(cves))
        ev_vec = np.array(epss_list)

        # Step B: Mapping physical boundaries of triangular severity (a, c, b)
        for idx, cve in enumerate(cves):
            iv = cve["impact_subscore"]
            xv = cve["exploitability_subscore"]
            sv = cve["scope_changed"]
            cv_mode = cve["base_score"]

            # Calculates exploitability boundaries under environmental pressure (Ai)
            lower_x, upper_x = compute_uncertainty_bounds(xv, ai, lambda_param=1.0)

            # Derives extreme severities (a = minimum plausible, b = maximum plausible)
            a_vec[idx] = calculate_deterministic_cvss(iv, lower_x, sv)
            c_vec[idx] = cv_mode
            b_vec[idx] = calculate_deterministic_cvss(iv, upper_x, sv)

        # Step C: Exact analytical calculation of each vulnerability's moments
        mu_c, var_c = compute_analytical_triangular_moments(a_vec, c_vec, b_vec)

        # Step D: Linear aggregation by Central Limit Theorem (CLT)
        # E[R_i] = Σ (E_v * μ_C,v)
        # Var(R_i) = Σ (E_v² * σ²_C,v)  <-- Assuming first-order independence
        mu_r = float(np.sum(ev_vec * mu_c))
        var_r = float(np.sum((ev_vec**2) * var_c))
        std_r = np.sqrt(var_r)

        image_expected_means[img_name] = mu_r
        image_expected_variances[img_name] = var_r

        # Generates theoretical Normal curve N(μ, σ²) to maintain 100% compatibility with .npz plotters
        if var_r > 0:
            clt_normal_distributions[img_name] = rng.normal(loc=mu_r, scale=std_r, size=n_compat_samples)
            clt_normal_distributions[img_name] = np.clip(clt_normal_distributions[img_name], a_min=0.0, a_max=None)
        else:
            clt_normal_distributions[img_name] = np.full(n_compat_samples, mu_r)
        
        print(f"  🔄 {img_name.ljust(25)}: Ai = {ai:.4f} | {len(cves):>4} CVEs ({kev_count:>2} KEV) | μ_R = {mu_r:>8.4f} | σ_R = {std_r:>6.4f}")

    # 3. Exact Theoretical Percentiles of the Ecosystem via Inverse Normal Function (PPF)
    master_ecosystem_pool = np.concatenate(list(clt_normal_distributions.values()))
    global_percentiles = np.percentile(master_ecosystem_pool, [5, 25, 50, 75, 90, 95])

    print("\n📈 Global Percentiles of Ecosystem (CLT Normal Approximation):")
    for p, val in zip([5, 25, 50, 75, 90, 95], global_percentiles):
        print(f"  P{p:>2}: {val:.4f}")

    # 4. Relative Risk Classification
    risk_classifications = {}
    for img_name, mean_risk in image_expected_means.items():
        if mean_risk < global_percentiles[0]:
            category = "Very low relative risk"
        elif mean_risk < global_percentiles[1]:
            category = "Low relative risk"
        elif mean_risk < global_percentiles[3]:
            category = "Intermediate relative risk"
        elif mean_risk < global_percentiles[5]:
            category = "High relative risk"
        else:
            category = "Very high or critical relative risk"
        
        risk_classifications[img_name] = category

    # 5. Exporting Data and Analytical Parameters
    output_dir = Path("aggregated_summary")
    
    with open(output_dir / "risk_classifications_environmental.json", "w", encoding="utf-8") as f:
        json.dump(risk_classifications, f, indent=4)

    # Exports ranking sorted by Analytical Means
    sorted_rank = dict(sorted(image_expected_means.items(), key=lambda item: item[1], reverse=True))
    with open(output_dir / "estimated_risks_export_environmental.json", "w", encoding="utf-8") as f:
        json.dump(sorted_rank, f, indent=4)

    # Exports Exact Analytical Moments (Mean, Variance, Standard Deviation, and KEV Metadata)
    analytical_summary = {
        img: {
            "expected_mean": image_expected_means[img],
            "variance": image_expected_variances[img],
            "std_dev": float(np.sqrt(image_expected_variances[img])),
            "aggregate_epss_ai": image_metadata_summary[img]["ai"],
            "total_cves": image_metadata_summary[img]["total_cves"],
            "kev_confirmed_count": image_metadata_summary[img]["kev_count"]
        }
        for img in image_expected_means
    }
    with open(output_dir / "analytical_clt_summary.json", "w", encoding="utf-8") as f:
        json.dump(analytical_summary, f, indent=4)

    # Keeps .npz export so plotting scripts work without structural modifications
    np.savez_compressed(output_dir / "environmental_simulation_arrays.npz", **clt_normal_distributions)

    print("\n✅ Analytical processing completed! Metadata, moments, and distributions exported.")
    print("🚀 File 'analytical_clt_summary.json' successfully generated to structure LADC tables.")

if __name__ == "__main__":
    main()