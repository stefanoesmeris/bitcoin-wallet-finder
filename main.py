# git clone https://github.com/stefanoesmeris/bitcoin-wallet-finder.git
# pip install bip-utils requests mnemonic

import time
import argparse

from api_utils import APIUtils
from config_utils import ConfigUtils
from bitcoin_utils import BitcoinUtils

# Instâncias globais
api = APIUtils()
config = ConfigUtils()
btc = BitcoinUtils()

def main():
    print("🔁 Starting main loop. Press Ctrl+C to stop.")

    parser = argparse.ArgumentParser(description="Script com configuração persistente")
    parser.add_argument('--N', type=int, help="Valor inicial para N (prioridade máxima)")
    parser.add_argument('--U', type=str, help="Valor inicial para URL (prioridade máxima)")
    args = parser.parse_args()

    setup = config.manipular_configuracao('ler') or {}

    N = args.N if args.N is not None else setup.get('N', 0)
    U = args.U if args.U is not None else setup.get('U', "http://127.0.0.1:8080/api")
    contador = setup.get('contador', 0)

    # Atualiza a URL da instância da API
    api.url = U
    config.manipular_configuracao('atualizar', {'contador': contador, 'N': N, 'U': U})

    try:
        while True:
            if N > 0:
                print("Contador:", contador)
                btc.process_mnemonic_seq(contador, N, config, api)
                contador += 1
                config.manipular_configuracao('atualizar', {'contador': contador, 'N': N, 'U': U})
            else:
                btc.process_mnemonic_rand(config, api)

            if contador > 2047:
                config.manipular_configuracao('atualizar', {'contador': 0, 'N': N, 'U': U})
                break

            # time.sleep(W)  # Descomente se quiser pausas entre execuções
    except KeyboardInterrupt:
        print("\n🛑 Loop stopped by user.")

if __name__ == "__main__":
    main()