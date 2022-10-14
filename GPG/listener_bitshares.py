"""
listener_bitshares.py
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

BitShares Block Operations Listener for Gateway Withdrawals

streaming statistical mode of websocket public api data
prints every operation in every transaction on every block
filtered by user selected operation id numbers

includes on_op definition for gateway withdrawal use upon issuer receipt of uia
may also run independently as a block ops listener for any Operation ID
"""

# DISABLE SELECT PYLINT TESTS
# pylint: disable=too-many-branches, too-many-nested-blocks, too-many-locals
# pylint: disable=broad-except, invalid-name, bad-continuation

# STANDARD PYTHON MODULES
import os
import time
import traceback
from random import randint
from multiprocessing import Process
from json import dumps as json_dumps
from json import loads as json_loads
from statistics import mode, StatisticsError

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.utilities import json_ipc, from_iso_date, it, raw_operations, timestamp
from GPG.utilities import wss_handshake, wss_query, block_ops_logo, line_number
from GPG.listener_eosio import listener_eosio, verify_eosio_account
from GPG.listener_ripple import listener_ripple, verify_ripple_account
from GPG.nodes import bitshares_nodes, eosio_nodes
from GPG.signing_eosio import eos_transfer
from GPG.signing_ripple import xrp_transfer
from GPG.decoder_ring import ovaltine
from GPG.config import configure


# CONSTANTS
BLOCK_MAVENS = min(5, len(bitshares_nodes()))
BLOCK_NUM_MAVENS = min(5, len(bitshares_nodes()))
BEGIN = int(time.time())
GATE = configure()["gate"]
PATH = str(os.path.dirname(os.path.abspath(__file__))) + "/"


def create_database():
    """
    initialize an empty text pipe IPC json_ipc
    :return None:
    """
    os.makedirs(PATH + "pipe", exist_ok=True)
    for maven_id in range(BLOCK_NUM_MAVENS):
        json_ipc(doc=f"block_num_maven_{maven_id}.txt", text=json_dumps([0,]))
    json_ipc(doc=f"block_number.txt", text=json_dumps([0,]))


def print_options(options):
    """
    Print a table of Operation ID options
    :param dict(options) static bitshares operation ids
    """
    print(it("yellow", "\n\n                         Operation ID Numbers\n"))
    msg = ""
    for idx in range(30):
        msg += "    " + str(idx).ljust(4) + str(options[idx]).ljust(30)
        try:
            msg += str(idx + 30).ljust(4) + str(options[idx + 30])
        except Exception:
            pass
        msg += "\n"
    print(it("yellow", msg))
    print(it("green", "\n\n    Enter ID number(s)"))


def choice():
    """
    Welcome and user input for stand alone listener app
    :return int(selection): operation id type number
    """
    print("\033c")
    print(it("blue", block_ops_logo()))
    print(
        it(
            "green",
            """
    Enter an Operation ID to stream below
    you can also enter a comma seperated list of ID's
    or Enter the letter "A" for All
    or press Enter for demo of Operations 0, 1, and 2
        """,
        )
    )

    operations = raw_operations()
    print_options(operations)
    selection = [0, 1, 2]
    user_select = input("\n\n")
    try:
        # if the user entered an ID number
        selection = [int(user_select)]
    except Exception:
        pass
    try:
        if "," in user_select:
            # if the user enter a list of numbers, attempt json conversion
            selection = json_loads(
                '["' + user_select.replace(",", '","').replace(" ", "") + '"]'
            )
            selection = [int(k) for k in selection]
    except Exception:
        pass
    if user_select.lower() == "a":
        selection = list(operations.keys())

    print("\033c")
    print(it("blue", block_ops_logo()))
    print(
        it(
            "green",
            "\n        BitShares Block Operations Listener\n"
            + "\n        operation(s) selected:    \n",
        )
    )
    print(it("blue", "        " + str(selection) + "\n"))
    for k in selection:
        print("       ", (operations[k]))
    print(it("green", "\n\n        fetching latest irreversible block number...\n"))
    return selection


def spawn_block_num_processes():
    """
    Several processes will concurrently update an array
    with external calls for irreversible block number
    later the statistical mode of the array will be used
    :return None:
    """
    for maven_id in range(BLOCK_NUM_MAVENS):
        block_num_processes = {}
        block_num_processes[maven_id] = Process(
            target=block_num_maven, args=(maven_id,)
        )
        block_num_processes[maven_id].start()


def block_num_maven(maven_id):
    """
    BTS public api maven opinion of last irreversible block number
    :param int(maven_id) used for inter process communication channel identification
    """
    rpc = ""
    rpc = wss_handshake(rpc)
    while True:
        if not randint(0, 100):
            rpc = wss_handshake(rpc)
        try:
            ret = wss_query(rpc, ["database", "get_dynamic_global_properties", []])
            block_time = from_iso_date(ret["time"])
            if time.time() - block_time > 10:
                continue
            block_num = int(ret["last_irreversible_block_num"])
            latest = json_ipc(doc="block_number.txt")[0]
            if latest + 1000 < block_num < latest - 10:
                continue
            json_ipc(
                doc=f"block_num_maven_{maven_id}.txt", text=json_dumps([block_num,])
            )
        except Exception:
            rpc = wss_handshake(rpc)
        time.sleep(3)


