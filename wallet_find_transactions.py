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
import bip_utils
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
DEFAULT_N = 12 # N = 12 - Define o número de palavras da seed (12, 15, 18, 21 ou 24)
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


# Função para derivar e verificar endereços
def check_addresses(derivation, coin_type, label, bip_number, mnemonic):
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    wallet = derivation.FromSeed(seed_bytes, coin_type)
    results = []
    good_seed = False
    for i in range(5):  # Varrer os primeiros 5 endereços externos
        path = f"m/{bip_number}'/0'/0'/0/{i}"
        addr = wallet.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
        active = GF.has_activity(addr)
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
        GF.write_good_seed_to_file(results, "dados.json")
        print(type(results),"\n")
        print(results)
    return results



def get_mnemonic(M, N):
    #N = 12 # Define o número de palavras da seed (12, 15, 18, 21 ou 24)
    #M = 0  # Index of word from BIP39
    seq = GF(0)
    lista = []
    lista = seq.get_next(int(M),int(N)) # Busca uma lista de mnemonic para ser avaliada.
    X = 0
    for phrase in lista:
        mnemonic = str(phrase)
        #mnemonic = "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong"
        data = []
        inicio = time.time()
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
        fim = time.time()
        tempo_total = fim - inicio
        print(f"A tarefa levou {tempo_total:.4f} segundos para ser concluída.\n")
        X += 1
        if X % 15 == 0:
            print("sleep for 15 seconds - because no one is made of iron")
            time.sleep(15)  # Sleep for 15 seconds
#
def main():
    print("🔁 Starting main loop. Press Ctrl+C to stop.")
    # N = 12 # Define o número de palavras da seed (12, 15, 18, 21 ou 24)
    #
    parser = argparse.ArgumentParser(description="Script com configuração persistente")
    parser.add_argument('--N', type=int, help="Valor inicial para N (prioridade máxima)")
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

    # 🧱 Inicializa contador
    contador = config['contador'] if config and 'contador' in config else DEFAULT_CONTADOR
    
    # 💾 Atualiza ou cria o arquivo com os valores iniciais
    
    manipular_configuracao('atualizar', {'contador': contador, 'N': N})

    try:
        while True:
            #
            print("Contador :", contador)
            get_mnemonic(int(contador), int(N))
            contador += 1
            manipular_configuracao('atualizar', {'contador': contador, 'N': N})
            if contador > 2047:
                break
            print("sleep for 30 seconds - because no one is made of iron")
            time.sleep(30)  # Sleep for 30 seconds
    except KeyboardInterrupt:
        print("\n🛑 Loop stopped by user.")
#
if __name__ == "__main__":

    main()


