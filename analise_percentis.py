import numpy as np

def analise_percentis(risco_geral):
    percentiles = np.percentile(risco_geral, [10, 25, 50, 75, 90])
    print("\n📈 Percentis do Risco Geral:"
          f"\n  10%: {percentiles[0]:.2f}"
          f"\n  25%: {percentiles[1]:.2f}"
          f"\n  50%: {percentiles[2]:.2f}"
          f"\n  75%: {percentiles[3]:.2f}"
          f"\n  90%: {percentiles[4]:.2f}"
          f"\n")