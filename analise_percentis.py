import json
import numpy as np

def analise_percentis(percentiles: np.ndarray, pesos: dict[str, float], versao_desejada: str, caminho_matrizes: str = "matrizes.json") -> None:

    with open(caminho_matrizes, "r") as f:
        dados = json.load(f)

    for versao, matriz in dados.items():
        for base, valores in matriz.items():
            chave = f"{versao}-{base}"
            if chave == versao_desejada:
                risco_real = sum(pesos[k] * valores.get(k, 0) for k in pesos)

                print(f"\nRisco real para {versao_desejada}: {risco_real:.2f}")
                if risco_real < percentiles[0]:
                    print("🔵 Abaixo do percentil 5% (extremamente segura)\n")
                elif risco_real < percentiles[1]:
                    print("🟢 Abaixo do percentil 25% (segura)\n")
                elif risco_real < percentiles[2]:
                    print("🟡 Abaixo do percentil 50% (moderada)\n")
                elif risco_real < percentiles[3]:
                    print("🟠 Abaixo do percentil 75% (considerável)\n")
                elif risco_real < percentiles[4]:
                    print("🔴 Abaixo do percentil 90% (alta)\n")
                elif risco_real < percentiles[5]:
                    print("⚫ Entre 90%-95% (crítica)\n")
                elif risco_real > percentiles[5]:
                    print("❌ Acima do percentil 95% (extremamente crítica)\n")

                return

    print(f"❌ Versão {versao_desejada} não encontrada em {caminho_matrizes}.")
