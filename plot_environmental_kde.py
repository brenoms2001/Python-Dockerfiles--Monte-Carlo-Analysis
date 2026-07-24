import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def main():
    # 1. Path configuration
    data_dir = Path("aggregated_summary")
    npz_path = data_dir / "environmental_simulation_arrays.npz"
    output_plot = data_dir / "family_risk_densities_kde.png"

    if not npz_path.exists():
        print(f"❌ Error: Simulation file '{npz_path}' was not found.")
        print("Please run the simulation engine first.")
        return

    print("📥 Loading compressed arrays from Monte Carlo simulation...")
    sim_data = np.load(npz_path)
    
    # 2. Dictionary to group raw data into the paper's 5 structural families
    family_groups = {
        "Alpine (Minimal)": [],
        "Debian Slim (Bookworm)": [],
        "Debian Slim (Bullseye)": [],
        "Full Debian (Bookworm)": [],
        "Full Debian (Bullseye)": []
    }

    print("⚙️  Grouping image configurations by OS families...")
    for img_name in sim_data.files:
        array_data = sim_data[img_name]
        
        # Mapping logic based on encoding variants
        if "alpine" in img_name.lower():
            family_groups["Alpine (Minimal)"].extend(array_data)
        elif "slim-bookworm" in img_name.lower():
            family_groups["Debian Slim (Bookworm)"].extend(array_data)
        elif "slim-bullseye" in img_name.lower():
            family_groups["Debian Slim (Bullseye)"].extend(array_data)
        elif "bookworm" in img_name.lower():
            family_groups["Full Debian (Bookworm)"].extend(array_data)
        elif "bullseye" in img_name.lower():
            family_groups["Full Debian (Bullseye)"].extend(array_data)

    # 3. Canvas initialization
    print("🎨 Rendering high-density custom KDE plot...")
    fig, ax = plt.subplots(figsize=(12, 8)) # Ideal ratio for column reuse

    # Official color palette aligned with the paper's aesthetic standard
    colors = {
        "Alpine (Minimal)": "#1f77b4",
        "Debian Slim (Bookworm)": "#2ca02c",
        "Debian Slim (Bullseye)": "#9467bd",
        "Full Debian (Bookworm)": "#ff7f0e",
        "Full Debian (Bullseye)": "#d62728"
    }

    # Iterative plotting of each density with translucent fill
    for family_name, data_list in family_groups.items():
        if len(data_list) > 0:
            sns.kdeplot(
                data=np.array(data_list),
                label=family_name,
                ax=ax,
                fill=True,
                alpha=0.2,
                linewidth=2.5,
                color=colors[family_name]
            )

    # ======= REQUIRED CRITICAL ADJUSTMENTS =======
    
    # A. ABSOLUTE REMOVAL OF TITLES (Global canvas cache obliteration)
    ax.set_title("")
    fig.suptitle("")

    # B. ROBUST EXPANSION OF LEGEND BOX AND TEXT
    ax.legend(
        title="Structural OS Families", 
        fontsize=20,            # Items font size expanded to 20
        title_fontsize=22,      # Legend title font size expanded to 22
        loc="upper right", 
        frameon=True, 
        shadow=True,            # Adds shadow for visual highlight
        facecolor="white",
        edgecolor="#cccccc"
    )

    # C. MAXIMIZATION OF AXES FONTS AND LABELS
    ax.set_xlabel("Simulated Exposure Risk Score ($\widetilde{R}_i$)", fontsize=20) # X title to 20
    ax.set_ylabel("Probability Density", fontsize=20)                                # Y title to 20
    ax.tick_params(axis='both', labelsize=20)                                        # Axis tick numbers to 20

    # Alignment settings and strict ecosystem limits
    ax.set_xlim(-5, 165)
    ax.xaxis.grid(True, linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)

    # 4. Tight layout adjustment and disk serialization
    plt.tight_layout()
    plt.savefig(output_plot, dpi=300)
    plt.close(fig)
    plt.close('all')
    
    print(f"✨ Success! KDE plot generated without titles, with enlarged fonts, and saved to: {output_plot}")

if __name__ == "__main__":
    main()