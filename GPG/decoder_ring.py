"""
decoder_ring.py
╔══════════════════════════╗
║ ╔═╗┬─┐┌─┐┌─┐┬ ┬┌─┐┌┐┌┌─┐ ║
║ ║ ╦├┬┘├─┤├─┘├─┤├┤ │││├┤  ║
║ ╚═╝┴└─┴ ┴┴  ┴ ┴└─┘┘└┘└─┘ ║
║ ╔═╗┬ ┬┌┬┐┬ ┬┌─┐┌┐┌       ║
║ ╠═╝└┬┘ │ ├─┤│ ││││       ║
║ ╩   ┴  ┴ ┴ ┴└─┘┘└┘       ║
║ ╔═╗┌─┐┌┬┐┌─┐┬ ┬┌─┐┬ ┬    ║
║ ║ ╦├─┤ │ ├┤ │││├─┤└┬┘    ║
║ ╚═╝┴ ┴ ┴ └─┘└┴┘┴ ┴ ┴     ║
╚══════════════════════════╝

WTFPL litepresence.com Jan 2021

Wrapper for Pybitshares Memo ECDSA decoding
"""

# PYBITSHARES MODULES
from graphenebase import PrivateKey, PublicKey
from graphenebase.memo import decode_memo

# GRAPHENE PYTHON GATEWAY MODULES
from config import configure


# GLOBAL CONSTANTS
GATE = configure()["gate"]
TEST = configure()["test"]
PREFIX = configure()["gate"]["uia"]["chain"]["prefix"]


def ovaltine(memo, private_key):
    """
    Decode BitShares Transfer Memo
    """
    return (
        decode_memo(
            PrivateKey(private_key),  # associated with memo["to"] public key
            PublicKey(memo["from"], prefix=PREFIX),
            memo["nonce"],
            memo["message"],
        )
        .replace("\n", "")
        .replace(" ", "")
    )


def main(memo=None, private_key=None):
    """
    Sample memo to decode, should say "test"
    """
    if memo is None:
        memo = {
            "from": "BTS6upQe7xWa15Rj757Szygi8memj1PCGXugyC17WWZuKxkSJ1iW2",
            "to": "BTS7kFHKTgvVic1XqUBKRd4apAUwGqvLNpRuSR1DP4DkWDg64BLSG",
            "nonce": "407795228621064",
            "message": "9823e23c5c00e4880ce76d0aed5453de",
        }
    if private_key is None:
        private_key = GATE["uia"]["eos"]["issuer_private"]
    print("memo:         ", memo)
    print("decoded memo: ", ovaltine(memo, private_key))


if __name__ == "__main__":

    main()
