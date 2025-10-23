#!/usr/bin/env python3
"""
liquid_wallet_balance.py

Fluxo:
1) Recebe uma seed BIP-39 (ou uma mnemonic)
2) Deriva N endereços (BIP32 derivation path configurável)
3) Gera blinding key para cada endereço
4) Consulta a API da Blockstream Liquid para obter UTXOs/txs
5) Tenta desblindar saídas confidenciais (se libwally estiver instalado)
6) Soma e imprime saldo total (em satoshis e em LBTC)

OBS:
- Algumas funções dependem de bindings nativos (libwally). Sem eles,
  o script ainda derivará chaves e consultará a API, mas não conseguirá
  desblindar saídas confidenciais.
- Ajuste os nomes de módulos/URLs conforme necessário para sua instalação.
"""

import binascii
import hashlib
import hmac
import json
import math
import os
from typing import List, Dict, Tuple, Optional

import requests

# Bibliotecas para BIP39/BIP32/EC:
# pip install bip-utils coincurve mnemonic
try:
    from bip_utils import Bip39SeedGenerator, Bip39MnemonicValidator, Bip39MnemonicGenerator, Bip44, Bip44Coins, Bip44Changes
except Exception as e:
    raise RuntimeError("Instale 'bip_utils' (pip install bip-utils) para executar este script. Erro: " + str(e))

try:
    import coincurve  # para operações EC (secp256k1)
except Exception:
    coincurve = None

# Opcional: libwally / bindings Elements para desblindagem
# Tente importar wally (nome do pacote pode variar: wallycore, wally)
wally = None
try:
    import wallycore as wally  # alguns builds usam este nome
except Exception:
    try:
        import wally  # alternativa
    except Exception:
        wally = None

# ----------------------------
# Configurações (ajustáveis)
# ----------------------------
BLOCKSTREAM_LIQUID_API = "https://blockstream.info/liquid/api"  # verifique; pode ser a URL correta no seu ambiente
DERIVATION_PATH_TEMPLATE = "m/84'/0'/{account}'/0/{index}"  # Exemplo: BIP84-like (adapte para Liquid coin/method)
# Nota: Bip44Coins para Liquid não é oficialmente suportado em todas libs; usaremos derivação manual via bip_utils Bip44Coins.BITCOIN as placeholder.
COIN = Bip44Coins.BITCOIN  # substitua por implementação específica de Liquid se disponível
ACCOUNT = 0
START_INDEX = 0
NUM_ADDRESSES = 5

# Rede: 'liquid' ou 'testnet' (apenas para exibir)
NETWORK = "liquid"

# ----------------------------
# Utilitários criptográficos
# ----------------------------

def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """Retorna seed (bytes) a partir do mnemonic BIP39."""
    if not Bip39MnemonicValidator().IsValid(mnemonic):
        raise ValueError("Mnemonic inválido")
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase)
    return seed_bytes


def derive_bip32_keys_from_seed(seed_bytes: bytes, account: int, num_addresses: int, start_index: int = 0) -> List[Dict]:
    """
    Deriva chaves (privkey, pubkey, address) usando bip_utils (BIP84-like).
    Para Liquid você pode precisar ajustar coin/network na biblioteca que suporte Liquid. Aqui usamos Bitcoin as placeholder.
    """
    addresses = []
    # Usamos Bip44 (como exemplo); adapte se tiver suporte a Liquid na sua versão de bip_utils
    bip44_mst = Bip44.FromSeed(seed_bytes, COIN)
    # vamos iterar com caminho /0/index (change 0)
    for i in range(start_index, start_index + num_addresses):
        # derivação: account -> change 0 -> address index i
        bip44_acc = bip44_mst.Purpose().Coin().Account(account)
        bip44_chg = bip44_acc.Change(Bip44Changes.CHAIN_EXT)
        bip44_addr = bip44_chg.AddressIndex(i)
        addr = bip44_addr.PublicKey().ToAddress()
        priv = bip44_addr.PrivateKey().Raw().ToHex()
        pub = bip44_addr.PublicKey().RawCompressed().ToHex()
        addresses.append({
            "index": i,
            "address": addr,
            "privkey_hex": priv,
            "pubkey_hex": pub,
        })
    return addresses


