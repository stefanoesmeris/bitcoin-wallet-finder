
from mnemonic import Mnemonic
import bip_utils
import requests
import time, os, json, argparse
from datetime import datetime

from bip_utils import (
    Bip39SeedGenerator, Bip39MnemonicValidator, Bip39MnemonicGenerator,
    Bip44, Bip49, Bip84,
    Bip44Coins, Bip49Coins, Bip84Coins,
    Bip44Changes, Bip39WordsNum
)

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
    def has_activity(self, addr, max_retries=5, timeout=5):
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
                elif response.status_code == 429:
                    print(f"[Tentativa {attempt+1}] - Codigo 429  servidor recusando - aguardar {(attempt+1) *5} minutos {datetime.now()}")
                    time.sleep(300  * (attempt + 1))
                else:
                    print(f"[Tentativa {attempt+1}] Código de status inesperado: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"[Tentativa {attempt+1}] Erro de conexão: {e}")
                time.sleep(2 ** attempt)  # Backoff exponencial
        # Se todas as tentativas falharem
        print("Falha ao consultar a API após múltiplas tentativas.")
        return False
    #
    def saldo_blockstream(self, addr, rede="btc", max_retries=5, timeout=5):
        if rede == "btc":
            url = f"https://blockstream.info/api/address/{addr}"
        elif rede == "liquid":
            url = f"https://blockstream.info/liquid/api/address/{addr}"
        else:
            return 0
        for attempt in range(max_retries):
            try:
                r = requests.get(url, timeout=timeout)
                if r.status_code == 200:
                    dados = r.json()
                    funded = dados.get("chain_stats", {}).get("funded_txo_sum", 0)
                    spent = dados.get("chain_stats", {}).get("spent_txo_sum", 0)
                    return (funded - spent) / 1e8
                else:
                    print(f"[Tentativa {attempt+1}] Código de status inesperado: {response.status_code}")    
            except requests.exceptions.RequestException as e:
                print(f"[Tentativa {attempt+1}] Erro de conexão: {e}")
                time.sleep(2 ** attempt)  # Backoff exponencial
                #pass
        return 0
    #
    def write_good_seed_to_file(self, data, filename):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                try:
                    dados_existentes = json.load(f)
                except json.JSONDecodeError:
                    dados_existentes = []
        else:
            dados_existentes = []
        # Adiciona o novo dado à lista
        dados_existentes.append(data)
        # Salva de volta no arquivo
        with open(filename, "w") as f:
            json.dump(dados_existentes, f, indent=4)
        print("\n✅ Resultado exportado para ", str(filename))
    #
    # Função para derivar e verificar endereços
    def check_addresses(self, derivation, coin_type, label, bip_number, mnemonic):
        seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
        wallet = derivation.FromSeed(seed_bytes, coin_type)
        results = []
        good_seed = False
        for i in range(5):  # Varrer os primeiros 5 endereços externos
            path = f"m/{bip_number}'/0'/0'/0/{i}"
            addr = wallet.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
            active = self.has_activity(self, addr)
            status = "Movimentado" if active else "unused"
            if active:
                good_seed = True
                results.append({
                    "Type": label,
                    "Address": addr,
                    "Path": path,
                    "Status": status,
                    "Mnemonic": mnemonic  # ⚠️ Cuidado: incluir apenas se necessário
                })
                print("Found a good seed")
                break # Basta encontrar um unico endereço que ja e suficiente!  Just finding a single address is enough!
        if good_seed:    
            self.write_good_seed_to_file(self, results, "dados.json")
            #print(results)
        return results


