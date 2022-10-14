"""
signing_eosio.py
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

Eosio Transfer Operations and Account Balances
"""

# DISABLE SELECT PYLINT TESTS
# pylint: disable=broad-except

# STANDARD PYTHON MODULES
import traceback
from statistics import mode
from json import dumps as json_dumps
from json import loads as json_loads

# THIRD PARTY MODULES
from requests import post

# EOSIOPY MODULES
from eosiopy.eosioparams import EosioParams
from eosiopy.nodenetwork import NodeNetwork
from eosiopy.rawinputparams import RawinputParams
from eosiopy import eosio_config

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.nodes import eosio_nodes
from GPG.utilities import it, precisely, timestamp, line_number
from GPG.config import configure

# CONSTANTS
KEYS = configure()
GATE = configure()["gate"]
TEST = configure()["test"]


def eos_balance(account):
    """
    eosio public api consensus of EOS balance
    """
    nodes = eosio_nodes()
    params = {"code": "eosio.token", "account": account, "symbol": "EOS"}
    mavens = []
    # print(params)
    while 1:
        nodes.append(nodes.pop(0))
        node = nodes[0]
        mavens = mavens[-len(nodes) :]
        try:
            url = f"{node}/v1/chain/get_currency_balance"
            data = json_dumps(params)
            ret = post(url, data=data, timeout=2).json()
            balance_data = json_dumps(ret)
            # print(balance_data)
            mavens.append(balance_data)
        except Exception:
            traceback.format_exc()
        if len(mavens) > 4:
            try:
                mode_balance = json_loads(mode(mavens))
                return float(mode_balance[0].split(" ")[0])
            except Exception:
                pass


def eos_transfer(order):
    """
    serialize, sign, and broadcast an order dictionary with nine keys
    """
    # FIXME log this event
    timestamp()
    line_number()
    print("\nORDER\n\n", {k: v for k, v in order.items() if k != "private"}, "\n")
    nodes = eosio_nodes()
    while 1:
        nodes.append(nodes.pop(0))
        node = nodes[0]
        # configure the url and port
        eosio_config.url = node
        eosio_config.port = ""
        print("\nADDRESS\n\n", node, "\n")
        # assemble the transfer operation dictionary
        operation = {
            "from": order["public"],
            "memo": "",
            # eos must have 4 decimal places formatted as string with space and "EOS"
            "quantity": precisely(order["quantity"], 4) + " EOS",
            "to": order["to"],
        }
        print("\nOPERATION\n\n", operation, "\n")
        # serialize the transfer operation
        raw = RawinputParams(
            "transfer",  # the operation type
            operation,  # the parameters
            "eosio.token",  # the contract; for our purposes always "eosio.token"
            order["public"] + "@active",  # the permitted party (or @owner)
        )
        print("\nSERIALIZE\n\n", raw.params_actions_list, "\n")
        # sign the transfer operation
        params = EosioParams(raw.params_actions_list, order["private"])
        print("\nSIGN\n\n", params.trx_json, "\n")
        # broadcast the transfer to the network
        try:
            ret = NodeNetwork.push_transaction(params.trx_json)
            print("\nBROADCAST\n\n", ret)
            if "processed" not in ret.keys():
                raise ValueError("NOT PROCESSED")
            print(it("red", "EOS TRANSFERRED"))
            break
        except Exception as error:
            print(error)
            print(it("red", "BROADCAST FAILED"), node, "attempting new api...")
            continue
    return ret


def unit_test_eos_transfer():
    """
    UNIT TEST demo transfer
    """
    try:
        order = {
            "private": TEST["eos"]["private"],
            "public": TEST["eos"]["public"],
            "to": GATE["eos"][1]["public"],
            "quantity": 0.0001,
        }

        # serialize, sign, and broadcast
        eos_transfer(order)
    except Exception:
        print(traceback.format_exc())


if __name__ == "__main__":

    unit_test_eos_transfer()