def derive_blinding_key_from_privkey_hex(privkey_hex: str, info: bytes = b"liquid_blinding") -> str:
    """
    Deriva uma blinding key a partir da privkey por HMAC-SHA256 (padrão custom).
    Observação: muitas carteiras usam uma BIP32 path separada para blinding key; se você
    preferir esse método, adapte a função para derivar via BIP32.
    """
    priv = bytes.fromhex(privkey_hex)
    blinding = hmac.new(b"blinding_key_seed" + info, priv, hashlib.sha256).digest()
    return blinding.hex()


# ----------------------------
# Funções para API Blockstream
# ----------------------------

def blockstream_address_utxos(address: str) -> List[Dict]:
    """
    Retorna UTXOs para um endereço pela API Blockstream (Liquid).
    Endpoint esperado: /address/:address/utxo
    """
    url = f"{BLOCKSTREAM_LIQUID_API}/address/{address}/utxo"
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"Falha ao consultar UTXOs para {address}: {r.status_code} - {r.text}")
    return r.json()


def blockstream_address_txs(address: str) -> List[Dict]:
    """
    Lista transações de um endereço.
    Endpoint esperado: /address/:address/txs
    """
    url = f"{BLOCKSTREAM_LIQUID_API}/address/{address}/txs"
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"Falha ao consultar TXs para {address}: {r.status_code} - {r.text}")
    return r.json()


# ----------------------------
# Desblindagem (unblinding)
# ----------------------------

def try_unblind_output_with_wally(tx_hex: str, vout_index: int, blinding_privkey_hex: str) -> Optional[Dict]:
    """
    Tenta desblindar um output confidencial usando libwally (quando disponível).
    Retorna dicionário com {'value': satoshis, 'asset': asset_hex} se conseguiu,
    ou None se falhar/nao for confidencial.
    ---
    OBS: nomes de funções do wally variam entre bindings; este código é um padrão aproximado.
    Ajuste caso sua instalação wally apresente outras funções.
    """
    if wally is None:
        return None
    try:
        # Abaixo usamos uma sequência genérica de chamadas; verifique a API do binding wally no seu ambiente.
        # 1) converter tx hex para estrutura wally
        # 2) desvendar output vout com wally.confidential_tx_output_get_value? (API de exemplo)
        # Este é um esqueleto: substitua por chamadas reais à sua versão do wally.
        #
        # Exemplo conceptual (NÃO pode existir exatamente assim):
        # wtx = wally.tx_from_hex(tx_hex)
        # unblinded = wally.confidential_tx_unblind_output(wtx, vout_index, bytes.fromhex(blinding_privkey_hex))
        # return {'value': unblinded.value_satoshi, 'asset': unblinded.asset_hex}
        #
        # Como não posso checar os nomes exatos, lanço NotImplementedError indicando que você deve ajustar.
        raise NotImplementedError("Função de unblind com wally precisa ser ajustada para seu binding wally específico.")
    except Exception as e:
        print("Erro ao tentar unblind com wally:", e)
        return None


# ----------------------------
# Fluxo principal
# ----------------------------

