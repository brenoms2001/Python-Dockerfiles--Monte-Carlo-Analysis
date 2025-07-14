#!/bin/bash

python3 pyDockerfiles_download.py # Download all the dockerfiles for python in the docker-library
python3 generate_image_CVEs.py # Runs trivy and generate the json with vulnerabilities
python3 vulnerabilities_agregator # Agregate the severities of each docker image in another json