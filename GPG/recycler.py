"""
recycler.py
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

ensure all inbound funds are transfered to the zero index outbound account
"""

# STANDARD PYTHON MODULES
import time

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.config import configure
from GPG.signing_eosio import eos_transfer, eos_balance
from GPG.signing_ripple import xrp_transfer, xrp_balance
from GPG.utilities import it, timestamp, line_number

# GLOBAL CONSTANTS
NIL_EOS = 0.1
NIL_XRP = 20.1
GATE = configure()["gate"]
TEST = configure()["test"]


def recycler():
    """
    in a background process, check incoming accounts & move funds to outbound accounts
    """
    networks = ["eos", "xrp"]
    print(it("red", f"INITIALIZING RECYCLER\n"), "networks:", networks, "\n")
    while 1:
        for network in networks:
            order = {}
            # EOS specific parameters
            if network == "eos":
                nil = NIL_EOS
                get_balance = eos_balance
                transfer = eos_transfer
            # XRP specific parameters
            elif network == "xrp":
                nil = NIL_XRP
                get_balance = xrp_balance
                transfer = xrp_transfer
            # recycle gateway incoming transfers to the outbound account
            for idx, gate in enumerate(GATE[network]):
                if idx:
                    balance = get_balance(gate["public"])
                    if balance > nil:
                        timestamp()
                        line_number()
                        print(it("red", f"{network} RECYCLER"))
                        print(gate["public"], balance, "\n")
                        # finalize the order
                        order["private"] = gate["private"]
                        order["public"] = gate["public"]
                        order["to"] = GATE[network][0]["public"]
                        order["quantity"] = balance - nil
                        # serialize, sign, and broadcast
                        print(transfer(order), "\n")
        time.sleep(60)


def gateway_balances(network=None):
    """
    print gateway balances
    """
    if network in ["xrp", None]:
        for gate in GATE["xrp"]:
            print(
                f"Gateway XRP balance for",
                gate["public"].rjust(40),
                xrp_balance(gate["public"]),
            )
    if network in ["eos", None]:
        for gate in GATE["eos"]:
            print(
                f"Gateway EOS balance for",
                gate["public"].rjust(40),
                eos_balance(gate["public"]),
            )


def unit_test_recycler():
    """
    quick test of the definitions above
    """
    gateway_balances()
    input("press Enter to continue")
    gateway_balances()
    print("\n\nRECYCLING\n\n")
    recycler()
    gateway_balances()


if __name__ == "__main__":

    unit_test_recycler()
