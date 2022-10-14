"""
signing_ripple.py
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

Ripple Transfer Operations and Account Balances
"""

# DISABLE SELECT PYLINT TESTS
# pylint: disable=broad-except

# STANDARD PYTHON MODULES
import time
import asyncio
from json import dumps as json_dumps

# THIRD PARTY MODULES
from requests import get

# ULAMLABS/AIOXRPY MODULES
from aioxrpy.definitions import RippleTransactionType, RippleTransactionFlags
from aioxrpy.keys import RippleKey
from aioxrpy.rpc import RippleJsonRpc

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.config import configure
from GPG.utilities import it, timestamp, line_number

# CONSTANTS
URL = "https://s1.ripple.com:51234/"
GATE = configure()["gate"]
TEST = configure()["test"]


def xrp_balance(account):
    """
    given a ripple public key return the xrp balance via request to public api
    """
    data = json_dumps(
        {
            "method": "account_info",
            "params": [
                {
                    "account": account,
                    "strict": True,
                    "ledger_index": "current",
                    "queue": True,
                }
            ],
        }
    )
    ret = get(URL, data=data).json()
    # print("\n\nreturned data:    ", ret)
    balance = 0
    try:
        # the response is in "ripple drops" we need to convert to xrp
        balance = float(ret["result"]["account_data"]["Balance"]) / 10 ** 6
        # print("\n\nBalance:    ", balance)
    except Exception as error:
        print("\n\nError:   ", error, "\n")
    return balance


async def xrp_transfer_execute(order):
    """
    using ulamlabs/aioxrpy
    given a simplified order dict with keys: [from, to, quantity]
    serialize and sign client side locally
    broadcast the xrp transfer to the ripple public api server
    """
    master = RippleKey(private_key=order["private"])
    rpc = RippleJsonRpc(URL)
    # reserve = await rpc.get_reserve()
    fee = await rpc.fee()

    trx = {
        "Account": master.to_account(),
        "Flags": RippleTransactionFlags.FullyCanonicalSig,
        "TransactionType": RippleTransactionType.Payment,
        "Amount": int(order["quantity"] * 10 ** 6),  # conversion to ripple "drops"
        "Destination": order["to"],
        "Fee": fee.minimum,
    }
    return await rpc.sign_and_submit(trx, master)


def xrp_transfer(order):
    """
    pretty wrap the asyncio xrp transfer
    """
    # FIXME log this event
    timestamp()
    line_number()
    print("\nORDER\n\n", {k: v for k, v in order.items() if k != "private"}, "\n")
    event = asyncio.get_event_loop().run_until_complete(xrp_transfer_execute(order))
    print(it("red", "XRP TRANSFERRED"))
    return event


def unit_test_xrp_transfer():
    """
    UNIT TEST

    given the first two accounts in the configuration file
    send 1 xrp 3 times from first ripple account to second ripple account
    """
    print("\033c")

    xrp_balance(TEST["xrp"]["public"])
    xrp_balance(GATE["xrp"][1]["public"])

    order = {
        "public": TEST["xrp"]["public"],
        "private": TEST["xrp"]["private"],
        "to": GATE["xrp"][1]["public"],
        "quantity": 10,
    }

    print(xrp_transfer(order), "\n")
    time.sleep(5)

    xrp_balance(TEST["xrp"]["public"])
    xrp_balance(GATE["xrp"][1]["public"])


if __name__ == "__main__":

    unit_test_xrp_transfer()
