import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

def plota_histogramas_simulados(samples: dict[str, np.ndarray],
                                 risco_geral: np.ndarray,
                                 pasta_saida: str | Path = "PlotsSimulados") -> None:
    
    Path(pasta_saida).mkdir(exist_ok=True)
    print(f"\n")
    for nivel, valores in samples.items():
        plt.figure(figsize=(6, 4))
        sns.histplot(valores, bins=50, kde=True, color="royalblue")
        plt.title(f"Distribuição Simulada – {nivel}")
        plt.xlabel("Número de CVEs simulados")
        plt.ylabel("Frequência")
        plt.grid(True)
        plt.tight_layout()
        caminho = Path(pasta_saida) / f"{nivel}_simulado.png"
        plt.savefig(caminho, dpi=300)
        plt.close()
        print(f"📊 Gráfico salvo: {caminho}")

    # Gráfico do risco geral
    plt.figure(figsize=(6, 4))
    sns.histplot(risco_geral, bins=50, kde=True, color="firebrick")
    plt.title("Distribuição Simulada – Risco Geral")
    plt.xlabel("Risco Geral Ponderado")
    plt.ylabel("Frequência")
    plt.grid(True)
    plt.tight_layout()
    caminho = Path(pasta_saida) / "risco_geral_simulado.png"
    plt.savefig(caminho, dpi=300)
    plt.close()
    print(f"📊 Gráfico salvo: {caminho}\n")
