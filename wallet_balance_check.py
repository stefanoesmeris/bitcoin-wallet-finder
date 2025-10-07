import json
import requests
from general_functions import General_Functions as GF

from bip_utils import (
    Bip39SeedGenerator, Bip39MnemonicValidator,
    Bip44, Bip49, Bip84,
    Bip44Coins, Bip49Coins, Bip84Coins,
    Bip44Changes, Bip44Levels, Bip44DepthError, Bip32Slip10Secp256k1, P2PKHAddr
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


#from bip_utils import Bip39SeedGenerator, Bip39MnemonicValidator, Bip32Slip10Secp256k1, P2pkhAddr

def derivar_enderecos_liquid(mnemonic):
    #if not Bip39MnemonicValidator(mnemonic).IsValid():
    #    return []

    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip32_ctx = Bip32Slip10Secp256k1.FromSeed(seed_bytes)

    enderecos = []
    for i in range(20):
        path = f"m/44'/1776'/0'/0/{i}"
        chave = bip32_ctx.DerivePath(path)
        endereco = P2PKHAddr.EncodeKey(chave.PublicKey())
        enderecos.append(endereco)

    return enderecos


#def derivar_enderecos_liquid(mnemonic):
    #if not Bip39MnemonicValidator(mnemonic).IsValid():
    #    return []

#    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    # Derivação manual: m/44'/1776'/0'/0/i
#    base_path = "m/44'/1776'/0'/0"
#    bip = Bip44.FromSeedAndPath(seed_bytes, base_path)
#
#    try:
#        carteira = bip.Account(0).Change(Bip44Changes.CHAIN_EXT)
#        return [carteira.AddressIndex(i).PublicKey().ToAddress() for i in range(20)]
#    except Bip44DepthError:
#        return []

# === Ler arquivo JSON ===
with open("dados.json", "r") as f:
    dados = json.load(f)

# === Processar cada carteira individualmente ===
for grupo in dados:
    for item in grupo:
        tipo = item["Type"]
        mnemonic = item["Mnemonic"]

        enderecos = derivar_enderecos(mnemonic, tipo)
        saldo_total_btc = sum(GF.saldo_blockstream(GF, addr, "btc") for addr in enderecos)
        #enderecos = derivar_enderecos_liquid(mnemonic)
        #saldo_total_liq = sum(GF.saldo_blockstream(GF, addr, "liquid") for addr in enderecos)

        print(f"\n🔐 Tipo: {tipo}")
        #print(f"📜 Mnemonic: {mnemonic[:-30]}...")  # mostra só o início por segurança
        print(f"📜 Últimas palavras: {' '.join(mnemonic.split()[-3:])}")
        if saldo_total_btc > 0:
            print(f"  ✅ Saldo total on-chain: {saldo_total_btc:.8f} BTC")
        else:
            print(f"   ➤ Saldo total on-chain: {saldo_total_btc:.8f} BTC")
        #if saldo_total_liq > 0:
        #    print(f"  ✅ Saldo total Liquid:   {saldo_total_liq:.8f} L-BTC")
        #else:          
        #    print(f"   ➤ Saldo total Liquid:   {saldo_total_liq:.8f} L-BTC")
#