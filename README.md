A simple script that attempts to discover a Bitcoin wallet through guesswork.
It generates a seed phase and checks whether any transactions have been made.
If any transactions have been made, it is considered an interesting wallet.

Usage: python3 main.py --N 0 --U http://your.api.here:8080/rest-api

--N - can be 0 for random, or 12, 15, 18, 21 or 24 to serialized search
--U - URL to store a good seeds if was found
