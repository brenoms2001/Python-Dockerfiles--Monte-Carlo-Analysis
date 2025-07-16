import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def distribuicoes_vulnerabilities(json_path: str | Path, plot_dir: str | Path = "Plots", salvar_valores: bool = True):

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]
    plot_dir = Path(plot_dir)
    plot_dir.mkdir(exist_ok=True)

    valores_por_risco = {}         # valores brutos
    parametros_triangular = {}     # resultado final

    for risk in RISK_LEVELS:
        all_cves = []

        print(f"\n📊 Estatísticas para nível de risco: **{risk}**")
        print("-" * 60)
        
        for version, imagens in data.items():
            valores = [imagens[img].get(risk, 0) for img in imagens]
            arr = pd.Series(valores)
            all_cves.extend(valores)

            presente = (arr > 0).mean()
            ausente = (arr == 0).mean()
            media = arr.mean()
            var = arr.var()
            std = arr.std()

            print(f"Versão {version}:")
            print(f"  Média       = {media:.2f}")
            print(f"  Variância   = {var:.2f}")
            print(f"  Desvio Padr.= {std:.2f}")
            print(f"  P(presente) = {presente:.2%}")
            print(f"  P(ausente)  = {ausente:.2%}")
        
        # Estatísticas globais
        geral = pd.Series(all_cves)
        min_v = int(geral.min())
        mode_v = int(geral.median())  # pode ser media também
        max_v = int(geral.max())

        parametros_triangular[risk] = {
            "min": min_v,
            "mode": mode_v,
            "max": max_v
        }

        print("\n🔎 Estatísticas globais:")
        print(f"  Média geral       = {geral.mean():.2f}")
        print(f"  Variância geral   = {geral.var():.2f}")
        print(f"  Desvio padrão     = {geral.std():.2f}")
        print(f"  P(presente) total = {(geral > 0).mean():.2%}")
        print(f"  P(ausente) total  = {(geral == 0).mean():.2%}")
        print(f"  Parâmetros triangulares: min={min_v}, mode={mode_v}, max={max_v}")

        # ----- Salvar gráfico ------------------------------------------------
        plt.figure(figsize=(6, 4))
        sns.histplot(all_cves, bins=10, kde=True, color="steelblue")
        plt.title(f"Histograma de CVEs – {risk}")
        plt.xlabel("Número de CVEs")
        plt.ylabel("Frequência")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(plot_dir / f"{risk}.png", dpi=300)
        plt.close()
        print(f"✅ Gráfico salvo em {plot_dir / f'{risk}.png'}")

    return parametros_triangular
