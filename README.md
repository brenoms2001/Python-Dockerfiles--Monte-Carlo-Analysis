# Monte Carlo Analysis of Python's Oficial Dockerfiles

This study is divided in two segments: Setting up all the files to be used and applying monte carlo to get an estimative of future vulnerabilities given the python version history.

## The Setup
The setup is divided in three segments: Installing dependencies, downloading the dockerfiles and generating the jsons of each docker image with the vulnerabilities associated.

### Installing dependencies
To run this repository's code is necessary to have Python, Trivy and Docker installed. Versions used in this study:

```bash
$ python3 --version
Python 3.12.3
```

```bash
$ trivy --version
Version: 0.64.1
Vulnerability DB:
  Version: 2
  UpdatedAt: 2025-07-12 12:26:53.792939262 +0000 UTC
  NextUpdate: 2025-07-13 12:26:53.792939112 +0000 UTC
  DownloadedAt: 2025-07-12 18:53:47.742980188 +0000 UTC
```

```bash
$ docker info
Client: Docker Engine - Community
 Version:    28.3.2
 Context:    desktop-linux
 Debug Mode: false
 Plugins:
  ai: Docker AI Agent - Ask Gordon (Docker Inc.)
    Version:  v1.1.3
    Path:     /usr/lib/docker/cli-plugins/docker-ai
  buildx: Docker Buildx (Docker Inc.)
    Version:  v0.22.0-desktop.1
    Path:     /usr/lib/docker/cli-plugins/docker-buildx
  cloud: Docker Cloud (Docker Inc.)
    Version:  0.2.20
    Path:     /usr/lib/docker/cli-plugins/docker-cloud
  compose: Docker Compose (Docker Inc.)
    Version:  v2.34.0-desktop.1
    Path:     /usr/lib/docker/cli-plugins/docker-compose
  debug: Get a shell into any image or container (Docker Inc.)
    Version:  0.0.38
    Path:     /usr/lib/docker/cli-plugins/docker-debug
  desktop: Docker Desktop commands (Beta) (Docker Inc.)
    Version:  v0.1.6
    Path:     /usr/lib/docker/cli-plugins/docker-desktop
  dev: Docker Dev Environments (Docker Inc.)
    Version:  v0.1.2
    Path:     /usr/lib/docker/cli-plugins/docker-dev
  extension: Manages Docker extensions (Docker Inc.)
    Version:  v0.2.27
    Path:     /usr/lib/docker/cli-plugins/docker-extension
  init: Creates Docker-related starter files for your project (Docker Inc.)
    Version:  v1.4.0
    Path:     /usr/lib/docker/cli-plugins/docker-init
  sbom: View the packaged-based Software Bill Of Materials (SBOM) for an image (Anchore Inc.)
    Version:  0.6.0
    Path:     /usr/lib/docker/cli-plugins/docker-sbom
  scout: Docker Scout (Docker Inc.)
    Version:  v1.17.0
    Path:     /usr/lib/docker/cli-plugins/docker-scout

```

### Dowloading the dockerfiles
pyDockerfiles_download.py is the script used to call GitHub's API passing the user's token to dowload each version of Python's oficial dockerfiles and saving under the 'baixados' directory. You also need to have a .env file with your token for better privacy.

### Generating Jsons
generate_image_CVEs.py is the script that builds each dockerfile, scans it with Trivy with the trivy image command and saves it under the 'analisados' directory.  
Because the json doesn't have the agreggation of vulnerabilities based on severity level, vulnerabilities_agregator.py generates a small json with this info.  
In case you are using Trivy's CLI, the agreggate is showed together with the vulnerabilities

### Run all
Just run the play.sh if you want to run the whole pipeline.
## The Analysis

After generating the vulnerability data for each Python Docker image, the next step is to analyze this information using statistical modeling and simulation.

### Step 1: Building Vulnerability Matrices

The script `criador_matrizes_vulnerabilities.py` processes all the individual JSON files of vulnerabilities and constructs matrices that group the number of vulnerabilities by severity level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) for each Python image version. These matrices are then stored in the file `matrizes.json`, which serves as the input for further analysis.

### Step 2: Creating Distributions

With the matrices ready, `distribuicoes_vulnerabilities.py` is responsible for generating triangular distributions for each severity level. These distributions represent possible values of vulnerabilities based on historical data and are used to simulate future scenarios. The parameters for each triangular distribution (minimum, mode, maximum) are derived from the observed values in the matrices.

### Step 3: Defining Risk Formula

A custom risk score is calculated using a weighted sum of vulnerabilities per severity level. The script `analise_percentis.py` defines this formula, assigning specific weights to each severity level to reflect their relative importance.

### Step 4: Monte Carlo Simulation

Using the triangular distributions and the risk formula, the script `simulacao_MC.py` performs a Monte Carlo simulation by generating 50,000 random samples of vulnerabilities per severity level for each image. The simulation provides a statistical estimate of the overall risk for each Python Docker image, based on historical tendencies and probabilistic modeling.

### Step 5: Visualizing the Results

The script `plota_histogramas_simulados.py` generates plots for the simulated distributions of each severity level and the overall risk. These visualizations help to understand the variability and behavior of the vulnerabilities across Python versions.

### Step 6: Classifying the Risk

Still in `analise_percentis.py`, percentiles of the simulated general risk distribution are used to classify each image's risk level (e.g., low, medium, high). These classifications are determined by comparing each image’s real risk value to the corresponding simulated percentiles.

### Step 7: Ranking the Images

Finally, the script `plot_ranking_riscos.py` produces a horizontal bar plot ranking the official Python images from the highest to the lowest estimated risk. This ranking offers an intuitive summary of which versions are more likely to present vulnerabilities in the future.

---
