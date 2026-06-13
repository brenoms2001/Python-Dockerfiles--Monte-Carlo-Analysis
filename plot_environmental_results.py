import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def shorten_image_label(label: str) -> str:
    """
    Compresses long image names into standardized short academic phenotypes
    to prevent axis clipping and optimize horizontal plot space.
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

def main():
    # 1. Setup paths
    data_dir = Path("aggregated_summary")
    npz_path = data_dir / "environmental_simulation_arrays.npz"
    output_plot = data_dir / "ecosystem_risk_dispersion_boxplot.png"

    if not npz_path.exists():
        print(f"❌ Error: Compressed simulation file '{npz_path}' not found.")
        print("Please run 'MC_simulation_environmental.py' first to generate the arrays.")
        return

    print("📥 Loading compressed Monte Carlo simulation arrays...")
    sim_data = np.load(npz_path)
    
    # 2. Extract keys and compute expected means to enforce strict risk ordering
    print("⚙️ Sorting image environments by their expected mean risk...")
    image_means = {}
    for img_name in sim_data.files:
        image_means[img_name] = float(np.mean(sim_data[img_name]))
        
    # Sort images from lowest expected risk to highest expected risk
    sorted_images = sorted(image_means.keys(), key=lambda k: image_means[k])

    # 3. Structure data and apply sampling to prevent bloated vector graphics
    print("🎲 Downsampling points safely (max 5,000 per image) for layout performance...")
    np.random.seed(42)  # Maintain perfect replication transparency
    
    boxplot_data = []
    boxplot_labels = []
    
    for img_name in sorted_images:
        full_array = sim_data[img_name]
        # Safe sampling toggle to preventValueError if arrays are smaller than 5000 runs
        sample_size = min(5000, len(full_array))
        
        if sample_size > 0:
            sampled_points = np.random.choice(full_array, size=sample_size, replace=False)
            boxplot_data.append(sampled_points)
        else:
            boxplot_data.append(full_array)
            
        # Apply the short label transformation dynamically
        boxplot_labels.append(shorten_image_label(img_name))

    # 4. Canvas rendering and customization via Matplotlib/Seaborn
    print("🎨 Rendering cleaned ecosystem risk boxplot...")
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Render horizontal boxplot with a standardized clean palette
    sns.boxplot(
        data=boxplot_data, 
        ax=ax, 
        orient='h', 
        palette="vlag",
        linewidth=1.2,
        fliersize=2
    )

    # ======= ENFORCED TITLE REMOVAL (ANTI-CACHE OBLITERATION) =======
    ax.set_title("")     # Force clears any axis-level title
    fig.suptitle("")     # Force clears any figure-level global title
    
    # B. FONT SIZE ELEVATION AND AXIS SHORTENING:
    ax.set_yticklabels(boxplot_labels, fontsize=16) # Elevated image tick labels to 12
    ax.tick_params(axis='x', labelsize=16)          # Elevated risk numbers to 12
    
    # C. AXES LABELS CUSTOMIZATION:
    ax.set_xlabel("Simulated Exposure Risk Score ($\widetilde{R}_i$)", fontsize=16)
    ax.set_ylabel("Official Python Image Configuration", fontsize=16)
    
    # Add subtle gridlines for rigorous coordinate alignment
    ax.xaxis.grid(True, linestyle='--', alpha=0.6)
    ax.set_axisbelow(True)

    # 5. Tight bounding boxes and disk serialization
    plt.tight_layout()
    plt.savefig(output_plot, dpi=300)
    plt.close(fig) # Explicitly closes the figure context to wipe RAM memory clean
    plt.close('all')
    
    print(f"✨ Success! The boxplot has been generated without titles, with compressed labels, and saved to: {output_plot}")

if __name__ == "__main__":
    main()