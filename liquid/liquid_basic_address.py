#!/usr/bin/env python3
"""
Gera endereços bech32 (P2WPKH) a partir de uma seed phrase BIP39.
HRP padrão configurado para "l1q" (troque se necessário).

Dependências:
pip install mnemonic bip32 bech32 ecdsa
"""

from mnemonic import Mnemonic
from bip32 import BIP32
from hashlib import sha256, new as hashlib_new
from bech32 import bech32_encode, convertbits
import binascii

# ---------- Configurações ----------
HRP = "l1q"                     # Human Readable Part do bech32 (ajuste se necessário)
DERIVATION_TEMPLATE = "m/84'/0'/0'/0/{}"  # padrão BIP84 - troque coin_type (0) se precisar
ADDRESS_COUNT = 5               # quantos endereços gerar
START_INDEX = 0                 # índice inicial
PASSPHRASE = ""                 # passphrase BIP39 se houver
# -----------------------------------

def mnemonic_to_seed(mnemonic_phrase: str, passphrase: str = "") -> bytes:
    m = Mnemonic("english")
    return m.to_seed(mnemonic_phrase, passphrase=passphrase)

def hash160(data: bytes) -> bytes:
    """RIPEMD160(SHA256(data))"""
    sha = sha256(data).digest()
    rip = hashlib_new('ripemd160', sha).digest()
    return rip

def pubkey_to_p2wpkh_bech32(pubkey_bytes: bytes, hrp: str) -> str:
    """
    Recebe pubkey comprimida (33 bytes) -> P2WPKH witness program (20 bytes) -> bech32 address.
    Usa witness version 0.
    """
    witprog = hash160(pubkey_bytes)  # 20 bytes
    # convert to 5-bit groups
    data = [0] + convertbits(witprog, 8, 5)
    return bech32_encode(hrp, data)

def derive_pubkey_from_path(seed: bytes, path: str) -> bytes:
    """
    Usa a biblioteca bip32 para derivar a chave pública comprimida de um caminho BIP32.
    path: string ex: "m/84'/0'/0'/0/0"
    Retorna pubkey comprimida (bytes).
    """
    bip32 = BIP32.from_seed(seed)
    # A biblioteca bip32 aceita caminho em formato string em get_pubkey_from_path
    # Alguns forks pedem lista; se der erro, converta a lista de índices.
    try:
        pub = bip32.get_pubkey_from_path(path)
        return pub
    except Exception as e:
        # fallback: tentar obter via método get_pubkey_from_path com lista (depende da versão)
        # converte "m/84'/0'/0'/0/0" em lista de ints com derivação hardened adicionando 2**31
        comps = path.strip().split('/')[1:]
        idxs = []
        for c in comps:
            if c.endswith("'") or c.endswith("h"):
                idxs.append(int(c[:-1]) + 0x80000000)
            else:
                idxs.append(int(c))
        pub = bip32.get_pubkey_from_path(idxs)
        return pub

def generate_addresses(mnemonic_phrase: str, hrp: str = HRP, start: int = START_INDEX, count: int = ADDRESS_COUNT, derivation_template: str = DERIVATION_TEMPLATE, passphrase: str = PASSPHRASE):
    seed = mnemonic_to_seed(mnemonic_phrase, passphrase)
    addresses = []
    for i in range(start, start + count):
        path = derivation_template.format(i)
        pubkey = derive_pubkey_from_path(seed, path)
        # pubkey pode vir em hex; garantimos bytes
        if isinstance(pubkey, str):
            pubkey = binascii.unhexlify(pubkey)
        addr = pubkey_to_p2wpkh_bech32(pubkey, hrp)
        addresses.append((path, addr))
    return addresses

if __name__ == "__main__":
    import getpass, argparse, sys

    parser = argparse.ArgumentParser(description="Gerar endereços Liquid (bech32) a partir de seed phrase BIP39")
    parser.add_argument("--mnemonic", "-m", help="seed phrase (entre aspas) — se omitida será pedida interativamente")
    parser.add_argument("--hrp", default=HRP, help=f"HRP bech32 (default: {HRP})")
    parser.add_argument("--start", type=int, default=START_INDEX)
    parser.add_argument("--count", type=int, default=ADDRESS_COUNT)
    parser.add_argument("--path", default=DERIVATION_TEMPLATE, help=f"Template de derivação com {{}} para índice (default: {DERIVATION_TEMPLATE})")
    parser.add_argument("--passphrase", "-p", help="passphrase BIP39 (opcional)")
    args = parser.parse_args()

    if not args.mnemonic:
        # pedir de forma oculta
        mnemonic = getpass.getpass("Digite sua seed phrase BIP39 (input oculto): ").strip()
    else:
        mnemonic = args.mnemonic.strip()

    passphrase = args.passphrase if args.passphrase is not None else ""
    try:
        addrs = generate_addresses(mnemonic, hrp=args.hrp, start=args.start, count=args.count, derivation_template=args.path, passphrase=passphrase)
        print("Derivação concluída:")
        for p, a in addrs:
            print(f"{p} -> {a}")
    except Exception as exc:
        print("Erro ao gerar endereços:", exc, file=sys.stderr)
        print("Dica: verifique se instalou as dependências: mnemonic bip32 bech32 ecdsa", file=sys.stderr)
