import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def distribuicoes_vulnerabilities(json_path: str | Path,
                                   plot_dir: str | Path = "Plots"):
    """
    Calcula estatísticas e salva um gráfico (boxplot + histograma)
    por nível de risco em <plot_dir>/<risk>.png.

    Parâmetros
    ----------
    json_path : str | Path
        Caminho para o arquivo matrizes.json.
    plot_dir : str | Path, opcional
        Pasta onde os PNGs serão gravados (default = "Plots").
    """
    # ----- Lê dados ---------------------------------------------------------
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]
    plot_dir = Path(plot_dir)
    plot_dir.mkdir(exist_ok=True)

    for risk in RISK_LEVELS:
        all_cves, version_labels = [], []

        for version, imagens in data.items():
            valores = [imagens[img].get(risk, 0) for img in imagens]
            all_cves.extend(valores)
            version_labels.extend([version] * len(valores))

        # ----- DataFrame para plotagem --------------------------------------
        df_plot = pd.DataFrame({
            "CVEs": all_cves,
        })

        # ----- Geração do gráfico -------------------------------------------
        plt.figure(figsize=(12, 6))
        plt.suptitle(f'Distribuição de CVEs – Nível: {risk}', fontsize=14)

        # Histograma + KDE
        sns.histplot(df_plot["CVEs"], bins=10, kde=True, color="skyblue")
        plt.title("Histograma Geral (KDE)")

        plt.tight_layout(rect=[0, 0, 1, 0.95])

        # Salva em PNG
        out_file = plot_dir / f"{risk}.png"
        plt.savefig(out_file, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"✅ Gráfico salvo em {out_file}")

    print("Todos os gráficos foram gerados e salvos com sucesso!")
