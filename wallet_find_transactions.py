# git clone https://github.com/stefanoesmeris/bitcoin-wallet-finder.git
# pip install bip-utils requests Mnemonic

import requests
import time, os, json, argparse
from general_functions import General_Functions as GF

from bip_utils import (
    Bip39SeedGenerator, Bip39MnemonicValidator, Bip39MnemonicGenerator,
    Bip44, Bip49, Bip84,
    Bip44Coins, Bip49Coins, Bip84Coins,
    Bip44Changes, Bip39WordsNum
)


# Instância global da classe
gf = GF()

def get_mnemonic_seq(M, N):
    lista = gf.get_next(int(M), int(N))
    X = 0
    for phrase in lista:
        mnemonic = str(phrase)
        print("CheckSum", X, "of", len(lista)-1, "Seed", mnemonic)

        gf.check_addresses(Bip44, Bip44Coins.BITCOIN, "Legacy (BIP44)", 44, mnemonic)
        print("Looking BIP44 Legacy\n")
        time.sleep(0.5)

        gf.check_addresses(Bip49, Bip49Coins.BITCOIN, "P2SH (BIP49)", 49, mnemonic)
        print("Looking BIP49 P2SH\n")
        time.sleep(0.5)

        gf.check_addresses(Bip84, Bip84Coins.BITCOIN, "SegWit (BIP84)", 84, mnemonic)
        print("Looking BIP84 SegWit\n")
        time.sleep(0.5)

        fim = time.time()
        tempo_total = fim - time.time()
        print(f"A tarefa levou {tempo_total:.4f} segundos para ser concluída.\n")
        X += 1

def get_mnemonic_rand():
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
    print(f"Mnemonic string: {mnemonic}")

    inicio = time.time()

    gf.check_addresses(Bip44, Bip44Coins.BITCOIN, "Legacy (BIP44)", 44, mnemonic)
    print("Looking BIP44 Legacy\n")
    time.sleep(0.5)

    gf.check_addresses(Bip49, Bip49Coins.BITCOIN, "P2SH (BIP49)", 49, mnemonic)
    print("Looking BIP49 P2SH\n")
    time.sleep(0.5)

    gf.check_addresses(Bip84, Bip84Coins.BITCOIN, "SegWit (BIP84)", 84, mnemonic)
    print("Looking BIP84 SegWit\n")
    time.sleep(0.5)

    fim = time.time()
    tempo_total = fim - inicio
    print(f"A tarefa levou {tempo_total:.4f} segundos para ser concluída.\n")

def main():
    print("🔁 Starting main loop. Press Ctrl+C to stop.")

    parser = argparse.ArgumentParser(description="Script com configuração persistente")
    parser.add_argument('--N', type=int, help="Valor inicial para N (prioridade máxima)")
    parser.add_argument('--U', type=str, help="Valor inicial para URL (prioridade máxima)")
    args = parser.parse_args()

    config = gf.manipular_configuracao('ler')

    if args.N is not None:
        N = args.N
    elif config and 'N' in config:
        N = config['N']
    else:
        N = gf.DEFAULT_N

    if args.U is not None:
        U = args.U
    elif config and 'U' in config:
        U = config['U']
    else:
        U = gf.DEFAULT_U

    contador = config['contador'] if config and 'contador' in config else gf.DEFAULT_CONTADOR

    # Atualiza a URL da instância
    gf.U = U

    gf.manipular_configuracao('atualizar', {'contador': contador, 'N': N, 'U': U})

    try:
        while True:
            if N > 0:
                print("Contador:", contador)
                W = 30
                get_mnemonic_seq(contador, N)
                contador += 1
                gf.manipular_configuracao('atualizar', {'contador': contador, 'N': N})
            else:
                W = 5
                get_mnemonic_rand()

            if contador > 2047:
                gf.manipular_configuracao('atualizar', {'contador': 0, 'N': N})
                break

            # time.sleep(W)  # Descomente se quiser pausas entre execuções
    except KeyboardInterrupt:
        print("\n🛑 Loop stopped by user.")

if __name__ == "__main__":
    main()