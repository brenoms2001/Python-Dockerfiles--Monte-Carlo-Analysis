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