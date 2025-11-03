from api_utils import APIUtils
from config_utils import ConfigUtils
from bitcoin_utils import BitcoinUtils

# Instâncias das classes refatoradas
config = ConfigUtils()
setup = config.manipular_configuracao('ler') or {}

# Recupera a URL da API das configurações
url_api = setup.get('U', "http://127.0.0.1:8080/api")
api = APIUtils(url_api)
btc = BitcoinUtils()

# === Processar cada carteira individualmente ===
def check_wallet(dados):
    for item in dados[::-1]:
        tipo = item["Type"]
        mnemonic = item["Mnemonic"]

        # Derivar endereços conforme o tipo
        if tipo == "Legacy (BIP44)":
            enderecos = btc.derive_addresses(mnemonic, "bip44")
        elif tipo == "P2SH (BIP49)":
            enderecos = btc.derive_addresses(mnemonic, "bip49")
        elif tipo == "SegWit (BIP84)":
            enderecos = btc.derive_addresses(mnemonic, "bip84")
        else:
            print(f"❌ Tipo desconhecido: {tipo}")
            continue

        saldo_total_btc = sum(btc.saldo_blockstream(addr, "btc") for addr in enderecos)

        print(f"\n🔐 Tipo: {tipo}")
        print(f"📜 Últimas palavras: {' '.join(mnemonic.split()[-3:])}")
        if saldo_total_btc > 0:
            print(f"  ✅ Saldo total on-chain: {saldo_total_btc:.8f} BTC")
        else:
            print(f"   ➤ Saldo total on-chain: {saldo_total_btc:.8f} BTC")

# === Executar verificação ===
dados = api.consultar_wallets()
print("Verificando", len(dados), "carteiras")

check_wallet(dados)
