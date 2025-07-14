import json
from pathlib import Path
from collections import Counter

entrada = Path("analisados")  # onde estão os JSONs
saida_agregados = Path("resumo_agregado")
saida_agregados.mkdir(exist_ok=True)

for path in entrada.rglob("trivy-image.json"):
    with open(path) as f:
        data = json.load(f)

    severidades = []

    for result in data.get("Results", []):
        for vuln in result.get("Vulnerabilities", []):
            severidades.append(vuln["Severity"])

    contagem = Counter(severidades)
    resumo = {
        "imagem": data.get("ArtifactName", "desconhecido"),
        "resumo": dict(contagem)
    }

    out_path = saida_agregados / path.relative_to(entrada).parent / "resumo.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as out:
        json.dump(resumo, out, indent=2)

    print(f"✅ Resumo gerado para {resumo['imagem']}")