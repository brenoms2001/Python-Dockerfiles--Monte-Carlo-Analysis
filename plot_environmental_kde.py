import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def main():
    # 1. Configuração de caminhos
    data_dir = Path("aggregated_summary")
    npz_path = data_dir / "environmental_simulation_arrays.npz"
    output_plot = data_dir / "family_risk_densities_kde.png"

    if not npz_path.exists():
        print(f"❌ Erro: O arquivo de simulação '{npz_path}' não foi encontrado.")
        print("Por favor, execute o motor de simulação primeiro.")
        return

    print("📥 Carregando arrays compactados da simulação de Monte Carlo...")
    sim_data = np.load(npz_path)
    
    # 2. Dicionário para agrupar os dados brutos nas 5 famílias estruturais do artigo
    family_groups = {
        "Alpine (Minimal)": [],
        "Debian Slim (Bookworm)": [],
        "Debian Slim (Bullseye)": [],
        "Full Debian (Bookworm)": [],
        "Full Debian (Bullseye)": []
    }

    print("⚙️  Agrupando as configurações de imagem por famílias de S.O...")
    for img_name in sim_data.files:
        array_data = sim_data[img_name]
        
        # Lógica de mapeamento baseada nas variantes de codificação
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

    # 3. Inicialização do Canvas de desenho
    print("🎨 Renderizando gráfico KDE customizado de alta densidade...")
    fig, ax = plt.subplots(figsize=(12, 8)) # Proporção ideal para reaproveitamento de colunas

    # Paleta de cores oficial alinhada com o padrão estético do artigo
    colors = {
        "Alpine (Minimal)": "#1f77b4",
        "Debian Slim (Bookworm)": "#2ca02c",
        "Debian Slim (Bullseye)": "#9467bd",
        "Full Debian (Bookworm)": "#ff7f0e",
        "Full Debian (Bullseye)": "#d62728"
    }

    # Plotagem iterativa de cada densidade com preenchimento translúcido
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

    # ======= AJUSTES CRÍTICOS EXIGIDOS =======
    
    # A. REMOÇÃO ABSOLUTA DE TÍTULOS (Obliteração de cache do canvas global)
    ax.set_title("")
    fig.suptitle("")

    # B. AMPLIAÇÃO ROBUSTA DA CAIXA E TEXTO DA LEGENDA
    ax.legend(
        title="Structural OS Families", 
        fontsize=20,            # Tamanho da fonte dos itens expandido para 13
        title_fontsize=22,      # Tamanho do título da legenda expandido para 14
        loc="upper right", 
        frameon=True, 
        shadow=True,            # Adiciona sombra para destaque visual
        facecolor="white",
        edgecolor="#cccccc"
    )

    # C. MAXIMIZAÇÃO DAS FONTES DOS EIXOS E MARCAÇÕES (LABELS)
    ax.set_xlabel("Simulated Exposure Risk Score ($\widetilde{R}_i$)", fontsize=20) # Título X para 15
    ax.set_ylabel("Probability Density", fontsize=20)                                # Título Y para 15
    ax.tick_params(axis='both', labelsize=20)                                        # Números dos eixos para 13

    # Configurações de alinhamento e limites estritos do ecossistema
    ax.set_xlim(-5, 165)
    ax.xaxis.grid(True, linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)

    # 4. Ajuste dimensional apertado e serialização em disco
    plt.tight_layout()
    plt.savefig(output_plot, dpi=300)
    plt.close(fig)
    plt.close('all')
    
    print(f"✨ Sucesso! O gráfico KDE foi gerado sem títulos, com fontes ampliadas e salvo em: {output_plot}")

if __name__ == "__main__":
    main()