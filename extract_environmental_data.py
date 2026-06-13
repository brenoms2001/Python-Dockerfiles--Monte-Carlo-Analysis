import json
import re
import urllib.request
import urllib.parse
from pathlib import Path

def parse_cvss_v3_vector(vector_str: str) -> tuple[float, float, bool]:
    """
    Decodifica a string do vetor CVSS v3.1 para extrair
    o Impact Subscore (Iv), Exploitability Subscore (Xv) e Escopo (Sv).
    """
    if not vector_str or ("3.1" not in vector_str and "3.0" not in vector_str):
        return 5.0, 1.9, False  # Fallback neutro se o vetor for inválido
        
    metrics = {}
    for part in vector_str.split('/'):
        if ':' in part:
            k, v = part.split(':')
            metrics[k] = v

    scope = metrics.get('S', 'U')
    scope_changed = (scope == 'C')

    av_map = {'N': 0.85, 'A': 0.62, 'L': 0.55, 'P': 0.20}
    ac_map = {'L': 0.77, 'H': 0.44}
    ui_map = {'N': 0.85, 'R': 0.62}
    pr_map = {
        'U': {'N': 0.85, 'L': 0.62, 'H': 0.27},
        'C': {'N': 0.85, 'L': 0.68, 'H': 0.50}
    }
    c_map = {'N': 0.0, 'L': 0.22, 'H': 0.56}
    i_map = {'N': 0.0, 'L': 0.22, 'H': 0.56}
    a_map = {'N': 0.0, 'L': 0.22, 'H': 0.56}

    av = av_map.get(metrics.get('AV', 'N'), 0.85)
    ac = ac_map.get(metrics.get('AC', 'L'), 0.77)
    pr = pr_map[scope].get(metrics.get('PR', 'N'), 0.85)
    ui = ui_map.get(metrics.get('UI', 'N'), 0.85)
    
    c = c_map.get(metrics.get('C', 'N'), 0.0)
    i = i_map.get(metrics.get('I', 'N'), 0.0)
    a = a_map.get(metrics.get('A', 'N'), 0.0)

    expl_subscore = round(8.22 * av * ac * pr * ui, 1)
    iss = 1 - (1 - c) * (1 - i) * (1 - a)
    
    if not scope_changed:
        impact_subscore = round(6.42 * iss, 1)
    else:
        impact_subscore = round(7.52 * (iss - 0.029) - 3.25 * (iss - 0.02)**15, 1)

    return impact_subscore, expl_subscore, scope_changed

def fetch_real_epss_scores(cve_list: list[str]) -> dict[str, float]:
    """
    Busca os scores EPSS reais diretamente da API pública e oficial do Fórum FIRST.
    Usa lotes de 80 para respeitar o limite estrito de caracteres da URL da API.
    """
    epss_map = {}
    clean_cves = [c for c in cve_list if c.startswith("CVE-")]
    if not clean_cves:
        return epss_map

    print(f"🌐 Consultando API do FIRST.org para {len(clean_cves)} CVEs únicas...")
    batch_size = 80  
    
    for i in range(0, len(clean_cves), batch_size):
        batch = clean_cves[i:i+batch_size]
        cve_param = ",".join(batch)
        url = f"https://api.first.org/data/v1/epss?cve={cve_param}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'TCC-MonteCarlo-Scanner/1.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode())
                results = data.get("data", [])
                for res in results:
                    cve_id = res.get("cve")
                    epss_val = float(res.get("epss", 0.0001))
                    epss_map[cve_id] = epss_val
        except Exception as e:
            print(f"  ⚠️ Aviso ao buscar lote {(i//batch_size) + 1}: {e}")
            continue
            
    print(f"✅ Mapeamento concluído: {len(epss_map)} CVEs associadas a scores EPSS reais.")
    return epss_map

def main():
    scans_dir = Path(".")  
    output_profile = Path("aggregated_summary/environmental_cve_profiles.json")
    output_profile.parent.mkdir(exist_ok=True)
    
    # ETAPA 1: Coleta preliminar das CVEs únicas
    all_discovered_cves = set()
    scan_files_mapped = []

    for json_file in scans_dir.rglob("*.json"):
        if json_file.name in ["matrices.json", "environmental_cve_profiles.json", "risk_classifications_environmental.json", "estimated_risks_export_environmental.json"]:
            continue
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                scan_data = json.load(f)
                if "ArtifactName" in scan_data and "Results" in scan_data:
                    scan_files_mapped.append(json_file)
                    for res in scan_data.get("Results", []):
                        for vuln in res.get("Vulnerabilities", []):
                            all_discovered_cves.add(vuln.get("VulnerabilityID", "UNKNOWN"))
            except Exception:
                continue

    # ETAPA 2: Busca os dados reais na API do FIRST
    epss_database = fetch_real_epss_scores(list(all_discovered_cves))

    # ETAPA 3: Processamento e gravação dos perfis por imagem
    environmental_dataset = {}

    for json_file in scan_files_mapped:
        with open(json_file, "r", encoding="utf-8") as f:
            scan_data = json.load(f)

        artifact_name = scan_data.get("ArtifactName", "unknown").replace("trivy-scan:", "")
        print(f"📦 Compilando métricas para o ambiente: {artifact_name}")
        environmental_dataset[artifact_name] = []

        for res in scan_data.get("Results", []):
            for vuln in res.get("Vulnerabilities", []):
                cve_id = vuln.get("VulnerabilityID", "UNKNOWN")
                
                cvss_obj = vuln.get("CVSS", {})
                nvd_v3 = cvss_obj.get("nvd", {}) or cvss_obj.get("redhat", {}) or cvss_obj.get("ghsa", {})
                vector_str = nvd_v3.get("V3Vector", "")
                
                iv, xv, sv = parse_cvss_v3_vector(vector_str)
                epss_value = epss_database.get(cve_id, 0.0001)
                
                environmental_dataset[artifact_name].append({
                    "cve": cve_id,
                    "impact_subscore": iv,
                    "exploitability_subscore": xv,
                    "scope_changed": sv,
                    "epss": epss_value
                })

    with open(output_profile, "w", encoding="utf-8") as f:
        json.dump(environmental_dataset, f, indent=4)
        
    print(f"\n✨ Sucesso! Dataset dinâmico gerado em: {output_profile}")

if __name__ == "__main__":
    main()