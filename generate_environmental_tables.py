import json
import numpy as np
from pathlib import Path

def identify_family(img_name: str) -> str:
    """Classifica a imagem na sua respectiva família de OS."""
    name_lower = img_name.lower()
    if "alpine" in name_lower:
        return "Alpine (Minimal)"
    elif "slim-bookworm" in name_lower:
        return "Debian Slim (Bookworm)"
    elif "slim-bullseye" in name_lower:
        return "Debian Slim (Bullseye)"
    elif "bookworm" in name_lower:
        return "Full Debian (Bookworm)"
    elif "bullseye" in name_lower:
        return "Full Debian (Bullseye)"
    return "Other"

def main():
    data_dir = Path("aggregated_summary")
    npz_path = data_dir / "environmental_simulation_arrays.npz"
    rank_path = data_dir / "estimated_risks_export_environmental.json"

    if not npz_path.exists() or not rank_path.exists():
        print("❌ Erro: Ficheiros de simulação não encontrados. Rode o pipeline primeiro.")
        return

    # 1. Carrega os dados brutos de simulação
    sim_data = np.load(npz_path)
    with open(rank_path, "r", encoding="utf-8") as f:
        image_ranking = json.load(f)

    print("📊 A processar distribuições para geração de tabelas estatísticas...")
    
    # Dicionário para armazenar métricas completas por imagem
    detailed_stats = {}
    family_grouped_risks = {}

    for img_name in sorted(sim_data.files):
        arr = sim_data[img_name]
        mean_val = np.mean(arr)
        std_val = np.std(arr)
        p5 = np.percentile(arr, 5)
        p50 = np.percentile(arr, 50)
        p95 = np.percentile(arr, 95)
        
        family = identify_family(img_name)
        if family not in family_grouped_risks:
            family_grouped_risks[family] = []
        family_grouped_risks[family].extend(arr)

        # Extrai versão do Python de forma limpa (ex: 3.11)
        python_version = img_name.split("-")[0] if "-" in img_name else img_name
        variant_name = img_name.replace(f"{python_version}-", "")

        detailed_stats[img_name] = {
            "python": python_version,
            "variant": variant_name,
            "family": family,
            "mean": mean_val,
            "std": std_val,
            "p5": p5,
            "p50": p50,
            "p95": p95
        }

    # =========================================================
    # TABELA 1: EXIBIÇÃO EM MARKDOWN NO TERMINAL (RANKING COMPLETO)
    # =========================================================
    print("\n📜 RANKING ESTATÍSTICO COMPLETO DO ECOSSISTEMA (MARKDOWN)")
    print(f"| {'Imagem Base':<25} | {'Média (E[R])':<12} | {'Desvio Pad (σ)':<14} | {'P5':<8} | {'P50 (Mediana)':<12} | {'P95':<8} |")
    print("|" + "-"*27 + "|" + "-"*14 + "|" + "-"*16 + "|" + "-"*10 + "|" + "-"*15 + "|" + "-"*10 + "|")
    
    # Ordena por risco médio decrescente
    sorted_images = sorted(detailed_stats.keys(), key=lambda k: detailed_stats[k]["mean"], reverse=True)
    for img in sorted_images:
        s = detailed_stats[img]
        print(f"| {img:<25} | {s['mean']:12.4f} | {s['std']:14.4f} | {s['p5']:8.4f} | {s['p50']:12.4f} | {s['p95']:8.4f} |")

    # =========================================================
    # COMPROVAÇÃO CIENTÍFICA DAS HIPÓTESES (ANÁLISE DE VARIÂNCIA)
    # =========================================================
    print("\n🔬 COMPROVAÇÃO MATEMÁTICA DAS HIPÓTESES DO ESTUDO")
    print("=" * 65)
    
    # Prova RQ1 & RQ3: Risco Médio e Incerteza Acumulada por Família de OS
    print("\n[RQ1 & RQ3 PROOF] Métricas Agregadas por Família Estrutural de OS:")
    for family, points in family_grouped_risks.items():
        pts_arr = np.array(points)
        print(f"  • {family:<25} -> Risco Médio: {np.mean(pts_arr):6.4f} | Incerteza Média (σ): {np.std(pts_arr):6.4f}")
    
    # Prova RQ2: Decomposição de Variância (OS vs Python Version)
    # Vamos calcular a variância entre as médias das famílias (Efeito OS) 
    # versus a variância entre as médias das versões do Python dentro da mesma família (Efeito Python)
    family_means = [np.mean(np.array(pts)) for pts in family_grouped_risks.values() if len(pts) > 0]
    variance_between_os = np.var(family_means)

    python_group_means = {}
    for img, s in detailed_stats.items():
        py = s["python"]
        if py not in python_group_means:
            python_group_means[py] = []
        python_group_means[py].append(s["mean"])
    
    variance_between_pythons = np.var([np.mean(m) for m in python_group_means.values()])

    print("\n[RQ2 PROOF] Decomposição de Variância Cruzada:")
    print(f"  • Variância Explicada pela escolha do S.O. (Variante) : {variance_between_os:.6f}")
    print(f"  • Variância Explicada pela versão do Interpretador Python: {variance_between_pythons:.6f}")
    
    ratio = variance_between_os / (variance_between_pythons if variance_between_pythons > 0 else 1e-9)
    print(f"  👉 CONCLUSÃO MATEMÁTICA: A escolha do Sistema Operacional é {ratio:.1f} vezes mais impactante no risco do que a versão do Python.")
    print("=" * 65)

    # =========================================================
    # GERADOR DE CÓDIGO LATEX PARA O ARTIGO (GRAVAÇÃO EM ARQUIVO)
    # =========================================================
    latex_output_path = data_dir / "environmental_tables_latex.tex"
    
    with open(latex_output_path, "w", encoding="utf-8") as f:
        f.write("% =========================================================\n")
        f.write("% TABELA LATEX GENERATED AUTOMATICALLY FOR OVERLEAF\n")
        f.write("% =========================================================\n\n")
        
        # Escreve Tabela de Decomposição de Variância (Resposta direta à RQ2)
        f.write("\\begin{table}[htbp]\n\\centering\n")
        f.write("\\caption{Variance Decomposition of Environment-Conditioned Risk (RQ2 Validation).}\n")
        f.write("\\label{tab:variance_decomposition}\n")
        f.write("\\begin{tabular}{lcc}\n\\toprule\n")
        f.write("\\textbf{Analysis Dimension} & \\textbf{Calculated Variance} & \\textbf{Relative Influence Factor} \\\\\n\\midrule\n")
        f.write(f"Operating System Base (Variant) & {variance_between_os:.6f} & {ratio:.1f}x \\\\\n")
        f.write(f"Python Runtime Version & {variance_between_pythons:.6f} & 1.0x \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n\n")
        
        # Escreve Tabela Completa de Métricas Agregadas do Ecossistema
        f.write("\\begin{table}[htbp]\n\\centering \\footnotesize\n")
        f.write("\\caption{Comprehensive Descriptive Statistics and Risk Percentiles of Python Base Images.}\n")
        f.write("\\label{tab:ecosystem_full_statistics}\n")
        f.write("\\begin{tabular}{lccccc}\n\\toprule\n")
        f.write("\\textbf{Image Configuration} & \\textbf{Mean ($\\mathbb{E}[\\widetilde{R}_i]$)} & \\textbf{Std Dev ($\\sigma$)} & \\textbf{$P_5$} & \\textbf{$P_{50}$} & \\textbf{$P_{95}$} \\\\\n\\midrule\n")
        
        current_family = ""
        for img in sorted_images:
            s = detailed_stats[img]
            if s["family"] != current_family:
                current_family = s["family"]
                f.write(f"\\midrule\n\\multicolumn{{6}}{{l}}{{\\textbf{{{current_family}}}}} \\\\\n")
            
            f.write(f"\\texttt{{{img}}} & {s['mean']:.4f} & {s['std']:.4f} & {s['p5']:.4f} & {s['p50']:.4f} & {s['p95']:.4f} \\\\\n")
            
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

    print(f"\n🚀 Sucesso! Código LaTeX gerado e salvo em: {latex_output_path}")

if __name__ == "__main__":
    main()