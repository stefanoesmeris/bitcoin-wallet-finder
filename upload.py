#!/usr/bin/python3

import os
import json
import requests

# Diretório onde o script está localizado
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminhos absolutos para os arquivos JSON
dados_path = os.path.join(SCRIPT_DIR, "dados.json")
setup_path = os.path.join(SCRIPT_DIR, "setup.json")

# 1. Verificar se existe o arquivo dados.json
if os.path.exists(dados_path):
    # 2. Ler setup.json e extrair a URL
    with open(setup_path, "r") as f:
        setup = json.load(f)
        url = setup.get("U")

    # 3. Ler o conteúdo de dados.json
    with open(dados_path, "r") as f:
        dados = json.load(f)

    # 4. Enviar POST com requests
    response = requests.post(url, json=dados)

    # 5. Exibir resultado
    print("Status:", response.status_code)
    print("Resposta:", response.text)
else:
    print("Arquivo dados.json não encontrado no diretório do script.")