def block_maven(maven_id, start, stop):
    """
    BitShares public api consensus of get_block() returns all tx's on a given block
    :param int(maven_id): used for inter process communication channel identification
    :param int(start): beginning block number to get block transaction data
    :param int(stop): latest irreversible block number
    :return None: reports via text file inter process communication
    """
    rpc = wss_handshake("")
    # dictionary that will contain a list of transactions on each block
    blocks = {}
    for block_num in range(start, stop):
        blocks[block_num] = []
    json_ipc(doc=f"block_maven_{maven_id}.txt", text=json_dumps(blocks))
    for block_num in range(start, stop):
        while True:
            try:
                ret = wss_query(rpc, ["database", "get_block", [block_num]])[
                    "transactions"
                ]
                if isinstance(ret, list):
                    blocks[block_num] = ret
                    break
                rpc = wss_handshake(rpc)
            except Exception:
                rpc = wss_handshake(rpc)
                continue
    json_ipc(doc=f"block_maven_{maven_id}.txt", text=json_dumps(blocks))


def rpc_account_id(rpc, account_name):
    """
    given an account name return an account id
    :param rpc: a BitShares public api websocket instance
    :param str(account_name): BitShares account name to be looked up
    :return str(account_id): a.b.c format
    """
    ret = wss_query(rpc, ["database", "lookup_accounts", [account_name, 1]])
    account_id = ret[0][1]
    return account_id


def rpc_get_objects(rpc, object_id):
    """
    Return data about objects in 1.7.x, 2.4.x, 1.3.x, etc. format
    """
    ret = wss_query(rpc, ["database", "get_objects", [object_id,]])
    return ret


def rpc_balances(rpc, account_name, asset_id):
    """
    no frills bitshares account balance for one asset by ID for testing
    NOTE amounts returned are graphene integers lacking precision
    return int(graphene_amount)
    """
    balance = wss_query(
        rpc, ["database", "get_named_account_balances", [account_name, [asset_id]],]
    )[0]
    return balance


def spawn_block_processes(start, stop):
    """
    Launch several subprocesses to gather block data
    :param int(start):
    :param int(stop):
    :return None:
    """
    block_processes = {}
    for maven_id in range(BLOCK_MAVENS):
        block_processes[maven_id] = Process(
            target=block_maven, args=(maven_id, start, stop)
        )
        block_processes[maven_id].start()
    for maven_id in range(BLOCK_MAVENS):
        block_processes[maven_id].join(6)
    for maven_id in range(BLOCK_MAVENS):
        block_processes[maven_id].terminate()


def print_op(op):
    """
    At the end of the main while loop we'll perform some action on every operation
    as a sample, we'll just color some operations and print the op
    :param list(op): op[0] is transaction type number and op[1] is the transaction
    :return None:
    """
    msg = op[1]
    if op[0] == 0:  # transfer
        msg = it("purple", msg)
        print(msg, "\n")
    if op[0] == 1:  # limit order create
        msg = it("green", msg)
        print(msg, "\n")
    if op[0] == 2:  # limit order cancel
        msg = it("red", msg)
        print(msg, "\n")


def withdraw(op):
    """
    in production print_op is replaced with withdraw

        The user has returned some UIA to the issuer!

    upon hearing an on chain UIA transfer to the gateway with memo
    from this definition we trigger a gateway withdrawal event
    release the user's foreign chain funds to the memo
    and burn the returned UIA upon irreversible receipt
    """
    # if its a transfer to gateway with a memo
    tgm = False
    if op[0] == 0:  # transfer
        if op[1]["to"] in [
            GATE["uia"]["eos"]["issuer_id"],
            GATE["uia"]["xrp"]["issuer_id"],
        ]:
            print(it("yellow", "gate uia transfer"))
            if "memo" in op[1].keys():
                print(
                    it("red", "TRANSFER TO GATEWAY WITH MEMO\n\n"),
                    it("yellow", op),
                    "\n",
                )
                tgm = True
            else:
                print(it("red", "WARN: transfer to gateway WITHOUT memo"))
    if tgm:
        timestamp()
        line_number()
        order = {}
        # extract the asset_id of the transfer
        uia_id = op[1]["amount"]["asset_id"]
        print("uia_id", uia_id, "\n")
        # EOS specific parameters
        if uia_id == GATE["uia"]["eos"]["asset_id"]:
            network = "eos"
            verify = verify_eosio_account
            listen = listener_eosio
            transfer = eos_transfer
            # eos transfers require a url
            order["url"] = eosio_nodes()[0]  # FIXME what happens if node fails?
        # XRP specific parameters
        elif uia_id == GATE["uia"]["xrp"]["asset_id"]:
            network = "xrp"
            verify = verify_ripple_account
            listen = listener_ripple
            transfer = xrp_transfer
        memo = op[1]["memo"]  # dict with keys("from", "to", "nonce", "message")
        order["private"] = GATE[network][0]["private"]
        order["public"] = GATE[network][0]["public"]
        # convert graphene operation amount to human readable
        order["quantity"] = (
            op[1]["amount"]["amount"] / 10 ** GATE["uia"][network]["asset_precision"]
        )
        # decode the client's memo using the issuers private key
        order["to"] = ovaltine(memo, GATE["uia"][network]["issuer_private"])
        print(f"decoded {network} client", order["to"], "\n")
        # confirm we're dealing with a legit client address
        if verify(order["to"]):
            listener = Process(
                target=listen,
                args=(
                    0,
                    order["quantity"],
                    "reserve",  # issuer_action
                    None,  # # always None for reserve
                ),
            )  # upon hearing real foreign chain transfer, reserve the uia equal
            listener.start()
            print(
                it(
                    "red",
                    f"STARTING {network} LISTENER TO RESERVE {order['quantity']}\n",
                )
            )
            # wait for listener subprocess to warm up then transfer the order
            time.sleep(30)
            timestamp()
            line_number()
            print(transfer(order))
        else:
            print(it("red", f"WARN: memo is NOT a valid {network} account name\n"))


