# git clone https://github.com/stefanoesmeris/bitcoin-wallet-finder.git
# pip install bip-utils requests Mnemonic
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
#import bip_utils
import requests
import time, os, json, argparse
from general_functions import General_Functions as GF


from bip_utils import (
    Bip39SeedGenerator, Bip39MnemonicValidator, Bip39MnemonicGenerator,
    Bip44, Bip49, Bip84,
    Bip44Coins, Bip49Coins, Bip84Coins,
    Bip44Changes, Bip39WordsNum
)

SETUP_FILE = 'setup.json'
DEFAULT_N = 12 # N = 12 - Define o número de palavras da seed (12, 15, 18, 21 ou 24) ou 0(zero) para aleatorio
DEFAULT_U = "http://127.0.0.1:8080/api"
DEFAULT_CONTADOR = 0


def manipular_configuracao(acao, novos_valores=None):
    if acao == 'ler':
        if os.path.exists(SETUP_FILE):
            with open(SETUP_FILE, 'r') as f:
                return json.load(f)
        else:
            return None
    elif acao == 'atualizar' and novos_valores:
        with open(SETUP_FILE, 'w') as f:
            json.dump(novos_valores, f, indent=4)

def get_mnemonic_seq(M, N):
    #N = 12 # Define o número de palavras da seed (12, 15, 18, 21 ou 24)
    #M = 0  # Index of word from BIP39
    #seq = GF(0)
    lista = []
    lista = GF.get_next(GF, int(M),int(N)) # Busca uma lista de mnemonic para ser avaliada.
    X = 0
    for phrase in lista:
        mnemonic = str(phrase)
        data = []
        inicio = time.time()
        print("CheckSum ", X, "of ", len(lista)-1, "Seed ", mnemonic)
        data = GF.check_addresses(GF, Bip44, Bip44Coins.BITCOIN, "Legacy (BIP44)", 44, mnemonic)
        print("Looking BIP44 Legacy\n")
        time.sleep(0.5)  # Sleep for half a second
        data = GF.check_addresses(GF, Bip49, Bip49Coins.BITCOIN, "P2SH (BIP49)", 49, mnemonic)
        print("Looking BIP49 P2SH\n")
        time.sleep(0.5)  # Sleep for half a second
        data = GF.check_addresses(GF, Bip84, Bip84Coins.BITCOIN, "SegWit (BIP84)", 84, mnemonic)
        print("Looking BIP84 SegWit\n")
        time.sleep(0.5)  # Sleep for half a second
        fim = time.time()
        tempo_total = fim - inicio
        print(f"A tarefa levou {tempo_total:.4f} segundos para ser concluída.\n")
        X += 1
        #if X % 15 == 0:
        #    print("sleep for 15 seconds - because no one is made of iron")
        #    time.sleep(15)  # Sleep for 15 seconds
#
def get_mnemonic_rand():
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
    print(f"Mnemonic string: {mnemonic}")
    # Gera a seed
    #seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    # Executa para os três padrões
    data = []
    inicio = time.time()
    data = GF.check_addresses(GF, Bip44, Bip44Coins.BITCOIN, "Legacy (BIP44)", 44, mnemonic)
    print("Looking BIP44 Legacy\n")
    time.sleep(0.5)  # Sleep for half a second
    data = GF.check_addresses(GF, Bip49, Bip49Coins.BITCOIN, "P2SH (BIP49)", 49, mnemonic)
    print("Looking BIP49 P2SH\n")
    time.sleep(0.5)  # Sleep for half a second
    data = GF.check_addresses(GF, Bip84, Bip84Coins.BITCOIN, "SegWit (BIP84)", 84, mnemonic)
    print("Looking BIP84 SegWit\n")
    time.sleep(0.5)  # Sleep for half a second
    fim = time.time()
    tempo_total = fim - inicio
    print(f"A tarefa levou {tempo_total:.4f} segundos para ser concluída.\n")
    
#    
def main():
    print("🔁 Starting main loop. Press Ctrl+C to stop.")
    # N = 12 # Define o número de palavras da seed (12, 15, 18, 21 ou 24)
    #
    parser = argparse.ArgumentParser(description="Script com configuração persistente")
    parser.add_argument('--N', type=int, help="Valor inicial para N (prioridade máxima)")
    parser.add_argument('--U', type=str, help="Valor inicial para URL (prioridade máxima)")
    args = parser.parse_args()
    config = manipular_configuracao('ler')
    #
    # 🧠 Determina valor de N com base na prioridade
    if args.N is not None:
        N = args.N
    elif config and 'N' in config:
        N = config['N']
    else:
        N = DEFAULT_N

    # 🧠 Determina valor de U com base na prioridade
    if args.U is not None:
        U = args.U
    elif config and 'U' in config:
        U = config['U']
    else:
        U = DEFAULT_U
        
    # 🧱 Inicializa contador
    contador = config['contador'] if config and 'contador' in config else DEFAULT_CONTADOR
    
    GF.U = U 
    
    # 💾 Atualiza ou cria o arquivo com os valores iniciais
    
    manipular_configuracao('atualizar', {'contador': contador, 'N': N, 'U': U})

    try:
        while True:
            #
            if N > 0:
                print("Contador :", contador)
                W = 30
                get_mnemonic_seq(int(contador), int(N))
                contador += 1
                manipular_configuracao('atualizar', {'contador': contador, 'N': N})
            else:
                W = 5
                get_mnemonic_rand()
            if contador > 2047:
                manipular_configuracao('atualizar', {'contador': 0, 'N': N})
                break
            #print("sleep for ", W, " seconds - because no one is made of iron")
            #time.sleep(W)  # Sleep for 30 seconds
    except KeyboardInterrupt:
        print("\n🛑 Loop stopped by user.")
#
if __name__ == "__main__":
    # Call the main function  and start aplication
    main()



