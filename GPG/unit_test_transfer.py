"""
unit_test_transfer.py
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

Get balances and transfer xrp and eos
"""

# STANDARD PYTHON MODULES
import time

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.signing_ripple import xrp_transfer, xrp_balance
from GPG.signing_eosio import eos_transfer, eos_balance
from GPG.config import configure

# GLOBAL CONSTANTS
GATE = configure()["gate"]
TEST = configure()["test"]


def balances(network):
    """
    eos and xrp account balance
    """
    if network == "eos":
        get_balance = eos_balance
    elif network == "xrp":
        get_balance = xrp_balance

    address = TEST[network]["public"]
    print(address, get_balance(address))
    for idx, _ in enumerate(GATE[network]):
        address = GATE[network][idx]["public"]
        print(address, get_balance(address))


def test_transfer(network):
    """
    print balances, transfer dust, print balances again
    """
    print("\033c")
    balances(network)
    order = {
        "to": GATE[network][1]["public"],
        "quantity": 0.1,
        "public": GATE[network][0]["public"],
        "private": GATE[network][0]["private"],
    }

    print(order)
    if network == "xrp":
        print(xrp_transfer(order))
    elif network == "eos":
        print(eos_transfer(order))
    time.sleep(5)
    balances(network)


def refill_test_account(network):
    """
    print balances, transfer dust, print balances again
    """
    print("\033c")
    balances(network)
    order = {
        "to": TEST[network]["public"],
        "quantity": 2,
        "public": GATE[network][0]["public"],
        "private": GATE[network][0]["private"],
    }

    print({k: v for k, v in order.items() if k != "private"})
    if network == "xrp":
        print(xrp_transfer(order))
    elif network == "eos":
        print(eos_transfer(order))
    time.sleep(5)
    balances(network)


def unit_test_transfer():
    """
    Enter 1 to refill test account or 2 to unit test
    """
    print("\033c")
    choice = int(input(unit_test_transfer.__doc__))
    dispatch = {
        1: refill_test_account(input("Enter XRP or EOS to refill\n\n   ").lower()),
        2: test_transfer(input("Enter XRP or EOS to test transfer\n\n   ").lower()),
    }
    dispatch[choice]  # pylint: disable=pointless-statement


if __name__ == "__main__":

    unit_test_transfer()
