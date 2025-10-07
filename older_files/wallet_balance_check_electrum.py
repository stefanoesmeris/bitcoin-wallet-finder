import json
import requests
from bip_utils import (
    Bip39SeedGenerator, Bip39MnemonicValidator,
    Bip44, Bip49, Bip84,
    Bip44Coins, Bip49Coins, Bip84Coins,
    Bip44Changes
)
from electrum.mnemonic import Mnemonic as ElectrumMnemonic
from electrum.keystore import from_seed as electrum_from_seed

# === Funções auxiliares ===
def is_electrum_seed(seed):
    return ElectrumMnemonic('en').check(seed)

def derivar_enderecos_bip(mnemonic, tipo):
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    if tipo == "Legacy (BIP44)":
        bip = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
    elif tipo == "P2SH (BIP49)":
        bip = Bip49.FromSeed(seed_bytes, Bip49Coins.BITCOIN)
    elif tipo == "SegWit (BIP84)":
        bip = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)
    else:
        return []

    carteira = bip.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    return [carteira.AddressIndex(i).PublicKey().ToAddress() for i in range(20)]

def derivar_enderecos_electrum(seed):
    ks = electrum_from_seed(seed, "", "standard")
    return ks.get_addresses()[:20]

def saldo_blockstream(endereco, rede="btc"):
    if rede == "btc":
        url = f"https://blockstream.info/api/address/{endereco}"
    elif rede == "liquid":
        url = f"https://blockstream.info/liquid/api/address/{endereco}"
    else:
        return 0

    try:
        r = requests.get(url)
        if r.status_code == 200:
            dados = r.json()
            funded = dados.get("chain_stats", {}).get("funded_txo_sum", 0)
            spent = dados.get("chain_stats", {}).get("spent_txo_sum", 0)
            return (funded - spent) / 1e8
    except:
        pass
    return 0

# === Ler arquivo JSON ===
with open("dados.json", "r") as f:
    dados = json.load(f)

# === Processar cada carteira individualmente ===
for grupo in dados:
    for item in grupo:
        tipo = item["Type"]
        mnemonic = item["Mnemonic"]

        if is_electrum_seed(mnemonic):
            enderecos = derivar_enderecos_electrum(mnemonic)
            origem = "Electrum"
        elif Bip39MnemonicValidator(mnemonic).IsValid():
            enderecos = derivar_enderecos_bip(mnemonic, tipo)
            origem = "BIP39"
        else:
            print(f"\n❌ Seed inválida ou não reconhecida: ...{mnemonic[-30:]}")
            continue

        saldo_total_btc = sum(saldo_blockstream(addr, "btc") for addr in enderecos)
        saldo_total_liq = sum(saldo_blockstream(addr, "liquid") for addr in enderecos)

        print(f"\n🔐 Tipo: {tipo} ({origem})")
        print(f"📜 Final da seed: ...{mnemonic[-30:]}")
        print(f"   ➤ Saldo total on-chain: {saldo_total_btc:.8f} BTC")
        print(f"   ➤ Saldo total Liquid:   {saldo_total_liq:.8f} L-BTC")