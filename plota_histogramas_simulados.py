import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

def plota_histogramas_simulados(samples: dict[str, np.ndarray],
                                 risco_geral: np.ndarray,
                                 pasta_saida: str | Path = "PlotsSimulados") -> None:
    """
    Plota histogramas com curvas KDE para os CVEs simulados por nível de risco,
    e também para o risco geral ponderado. Salva os plots em arquivos PNG.

    Parâmetros:
    -----------
    samples : dict[str, np.ndarray]
        Dicionário com arrays de CVEs simulados por nível de risco.
    risco_geral : np.ndarray
        Array com os valores simulados do risco geral ponderado.
    pasta_saida : str | Path
        Caminho onde os gráficos serão salvos.
    """
    Path(pasta_saida).mkdir(exist_ok=True)

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
    print(f"📊 Gráfico salvo: {caminho}")
