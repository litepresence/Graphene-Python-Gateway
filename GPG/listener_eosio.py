"""
listener_eosio.py
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

EOSIO Block Ops Listener

triggers:

    issue UIA upon deposited foreign coin
    reserve UIA upon confirmed withdrawal
"""

# DISABLE SELECT PYLINT TESTS
# pylint: disable=too-many-locals, too-many-nested-blocks, broad-except
# pylint: disable=bad-continuation, too-many-branches, too-many-statements

# REFERENCE
# https://github.com/eosmoto/eosiopy
# https://eosnodes.privex.io/?config=1
# https://developers.eos.io/welcome/latest/index
# https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin
#     /api-reference/index#operation/get_info << latest block numbern
#     /api-reference/index#operation/get_block  << transactions on a block
#     /api-reference/index#operation/get_block_header_state   << confirmations
# {protocol}://{host}:{port}/v1/chain/get_block_header_state

# STANDARD PYTHON MODULES
from multiprocessing import Process, Manager, Value
from json import dumps as json_dumps
from ctypes import c_wchar_p
import traceback
import time

# THIRD PARTY MODULES
from requests import post

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.nodes import eosio_nodes
from GPG.config import configure
from GPG.signing_bitshares import issue, reserve
from GPG.gateway_state import unlock_address
from GPG.utilities import it, timestamp, line_number

# GLOBAL CONSTANTS
GATE = configure()["gate"]
DEPOSIT_TIMEOUT = 1800
DEPOSIT_PAUSE = 600
POST_TIMEOUT = 5
MAVENS = min(5, len(eosio_nodes()))
NODE = eosio_nodes()[-1]
DEV = False  # fast forward past irr block and print every transfer


def get_irreversible_block():
    """
    no frills get current block number
    """
    url = f"{NODE}/v1/chain/get_info"
    ret = post(url, timeout=POST_TIMEOUT).json()
    return ret["last_irreversible_block_num"]


def get_block(block_num, blocks_pipe):
    """
    return the block data via multiprocessing Value pipe
    """
    url = f"{NODE}/v1/chain/get_block"
    data = json_dumps({"block_num_or_id": str(block_num)})
    ret = post(url, data=data, timeout=POST_TIMEOUT).json()
    blocks_pipe[block_num].value = ret


def verify_eosio_account(account_name):
    """
    eosio public api consensus of get_account() returns True or False on existance
    :param str(account_name): eosio 12 character account name
    """
    url = f"{NODE}/v1/chain/get_account"
    params = {"account_name": str(account_name)}
    data = json_dumps(params)
    ret = post(url, data=data, timeout=POST_TIMEOUT).json()
    return "created" in ret.keys()


