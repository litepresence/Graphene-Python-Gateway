"""
gateway_state.py
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

Gateway State IPC

binary interprocess communication for address in use
[1,1,1,1,1,1] means there are 6 eos gateway addresses
[0,1,0,1,1,1] will mean addresses at index 0 and 2 are in use
allowing for concurrent on_get api server operations
on a finite number of accounts
"""
# STANDARD PYTHON MODULES
import time
from json import dumps as json_dumps
from multiprocessing import Process

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.utilities import json_ipc
from GPG.config import configure

# GLOBAL CONSTANTS
GATE = configure()["gate"]


def initialize_addresses(chain):
    """
    create the IPC file with a list of ones ie [1,1,1,...]
    the addresses are "all available" on startup.
    """
    doc = f"{chain}_gateway_state.txt"
    initial_state = [1 for _ in GATE[chain]]
    json_ipc(doc=doc, text=json_dumps(initial_state))


def lock_address(chain):
    """
    check the binary state of the gateway addresses
    if an address is available, switch its state to zero and return its index
    else return None
    """
    doc = f"{chain}_gateway_state.txt"
    gateway_idx = None
    gateway_state = json_ipc(doc=doc)
    for idx, state in enumerate(gateway_state):
        if state:
            gateway_idx = idx
            gateway_state[idx] = 0
            break
    json_ipc(doc=doc, text=json_dumps(gateway_state))

    return gateway_idx


def unlock_address_process(chain, idx, delay):
    """
    check the binary state of the gateway addresses
    reset the freed address state to 1
    """
    time.sleep(delay)
    doc = f"{chain}_gateway_state.txt"
    gateway_state = json_ipc(doc=doc)
    gateway_state[idx] = 1
    json_ipc(doc=doc, text=json_dumps(gateway_state))


def unlock_address(chain, idx, delay):
    """
    a process wrapper to delay unlocking an address
    """
    unlock = Process(target=unlock_address_process, args=(chain, idx, delay,))
    unlock.start()


def unit_test_gateway_state():
    """
    initialize the state machine with list of 1's
    claim two gateway addresses for deposit
    launch two supbrocesses to release the deposit addresses; on now another later
    check state, wait, check state again
    """
    print("\033c")
    print("\n\nunit test gateway deposit address state machine\n\n")
    initialize_addresses("xrp")
    print(json_ipc("xrp_gateway_state.txt"))
    print("\n\nlocking an xrp address\n")
    address_idx = lock_address("xrp")
    print("address index", address_idx)
    print(json_ipc("xrp_gateway_state.txt"))
    print("\n\nlocking another xrp address\n")
    address_idx = lock_address("xrp")
    print("address index", address_idx)
    print(json_ipc("xrp_gateway_state.txt"))
    print("\n\nlaunching subprocess unlocking xrp address 0 immediately\n\nAND")
    print("\nlaunching second subprocess unlocking xrp address 1 after 10 seconds\n")
    time.sleep(0.1)
    unlock_address("xrp", 0, 0)
    time.sleep(0.1)
    unlock_address("xrp", 1, 10)
    print(json_ipc("xrp_gateway_state.txt"))
    print("\n\nprimary process waiting 10 seconds\n")
    time.sleep(11)
    print(json_ipc("xrp_gateway_state.txt"))


if __name__ == "__main__":

    unit_test_gateway_state()
