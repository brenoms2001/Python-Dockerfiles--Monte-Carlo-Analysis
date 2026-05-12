import json
import numpy as np

def analise_percentis(percentiles: np.ndarray, weights: dict[str, float], target_version: str, path_matrices: str = "matrices.json") -> None:

    with open(path_matrices, "r") as f:
        data = json.load(f)

    for version, matrix in data.items():
        for base, value in matrix.items():
            key = f"{version}-{base}"
            if key == target_version:
                real_risk = sum(weights[k] * value.get(k, 0) for k in weights)

                print(f"\nReal risk for {target_version}: {real_risk:.2f}")
                if real_risk < percentiles[0]:
                    print("🔵 Below percentile 5% (extremely safe)")
                elif real_risk < percentiles[1]:
                    print("🟢 Below percentile 25% (safe)")
                elif real_risk < percentiles[2]:
                    print("🟡 Below percentile 50% (moderate)")
                elif real_risk < percentiles[3]:
                    print("🟠 Below percentile 75% (substantial)")
                elif real_risk < percentiles[4]:
                    print("🔴 Below percentile 90% (high)")
                elif real_risk < percentiles[5]:
                    print("⚫ Between 90%-95% (critical)")
                else:
                    print("❌ Above percentile 95% (extremely crictical)")
                
                return real_risk

    print(f"❌ Version {target_version} not found in {path_matrices}.")
