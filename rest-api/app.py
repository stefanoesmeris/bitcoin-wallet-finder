from flask import Flask, request, jsonify
from models import db, Wallet

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wallets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/wallets', methods=['POST'])
def add_wallets():
    data = request.get_json()
    added = 0
    for group in data:
        for item in group:
            if Wallet.query.get(item['Address']):
                continue  # Ignora duplicatas
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)