def compute_wallet_balance_from_mnemonic(mnemonic: str, passphrase: str = "", num_addresses: int = 5, start_index: int = 0) -> Dict:
    """
    Deriva chaves, gera blinding keys, consulta a API e soma o saldo.
    Retorna dict com detalhamento.
    """
    seed = mnemonic_to_seed(mnemonic, passphrase)
    print("Seed gerada (hex):", seed.hex()[:64], "... (truncado)")

    derived = derive_bip32_keys_from_seed(seed, ACCOUNT, num_addresses, start_index)
    result = {
        "network": NETWORK,
        "addresses": [],
        "total_sats": 0,
        "total_lbtc": 0.0,
        "warnings": []
    }
    total_sats = 0

    for item in derived:
        addr = item["address"]
        priv = item["privkey_hex"]
        pub = item["pubkey_hex"]
        blind_key = derive_blinding_key_from_privkey_hex(priv)
        print(f"\nAddress idx {item['index']}: {addr}")
        print(f"  pub: {pub}")
        print(f"  priv (hex truncated): {priv[:10]}...{priv[-10:]}")
        print(f"  blinding_key (hex): {blind_key}")

        # Consulta UTXOs (Blockstream)
        try:
            utxos = blockstream_address_utxos(addr)
        except Exception as e:
            result["warnings"].append(f"Erro ao buscar UTXOs para {addr}: {e}")
            utxos = []

        addr_sats = 0
        utxo_details = []
        for u in utxos:
            # Estrutura esperada do Blockstream: { "txid": "...", "vout": n, "value": <int?>, ... }
            # Para Liquid, se output for confidencial, pode não existir campo 'value' (ou terá commit)
            txid = u.get("txid") or u.get("tx_hash") or u.get("txid")
            vout = u.get("vout") if "vout" in u else u.get("vout")
            value = u.get("value")  # pode ser None se confidencial
            is_confidential = False
            if value is None:
                # normalmente, ausência de 'value' indica conf.
                is_confidential = True

            unblinded_value = None
            asset = u.get("asset") or u.get("asset_id")
            # Tentar unblind quando possível
            if is_confidential:
                # precisamos do hex da tx para desblindar
                try:
                    tx_hex = requests.get(f"{BLOCKSTREAM_LIQUID_API}/tx/{txid}/hex", timeout=15).text
                except Exception as e:
                    result["warnings"].append(f"Não foi possível baixar tx hex {txid}: {e}")
                    tx_hex = None

                if tx_hex:
                    unbl = try_unblind_output_with_wally(tx_hex, vout, blind_key)
                    if unbl:
                        unblinded_value = unbl.get("value")
                        asset = unbl.get("asset", asset)
                    else:
                        result["warnings"].append(f"Falha ao desblindar output {txid}:{vout} (endereço {addr}). Instale e configure libwally/libwallybindings.")
            else:
                # output não confidencial, 'value' presente em satoshis
                if value is None:
                    # Alguns explorers para Liquid retornam 'value' como string ou 'value_commitment' etc.
                    # Se não existir, marque warning.
                    result["warnings"].append(f"UTXO {txid}:{vout} sem campo 'value' e não marcado confidencial.")
                else:
                    # garantimos inteiro
                    try:
                        unblinded_value = int(value)
                    except Exception:
                        # pode ser string: "0.0001" etc - converter se necessário
                        try:
                            # se veio em BTC-like string, multiplicar 1e8
                            unblinded_value = int(float(value) * 1e8)
                        except Exception:
                            unblinded_value = None
                            result["warnings"].append(f"Formato de value inesperado para {txid}:{vout} => {value}")

            if unblinded_value is not None:
                addr_sats += unblinded_value

            utxo_details.append({
                "txid": txid,
                "vout": vout,
                "confidential": is_confidential,
                "value_sats": unblinded_value,
                "asset": asset,
            })

        print(f"  UTXOs encontradas: {len(utxos)}  => sats conhecidos: {addr_sats}")
        total_sats += addr_sats

        result["addresses"].append({
            "index": item["index"],
            "address": addr,
            "pubkey": pub,
            "privkey_hex_trunc": priv[:6] + "..." + priv[-6:],
            "blinding_key_hex": blind_key,
            "utxos": utxo_details,
            "address_sats": addr_sats
        })

    result["total_sats"] = total_sats
    result["total_lbtc"] = total_sats / 1e8
    return result


# ----------------------------
# Interface CLI
# ----------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Deriva endereços Liquid de uma seed BIP39, tenta desblindar e soma saldo.")
    parser.add_argument("--mnemonic", "-m", required=False, help="mnemonic BIP39 (entre entre aspas) - se ausente, será gerada uma nova.", default=None)
    parser.add_argument("--num", "-n", type=int, default=NUM_ADDRESSES, help="Número de endereços a derivar")
    parser.add_argument("--start", "-s", type=int, default=START_INDEX, help="Índice inicial")
    parser.add_argument("--passphrase", "-p", default="", help="Passphrase BIP39 (opcional)")
    args = parser.parse_args()

    if args.mnemonic is None:
        # Gerar novo
        mn = Bip39MnemonicGenerator().FromWordsNumber(12)
        mnemonic = mn.ToStr()
        print("Nenhum mnemonic fornecido: gerando novo (ATENÇÃO: não use seed gerada aqui para fundos reais!).")
        print("mnemonic:", mnemonic)
    else:
        mnemonic = args.mnemonic

    res = compute_wallet_balance_from_mnemonic(mnemonic, args.passphrase, args.num, args.start)
    print("\n--- RESULTADO ---")
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
