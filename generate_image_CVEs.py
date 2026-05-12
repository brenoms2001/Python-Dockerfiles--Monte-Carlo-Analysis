import os
import subprocess
from pathlib import Path

downloaded = Path("downloaded") # images directory 
analyzed = Path("analyzed") # jsons directory

# Store the names of the created images for later removal
# Optimize the download and save storage at the end
images = []

# Creates an output directory (if it doesn't already exist).
analyzed.mkdir(exist_ok=True)

def docker_build_and_scan(dockerfile_path: Path):
    version = dockerfile_path.parts[1]     
    sub_version = dockerfile_path.parts[2]   
    tag = f"trivy-scan:{version}-{sub_version}".replace("/", "-")

    # Path to the directory where the Dockerfile is located.
    build_context = dockerfile_path.parent

    # Mirrored path in the analyzed directory
    output_path = analyzed / version / sub_version
    output_path.mkdir(parents=True, exist_ok=True)
    output_json = output_path / "trivy-image.json"

    # Download the Dockerfile from the downloaded folder, build it, 
    # scan it with Trivy, and save the JSON file containing the CVEs 
    # in the analyzed folder within the subfolder of the same name.
    
    try:
        print(f"🐳 Building {tag}...")
        subprocess.run(
            ["docker", "build", "-f", str(dockerfile_path), "-t", tag, str(build_context)],
            check=True
        )

        # Alternative approach because the code was written to run with Docker Desktop.
        # The file is not placed in the same location as in a conventional Docker container
        docker_host = f'unix://{os.environ["HOME"]}/.docker/desktop/docker.sock'
        print(f"🔍 Scanning with Trivy: {tag}")
        subprocess.run(
            ["trivy", "image", "--docker-host", docker_host, "-f", "json", "-o", str(output_json), tag],
            check=True
        )
        images.append(tag)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {tag}: {e}")
    
# Iterating recursively through all the Dockerfiles.
for dockerfile in downloaded.rglob("Dockerfile"):
    docker_build_and_scan(dockerfile)

## Deleting images and clearing storage
#print("\n🧹 Removing all temporary images...")
#for tag in images:
#    subprocess.run(["docker", "rmi", "-f", tag], stdout=subprocess.DEVNULL)
#    print(f"🗑️  Removed: {tag}")