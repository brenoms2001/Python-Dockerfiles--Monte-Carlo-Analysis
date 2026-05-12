import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

def plot_simulated_histograms(samples: dict[str, np.ndarray],
                                 overall_risk: np.ndarray,
                                 output_directory: str | Path = "SimulatedPlots") -> None:
    
    Path(output_directory).mkdir(exist_ok=True)
    print(f"\n")
    for level, values in samples.items():
        plt.figure(figsize=(6, 4))
        sns.histplot(values, bins=50, kde=True, color="royalblue")
        plt.title(f"Simulated Distribution – {level}")
        plt.xlabel("Number of simulated CVEs")
        plt.ylabel("Frequency")
        plt.grid(True)
        plt.tight_layout()
        path = Path(output_directory) / f"{level}_simulated.png"
        plt.savefig(path, dpi=300)
        plt.close()
        print(f"📊 Saved chart: {path}")

    # Overall Risk Chart
    plt.figure(figsize=(6, 4))
    sns.histplot(overall_risk, bins=50, kde=True, color="firebrick")
    plt.title("Simulated Distribution – Overall Risk")
    plt.xlabel("Weighted Overall Risk")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.tight_layout()
    path = Path(output_directory) / "overall_risk_simulated.png"
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"📊 Saved chart: {path}\n")
