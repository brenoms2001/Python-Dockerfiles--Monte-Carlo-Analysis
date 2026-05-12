import matplotlib.pyplot as plt
from typing import Dict

def plot_ranking_risks(real_risks: Dict[str, float], output_path: str = "Plots/ranking_versions_real_risk.png") -> None:
    # Organize from highest to lowest risk
    ordered_risks = sorted(real_risks.items(), key=lambda x: x[1], reverse=True)
    names = [k for k, _ in ordered_risks]
    values = [v for _, v in ordered_risks]

    # Plot
    plt.figure(figsize=(14, 7))
    plt.barh(names, values, color='crimson')
    plt.xlabel("Weighted Real Risk")
    plt.ylabel("Docker Image Version")
    plt.title("Real Risk Ranking by Version")
    plt.gca().invert_yaxis()
    plt.grid(axis='x', linestyle='--', alpha=0.4)

    plt.tight_layout()
    plt.savefig(output_path)