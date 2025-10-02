#
#pip install bip-utils requests pandas
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
import time

found_flag = True
seed_bytes = ""

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
    wallet = derivation.FromSeed(seed_bytes, coin_type)
    results = []
    global found_flag
    for i in range(5):  # Varrer os primeiros 5 endereços externos
        path = f"m/{bip_number}'/0'/0'/0/{i}"
        addr = wallet.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
        active = has_activity(addr)
        status = "Movimentado" if active else "unused"
        if active:
            found_flag = False
            results.append({
                "Tipo": label,
                "Endereço": addr,
                "Caminho": path,
                "Status": status,
                "Mnemonic": mnemonic  # ⚠️ Cuidado: incluir apenas se necessário
            })
            write_file(results,mnemonic)            
    return results
    #write_file(results,mnemonic)

def write_file(data,mnemonic):
    global found_flag
    if found_flag:
        data = []
        data.append({"Status": 'unused :', "Mnemonic": mnemonic})
        df = pd.DataFrame(data)        
        df.to_csv("carteira_bitcoin_not_found.txt", mode='a', index=False)
    else:
        df = pd.DataFrame(data)
        df.to_csv("carteira_bitcoin_good.txt", mode='a', index=False)
    print("\n✅ Resultado exportado para 'carteira_bitcoin_.txt'")   



# Valida o mnemonic
#if not Bip39MnemonicValidator(mnemonic).IsValid():
#    print("Mnemonic inválido.")
#    exit()


def main():
    global found_flag
    global seed_bytes
    print("🔁 Starting main loop. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Generate random mnemonic
            mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
            # Palavras sementes (substitua pelas suas)
            #mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
            print(f"Mnemonic string: {mnemonic}")
            # Gera a seed
            seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
            # Executa para os três padrões
            data = []
            data = check_addresses(Bip44, Bip44Coins.BITCOIN, "Legacy (BIP44)", 44, mnemonic)
            time.sleep(0.5)  # Sleep for half a second
            data = check_addresses(Bip49, Bip49Coins.BITCOIN, "P2SH (BIP49)", 49, mnemonic)
            time.sleep(0.5)  # Sleep for half a second
            data = check_addresses(Bip84, Bip84Coins.BITCOIN, "SegWit (BIP84)", 84, mnemonic)
            time.sleep(0.5)  # Sleep for half a second
            write_file(data,mnemonic)
            #time.sleep(1.5)  # Sleep for half a second
    except KeyboardInterrupt:
        print("\n🛑 Loop stopped by user.")

if __name__ == "__main__":
    main()