import requests
from pathlib import Path
from dotenv import load_dotenv
import os

# Import github account credentials
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Specify directory
user = "docker-library"
repo = "python"
base_path = "downloaded"
versions = ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14-rc"]

def download_files(relative_path, destination_folder):
    api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{relative_path}"
    resp = requests.get(api_url, headers=HEADERS)

    if resp.status_code != 200:
        print(f"❌ Error accessing {api_url}: {resp.status_code}")
        return

    files = resp.json()
    for file in files:
        if file["type"] == "file" and file.get("download_url"):
            file_path = Path(base_path) / destination_folder / file["name"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(file["download_url"], headers=HEADERS)
            if r.status_code == 200:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print(f"✅ Downloaded: {file_path}")
            else:
                print(f"⚠️ Failed to download {file['name']}")
        elif file["type"] == "dir":
            new_path = f"{relative_path}/{file['name']}"
            new_destination_folder = Path(destination_folder) / file["name"]
            download_files(new_path, new_destination_folder)

# Main loop: for each version, enter the subdirectories
# since there's no way to download the directories containing the files directly, the code needs loops.
for version in versions:
    print(f"🔍 Exploring version {version}")
    api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{version}"
    resp = requests.get(api_url, headers=HEADERS)

    if resp.status_code != 200:
        print(f"❌ Error accessing version {version}: {resp.status_code}")
        continue

    sub_directories = resp.json()
    for sub in sub_directories:
        if sub["type"] == "dir":
            subdir_path = f"{version}/{sub['name']}"
            destination = f"{version.replace('/', '_')}/{sub['name']}"
            download_files(subdir_path, destination)