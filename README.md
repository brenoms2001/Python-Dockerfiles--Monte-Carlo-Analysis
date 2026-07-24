---

```markdown
# Environment-Conditioned CVSS Distributions for Dependable Risk Analysis of Python Docker Images

This repository contains the open-source analytical engine, empirical datasets, and reproduction suite for our LADC 2026 research paper. 

Our framework replaces static, deterministic Common Vulnerability Scoring System (CVSS) point estimates and computationally expensive Monte Carlo simulations with an **environment-conditioned parametric model**. By treating CVSS Exploitability subscores as triangular random variables scaled by real-world threat intelligence (FIRST.org EPSS) and propagating their statistical moments through the **Central Limit Theorem (CLT)**, this engine calculates exact container risk distributions ($\mathbb{E}[\widetilde{R}_i]$ and $\sigma_{R_i}$) in linear time ($\mathcal{O}(N)$).

---

## 🏗️ System Requirements & Environment Setup

To execute the automated image harvesting, local compilation, vulnerability inspection, and parametric CLT calculations, ensure your environment meets the following baseline dependencies:

### Core Dependencies
```bash
$ python3 --version
Python 3.12.3 (or >= 3.11)

$ trivy --version
Version: 0.64.1 (or latest)

$ docker info
Client: Docker Engine - Community
 Version: 28.3.2

```

### Python Scientific Stack

Install the required analytical and visualization libraries:

```bash
pip install numpy scipy matplotlib seaborn requests python-dotenv

```

---

## ⚙️ Phase 1: The Empirical Pipeline (Harvesting, Build & Scanning)

The empirical data collection pipeline executes in three sequential stages to ensure filesystem accuracy and reproducible threat intelligence binding.

### 1. Harvesting Official Dockerfiles

The script `pyDockerfiles_download.py` queries the GitHub REST API to download the complete matrix of official Python build configurations from the canonical `docker-library/python` repository.

* **Scope:** 36 distinct container configurations covering Python 3.9 through 3.14-rc across structural OS families: Alpine Linux (`alpine3.21`, `alpine3.22`), streamlined Debian (`slim-bookworm`, `slim-bullseye`), and full Debian (`bookworm`, `bullseye`).
* **Note:** Create a local `.env` file containing your GitHub personal access token (`GITHUB_TOKEN=your_token_here`) to prevent API rate-limiting during collection.

### 2. Local Image Compilation & Filesystem Scanning

The script `generate_image_CVEs.py` compiles each harvested Dockerfile within an isolated local Docker daemon using the default `docker build` engine (without caching overrides). Crucially, scanning must occur on locally built artifacts rather than static Dockerfiles to accurately capture dynamic build-time package resolutions and OS dependency pulling.

Once compiled, Trivy inspects each local filesystem, exporting structured JSON reports containing package inventories, CVE identifiers, and qualitative severity classifications into the `/analisados` directory.

### 3. Threat Intelligence Ingestion & Subscore Extraction

The script `extract_environmental_data.py` bridges raw scanner inspection logs with our mathematical model:

1. **Native Subscore Extraction:** Disassembles raw CVSS v3.1 vector strings to extract intrinsic Impact ($I_v$) and Exploitability ($X_v$) subscores natively.
2. **Dynamic EPSS Binding:** Executes asynchronous HTTP batch requests to the official FIRST.org API to bind real-world Exploit Prediction Scoring System ($E_v \in [0,1]$) probabilities to every CVE.
3. **Forensic CISA KEV Auditing:** Cross-references all identified vulnerabilities against the authoritative Cybersecurity and Infrastructure Security Agency (CISA) Known Exploited Vulnerabilities catalog, appending a boolean active threat indicator (`in_cisa_kev`).

The consolidated output is saved to `environmental_cve_profiles.json`, serving as the empirical input for the analytical engine.

---

## 🧮 Phase 2: The Analytical CLT Engine ($\mathcal{O}(N)$ Execution)

Unlike iterative simulation models that introduce pseudo-random sampling noise and require thousands of computational rounds ($M$) to converge, our analytical framework calculates exact parametric moments in linear time ($\mathcal{O}(N)$).

### 1. Parametric Risk Propagation (`generate_environmental_tables.py`)

This core execution module implements the exact Central Limit Theorem equations derived in our paper:

* **Aggregate Exposure ($A_i$):** Calculates the Initial Breach Surface Approximation across the container's package payload under a first-order statistical independence assumption.
* **Triangular Exploitability Uncertainty:** Models Exploitability as a continuous triangular random variable $\widetilde{X}_{v|i} \sim \mathrm{Triangular}(L_{v|i}, X_v, U_{v|i})$ whose half-width is dynamically scaled by $A_i$.
* **Analytical Moments:** Computes exact package-level expectation ($\mu_{C,v|i}$) and variance ($\sigma_{C,v|i}^2$), aggregating them linearly via Lindeberg-Lévy CLT convergence ($\widetilde{R}_i \sim \mathcal{N}(\mu_{R_i}, \sigma_{R_i}^2)$).
* **Deterministic Percentiles:** Derives exact dependability percentiles ($P_5, P_{50}, P_{95}$) using the standard normal inverse cumulative distribution function (`scipy.stats.norm.ppf`).

⚡ **Performance:** Because it relies on vectorized NumPy linear algebra rather than iterative Monte Carlo loops, this script processes all 36 enterprise container configurations in **under 150 milliseconds**, making it ideal for automated CI/CD quality gating.

### 2. Actionable DevSecOps Triaging Suites

To translate analytical probability distributions into engineering decision support, the repository includes two specialized validation modules:

* **CI/CD Remediation Heuristic (`generate_cicd_prioritization.py`):** Evaluates container remediation efficiency against standard industry point-estimate filters (CVSS $\ge 7.0$). It applies an algorithmic **Pareto 85% cumulative risk threshold** enriched with mandatory CISA KEV promotion rules, generating an actionable DevSecOps patching manifest (`actionable_remediation.json`). This heuristic reduces manual patching workloads by up to **43.74%** in full Debian images while achieving **100% parity** in capturing active real-world threat vectors.
* **Zero-Day Exploit Drift Harness (`run_exploit_drift_study.py`):** A stress-testing script designed to evaluate runtime resilience during sudden threat escalations. It isolates shared foundational libraries across distinct image architectures, dynamically injects active zero-day exploit drift parameters ($E_v \to 0.85$ on target CVEs), and recalculates system variance shifts ($\sigma_R$) in memory. This module mathematically demonstrates the **Environmental Saturation Effect**, proving that high-density Debian runtimes amplify single-vulnerability risk jumps by **5.1x** compared to slim baselines.

---

## 🚀 Quickstart: Running the End-to-End Suite

To execute the complete pipeline—from Dockerfile downloading and local compilation to CLT parametric calculation, DevSecOps triaging, and analytical visualization rendering—run the master automation script:

```bash
chmod +x play.sh
./play.sh

```

### Generated Analytical Artifacts

Upon completion, the suite outputs all necessary empirical tables and publication-ready figures into the root directory and `/figures`:

* `matrizes.json` & `environmental_cve_profiles.json` — Enriched vulnerability databases.
* `actionable_remediation.json` — CI/CD Pareto 85% patching manifests.
* `family_risk_densities_kde.png` — Kernel Density Estimation of expected risk across OS base families (RQ1).
* `ecosystem_risk_dispersion_boxplot.png` — Global risk dispersion and runtime volatility ranking (RQ1 / RQ3).
* *ANOVA Variance Decomposition Logs* — Confirming that base OS selection is **78,111.1x** more critical to container dependability than Python interpreter upgrades (RQ2).

---

```

```

```
