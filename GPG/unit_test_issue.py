"""
unit_test_issue.py
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

Unit Test BitShares:

ISSUE asset to TEST client
TRANSFER asset back to GATE
RESERVE asset
"""

# GRAPHENE PYTHON GATEWAY MODULES
from signing_bitshares import broker
from nodes import bitshares_nodes
from config import configure


AMOUNT = 1  # must be integer during testing due to precision of test uia
GATE = configure()["gate"]
TEST = configure()["test"]


def unit_test_issue(network):
    """
    print chain state
    issue, transfer, reserve a BitShares UIA
    print chain state again
    """
    gate_header = {
        "asset_id": GATE["uia"][network]["asset_id"],
        "asset_precision": GATE["uia"][network]["asset_precision"],
        # gate account details
        "account_id": GATE["uia"][network]["issuer_id"],
        "account_name": GATE["uia"][network]["issuer_public"],
        "wif": GATE["uia"][network]["issuer_private"],
    }
    test_header = {
        "asset_id": GATE["uia"][network]["asset_id"],
        "asset_precision": GATE["uia"][network]["asset_precision"],
        # test account details
        "account_id": TEST["bts"]["id"],
        "account_name": TEST["bts"]["public"],
        "wif": TEST["bts"]["private"],
    }
    order = {"nodes": bitshares_nodes()}
    # login to accounts
    order["edicts"] = [{"op": "login"}]
    order["header"] = test_header
    print("Log In", order["header"]["account_name"], broker(order), "\n\n")
    order["header"] = gate_header
    print("Log In", order["header"]["account_name"], broker(order), "\n\n")
    # issue asset
    order["edicts"] = [
        {
            "op": "issue",
            "amount": AMOUNT,
            "account_id": test_header["account_id"],
            "memo": "",
        }
    ]
    print({k: v for k, v in order["header"].items() if k != "wif"})
    print("Issue Asset", order["edicts"], broker(order), "\n\n")
    # transfer
    order["header"] = test_header
    order["edicts"] = [
        {
            "op": "transfer",
            "amount": AMOUNT,
            "account_id": gate_header["account_id"],
            "memo": "",
        }
    ]
    print({k: v for k, v in order["header"].items() if k != "wif"})
    print("Transfer Asset", order["edicts"], broker(order), "\n\n")
    # reserve asset
    order["header"] = gate_header
    order["edicts"] = [{"op": "reserve", "amount": AMOUNT}]
    print({k: v for k, v in order["header"].items() if k != "wif"})
    print("Reserve Asset", order["edicts"], broker(order), "\n\n")


def refill_test_account():
    """
    manually add uia funds to continue testing
    """
    networks = ["xrp", "eos"]
    for network in networks:
        order = {"nodes": bitshares_nodes()}
        order["header"] = {
            "asset_id": GATE["uia"][network]["asset_id"],
            "asset_precision": GATE["uia"][network]["asset_precision"],
            # gate account details
            "account_id": GATE["uia"][network]["issuer_id"],
            "account_name": GATE["uia"][network]["issuer_public"],
            "wif": GATE["uia"][network]["issuer_private"],
        }
        order["edicts"] = [
            {"op": "issue", "amount": 100, "account_id": TEST["bts"]["id"], "memo": "",}
        ]
        print({k: v for k, v in order["header"].items() if k != "wif"})
        print("Issue Asset", order["edicts"], broker(order), "\n\n")


def main():
    """
    Enter 1 to refill test account or 2 to unit test
    """
    choice = int(input(main.__doc__))
    dispatch = {
        1: refill_test_account(),
        2: unit_test_issue(
            input(
                "Enter XRP or EOS to unit test Bitshares UIA Issue, "
                + "Transfer, and Reserve"
            ).lower()
        ),
    }
    dispatch[choice]  # ignore pointless-statement


if __name__ == "__main__":

    main()
