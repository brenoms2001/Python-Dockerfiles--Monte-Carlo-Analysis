from distribuicoes_vulnerabilities import distribuicoes_vulnerabilities
from criador_matrizes_vulnerabilities import monta_matrizes
from plota_histogramas_simulados import plota_histogramas_simulados
import numpy as np
from scipy.stats import triang
from typing import Dict, List

# ---------- Pesos para o risco_geral --------------------------
RISK_WEIGHTS = {
    "UNKNOWN": 0.5,
    "LOW": 1,
    "MEDIUM": 3,
    "HIGH": 7,
    "CRITICAL": 10,
}

def _cria_distrib_triangular(param: Dict[str, int]):
    """
    Constrói uma distribuição triangular scipy.stats.triang
    a partir de {min, mode, max}.
    """
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
    risco_geral = sum(samples[nivel] * RISK_WEIGHTS[nivel]
                      for nivel in samples)

    return samples, risco_geral

def resumo_distrib(arr: np.ndarray, label: str):
    print(f"\n📊 {label}")
    print(f"  Média     : {arr.mean():.2f}")
    print(f"  Variância : {arr.var():.2f}")
    print(f"  Desvio P. : {arr.std():.2f}")
    print(f"  Mín–Máx   : {arr.min():.0f} – {arr.max():.0f}")



from simulacao_MC import simula_monte_carlo, resumo_distrib, plota_histogramas_simulados

def main() -> None:
    monta_matrizes()
    parametros = distribuicoes_vulnerabilities("matrizes.json")

    n = 50_000  # número de amostras
    samples, risco_geral = simula_monte_carlo(parametros, n)

    for nivel, arr in samples.items():
        resumo_distrib(arr, f"{nivel} CVEs")

    resumo_distrib(risco_geral, "RISCO GERAL ponderado")

    plota_histogramas_simulados(samples, risco_geral)

if __name__ == "__main__":
    main()