import requests
from pathlib import Path
from dotenv import load_dotenv
import os

# Importa as credenciais da conta no github
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Especifica o diretório
user = "docker-library"
repo = "python"
base_path = "baixados"
versoes = ["3.9", "3.10", "3.11", "3.12", "3.13"]

def baixar_arquivos(path_relativo, pasta_destino):
    api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{path_relativo}"
    resp = requests.get(api_url, headers=HEADERS)

    if resp.status_code != 200:
        print(f"❌ Erro ao acessar {api_url}: {resp.status_code}")
        return

    files = resp.json()
    for file in files:
        if file["type"] == "file" and file.get("download_url"):
            caminho_arquivo = Path(base_path) / pasta_destino / file["name"]
            caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(file["download_url"], headers=HEADERS)
            if r.status_code == 200:
                with open(caminho_arquivo, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print(f"✅ Baixado: {caminho_arquivo}")
            else:
                print(f"⚠️ Falha ao baixar {file['name']}")
        elif file["type"] == "dir":
            novo_path = f"{path_relativo}/{file['name']}"
            nova_pasta_destino = Path(pasta_destino) / file["name"]
            baixar_arquivos(novo_path, nova_pasta_destino)

# Loop principal: para cada versão, entrar nos subdiretórios
# como não tem um modo de baixar os diretórios com arquivos diretamente, o código precisa de loops
for versao in versoes:
    print(f"🔍 Explorando versão {versao}")
    api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{versao}"
    resp = requests.get(api_url, headers=HEADERS)

    if resp.status_code != 200:
        print(f"❌ Erro ao acessar versão {versao}: {resp.status_code}")
        continue

    subpastas = resp.json()
    for sub in subpastas:
        if sub["type"] == "dir":
            subdir_path = f"{versao}/{sub['name']}"
            destino = f"{versao.replace('/', '_')}/{sub['name']}"
            baixar_arquivos(subdir_path, destino)