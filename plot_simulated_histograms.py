import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
from typing import Dict

def plot_simulated_histograms(samples: Dict[str, np.ndarray],
                              overall_risk: np.ndarray,
                              output_directory: str | Path = "SimulatedPlots",
                              show_kde: bool = True) -> None:
    """
    Gera os histogramas das simulações.
    O argumento show_kde controla a exibição da linha de densidade (padrão é True).
    """
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    print("\n")
    
    sns.set_theme(style="whitegrid")

    # 1. Gráficos individuais por severidade
    for level, values in samples.items():
        plt.figure(figsize=(6, 4))
        
        # O KDE agora é ligado ou desligado baseado no argumento
        sns.histplot(values, bins=50, kde=show_kde, color="royalblue", stat="density")
        
        plt.title(f"Simulated Distribution – {level}")
        plt.xlabel("Number of simulated CVEs")
        plt.ylabel("Density")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        path = Path(output_directory) / f"{level}_simulated.png"
        plt.savefig(path, dpi=300)
        plt.close()
        print(f"📊 Saved chart: {path}")

    # 2. Gráfico do Risco Total
    plt.figure(figsize=(6, 4))
    
    sns.histplot(overall_risk, bins=50, kde=show_kde, color="firebrick", stat="density")
    
    plt.title("Simulated Distribution – Estimated Overall Risk")
    plt.xlabel("Weighted Overall Risk")
    plt.ylabel("Density")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    path = Path(output_directory) / "overall_risk_simulated.png"
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"📊 Saved chart: {path}\n")