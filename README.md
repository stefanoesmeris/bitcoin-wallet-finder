A simple script that attempts to discover a Bitcoin wallet through guesswork.
It generates a seed phase and checks whether any transactions have been made.
If any transactions have been made, it is considered an interesting wallet.

Usage: python3 main.py --N 0 --U http://your.api.here:8080/rest-api

--N - can be 0 for random, or 12, 15, 18, 21 or 24 to serialized search

--U - URL to store a good seeds if was found

The values --U and --N can informed once time, after this it's stored in a local file "setup.json"
Use these args again if you want update them.

git clone https://github.com/stefanoesmeris/bitcoin-wallet-finder.git

pip3 install bip-utils requests mnemonic
