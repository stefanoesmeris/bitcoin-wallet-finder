import requests
import time
from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44Changes
from bip_utils import (
    Bip39MnemonicGenerator, Bip39WordsNum,
    Bip44, Bip49, Bip84,
    Bip44Coins, Bip49Coins, Bip84Coins, Bip32Slip10Secp256k1, P2PKHAddr
)


class BitcoinUtils:
    @staticmethod
    def get_next(M, N):
        mnemo = Mnemonic("english")
        first_word = mnemo.wordlist[M]
        base_phrase = [first_word] * (N - 1)
        return [
            " ".join(base_phrase + [candidate])
            for candidate in mnemo.wordlist
            if mnemo.check(" ".join(base_phrase + [candidate]))
        ]

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
                    time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                print(f"[{attempt+1}] Erro de conexão: {e}")
                time.sleep(2 ** attempt)
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

    def check_addresses(self, derivation, coin_type, label, bip_number, mnemonic, config, api):
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
            config.write_good_seed_to_file(results, "dados.json")
            api.enviar_wallets(results)

        return results

    def process_mnemonic_seq(self, M, N, config, api):
        lista = self.get_next(int(M), int(N))
        for X, phrase in enumerate(lista):
            mnemonic = str(phrase)
            print("CheckSum", X, "of", len(lista)-1, "Seed", mnemonic)

            self.check_addresses(Bip44, Bip44Coins.BITCOIN, "Legacy (BIP44)", 44, mnemonic, config, api)
            print("Looking BIP44 Legacy\n")
            time.sleep(0.2)

            self.check_addresses(Bip49, Bip49Coins.BITCOIN, "P2SH (BIP49)", 49, mnemonic, config, api)
            print("Looking BIP49 P2SH\n")
            time.sleep(0.2)

            self.check_addresses(Bip84, Bip84Coins.BITCOIN, "SegWit (BIP84)", 84, mnemonic, config, api)
            print("Looking BIP84 SegWit\n")
            time.sleep(0.2)

            print("✅ Tarefa concluída.\n")

    def process_mnemonic_rand(self, config, api):
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
        print(f"Mnemonic string: {mnemonic}")

        self.check_addresses(Bip44, Bip44Coins.BITCOIN, "Legacy (BIP44)", 44, mnemonic, config, api)
        print("Looking BIP44 Legacy\n")
        time.sleep(0.5)

        self.check_addresses(Bip49, Bip49Coins.BITCOIN, "P2SH (BIP49)", 49, mnemonic, config, api)
        print("Looking BIP49 P2SH\n")
        time.sleep(0.5)

        self.check_addresses(Bip84, Bip84Coins.BITCOIN, "SegWit (BIP84)", 84, mnemonic, config, api)
        print("Looking BIP84 SegWit\n")
        time.sleep(0.5)

        print("✅ Tarefa concluída.\n")        


    def derive_addresses(self, mnemonic, tipo):
        seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

        if tipo == "bip44":
            bip = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
        elif tipo == "bip49":
            bip = Bip49.FromSeed(seed_bytes, Bip49Coins.BITCOIN)
        elif tipo == "bip84":
            bip = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)
        else:
            return []

        carteira = bip.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
        return [carteira.AddressIndex(i).PublicKey().ToAddress() for i in range(20)]

    def derive_addresses_liquid(self, mnemonic):
        seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
        bip32_ctx = Bip32Slip10Secp256k1.FromSeed(seed_bytes)

        enderecos = []
        for i in range(20):
            path = f"m/44'/1776'/0'/0/{i}"
            chave = bip32_ctx.DerivePath(path)
            endereco = P2PKHAddr.EncodeKey(chave.PublicKey())
            enderecos.append(endereco)


        return enderecos        

