
from mnemonic import Mnemonic
import bip_utils
import requests
import time, os, json, argparse

class General_Functions:
    def __init__(self, INDEX=0):
        self.N = 12
        self.M = 0
        
    def get_next(self, M, N):
        # Inicializa o gerador BIP39 em inglês
        mnemo = Mnemonic("english")

        # Define o número de palavras da seed (12, 15, 18, 21 ou 24)
        #N = 12
        #M = 0 # Index of word from BIP39

        # Pega a primeira palavra da lista BIP39
        first_word = mnemo.wordlist[M]  # geralmente 'abandon'

        # Cria a base da frase com N - 1 repetições da primeira palavra
        base_phrase = [first_word] * (N - 1)

        # Dicionário para armazenar frases válidas
        #valid_phrases = {}
        my_list = []

        # Testa todas as palavras possíveis como última palavra
        for candidate in mnemo.wordlist:
            test_phrase = base_phrase + [candidate]
            phrase_str = " ".join(test_phrase)
            if mnemo.check(phrase_str):
                #valid_phrases[candidate] = phrase_str
                my_list.append(phrase_str)

        # Exibe os resultados
        #print(f"Frases válidas encontradas: {len(valid_phrases)}")
        #for word, phrase in valid_phrases.items():
        #    print(f"{phrase}")

        return(my_list)
        
    # Consulta histórico de transações via Blockstream API
    def has_activity(addr, max_retries=5, timeout=5):
        url = f"https://blockstream.info/api/address/{addr}/txs"
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    txs = response.json()
                    # Verifica se é uma lista e se contém dados
                    if isinstance(txs, list) and txs:
                        return True
                    else:
                        # Dados vazios ou não listados
                        return False
                else:
                    print(f"[Tentativa {attempt+1}] Código de status inesperado: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"[Tentativa {attempt+1}] Erro de conexão: {e}")
                time.sleep(2 ** attempt)  # Backoff exponencial
        # Se todas as tentativas falharem
        print("Falha ao consultar a API após múltiplas tentativas.")
        return False
    #
    def write_good_seed_to_file(data, filename):
        if os.path.exists(filename):
            with open("dados.json", "r") as f:
                try:
                    dados_existentes = json.load(f)
                except json.JSONDecodeError:
                    dados_existentes = []
        else:
            dados_existentes = []
        # Adiciona o novo dado à lista
        dados_existentes.append(data)
        # Salva de volta no arquivo
        with open("dados.json", "w") as f:
            json.dump(dados_existentes, f, indent=4)
        print("\n✅ Resultado exportado para 'dados.json'")   