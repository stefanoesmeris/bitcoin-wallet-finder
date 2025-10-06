# git clone https://github.com/stefanoesmeris/bitcoin-wallet-finder.git
# pip install bip-utils requests pandas Mnemonic
#
# O que este script faz:
# 
# 	Importa as palavras sementes
# 	Deriva os endereços nos padrões BIP44, BIP49 e BIP84
# 	Verifica se houve movimentações (mesmo com saldo zerado)
# 	Exporta os resultados para um arquivo  contendo:
# 	Endereço
# 	Caminho de derivação (ex: )
# 	Tipo (BIP44, BIP49, BIP84)
# 	Status de movimentação
# 	Palavras sementes (opcional — cuidado com segurança!)
import bip_utils
import requests
import pandas as pd
import time, os, json
from sequencial import Sequencial

#seed_bytes = ""

# Palavras sementes (substitua pelas suas)
#mnemonic = ""
#mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
#mnemonic = "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong"

from bip_utils import (
    Bip39SeedGenerator, Bip39MnemonicValidator, Bip39MnemonicGenerator,
    Bip44, Bip49, Bip84,
    Bip44Coins, Bip49Coins, Bip84Coins,
    Bip44Changes, Bip39WordsNum
)

# Consulta histórico de transações via Blockstream API
def has_activity(addr):
    url = f"https://blockstream.info/api/address/{addr}/txs"
    response = requests.get(url)
    if response.status_code == 200:
        txs = response.json()
        return len(txs) > 0
    else:
        return False

# Função para derivar e verificar endereços
def check_addresses(derivation, coin_type, label, bip_number, mnemonic):
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    wallet = derivation.FromSeed(seed_bytes, coin_type)
    results = []
    good_seed = False
    for i in range(5):  # Varrer os primeiros 5 endereços externos
        path = f"m/{bip_number}'/0'/0'/0/{i}"
        addr = wallet.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
        active = has_activity(addr)
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
            break
    if good_seed:    
        write_good_seed_to_file(results)
        print(type(results),"\n")
        print(results)
    return results

def write_good_seed_to_file(data):
    df = pd.DataFrame(data)
    df.to_csv("s_carteira_bitcoin_good.txt", mode='a', index=False)
    if os.path.exists("dados.json"):
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
    print("\n✅ Resultado exportado para 's_carteira_bitcoin_good.txt'")

def get_mnemonic(M, N):
    #N = 12 # Define o número de palavras da seed (12, 15, 18, 21 ou 24)
    #M = 0  # Index of word from BIP39
    seq = Sequencial(0)
    #global seed_bytes
    lista = []
    lista = seq.get_next(int(M),int(N))
    X = 0
    for phrase in lista:
        mnemonic = str(phrase)
        #print(mnemonic)
        #mnemonic = "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong"
        #seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
        data = []
        print("CheckSum ", X, "of ", len(lista)-1, "Seed ", mnemonic)
        data = check_addresses(Bip44, Bip44Coins.BITCOIN, "Legacy (BIP44)", 44, mnemonic)
        print("Looking BIP44 Legacy\n")
        time.sleep(0.5)  # Sleep for half a second
        data = check_addresses(Bip49, Bip49Coins.BITCOIN, "P2SH (BIP49)", 49, mnemonic)
        print("Looking BIP49 P2SH\n")
        time.sleep(0.5)  # Sleep for half a second
        data = check_addresses(Bip84, Bip84Coins.BITCOIN, "SegWit (BIP84)", 84, mnemonic)
        print("Looking BIP84 SegWit\n")
        time.sleep(0.5)  # Sleep for half a second
        X += 1
        if X % 15 == 0:
            print("sleep for 15 seconds - because no one is made of iron")
            time.sleep(15)  # Sleep for 15 seconds
#
def main():
    #global seed_bytes
    print("🔁 Starting main loop. Press Ctrl+C to stop.")
    contador = 0
    #N = 12 # Define o número de palavras da seed (12, 15, 18, 21 ou 24)
    N = 12
    # Nome do arquivo onde o contador será armazenado
    arquivo = "contador.txt"
    # Verifica se o arquivo existe
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f:
            try:
                contador = int(f.read())
            except ValueError:
                contador = 0 # Se nao for valido
    else:
        with open(arquivo, "w") as f:
            f.write(str(contador))
    try:
        while True:
            #
            print("Contador :", contador)
            get_mnemonic(int(contador), int(N))
            contador += 1
            with open(arquivo, "w") as f:
                f.write(str(contador))
            if contador > 2047:
                break
            print("sleep for 30 seconds - because no one is made of iron")
            time.sleep(30)  # Sleep for 30 seconds
    except KeyboardInterrupt:
        print("\n🛑 Loop stopped by user.")
#
if __name__ == "__main__":

    main()


