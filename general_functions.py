from mnemonic import Mnemonic
import bip_utils
import requests
import time, os, json
from datetime import datetime

from bip_utils import (
    Bip39SeedGenerator, Bip39MnemonicValidator, Bip39MnemonicGenerator,
    Bip44, Bip49, Bip84,
    Bip44Coins, Bip49Coins, Bip84Coins,
    Bip44Changes, Bip39WordsNum
)

class General_Functions:
    def __init__(self):
        self.N = 12
        self.M = 0
        self.U = "http://127.0.0.1:5000/api"
        self.SETUP_FILE = 'setup.json'
        self.DEFAULT_N = 0
        self.DEFAULT_U = "http://127.0.0.1:8080/api"
        self.DEFAULT_CONTADOR = 0

    @staticmethod
    def get_next(M, N):
        mnemo = Mnemonic("english")
        first_word = mnemo.wordlist[M]
        base_phrase = [first_word] * (N - 1)
        my_list = []

        for candidate in mnemo.wordlist:
            test_phrase = base_phrase + [candidate]
            phrase_str = " ".join(test_phrase)
            if mnemo.check(phrase_str):
                my_list.append(phrase_str)

        return my_list

    def consultar_wallets(self):
        try:
            resposta = requests.get(self.U)
            if resposta.status_code == 200:
                return resposta.json()
            else:
                print("Erro ao consultar:", resposta.status_code)
                return []
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")
            time.sleep(2)
        print("Falha ao consultar a API após múltiplas tentativas.")
        return False

    def manipular_configuracao(self, acao, novos_valores=None):
        if acao == 'ler':
            if os.path.exists(self.SETUP_FILE):
                with open(self.SETUP_FILE, 'r') as f:
                    return json.load(f)
            else:
                return None
        elif acao == 'atualizar' and novos_valores:
            with open(self.SETUP_FILE, 'w') as f:
                json.dump(novos_valores, f, indent=4)

    def enviar_wallets(self, dados):
        try:
            if isinstance(dados, list) and all(isinstance(item, dict) for item in dados):
                dados_formatados = [dados]
            else:
                raise ValueError("Formato inválido: esperado lista de dicionários.")

            resposta = requests.post(self.U, json=dados_formatados)

            if resposta.status_code == 200:
                print("✅ Dados enviados com sucesso!")
                print("Resposta:", resposta.json())
            else:
                print(f"⚠️ Erro ao enviar dados: {resposta.status_code}")
                print("Detalhes:", resposta.text)

        except Exception as e:
            print("❌ Erro ao processar:", e)

    def has_activity(self, addr, max_retries=5, timeout=5):
        url = f"https://blockstream.info/api/address/{addr}/txs"
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    txs = response.json()
                    return isinstance(txs, list) and bool(txs)
                elif response.status_code == 429:
                    print(f"[{attempt+1}] Código 429 - aguardando {(attempt+1) * 5} minutos")
                    time.sleep(300 * (attempt + 1))
                else:
                    print(f"[{attempt+1}] Código inesperado: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"[{attempt+1}] Erro de conexão: {e}")
                time.sleep(2 ** attempt)
        print("Falha ao consultar a API após múltiplas tentativas.")
        return False

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
                    print(f"[{attempt+1}] Código inesperado: {r.status_code}")
                    time.sleep(60 * (attempt + 1))
            except requests.exceptions.RequestException as e:
                print(f"[{attempt+1}] Erro de conexão: {e}")
                time.sleep(2 ** attempt)
        return 0

    @staticmethod
    def write_good_seed_to_file(data, filename):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                try:
                    dados_existentes = json.load(f)
                except json.JSONDecodeError:
                    dados_existentes = []
        else:
            dados_existentes = []

        dados_existentes.append(data)
        with open(filename, "w") as f:
            json.dump(dados_existentes, f, indent=4)

    def check_addresses(self, derivation, coin_type, label, bip_number, mnemonic):
        D = 3
        seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
        wallet = derivation.FromSeed(seed_bytes, coin_type)
        results = []
        good_seed = False

        for i in range(D):
            path = f"m/{bip_number}'/0'/0'/0/{i}"
            addr = wallet.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
            active = self.has_activity(addr)
            status = "Movimentado" if active else "unused"
            if active:
                good_seed = True
                results.append({
                    "Type": label,
                    "Address": addr,
                    "Path": path,
                    "Status": status,
                    "Mnemonic": mnemonic
                })
                print("Found a good seed")
                break

        if good_seed:
            self.write_good_seed_to_file(results, "dados.json")
            self.enviar_wallets(results)

        return results