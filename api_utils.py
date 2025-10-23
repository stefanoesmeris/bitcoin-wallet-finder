import requests
import time

class APIUtils:
    def __init__(self, url="http://127.0.0.1:5000/api"):
        self.url = url

    def consultar_wallets(self):
        try:
            resposta = requests.get(self.url)
            if resposta.status_code == 200:
                return resposta.json()
            print("Erro ao consultar:", resposta.status_code)
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")
            time.sleep(2)
        print("Falha ao consultar a API após múltiplas tentativas.")
        return False

    def enviar_wallets(self, dados):
        try:
            if isinstance(dados, list) and all(isinstance(item, dict) for item in dados):
                dados_formatados = [dados]
            else:
                raise ValueError("Formato inválido: esperado lista de dicionários.")

            resposta = requests.post(self.url, json=dados_formatados)
            if resposta.status_code == 200:
                print("✅ Dados enviados com sucesso!")
                print("Resposta:", resposta.json())
            else:
                print(f"⚠️ Erro ao enviar dados: {resposta.status_code}")
                print("Detalhes:", resposta.text)
        except Exception as e:
            print("❌ Erro ao processar:", e)