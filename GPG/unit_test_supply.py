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

BitShares UIA Dynamic Supply
"""

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.listener_bitshares import rpc_get_objects
from GPG.utilities import wss_handshake
from GPG.config import configure

# GLOBAL CONSTANTS
GATE = configure()["gate"]


def unit_test_supply():
    """
    get_objects(1.3.x) # static asset objects
    get_objects(2.3.x) # dynamic asset objects
    """
    rpc = wss_handshake("")
    eos_object = rpc_get_objects(rpc, [GATE["uia"]["eos"]["asset_id"]])[0]
    eos_dynamic = rpc_get_objects(rpc, [GATE["uia"]["eos"]["dynamic_id"]])[0]
    xrp_object = rpc_get_objects(rpc, [GATE["uia"]["xrp"]["asset_id"]])[0]
    xrp_dynamic = rpc_get_objects(rpc, [GATE["uia"]["xrp"]["dynamic_id"]])[0]
    print(eos_object["symbol"])
    print(eos_dynamic["current_supply"])
    print(xrp_object["symbol"])
    print(xrp_dynamic["current_supply"])


if __name__ == "__main__":

    unit_test_supply()
