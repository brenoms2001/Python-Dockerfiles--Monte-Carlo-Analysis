from distribuicoes_vulnerabilities import distribuicoes_vulnerabilities
from criador_matrizes_vulnerabilities import monta_matrizes
from plota_histogramas_simulados import plota_histogramas_simulados
from analise_percentis import analise_percentis
from plot_ranking_riscos import plot_ranking_riscos
import numpy as np
from scipy.stats import triang
from typing import Dict, List

# ---------- Pesos para o risco_geral --------------------------
pesos_riscos = {
    "UNKNOWN": 0.5,
    "LOW": 1,
    "MEDIUM": 3,
    "HIGH": 7,
    "CRITICAL": 10,
}

def _cria_distrib_triangular(param: Dict[str, int]):
    a, c, b = param["min"], param["mode"], param["max"]
    if b == a:                  # degenera (tudo igual) → usa delta dirac
        return lambda n: np.full(n, a)
    scale = b - a
    loc = a
    shape_c = (c - a) / scale   # posição do modo em [0,1]
    dist = triang(shape_c, loc=loc, scale=scale)
    return dist.rvs             # devolve função amostradora

def simula_monte_carlo(parametros: Dict[str, Dict[str, int]], n_amostras: int = 10000, seed: int | None = None):
    
    rng = np.random.default_rng(seed)
    np.random.seed(rng.integers(0, 2**32 - 1))  # compat. para scipy
    
    samples: Dict[str, np.ndarray] = {}
    for nivel, param in parametros.items():
        amostrador = _cria_distrib_triangular(param)
        samples[nivel] = amostrador(n_amostras).astype(int)

    # risco geral ponderado
    risco_geral = sum(samples[nivel] * pesos_riscos[nivel]
                      for nivel in samples)

    return samples, risco_geral

def resumo_distrib(arr: np.ndarray, label: str):
    print(f"\n\n📊 {label}")
    print(f"  Média     : {arr.mean():.2f}")
    print(f"  Variância : {arr.var():.2f}")
    print(f"  Desvio P. : {arr.std():.2f}")
    print(f"  Mín–Máx   : {arr.min():.0f} – {arr.max():.0f}")



def main() -> None:
    monta_matrizes()
    parametros = distribuicoes_vulnerabilities("matrizes.json")

    n = 50_000  # número de amostras
    samples, risco_geral = simula_monte_carlo(parametros, n)

    for nivel, arr in samples.items():
        resumo_distrib(arr, f"{nivel} CVEs")

    resumo_distrib(risco_geral, "RISCO GERAL ponderado")
    
    # Análise de percentis
    percentiles = np.percentile(risco_geral, [5, 25, 50, 75, 90, 95])
    print("\n📈 Percentis do Risco Geral Simulado:")
    for p, val in zip([5, 25, 50, 75, 90, 95], percentiles):
        print(f"  {p:>2}%: {val:.2f}")

    # Armazena os riscos reais
    riscos_reais_dict = {}

    for v in ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14-rc"]:
        print(f"\n\n🔍 Análise de {v}----------------------------------")
        for version in ["alpine3.21", "alpine3.22", "bookworm", "bullseye", "slim-bookworm", "slim-bullseye"]:
            versao_desejada = f"{v}-{version}"
            risco_real = analise_percentis(percentiles, pesos_riscos, versao_desejada)
            if risco_real >= 0:
                    riscos_reais_dict[versao_desejada] = risco_real
    
    plot_ranking_riscos(riscos_reais_dict)


    plota_histogramas_simulados(samples, risco_geral)


if __name__ == "__main__":
    main()