def listener_eosio(
    account_idx=0, amount=None, issuer_action=None, client_id=None, nonce=0
):
    """
    for every block from initialized until detected
        check for transaction to the gateway
            issue or reserve uia upon receipt of gateway transfer

    :param int(account_idx) # from gateway_state.py
    :param float(amount)
    :param str(issuer_action) # None in unit test case
    :param str(client_id) #1.2.X
    :return None:
    """
    gateway = GATE["eos"][account_idx]["public"]
    uia = GATE["uia"]["eos"]["asset_name"]
    start_block_num = get_irreversible_block()
    checked_blocks = [start_block_num]
    print("Start Block:", start_block_num, "\n")
    # block["transactions"][0]["trx"]["transaction"]["actions"][0] holds:
    #   ["name"] # str("transfer") etc.
    #   ["data"] # dict.keys() [to, from, quantity]
    start = time.time()
    while 1:
        elapsed = time.time() - start
        if elapsed > DEPOSIT_TIMEOUT:
            print(
                f"nonce {nonce}",
                it("red", f"{nonce} EOS GATEWAY TIMEOUT"),
                gateway,
                "\n",
            )
            # 10 minutes after timeout, release the address
            if issuer_action == "issue":
                unlock_address("eos", account_idx, DEPOSIT_PAUSE)
            break
        # get the latest irreversible block number
        current_block = get_irreversible_block()
        # get the latest block number we checked
        max_checked_block = max(checked_blocks)
        # if there are any new irreversible blocks
        if current_block > max_checked_block + 1:
            new_blocks = range(max_checked_block + 1, current_block)
            # eosio has a 0.5 second block time, to prevail over network latency:
            # *concurrently* fetch all new blocks
            block_processes = {}  # dictionary of multiprocessing "Process" events
            blocks_pipe = {}  # dictionary of multiprocessing "Value" pipes
            # spawn multpiple processes to gather the "new" blocks
            for block_num in new_blocks:
                manager = Manager()
                blocks_pipe[block_num] = manager.Value(c_wchar_p, "")
                block_processes[block_num] = Process(
                    target=get_block, args=(block_num, blocks_pipe,)
                )
                block_processes[block_num].start()
            # join all subprocess back to main process; wait for all to finish
            for block_num in new_blocks:
                block_processes[block_num].join()
            # extract the blocks from each "Value" in blocks_pipe
            blocks = {block_num: block.value for block_num, block in blocks_pipe.items()}
            # with new cache of blocks, check every block from last check till now
            for block_num in new_blocks:
                print(
                    f"nonce {nonce}",
                    it("purple", "Eosio Irreversible Block"),
                    it("yellow", block_num),
                    time.ctime()[11:19],
                    it("purple", int(time.time())),
                    "\n",
                )
                # get each new irreversible block
                block = blocks[block_num]
                transactions = []
                try:
                    transactions = block["transactions"]
                except Exception:
                    pass
                # iterate through all transactions in the list of transactions
                for trx in transactions:
                    actions = []
                    try:
                        actions = trx["trx"]["transaction"]["actions"]
                    except Exception:
                        pass
                    # if there are any, iterate through the actions
                    for action in actions:
                        try:
                            # sort by tranfer ops
                            if (
                                action["name"] == "transfer"
                                # SECURITY: ensure it is the correct contract!!!
                                and action["account"] == "eosio.token"
                            ):
                                # extract transfer op data
                                qty = action["data"]["quantity"]
                                trx_asset = qty.split(" ")[1].upper()
                                trx_amount = float(qty.split(" ")[0])
                                # sort again by > nil amount of eos
                                if trx_amount > 0.0001 and trx_asset == "EOS":
                                    # during unit testing
                                    # if issuer_action is None:
                                    if DEV:
                                        print(f"nonce {nonce}", block_num, action, "\n")
                                    trx_to = action["data"]["to"]
                                    trx_from = action["data"]["from"]
                                    # if there are any transfers listed
                                    if gateway in [trx_from, trx_to]:
                                        timestamp()
                                        line_number()
                                        print(
                                            f"nonce {nonce}",
                                            it("red", "GATEWAY TRANSFER DETECTED\n"),
                                            f"amount {trx_amount} {trx_asset}\n",
                                            f"from {trx_from}\n",
                                            f"to {trx_to}\n",
                                        )

                                        # issue UIA to client_id
                                        # upon receipt of their foreign funds
                                        if (
                                            issuer_action == "issue"
                                            and trx_to == gateway
                                        ):
                                            print(
                                                f"nonce {nonce}",
                                                it(
                                                    "red",
                                                    f"ISSUING {trx_amount} {uia} to "
                                                    + f"{client_id}\n",
                                                ),
                                            )
                                            issue("eos", trx_amount, client_id)
                                            # unlock the deposit address after some time
                                            delay = (
                                                DEPOSIT_TIMEOUT
                                                - elapsed
                                                + DEPOSIT_PAUSE
                                            )
                                            unlock_address("eos", account_idx, delay)
                                            return
                                        # when returning foreign funds to client,
                                        # upon receipt, reserve equal in UIA
                                        if (
                                            issuer_action == "reserve"
                                            and trx_from == gateway
                                            and trx_amount == amount
                                        ):
                                            print(
                                                f"nonce {nonce}",
                                                it(
                                                    "red", f"RESERVING {amount} {uia}\n"
                                                ),
                                            )
                                            reserve("eos", trx_amount)
                                            return
                        except Exception:
                            print(f"nonce {nonce}", "action", action, "\n")
                            print(traceback.format_exc(), "\n")

                if block_num not in checked_blocks:
                    checked_blocks.append(block_num)


def main():
    """
    UNIT TEST listener demonstration
    """
    print("\033c")
    print(time.ctime())
    print("\nEOS Account Verification\n============================")
    gateway = GATE["eos"][0]["public"]
    print("verify_eosio_account(", gateway, ")", verify_eosio_account(gateway))
    print("verify_eosio_account(", "test fail )", verify_eosio_account("test fail"))
    print("\nEOS Transaction Listener\n============================")
    listener_eosio()


if __name__ == "__main__":

    main()
