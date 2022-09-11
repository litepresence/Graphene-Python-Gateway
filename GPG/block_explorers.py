"""
block_explorers.py
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

Open 3rd party block explorers in web browser for all pertinent accounts
"""


# STANDARD PYTHON MODULES
from webbrowser import open as browse

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.config import configure

# GLOBAL CONSTANTS
GATE = configure()["gate"]
TEST = configure()["test"]
BITSHARES_EXPLORER = "http://www.cryptofresh.com/u/"
RIPPLE_EXPLORER = "http://www.bithomp.com/explorer/"
EOSIO_EXPLORER = "http://www.eosflare.io/account/"


def block_explorers():
    """
    use system browser to open block explorers
    """
    print("opening block explorers for client test accounts...")
    for coin, account in TEST.items():
        if coin == "bts":
            browse(BITSHARES_EXPLORER + account["public"], 1)  # 1 = open a new window
        elif coin == "xrp":
            browse(RIPPLE_EXPLORER + account["public"], 2)  # 2 = open a new tab
        elif coin == "eos":
            browse(EOSIO_EXPLORER + account["public"], 2)
    print("opening block explorers for ripple gateway deposit accounts...")
    for idx, account in enumerate(GATE["xrp"]):
        browse(RIPPLE_EXPLORER + account["public"], int(bool(idx)) + 1)
    print("opening block explorers for eosio gateway deposit accounts...")
    for idx, account in enumerate(GATE["eos"]):
        browse(EOSIO_EXPLORER + account["public"], int(bool(idx)) + 1)
    print("opening block explorers for bitshares asset issuer accounts...")
    browse(BITSHARES_EXPLORER + GATE["uia"]["eos"]["issuer_public"], 1)
    browse(BITSHARES_EXPLORER + GATE["uia"]["xrp"]["issuer_public"], 2)
    print("done")


if __name__ == "__main__":

    block_explorers()
