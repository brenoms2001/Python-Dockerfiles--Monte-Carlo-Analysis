import math
import numpy as np

def compute_aggregate_epss_exposure(epss_scores: list[float]) -> float:
    """
    Implementa a Equação do Artigo: Ai = 1 - Produtório(1 - ev)
    Calcula a pressão de explotação agregada do ambiente.
    """
    if not epss_scores:
        return 0.0
    # Produtório de (1 - ev)
    complement_product = np.prod([1.0 - float(e) for e in epss_scores])
    return float(1.0 - complement_product)

def compute_uncertainty_bounds(xv: float, ai: float, lambda_param: float = 1.0, x_max: float = 3.9) -> tuple[float, float]:
    """
    Implementa as Equações de Janela e Fronteiras Físicas do Artigo:
    hi = (lambda * Ai * Xmax) / 2
    L = max(0, Xv - hi)
    U = min(Xmax, Xv + hi)
    """
    hi = (lambda_param * ai * x_max) / 2.0
    lower_bound = max(0.0, xv - hi)
    upper_bound = min(x_max, xv + hi)
    return lower_bound, upper_bound

def round_up_1(value: float) -> float:
    """
    Implementa a função RoundUp1 exigida formalmente pelo padrão CVSS v3.1.
    Arredonda para cima com precisão estrita de uma casa decimal.
    """
    int_val = int(value * 100000)
    if int_val % 10000 == 0:
        return round(value, 1)
    else:
        return math.ceil(value * 10.0) / 10.0

def calculate_cvss_base_score(impact_subscore: float, exploitability_subscore: float, scope_changed: bool) -> float:
    """
    Implementa a Equação oficial do CVSS v3.1 (Equation 2 do seu artigo).
    Recebe os subscores e retorna a nota final tratada por condicionais de escopo.
    """
    if impact_subscore <= 0:
        return 0.0
        
    if not scope_changed:
        return round_up_1(min(impact_subscore + exploitability_subscore, 10.0))
    else:
        return round_up_1(min(1.08 * (impact_subscore + exploitability_subscore), 10.0))