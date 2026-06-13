import json
import numpy as np
from pathlib import Path
from typing import Dict, Any

# Importamos os módulos matemáticos puros criados na Prioridade 2
from cvss_environmental_math import compute_aggregate_epss_exposure, compute_uncertainty_bounds

def calculate_cvss_base_score_vectorized(impact: float, exploitability_array: np.ndarray, scope_changed: bool) -> np.ndarray:
    """
    Versão vetorizada em alta performance da equação oficial do CVSS v3.1.
    Processa um array NumPy de 50.000 amostras de explorabilidade de uma só vez.
    """
    if impact <= 0:
        return np.zeros_like(exploitability_array)
    
    # Aplica as condicionais de Escopo (Scope) do padrão do Fórum FIRST
    if not scope_changed:
        scores = np.minimum(impact + exploitability_array, 10.0)
    else:
        scores = np.minimum(1.08 * (impact + exploitability_array), 10.0)
    
    # Implementação estrita e vetorizada do RoundUp1 do CVSS v3.1
    # Se o valor for um múltiplo exato de 0.1 mantém, caso contrário arredonda para cima.
    scores_int = np.round(scores * 100000).astype(int)
    rounded = np.where(scores_int % 10000 == 0, np.round(scores, 1), np.ceil(np.round(scores, 9) * 10.0) / 10.0)
    return rounded

def main():
    # 1. Carrega o Dataset gerado na Prioridade 1
    profile_path = Path("aggregated_summary/environmental_cve_profiles.json")
    if not profile_path.exists():
        print("❌ Erro: Ficheiro environmental_cve_profiles.json não encontrado. Executa o extrator primeiro.")
        return
        
    with open(profile_path, "r", encoding="utf-8") as f:
        cve_dataset = json.load(f)

    n_samples = 50000
    rng = np.random.default_rng(seed=42) # Semente fixa para reprodutibilidade estrita (RQ3)
    
    # Dicionários para armazenar os resultados da simulação por ambiente
    all_image_distributions: Dict[str, np.ndarray] = {}
    image_expected_means: Dict[str, float] = {}
    image_metadata_summary: Dict[str, Dict[str, Any]] = {}

    print(f"🎲 A iniciar a Simulação de Monte Carlo por Ambiente ({n_samples} amostras por imagem)...")

    # 2. Executa o Loop Principal sobre cada uma das imagens do ecossistema
    for img_name, cves in cve_dataset.items():
        if not cves:
            # Tratamento robusto para imagens totalmente limpas (ex: algumas vertentes Alpine)
            all_image_distributions[img_name] = np.zeros(n_samples)
            image_expected_means[img_name] = 0.0
            image_metadata_summary[img_name] = {"ai": 0.0, "total_cves": 0}
            print(f"  🟢 {img_name.ljust(25)}: Ai = 0.0000 | 0 CVEs (Risco Médio: 0.00)")
            continue

        # Passo A: Extrai a lista de EPSS reais e calcula a Exposição Agregada (Ai) da imagem
        epss_list = [cve["epss"] for cve in cves]
        ai = compute_aggregate_epss_exposure(epss_list)
        image_metadata_summary[img_name] = {"ai": ai, "total_cves": len(cves)}

        # Inicializa o array acumulador de risco da imagem para as 50.000 rodadas
        image_risk_accumulated = np.zeros(n_samples)

        # Passo B, C e D: Simulação interna por componente de cada CVE individual
        for cve in cves:
            iv = cve["impact_subscore"]
            xv = cve["exploitability_subscore"]
            sv = cve["scope_changed"]
            ev = cve["epss"]

            # Calcula os limites físicos simétricos (L e U) baseados no Ai da imagem
            lower, upper = compute_uncertainty_bounds(xv, ai, lambda_param=1.0)

            # Sorteia as 50.000 novas métricas de explorabilidade sob a curva triangular do ambiente
            if lower == upper:
                expl_samples = np.full(n_samples, lower)
            else:
                expl_samples = rng.triangular(lower, xv, upper, size=n_samples)

            # Passa o lote de amostras pela equação oficial vetorizada do CVSS v3.1
            simulated_base_scores = calculate_cvss_base_score_vectorized(iv, expl_samples, sv)

            # Passo E: Acumula o Risco ponderado pela probabilidade real (EPSS) da vulnerabilidade
            image_risk_accumulated += (ev * simulated_base_scores)

        # Guarda a distribuição empírica final da imagem
        all_image_distributions[img_name] = image_risk_accumulated
        image_expected_means[img_name] = float(np.mean(image_risk_accumulated))
        
        print(f"  🔄 {img_name.ljust(25)}: Ai = {ai:.4f} | {len(cves)} CVEs (Risco Médio: {image_expected_means[img_name]:.2f})")

    # 3. Construção do Universo Base do Ecossistema (Master Pool para Percentis)
    # Concatenamos todas as distribuições para criar a variância global do ecossistema oficial Python
    master_ecosystem_pool = np.concatenate(list(all_image_distributions.values()))
    global_percentiles = np.percentile(master_ecosystem_pool, [5, 25, 50, 75, 90, 95])

    print("\n📈 Percentis Globais de Referência do Ecossistema Combinado:")
    for p, val in zip([5, 25, 50, 75, 90, 95], global_percentiles):
        print(f"  P{p:>2}: {val:.2f}")

    # 4. Classificação de Risco Relativo das Imagens Reais
    risk_classifications = {}
    for img_name, mean_risk in image_expected_means.items():
        if mean_risk < global_percentiles[0]:
            category = "Very low relative risk"
            tag = "🔵"
        elif mean_risk < global_percentiles[1]:
            category = "Low relative risk"
            tag = "🟢"
        elif mean_risk < global_percentiles[3]:
            category = "Intermediate relative risk"
            tag = "🟡"
        elif mean_risk < global_percentiles[5]:
            category = "High relative risk"
            tag = "🟠"
        else:
            category = "Very high or critical relative risk"
            tag = "🔴"
        
        risk_classifications[img_name] = category

    # 5. Exportação dos Resultados Consolidados para Suporte do Artigo
    output_dir = Path("aggregated_summary")
    
    with open(output_dir / "risk_classifications_environmental.json", "w", encoding="utf-8") as f:
        json.dump(risk_classifications, f, indent=4)

    # Exporta o ranking ordenado de médias para a construção das tabelas LaTeX
    sorted_rank = dict(sorted(image_expected_means.items(), key=lambda item: item[1], reverse=True))
    with open(output_dir / "estimated_risks_export_environmental.json", "w", encoding="utf-8") as f:
        json.dump(sorted_rank, f, indent=4)

    # Salva as matrizes de simulação brutas em formato comprimido NumPy (.npz) 
    # Isto permitirá que o script de plotagem da Prioridade 4 leia os dados instantaneamente
    np.savez_compressed(output_dir / "environmental_simulation_arrays.npz", **all_image_distributions)

    print("\n✅ Ficheiros de metadados e classificações gerados com sucesso na pasta 'aggregated_summary'!")
    print("🚀 Pronto para avançar para a Prioridade 4: Visualização e Gráficos Científicos.")

if __name__ == "__main__":
    main()