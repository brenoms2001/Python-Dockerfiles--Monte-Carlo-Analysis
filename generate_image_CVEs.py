import os
import subprocess
from pathlib import Path

baixados = Path("baixados") #pasta com as imagens 
analisados = Path("analisados") #pasta para onde vão os jsons

# Armazenar os nomes das imagens criadas para remover depois
# Otimiza o donwload e no final salva armazenamento
imagens = []

# Cria diretório de saída (caso não exista)
analisados.mkdir(exist_ok=True)

def docker_build_and_scan(dockerfile_path: Path):
    versao = dockerfile_path.parts[1]     
    sub_versao = dockerfile_path.parts[2]   
    tag = f"trivy-scan:{versao}-{sub_versao}".replace("/", "-")

    # Caminho do diretório onde está o Dockerfile
    build_context = dockerfile_path.parent

    # Caminho espelhado no diretório analisados/
    output_path = analisados / versao / sub_versao
    output_path.mkdir(parents=True, exist_ok=True)
    output_json = output_path / "trivy-image.json"

    # Pega o dockerfile na pasta baixados, builda, escaneia com trivy
    # e salva o json com as CVEs na pasta analisados na subpasta de 
    # mesmo nome
    
    try:
        print(f"🐳 Buildando {tag}...")
        subprocess.run(
            ["docker", "build", "-f", str(dockerfile_path), "-t", tag, str(build_context)],
            check=True
        )

        docker_host = f'unix://{os.environ["HOME"]}/.docker/desktop/docker.sock'
        print(f"🔍 Escaneando com Trivy: {tag}")
        subprocess.run(
            ["trivy", "image", "--docker-host", docker_host, "-f", "json", "-o", str(output_json), tag],
            check=True
        )

        imagens.append(tag)


    except subprocess.CalledProcessError as e:
        print(f"❌ Erro com {tag}: {e}")
    

# Percorrendo recursivamente todos os Dockerfiles
for dockerfile in baixados.rglob("Dockerfile"):
    docker_build_and_scan(dockerfile)

## Apagando imagens e limpando armazenamento
#print("\n🧹 Removendo todas as imagens temporárias...")
#for tag in imagens:
#    subprocess.run(["docker", "rmi", "-f", tag], stdout=subprocess.DEVNULL)
#    print(f"🗑️  Removida: {tag}")