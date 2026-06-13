import json
import math
from pathlib import Path

def calculate_nominal_cvss_base(impact: float, exploitability: float, scope_changed: bool) -> float:
    """
    Calcula o CVSS Base Score nominal exato seguindo a especificação
    oficial do CVSS v3.1 com a aproximação de teto (RoundUp).
    """
    if impact <= 0:
        return 0.0
    
    if not scope_changed:
        score = min(impact + exploitability, 10.0)
    else:
        score = min(1.08 * (impact + exploitability), 10.0)
        
    # Implementação do teto padrão do CVSS (1 casa decimal)
    return min(10.0, math.ceil(score * 10) / 10.0)

def main():
    # 1. Configuração de caminhos de arquivos
    data_dir = Path("aggregated_summary")
    input_profile = data_dir / "environmental_cve_profiles.json"
    output_actionable = data_dir / "actionable_remediation.json"

    if not input_profile.exists():
        print(f"❌ Erro: O arquivo de entrada '{input_profile}' não foi encontrado.")
        print("Certifique-se de rodar o 'extract_environmental_data.py' primeiro para popular os dados.")
        return

    # 2. Carrega o perfil ambiental de CVEs
    print("📥 Lendo perfis de CVEs e scores de explotação reais...")
    with open(input_profile, "r", encoding="utf-8") as f:
        cve_dataset = json.load(f)

    remediation_report = {}
    
    # Cabeçalho da tabela Markdown no terminal
    markdown_lines = [
        "| Configuração da Imagem | Total CVEs | CVEs Críticas (Corte 90%) | Redução de Esforço |",
        "|------------------------|------------|----------------------------|--------------------|"
    ]

    print("⚙️ Processando matrizes de risco individual e aplicando o Princípio de Pareto (90%)...")

    # 3. Processamento por Imagem
    # Ordena as chaves para que a tabela fique esteticamente organizada por criticidade
    for img_name in sorted(cve_dataset.keys()):
        cves = cve_dataset[img_name]
        total_cves = len(cves)
        
        if total_cves == 0:
            # Imagens limpas (como algumas variantes do Alpine)
            remediation_report[img_name] = {
                "metrics": {
                    "total_cves": 0,
                    "cves_to_remediate": 0,
                    "remediation_ratio_percentage": 0.0,
                    "effort_reduction_percentage": 100.0
                },
                "target_patches": []
            }
            markdown_lines.append(f"| {img_name:<22} | {0:<10} | {0:<26} | {100.00:6.2f}% |")
            continue

        # Calcula o risco individual e absoluto de cada CVE nesta imagem
        total_image_risk = 0.0
        processed_cves = []
        
        for cve in cves:
            cve_id = cve["cve"]
            iv = cve["impact_subscore"]
            xv = cve["exploitability_subscore"]
            sv = cve["scope_changed"]
            ev = cve["epss"]
            
            # Calcula o CVSS nominal estático
            base_score = calculate_nominal_cvss_base(iv, xv, sv)
            # Risco Ponderado: Probabilidade Real (EPSS) x Severidade (CVSS)
            individual_risk = ev * base_score
            total_image_risk += individual_risk
            
            processed_cves.append({
                "cve": cve_id,
                "risk": individual_risk
            })

        # Ordena as CVEs pelo risco individual decrescente (Gargalos no topo)
        processed_cves.sort(key=lambda x: x["risk"], reverse=True)

        # Filtro de Pareto: Acumula o risco até bater 90% da exposição total do ambiente
        accumulated_risk = 0.0
        target_patches = []
        
        for cve in processed_cves:
            # Se o risco total da imagem for zero (todas as falhas com EPSS nulo e CVSS zero)
            if total_image_risk == 0:
                break
                
            accumulated_risk += cve["risk"]
            target_patches.append(cve["cve"])
            
            # Linha de corte atingida
            if accumulated_risk >= 0.90 * total_image_risk:
                break

        # Garante pelo menos 1 CVE se houver risco real e o loop não disparar
        if total_image_risk > 0 and len(target_patches) == 0:
            target_patches.append(processed_cves[0]["cve"])

        # Cálculo de métricas de engenharia
        cves_to_remediate = len(target_patches)
        effort_reduction = 100.0 - ((cves_to_remediate / total_cves) * 100.0)
        remediation_ratio = (cves_to_remediate / total_cves) * 100.0

        # Alimenta o dicionário de saída estruturada
        remediation_report[img_name] = {
            "metrics": {
                "total_cves": total_cves,
                "cves_to_remediate": cves_to_remediate,
                "remediation_ratio_percentage": round(remediation_ratio, 2),
                "effort_reduction_percentage": round(effort_reduction, 2)
            },
            "target_patches": target_patches
        }

        # Adiciona a linha formatada no relatório Markdown
        markdown_lines.append(
            f"| {img_name:<22} | {total_cves:<10} | {cves_to_remediate:<26} | {effort_reduction:6.2f}% |"
        )

    # 4. Gravação do arquivo JSON acionável para o CI/CD
    with open(output_actionable, "w", encoding="utf-8") as f:
        json.dump(remediation_report, f, indent=4)

    # 5. Imprime o relatório final no terminal
    print("\n🚀 RELATÓRIO DE EFICIÊNCIA OPERACIONAL DEVSECOPS (MARKDOWN):\n")
    for line in markdown_lines:
        print(line)

    print(f"\n💾 Arquivo de remediação automatizada salvo em: {output_actionable}")
    print("✨ Sucesso! O pipeline CI/CD já pode consumir as 'target_patches' para atualizações focadas.")

if __name__ == "__main__":
    main()