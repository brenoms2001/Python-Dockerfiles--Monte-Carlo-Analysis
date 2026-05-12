import json
from pathlib import Path
from collections import Counter

entry = Path("analyzed")  # where the JSONs are
aggregates_output = Path("aggregated_summary")
aggregates_output.mkdir(exist_ok=True)

for path in entry.rglob("trivy-image.json"):
    with open(path) as f:
        data = json.load(f)

    severities = []

    for result in data.get("Results", []):
        for vuln in result.get("Vulnerabilities", []):
            severities.append(vuln["Severity"])

    count = Counter(severities)
    summary = {
        "image": data.get("ArtifactName", "unknown"),
        "summary": dict(count)
    }

    out_path = aggregates_output / path.relative_to(entry).parent / "summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as out:
        json.dump(summary, out, indent=2)

    print(f"✅ Summary generated for {summary['image']}")