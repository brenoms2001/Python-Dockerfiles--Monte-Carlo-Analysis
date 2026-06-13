import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def main():
    # 1. Configuração de caminhos
    data_dir = Path("aggregated_summary")
    output_dir = Path("Plots_Environmental")
    output_dir.mkdir(exist_ok=True)
    
    npz_path = data_dir / "environmental_simulation_arrays.npz"
    if not npz_path.exists():
        print("❌ Erro: Ficheiro environmental_simulation_arrays.npz não encontrado. Corre o pipeline primeiro.")
        return

    # 2. Carrega as matrizes brutas de simulação
    sim_data = np.load(npz_path)
    
    # Selecionamos configurações altamente representativas de cada uma das 5 famílias do ecossistema
    target_images = [
        "3.9-bullseye",        # Extremo Crítico (Full Bullseye)
        "3.11-bookworm",       # Alto Risco (Full Bookworm)
        "3.9-slim-bullseye",   # Intermediário Moderado (Slim Bullseye)
        "3.11-slim-bookworm",  # Baixo Risco (Slim Bookworm)
        "3.11-alpine3.22"      # Risco Mínimo (Alpine)
    ]
    
    # Configuração estética do gráfico científico
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    
    # Paleta de cores idêntica à que usamos no KDE e no Boxplot para manter a consistência do artigo
    colors = {
        "3.9-bullseye": "#d62728",
        "3.11-bookworm": "#ff7f0e",
        "3.9-slim-bullseye": "#9467bd",
        "3.11-slim-bookworm": "#2ca02c",
        "3.11-alpine3.22": "#1f77b4"
    }

    print("📊 A calcular a estabilização estatística das médias móveis incluindo Alpine...")
    
    # 3. Loop de cálculo da Média Acumulada
    for img in target_images:
        if img in sim_data.files:
            arr = sim_data[img]
            
            # Executa o cálculo vetorizado em alta performance: np.cumsum acumula a soma,
            # e dividimos pelo índice do passo atual (de 1 a 50.000)
            running_mean = np.cumsum(arr) / np.arange(1, len(arr) + 1)
            
            # Desenha a linha de evolução da imagem
            plt.plot(
                running_mean, 
                color=colors[img], 
                label=f"{img} ($\mathbb{{E}}[R]$ Final: {running_mean[-1]:.3f})", 
                linewidth=2.2
            )
            
    # 4. Ajustes finais de labels (usando strings brutas para evitar o SyntaxWarning)
    plt.title("Monte Carlo Convergence Analysis (Running Mean Stability)")
    plt.xlabel(r"Number of Iterations ($M$)")
    plt.ylabel(r"Cumulative Expected Risk ($\mathbb{E}[\widetilde{R}_i]$)")
    plt.xlim(0, 50000)
    plt.legend(title="Monitored Base Environments", loc="upper right")
    plt.tight_layout()
    
    output_path = output_dir / "monte_carlo_convergence.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"✅ Gráfico de convergência atualizado e salvo com sucesso em: {output_path}")

if __name__ == "__main__":
    main()