def listener_bitshares(selection=None):
    """
    primary listener event loop
    :param int(selection) or None: user choice for demonstration of listener
    :run forever:
    """
    # get node list from github repo for bitshares ui staging; write to file
    nodes = bitshares_nodes()
    options = raw_operations()
    json_ipc(doc="nodes.txt", text=json_dumps(nodes))
    # create a subfolder for the database; write to file
    create_database()
    # initialize block number
    last_block_num = curr_block_num = 0
    # bypass user input... gateway transfer ops
    act = print_op
    if selection is None:
        selection = 0
        act = withdraw
    # spawn subprocesses for gathering streaming consensus irreversible block number
    spawn_block_num_processes()
    # continually listen for last block["transaction"]["operations"]
    print(it("red", "\nINITIALIZING WITHDRAWAL LISTENER\n\n"))
    while True:
        try:
            # get the irreversible block number reported by each maven subprocess
            block_numbers = []
            for maven_id in range(BLOCK_NUM_MAVENS):
                block_num = json_ipc(doc=f"block_num_maven_{maven_id}.txt")[0]
                block_numbers.append(block_num)
            # the current block number is the statistical mode of the mavens
            # NOTE: may throw StatisticsError when no mode
            curr_block_num = mode(block_numbers)
            # print(curr_block_num)
            json_ipc(doc=f"block_number.txt", text=json_dumps([curr_block_num,]))
            # if the irreverisble block number has advanced
            if curr_block_num > last_block_num:
                print(
                    "\033[F",  # go back one line
                    it("blue", "BitShares Irreversible Block"),
                    it("yellow", curr_block_num),
                    time.ctime()[11:19],
                    it("blue", int(time.time())),
                )
                if last_block_num > 0:  # not on first iter
                    # spawn some new mavens to get prospective block data
                    start = last_block_num + 1
                    stop = curr_block_num + 1
                    spawn_block_processes(start, stop)
                    # inititialize blocks as a dict of empty transaction lists
                    blocks = {}
                    for block_num in range(start, stop):
                        blocks[block_num] = []
                    # get block transactions from each maven subprocesses
                    for maven_id in range(BLOCK_MAVENS):
                        # print(maven_id)
                        maven_blocks = json_ipc(doc=f"block_maven_{maven_id}.txt")
                        # for each block that has past since last update
                        for block_num in range(start, stop):
                            # print(block_num)
                            # get the maven's version of that block from the dictionary
                            # NOTE: may throw KeyError, TODO: find out why?
                            maven_block = maven_blocks[str(block_num)]
                            # append that version to the list
                            # of maven opinions for that block number
                            blocks[block_num].append(json_dumps(maven_block))
                    # get the mode of the mavens for each block in the blocks dict
                    # NOTE: may throw StatisticsError when no mode
                    # for example half the nodes are on the next block number
                    blocks = {k: json_loads(mode(v)) for k, v in blocks.items()}
                    # triple nested:
                    # for each operation, in each transaction, on each block
                    for block_num, transactions in blocks.items():
                        for item, trx in enumerate(transactions):
                            for op in trx["operations"]:
                                # add the block and transaction numbers to the operation
                                op[1]["block"] = block_num
                                op[1]["trx"] = item + 1
                                op[1]["operation"] = (op[0], options[op[0]])
                                # spin off withdrawal act so listener can continue
                                process = Process(target=act, args=(op,))
                                process.start()
                last_block_num = curr_block_num
            time.sleep(6)
        # statistics and key errors can be safely ignored, restart loop
        except (StatisticsError, KeyError):
            continue
        # in all other cases provide stack trace
        except Exception as error:
            print("\n\n", it("yellow", error), "\n\n")
            print(traceback.format_exc(), "\n")
            continue


def main():
    """
    UNIT TEST

    Aside from use as gateway withdrawal listener module, the script may also
    run independently as a bitshares block ops listener for any Operation ID
    """
    # FIXME lots of changes since last unit test; should retest module
    selection = choice()
    listener_bitshares(selection)


if __name__ == "__main__":

    main()
