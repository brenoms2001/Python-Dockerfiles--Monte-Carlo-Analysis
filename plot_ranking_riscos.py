import matplotlib.pyplot as plt
from typing import Dict

def plot_ranking_riscos(riscos_reais: Dict[str, float], caminho_saida: str = "Plots/ranking_versoes_risco_real.png") -> None:
    # Organiza do maior para o menor risco
    riscos_ordenados = sorted(riscos_reais.items(), key=lambda x: x[1], reverse=True)
    nomes = [k for k, _ in riscos_ordenados]
    valores = [v for _, v in riscos_ordenados]

    # Plot
    plt.figure(figsize=(14, 7))
    plt.barh(nomes, valores, color='crimson')
    plt.xlabel("Risco Real Ponderado")
    plt.ylabel("Versão da Imagem Docker")
    plt.title("Ranking de Risco Real por Versão")
    plt.gca().invert_yaxis()
    plt.grid(axis='x', linestyle='--', alpha=0.4)

    plt.tight_layout()
    plt.savefig(caminho_saida)
    plt.show()
