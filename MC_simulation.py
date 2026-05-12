from distributions_vulnerabilities import distributions_vulnerabilities
from build_vulnerabilities_matrices import build_matrices
from plot_simulated_histograms import plot_simulated_histograms
from analise_percentis import analise_percentis
from plot_ranking_risks import plot_ranking_risks
import numpy as np
from scipy.stats import triang
from typing import Dict

# ---------- Weights for overall risk --------------------------
weights_risks = {
    "UNKNOWN": 0.5,
    "LOW": 1,
    "MEDIUM": 3,
    "HIGH": 7,
    "CRITICAL": 10,
}

def _create_triangular_distribution(param: Dict[str, int]):
    a, c, b = param["min"], param["mode"], param["max"]
    if b == a:                  # degenerates (all the same) → uses delta dirac
        return lambda n: np.full(n, a)
    scale = b - a
    loc = a
    shape_c = (c - a) / scale   # mode position in [0,1]
    dist = triang(shape_c, loc=loc, scale=scale)
    return dist.rvs             # returns sampling function

def simulate_monte_carlo(parameters: Dict[str, Dict[str, int]], n_samples: int = 10000, seed: int | None = None):
    
    rng = np.random.default_rng(seed)
    np.random.seed(rng.integers(0, 2**32 - 1))  # compact. to scipy
    
    samples: Dict[str, np.ndarray] = {}
    for level, param in parameters.items():
        sampler = _create_triangular_distribution(param)
        samples[level] = sampler(n_samples).astype(int)

    # weighted overall risk
    overall_risk = sum(samples[level] * weights_risks[level]
                      for level in samples)

    return samples, overall_risk

def distribution_summary(arr: np.ndarray, label: str):
    print(f"\n\n📊 {label}")
    print(f"  Mean      : {arr.mean():.2f}")
    print(f"  Variance  : {arr.var():.2f}")
    print(f"  Std. Dev. : {arr.std():.2f}")
    print(f"  Min–Max   : {arr.min():.0f} – {arr.max():.0f}")

def main() -> None:
    build_matrices()
    parameters = distributions_vulnerabilities("matrices.json")

    n = 50_000  # number of samples
    samples, overall_risk = simulate_monte_carlo(parameters, n)

    for level, arr in samples.items():
        distribution_summary(arr, f"{level} CVEs")

    distribution_summary(overall_risk, "WEIGHTED OVERALL RISK")
    
    # Percentile analysis
    percentiles = np.percentile(overall_risk, [5, 25, 50, 75, 90, 95])
    print("\n📈 Percentiles of Simulated Overall Risk:")
    for p, val in zip([5, 25, 50, 75, 90, 95], percentiles):
        print(f"  {p:>2}%: {val:.2f}")

    # Stores the real risks
    real_risks_dict = {}

    for v in ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14-rc"]:
        print(f"\n\n🔍 Analysis of {v}----------------------------------")
        for version in ["alpine3.21", "alpine3.22", "bookworm", "bullseye", "slim-bookworm", "slim-bullseye"]:
            target_version = f"{v}-{version}"
            real_risk = analise_percentis(percentiles, weights_risks, target_version)
            if real_risk >= 0:
                    real_risks_dict[target_version] = real_risk
    
    plot_ranking_risks(real_risks_dict)
    plot_simulated_histograms(samples, overall_risk)


if __name__ == "__main__":
    main()