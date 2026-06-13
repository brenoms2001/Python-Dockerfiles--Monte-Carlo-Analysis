#!/bin/bash

# Passo 1: Extrai os dados de componentes de cada CVE dos relatórios brutos do Trivy
python3 extract_environmental_data.py

# Passo 2: Executa as 50.000 rodadas de Monte Carlo com o framework de incerteza do CVSS
python3 MC_simulation_environmental.py

# Passo 3: Consome as matrizes binárias e gera os gráficos científicos finais
python3 plot_environmental_results.py

python3 generate_environmental_tables.py

python plot_convergence.py
