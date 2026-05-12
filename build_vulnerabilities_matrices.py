import pip
pip.main(['install', 'pandas'])
from pathlib import Path
import json
import pandas as pd

# --- CONFIGURATIONS  ----------------------------------------------------------
ROOT = Path(__file__).resolve().parent        # script directory
BASE = ROOT / "aggregated_summary"            # where the JSONs are
IMAGES = [                                    # fixed order of images
    "alpine3.21",
    "alpine3.22",
    "bookworm",
    "bullseye",
    "slim-bookworm",
    "slim-bullseye",
]
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]
# ----------------------------------------------------------------------------

def collect_summaries(directory: Path) -> dict[tuple[str, str], dict]:
    data = {}
    for json_path in directory.rglob("summary.json"):
        version, variant = json_path.parts[-3:-1]
        with json_path.open(encoding="utf-8") as f:
            summary = json.load(f)["summary"]
        data[(version, variant)] = summary
    return data

def build_matrix_by_version(data: dict) -> dict[str, pd.DataFrame]:
    matrices = {}
    versions = sorted({v for v, _ in data.keys()}, key=lambda s: (s.count("."), s))
    for version in versions:
        rows = []
        for variant in IMAGES:
            summary = data.get((version, variant), {})
            rows.append([summary.get(risk, 0) for risk in RISK_LEVELS])
        df = pd.DataFrame(rows, index=IMAGES, columns=RISK_LEVELS)
        matrices[version] = df
    return matrices

def save_json(matrices: dict[str, pd.DataFrame], target: Path) -> None:
    
    result = {
        version: df.to_dict(orient="index")
        for version, df in matrices.items()
    }
    with open(target, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

def build_matrices() -> None:
    data = collect_summaries(BASE)
    matrices = build_matrix_by_version(data)

    target_json = ROOT / "matrices.json"

    save_json(matrices, target_json)

    print("✅ Arrays saved in JSON!")
    print("Example (3.11):\n", matrices["3.11"])