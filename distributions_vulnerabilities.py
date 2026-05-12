import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def distributions_vulnerabilities(json_path: str | Path, plot_dir: str | Path = "Plots"):

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]
    plot_dir = Path(plot_dir)
    plot_dir.mkdir(exist_ok=True)

    triangular_parameters = {}     # final result

    for risk in RISK_LEVELS:
        all_cves = []

        print(f"\n📊 Statistics for risk level: **{risk}**")
        print("-" * 60)
        
        for version, images in data.items():
            values = [images[img].get(risk, 0) for img in images]
            arr = pd.Series(values)
            all_cves.extend(values)

            present = (arr > 0).mean()
            absent = (arr == 0).mean()
            mean = arr.mean()
            var = arr.var()
            std = arr.std()

            print(f"Version {version}:")
            print(f"  Mean       = {mean:.2f}")
            print(f"  Variance   = {var:.2f}")
            print(f"  Std. Dev.  = {std:.2f}")
            print(f"  P(present) = {present:.2%}")
            print(f"  P(absent)  = {absent:.2%}")
        
        # Global statistics
        general = pd.Series(all_cves)
        min_v = int(general.min())
        mode_v = int(general.median())  # may also be the mean
        max_v = int(general.max())

        triangular_parameters[risk] = {
            "min": min_v,
            "mode": mode_v,
            "max": max_v
        }

        print("\n🔎 Global statistics:")
        print(f"  General mean       = {general.mean():.2f}")
        print(f"  General variance   = {general.var():.2f}")
        print(f"  Standard Deviation = {general.std():.2f}")
        print(f"  P(present) total   = {(general > 0).mean():.2%}")
        print(f"  P(ausente) total   = {(general == 0).mean():.2%}")
        print(f"  Triangular parameters: min={min_v}, mode={mode_v}, max={max_v}")

        # ----- Save chart ------------------------------------------------
        plt.figure(figsize=(6, 4))
        sns.histplot(all_cves, bins=10, kde=True, color="steelblue")
        plt.title(f"CVE histogram – {risk}")
        plt.xlabel("Number of CVEs")
        plt.ylabel("Frequency")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(plot_dir / f"{risk}.png", dpi=300)
        plt.close()
        print(f"✅ Chart saved in {plot_dir / f'{risk}.png'}")

    return triangular_parameters