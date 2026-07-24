import json
from pathlib import Path
from typing import Dict, Any, List

# CONFIGURABLE DEVSECOPS HEURISTIC PARAMETER
# 0.85 represents the classic Pareto Law threshold (focusing on primary bottlenecks)
PARETO_THRESHOLD = 0.85 

def main():
    data_dir = Path("aggregated_summary")
    input_profile = data_dir / "environmental_cve_profiles.json"
    output_actionable = data_dir / "actionable_remediation.json"

    if not input_profile.exists():
        print(f"❌ Error: Input file '{input_profile}' was not found.")
        print("Make sure to run 'extract_environmental_data.py' first.")
        return

    print(f"📥 Reading CVE profiles and applying Pareto Heuristic ({int(PARETO_THRESHOLD*100)}%) + KEV Promotion...")
    with open(input_profile, "r", encoding="utf-8") as f:
        cve_dataset = json.load(f)

    remediation_report: Dict[str, Any] = {}
    
    markdown_lines = [
        f"| Image Configuration | Total | Industry Standard (≥7.0) | Our Model (Pareto {int(PARETO_THRESHOLD*100)}%) | Industry KEV | Model KEV | Operational Advantage (vs Industry) |",
        "|---------------------|-------|---------------------------|-------------------------|--------------|-----------|-------------------------------------|"
    ]

    for img_name in sorted(cve_dataset.keys()):
        cves = cve_dataset[img_name]
        total_cves = len(cves)
        
        if total_cves == 0:
            remediation_report[img_name] = {
                "metrics": {
                    "total_cves": 0,
                    "industry_standard_count": 0,
                    "cves_to_remediate": 0,
                    "effort_reduction_vs_industry_percentage": 0.0,
                    "kev_captured_by_model": 0,
                    "kev_captured_by_industry": 0,
                    "blind_spots_caught_count": 0
                },
                "target_patches": [],
                "blind_spots_details": []
            }
            markdown_lines.append(f"| {img_name:<19} | {0:<5} | {0:<25} | {0:<23} | {0:<12} | {0:<9} | {'Full Parity':<35} |")
            continue

        # A. Industry Standard Filter Analysis (CVSS >= 7.0)
        industry_target_cves = [c for c in cves if c.get("base_score", 0.0) >= 7.0]
        industry_count = len(industry_target_cves)
        industry_kev_count = sum(1 for c in industry_target_cves if c.get("in_cisa_kev", False))

        # B. Individual Risk Calculation (EPSS * Base Score)
        total_image_risk = 0.0
        processed_cves = []
        
        for cve in cves:
            cve_id = cve["cve"]
            ev = cve["epss"]
            base_score = cve.get("base_score", 0.0)
            is_kev = cve.get("in_cisa_kev", False)
            
            individual_risk = ev * base_score
            total_image_risk += individual_risk
            
            processed_cves.append({
                "cve": cve_id,
                "base_score": base_score,
                "risk": individual_risk,
                "in_cisa_kev": is_kev
            })

        # Sorts CVEs by descending individual risk
        processed_cves.sort(key=lambda x: x["risk"], reverse=True)

        # C. Pareto Filter Application + Mandatory KEV Promotion
        accumulated_risk = 0.0
        target_patches_set = set()
        model_kev_count = 0
        blind_spots_caught: List[Dict[str, Any]] = []
        
        # Step 1: Select by risk mass (Pareto)
        for cve in processed_cves:
            if total_image_risk == 0:
                break
                
            accumulated_risk += cve["risk"]
            target_patches_set.add(cve["cve"])
            
            if accumulated_risk >= PARETO_THRESHOLD * total_image_risk:
                break

        # Step 2: KEV Promotion Rule (Ensures no active KEV is left out, even if in the long tail)
        for cve in processed_cves:
            if cve["in_cisa_kev"]:
                target_patches_set.add(cve["cve"])

        # Re-processes the final selected list to extract metrics and blind spots
        target_patches = list(target_patches_set)
        
        for cve in processed_cves:
            if cve["cve"] in target_patches_set:
                if cve["in_cisa_kev"]:
                    model_kev_count += 1
                if cve["base_score"] < 7.0:
                    blind_spots_caught.append({
                        "cve": cve["cve"],
                        "base_score": cve["base_score"],
                        "risk": round(cve["risk"], 4),
                        "in_cisa_kev": cve["in_cisa_kev"]
                    })

        if total_image_risk > 0 and len(target_patches) == 0:
            top_cve = processed_cves[0]
            target_patches.append(top_cve["cve"])
            if top_cve["in_cisa_kev"]:
                model_kev_count = 1

        # D. Effort Calculation (Compared against Industry)
        cves_to_remediate = len(target_patches)
        
        if industry_count > 0:
            effort_reduction_vs_industry = ((industry_count - cves_to_remediate) / float(industry_count)) * 100.0
        else:
            effort_reduction_vs_industry = 0.0 if cves_to_remediate == 0 else -100.0

        if cves_to_remediate < industry_count:
            advantage_str = f"+{effort_reduction_vs_industry:.2f}% (Patch Savings)"
        elif cves_to_remediate > industry_count:
            diff_blind = cves_to_remediate - industry_count
            advantage_str = f"Catches {diff_blind} Blind Spots"
        else:
            advantage_str = "Industry Parity"

        remediation_report[img_name] = {
            "metrics": {
                "pareto_threshold_used": PARETO_THRESHOLD,
                "total_cves": total_cves,
                "industry_standard_count": industry_count,
                "cves_to_remediate": cves_to_remediate,
                "effort_reduction_vs_industry_percentage": round(effort_reduction_vs_industry, 2),
                "kev_captured_by_model": model_kev_count,
                "kev_captured_by_industry": industry_kev_count,
                "blind_spots_caught_count": len(blind_spots_caught)
            },
            "target_patches": target_patches,
            "blind_spots_details": blind_spots_caught
        }

        markdown_lines.append(
            f"| {img_name:<19} | {total_cves:<5} | {industry_count:<25} | {cves_to_remediate:<23} | "
            f"{industry_kev_count:<12} | {model_kev_count:<9} | {advantage_str:<35} |"
        )

    with open(output_actionable, "w", encoding="utf-8") as f:
        json.dump(remediation_report, f, indent=4)

    print("\n🚀 OPERATIONAL EFFICIENCY COMPARATIVE REPORT (PARETO 85% + KEV):\n")
    for line in markdown_lines:
        print(line)

    print(f"\n💾 CI/CD remediation file saved to: {output_actionable}")
    print("✨ Success! Remediation heuristic updated with strict reproducibility.")

if __name__ == "__main__":
    main()