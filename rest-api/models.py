from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Wallet(db.Model):
    __tablename__ = 'wallets'
    Address = db.Column(db.String, primary_key=True)
    Type = db.Column(db.String)
    Path = db.Column(db.String)
    Status = db.Column(db.String)
    Mnemonic = db.Column(db.String)
