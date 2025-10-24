from flask import Flask, request, jsonify, render_template, redirect, url_for
from models import db, Wallet
import qrcode
import io
import base64
import json

'''
wallet_app/
├── app.py                  # Servidor Flask principal
├── models.py               # Definição do modelo Wallet e banco de dados
├── templates/
│   └── viewer.html         # Template HTML para visualização com QR Code
└── static/
    └── style.css           # Estilos opcionais
    
pip install flask flask_sqlalchemy qrcode[pil]    
'''

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wallets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

wallet_index = 0

def generate_qr_code(data):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")
    
'''
def generate_qr_code(wallet):
    type_map = {
        "SegWit (BIP84)": "HDsegwitBech32",
        "Legacy (BIP44)": "HDlegacy",
        "P2SH (BIP49)": "HDsegwitP2SH"
    }

    qr_payload = {
        "type": type_map.get(wallet.Type, "HDsegwitBech32"),
        "label": f"Wallet {wallet.Address[:6]}",
        "mnemonic": wallet.Mnemonic,
        "passphrase": "",
        "network": "mainnet"
    }

    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(json.dumps(qr_payload))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")
'''


@app.route('/wallets', methods=['POST'])
def add_wallets():
    data = request.get_json()
    added = 0
    for group in data:
        for item in group:
            if Wallet.query.get(item['Address']):
                continue
            wallet = Wallet(**item)
            db.session.add(wallet)
            added += 1
    db.session.commit()
    return jsonify({'message': f'{added} wallet(s) added successfully.'})

@app.route('/wallets', methods=['GET'])
def get_wallets():
    wallets = Wallet.query.all()
    result = [{
        'Type': w.Type,
        'Address': w.Address,
        'Path': w.Path,
        'Status': w.Status,
        'Mnemonic': w.Mnemonic
    } for w in wallets]
    return jsonify(result)

@app.route("/", methods=["GET"])
def wallet_viewer():
    global wallet_index
    wallets = Wallet.query.all()
    total_wallets = len(wallets)

    if total_wallets == 0:
        return "<h2>Nenhuma carteira disponível</h2>"

    wallet = wallets[wallet_index]
    qr_code = generate_qr_code(wallet.mnemonic)

    return render_template(
        "viewer.html",
        wallet=wallet,
        qr_code=qr_code,
        total_wallets=total_wallets,
        current_index=wallet_index + 1  # para exibir como 1-based
    )
@app.route("/navigate/<direction>", methods=["POST"])
def navigate_wallet(direction):
    global wallet_index
    wallets = Wallet.query.all()
    if not wallets:
        return redirect(url_for("wallet_viewer"))

    if direction == "next":
        wallet_index = (wallet_index + 1) % len(wallets)
    elif direction == "prev":
        wallet_index = (wallet_index - 1) % len(wallets)

    return redirect(url_for("wallet_viewer"))

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=80, debug=True)



