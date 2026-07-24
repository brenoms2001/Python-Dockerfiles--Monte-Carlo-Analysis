import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any

def shorten_image_label(label: str) -> str:
    """
    Compresses long image names into short academic phenotypes
    to prevent Y-axis clipping and optimize horizontal space in LADC columns.
    Example: 3.10-slim-bookworm -> 3.10 SB
    """
    parts = label.split('-')
    version = parts[0]
    variant = "-".join(parts[1:])
    
    if "slim-bookworm" in variant:
        short = "SB"
    elif "slim-bullseye" in variant:
        short = "SBU"
    elif "bookworm" in variant:
        short = "B"
    elif "bullseye" in variant:
        short = "BU"
    elif "alpine" in variant:
        short = "A"
    else:
        short = variant
        
    return f"{version} {short}"

def render_dispersion_boxplot(sim_data: np.lib.npyio.NpzFile, output_path: Path) -> None:
    """
    Generates the horizontal risk dispersion boxplot for the ecosystem (Figure 4 of the paper).
    Sorted from lowest to highest expected analytical risk.
    """
    print("🎨 [1/2] Rendering Ecosystem Dispersion Boxplot (CLT Approximation)...")
    
    # Sorts images by analytical mean
    image_means = {img_name: float(np.mean(sim_data[img_name])) for img_name in sim_data.files}
    sorted_images = sorted(image_means.keys(), key=lambda k: image_means[k])

    # Safe sampling to optimize Matplotlib vector rendering
    np.random.seed(42)
    boxplot_data = []
    boxplot_labels = []
    
    for img_name in sorted_images:
        full_array = sim_data[img_name]
        sample_size = min(5000, len(full_array))
        
        if sample_size > 0:
            sampled_points = np.random.choice(full_array, size=sample_size, replace=False)
            boxplot_data.append(sampled_points)
        else:
            boxplot_data.append(full_array)
            
        boxplot_labels.append(shorten_image_label(img_name))

    fig, ax = plt.subplots(figsize=(12, 9))
    
    sns.boxplot(
        data=boxplot_data, 
        ax=ax, 
        orient='h', 
        palette="vlag",
        linewidth=1.2,
        fliersize=2
    )

    # Strict title cleanup for compatibility with LaTeX captions (\caption)
    ax.set_title("")
    fig.suptitle("")
    
    ax.set_yticklabels(boxplot_labels, fontsize=14)
    ax.tick_params(axis='x', labelsize=14)
    
    # Updated to analytical terminology (CLT)
    ax.set_xlabel("Analytical Exposure Risk Distribution ($\widetilde{R}_i$)", fontsize=16)
    ax.set_ylabel("Official Python Image Configuration", fontsize=16)
    
    ax.xaxis.grid(True, linestyle='--', alpha=0.6)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"  ✅ Boxplot saved to: {output_path}")

def render_analytical_ranking_barchart(summary_data: Dict[str, Any], output_path: Path) -> None:
    """
    Generates the expected risk ranking with standard deviation error bars (E[R] ± σ_R).
    Replaces the old plot_ranking_risks.py with elevated statistical rigor.
    """
    print("🎨 [2/2] Rendering Analytical Ranking with Error Bars ($\pm 1\sigma_R$)....")
    
    # Sorts from highest to lowest expected risk for top-down visualization
    ordered_items = sorted(summary_data.items(), key=lambda x: x[1]["expected_mean"], reverse=True)
    
    labels = [shorten_image_label(k) for k, _ in ordered_items]
    means = [v["expected_mean"] for _, v in ordered_items]
    std_devs = [v["std_dev"] for _, v in ordered_items]

    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Horizontal bar plot with analytical error bars
    y_pos = np.arange(len(labels))
    ax.barh(
        y_pos, 
        means, 
        xerr=std_devs, 
        align='center', 
        color='indianred', 
        edgecolor='black', 
        linewidth=0.8,
        alpha=0.85,
        capsize=3,
        error_kw={'ecolor': 'dimgray', 'elinewidth': 1.2}
    )
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=14)
    ax.tick_params(axis='x', labelsize=14)
    ax.invert_yaxis()  # Highest risk image at the top
    
    # Title cleanup and academic styling
    ax.set_title("")
    fig.suptitle("")
    ax.set_xlabel("Expected Exposure Risk Score ($\mathbb{E}[\widetilde{R}_i] \pm \sigma_{R_i}$)", fontsize=16)
    ax.set_ylabel("Official Python Image Configuration", fontsize=16)
    
    ax.xaxis.grid(True, linestyle='--', alpha=0.6)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"  ✅ Ranking chart saved to: {output_path}")

def main():
    data_dir = Path("aggregated_summary")
    npz_path = data_dir / "environmental_simulation_arrays.npz"
    summary_path = data_dir / "analytical_clt_summary.json"
    
    output_boxplot = data_dir / "ecosystem_risk_dispersion_boxplot.png"
    output_ranking = data_dir / "analytical_risk_ranking_barchart.png"

    if not npz_path.exists() or not summary_path.exists():
        print("❌ Error: Data files not found in the 'aggregated_summary/' folder.")
        print("Run 'MC_simulation_environmental.py' first.")
        return

    print("📥 Loading analytical matrices and statistical summaries...")
    sim_data = np.load(npz_path)
    
    with open(summary_path, "r", encoding="utf-8") as f:
        summary_data = json.load(f)

    # Executes unified rendering
    render_dispersion_boxplot(sim_data, output_boxplot)
    render_analytical_ranking_barchart(summary_data, output_ranking)
    
    plt.close('all')
    print("\n✨ Success! Both plots were generated and standardized for LADC 2026.")

if __name__ == "__main__":
    main()