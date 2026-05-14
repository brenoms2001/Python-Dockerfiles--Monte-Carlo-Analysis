import json
from pathlib import Path
from collections import Counter
from epss_api import fetch_epss_scores

# --- FALLBACK SETTINGS ---
# Default CVSS values ​​if the vulnerability does not have a V3 rating (e.g., UNKNOWN)
DEFAULT_CVSS = {
    "LOW": 2.0,
    "MEDIUM": 5.5,
    "HIGH": 8.0,
    "CRITICAL": 9.5,
    "UNKNOWN": 5.0
}
# Extremely low EPS value for failures that do not exist in the FIRST.org database
DEFAULT_EPSS = 0.0001 

entry = Path("analyzed")  
aggregates_output = Path("aggregated_summary")
aggregates_output.mkdir(exist_ok=True)

# ---------------------------------------------------------
# STAGE 1: Gathering all unique CVEs to optimize the API.
# ---------------------------------------------------------
all_cves = set()
for path in entry.rglob("trivy-image.json"):
    with open(path) as f:
        data = json.load(f)
    for result in data.get("Results", []):
        for vuln in result.get("Vulnerabilities", []):
            vuln_id = vuln.get("VulnerabilityID")
            if vuln_id and vuln_id.startswith("CVE"):
                all_cves.add(vuln_id)

print(f"🔍 Found {len(all_cves)} unique CVEs. Querying EPSS API...")

cve_list = list(all_cves)
epss_mapping = {}
chunk_size = 100 # to not overload the API

for i in range(0, len(cve_list), chunk_size):
    chunk = cve_list[i:i + chunk_size]
    scores = fetch_epss_scores(chunk)
    epss_mapping.update(scores)
    
print(f"✅ EPSS downloaded successfully to {len(epss_mapping)} CVEs.")

# ---------------------------------------------------------
# STAGE 2: Image Processing and Profile Generation
# ---------------------------------------------------------
profiles = {
    "LOW": {"CVSS": [], "EPSS": []},
    "MEDIUM": {"CVSS": [], "EPSS": []},
    "HIGH": {"CVSS": [], "EPSS": []},
    "CRITICAL": {"CVSS": [], "EPSS": []},
    "UNKNOWN": {"CVSS": [], "EPSS": []}
}

for path in entry.rglob("trivy-image.json"):
    with open(path) as f:
        data = json.load(f)

    severities = []
    estimated_risk = 0.0  

    for result in data.get("Results", []):
        for vuln in result.get("Vulnerabilities", []):
            vuln_id = vuln.get("VulnerabilityID")
            severity = vuln.get("Severity", "UNKNOWN")
            
            severities.append(severity)
            
            # --- 1. CVSS V3 Extraction ---
            cvss_v3_scores = []
            cvss_data = vuln.get("CVSS", {})
            # We'll just take the V3s
            for provider, scores in cvss_data.items():
                if "V3Score" in scores:
                    cvss_v3_scores.append(scores["V3Score"])
            
            # If there is more than one V3Score (e.g., NVD and RedHat differ), use the average, rounded.
            if cvss_v3_scores:
                cvss_val = round(sum(cvss_v3_scores) / len(cvss_v3_scores), 2)
            else:
                # Fallback
                cvss_val = DEFAULT_CVSS.get(severity, 5.0)
                
            # --- 2. EPSS Extraction ---
            epss_val = epss_mapping.get(vuln_id, DEFAULT_EPSS)
            
            # --- 3. Population of Profiles (Allowing Repetitions) ---
            if severity in profiles:
                profiles[severity]["CVSS"].append(cvss_val)
                profiles[severity]["EPSS"].append(epss_val)
            
            # --- 4. Calculation of the Estimated Risk of This Image ---
            estimated_risk += (cvss_val * epss_val)

    # Consolida os dados
    count = Counter(severities)
    summary = {
        "image": data.get("ArtifactName", "unknown"),
        "summary": dict(count),
        "estimated_risk": estimated_risk
    }

    out_path = aggregates_output / path.relative_to(entry).parent / "summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as out:
        json.dump(summary, out, indent=2)

    print(f"✅ Summary of {summary['image']} | Estimated Risk: {estimated_risk:.2f}")

# ---------------------------------------------------------
# STAGE 3: Save the database for Monte Carlo
# ---------------------------------------------------------
profiles_path = aggregates_output / "cvss_epss_profiles.json"
with open(profiles_path, "w") as f:
    json.dump(profiles, f, indent=2)
    
print(f"\\n🎯 Statistical profiles of CVSS and EPSS saved in: {profiles_path}")