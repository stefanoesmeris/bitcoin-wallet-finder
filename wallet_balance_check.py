import json
import requests
from bip_utils import (
    Bip39SeedGenerator, Bip39MnemonicValidator,
    Bip44, Bip49, Bip84,
    Bip44Coins, Bip49Coins, Bip84Coins,
    Bip44Changes
)

# === Funções auxiliares ===
def derivar_enderecos(mnemonic, tipo):
    #if not Bip39MnemonicValidator(mnemonic).IsValid():
    #    return []

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

        enderecos = derivar_enderecos(mnemonic, tipo)
        saldo_total_btc = sum(saldo_blockstream(addr, "btc") for addr in enderecos)
        saldo_total_liq = sum(saldo_blockstream(addr, "liquid") for addr in enderecos)

        print(f"\n🔐 Tipo: {tipo}")
        print(f"📜 Mnemonic: {mnemonic[:-30]}...")  # mostra só o início por segurança
        print(f"📜 Últimas palavras: {' '.join(mnemonic.split()[-3:])}")
        print(f"   ➤ Saldo total on-chain: {saldo_total_btc:.8f} BTC")
        print(f"   ➤ Saldo total Liquid:   {saldo_total_liq:.8f} L-BTC")