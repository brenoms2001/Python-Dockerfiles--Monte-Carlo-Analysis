

import pip

from distribuicoes_vulnerabilities import distribuicoes_vulnerabilities
pip.main(['install', 'pandas'])
from pathlib import Path
import json
import pandas as pd

# --- CONFIGURAÇÕES ----------------------------------------------------------
ROOT = Path(__file__).resolve().parent          # pasta do script
BASE = ROOT / "resumo_agregado"                 # onde estão os JSON
IMAGES = [                                      # ordem fixa das imagens
    "alpine3.21",
    "alpine3.22",
    "bookworm",
    "bullseye",
    "slim-bookworm",
    "slim-bullseye",
]
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]
# ----------------------------------------------------------------------------


def coleta_resumos(pasta: Path) -> dict[tuple[str, str], dict]:
    dados = {}
    for json_path in pasta.rglob("resumo.json"):
        versao, variante = json_path.parts[-3:-1]
        with json_path.open(encoding="utf-8") as f:
            resumo = json.load(f)["resumo"]
        dados[(versao, variante)] = resumo
    return dados


def monta_matrix_por_versao(dados: dict) -> dict[str, pd.DataFrame]:
    matrizes = {}
    versoes = sorted({v for v, _ in dados.keys()}, key=lambda s: (s.count("."), s))
    for versao in versoes:
        linhas = []
        for variante in IMAGES:
            resumo = dados.get((versao, variante), {})
            linhas.append([resumo.get(risco, 0) for risco in RISK_LEVELS])
        df = pd.DataFrame(linhas, index=IMAGES, columns=RISK_LEVELS)
        matrizes[versao] = df
    return matrizes


def salva_json(matrizes: dict[str, pd.DataFrame], destino: Path) -> None:
    
    resultado = {
        versao: df.to_dict(orient="index")
        for versao, df in matrizes.items()
    }
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)


def main() -> None:
    dados = coleta_resumos(BASE)
    matrizes = monta_matrix_por_versao(dados)

    destino_json = ROOT / "matrizes.json"

    salva_json(matrizes, destino_json)

    print("✅ Matrizes salvas em JSON!")
    print("Exemplo (3.11):\n", matrizes["3.11"])

    distribuicoes_vulnerabilities("matrizes.json")  



if __name__ == "__main__":
    main()
