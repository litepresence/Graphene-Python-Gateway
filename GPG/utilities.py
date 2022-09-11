"""
utilities.py
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

a collection of shared utilities for Graphene Python Gateway
"""
# DISABLE SELECT PYLINT TESTS
# pylint: disable=too-many-arguments, broad-except, invalid-name

# STANDARD PYTHON MODULES
import os
import time
import inspect
import traceback
from random import shuffle
from calendar import timegm
from json import dumps as json_dumps
from json import loads as json_loads

# THIRD PARTY MODULES
from websocket import create_connection as wss

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.nodes import bitshares_nodes


def milleseconds():
    """
    milleseconds as integer
    """
    return int(time.time() * 1000)


def json_ipc(doc="", text="", initialize=False):
    """
    JSON IPC

    Concurrent Interprocess Communication via Read and Write JSON

    features to mitigate race condition:

        open file using with statement
        explicit close() in with statement
        finally close()
        json formatting required
        postscript clipping prevents misread due to overwrite without erase
        read and write to the text pipe with a single definition
        growing delay between attempts prevents cpu leak

    to view your live streaming database, navigate to the pipe folder in the terminal:

        tail -F your_json_ipc_database.txt

    :dependencies: os, traceback, json.loads, json.dumps
    :warn: incessant read/write concurrency may damage older spinning platter drives
    :warn: keeping a 3rd party file browser pointed to the pipe folder may consume RAM
    :param str(doc): name of file to read or write
    :param str(text): json dumped list or dict to write; if empty string: then read
    :return: python list or dictionary if reading, else None

    wtfpl2020 litepresence.com
    """
    # initialize variables
    data = None
    msg = "writing"
    tag = "<<< JSON IPC >>>"
    # determine where we are in the file system; change directory to pipe folder
    path = os.path.dirname(os.path.abspath(__file__)) + "/pipe"
    # ensure we're writing json then add prescript and postscript for clipping
    text = tag + json_dumps(json_loads(text)) + tag if text else text
    # create the pipe subfolder
    if initialize:
        os.makedirs(path, exist_ok=True)
    if doc:
        doc = path + "/" + doc
        # race read/write until satisfied
        iteration = 0
        while True:
            time.sleep(0.01 * iteration ** 2)
            try:
                if text:
                    # write to file operation
                    with open(doc, "w+") as handle:
                        handle.write(text)
                        handle.close()
                        break
                else:
                    msg = "reading"
                    # read from file operation
                    with open(doc, "r") as handle:
                        # only accept legitimate json
                        data = json_loads(handle.read().split(tag)[1])
                        handle.close()
                        break
            except Exception:
                if iteration == 1:
                    print(  # only if it happens more than once
                        f"{iteration}: json_ipc race condition while {msg} {doc}\n",
                    )
                elif iteration == 5:
                    print(traceback.format_exc())
                continue
            # deliberately double check that the file is closed
            finally:
                try:
                    handle.close()
                except Exception:
                    pass
            iteration += 1
    return data


def line_number():
    """
    prints file name, line number and function of the caller; h/t @ Streamsoup
    """
    stack = inspect.stack()
    full_stack = str(stack[1][1]) + ":" + str(stack[1][2]) + ":" + str(stack[1][3])
    print(full_stack)
    return full_stack


def timestamp():
    """
    print local time, timezone, and unix timestamp
    """
    now = (
        str(time.ctime())
        + " "
        + str(time.tzname[0])
        + " epoch "
        + str(int(time.time()))
    )
    print(now)
    return now


def from_iso_date(date):
    """
    BitShares ISO8601 to UNIX time conversion
    """
    return int(timegm(time.strptime(str(date), "%Y-%m-%dT%H:%M:%S")))


def logo():
    """
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
    """
    return logo.__doc__


def precisely(number, precision):
    """
    format float or int as string to specific number of decimal places
    :param number: int or float to be returned to specific number of decimal places
    :param int(precision): truncated decimal places to return; no more no less
    :return str(): string representation of a decimal to specific number of places
    """
    num = str(float(number))
    for _ in range(precision):
        num += "0"
    return num[: num.find(".") + precision + 1]


def it(style, text):
    """
    Color printing in terminal
    """
    emphasis = {
        "red": 91,
        "green": 92,
        "yellow": 93,
        "blue": 94,
        "purple": 95,
        "cyan": 96,
    }
    ret = f"\033[{emphasis[style]}m" + str(text) + "\033[0m"
    return ret


def raw_operations():
    """
    bitshares/python-bitshares/master/bitsharesbase/operationids.py"
    """
    return {
        0: "transfer",
        1: "limit_order_create",
        2: "limit_order_cancel",
        3: "call_order_update",
        4: "fill_order",
        5: "account_create",
        6: "account_update",
        7: "account_whitelist",
        8: "account_upgrade",
        9: "account_transfer",
        10: "asset_create",
        11: "asset_update",
        12: "asset_update_bitasset",
        13: "asset_update_feed_producers",
        14: "asset_issue",
        15: "asset_reserve",
        16: "asset_fund_fee_pool",
        17: "asset_settle",
        18: "asset_global_settle",
        19: "asset_publish_feed",
        20: "witness_create",
        21: "witness_update",
        22: "proposal_create",
        23: "proposal_update",
        24: "proposal_delete",
        25: "withdraw_permission_create",
        26: "withdraw_permission_update",
        27: "withdraw_permission_claim",
        28: "withdraw_permission_delete",
        29: "committee_member_create",
        30: "committee_member_update",
        31: "committee_member_update_global_parameters",
        32: "vesting_balance_create",
        33: "vesting_balance_withdraw",
        34: "worker_create",
        35: "custom",
        36: "assert",
        37: "balance_claim",
        38: "override_transfer",
        39: "transfer_to_blind",
        40: "blind_transfer",
        41: "transfer_from_blind",
        42: "asset_settle_cancel",
        43: "asset_claim_fees",
        44: "fba_distribute",
        45: "bid_collateral",
        46: "execute_bid",
        47: "asset_claim_pool",
        48: "asset_update_issuer",
        49: "htlc_create",
        50: "htlc_redeem",
        51: "htlc_redeemed",
        52: "htlc_extend",
        53: "htlc_refund",
    }


def wss_handshake(rpc):
    """
    Create a websocket handshake
    """

    while True:
        nodes = json_ipc(doc="nodes.txt")
        try:
            rpc.close()
        except Exception:
            pass
        try:
            shuffle(nodes)
            node = nodes[0]
            start = time.time()
            rpc = wss(node, timeout=4)
            if time.time() - start < 3:
                # print(node)
                break
        except Exception:
            nodes = [n for n in nodes if n != node]
            if len(nodes) < 7:
                nodes = bitshares_nodes()
            json_ipc(doc="nodes.txt", text=json_dumps(nodes))
    return rpc


def wss_query(rpc, params):
    """
    Send and receive websocket requests
    """
    query = json_dumps({"method": "call", "params": params, "jsonrpc": "2.0", "id": 1})
    # print(query)
    rpc.send(query)
    ret = rpc.recv()
    # print(ret)
    ret = json_loads(ret)
    # print(ret)
    try:
        return ret["result"]  # if there is result key take it
    except Exception:
        try:
            print(ret)
        except Exception:
            pass
        print(traceback.format_exc())


def block_ops_logo():
    """
     ######  ## ######## ####### ##   ##  #####  ######  ####### #######
     ##   ## ##    ##    ##      ##   ## ##   ## ##   ## ##      ##
     ######  ##    ##    ####### ####### ####### ######  #####   #######
     ##   ## ##    ##         ## ##   ## ##   ## ##   ## ##           ##
     ######  ##    ##    ####### ##   ## ##   ## ##   ## ####### #######

    ######  ##       ######   ###### ##   ##      ######  ######  #######
    ##   ## ##      ##    ## ##      ##  ##      ##    ## ##   ## ##
    ######  ##      ##    ## ##      #####       ##    ## ######  #######
    ##   ## ##      ##    ## ##      ##  ##      ##    ## ##           ##
    ######  #######  ######   ###### ##   ##      ######  ##      #######

        ##      ## ####### ######## ####### ###    ## ####### ######
        ##      ## ##         ##    ##      ####   ## ##      ##   ##
        ##      ## #######    ##    #####   ## ##  ## #####   ######
        ##      ##      ##    ##    ##      ##  ## ## ##      ##   ##
        ####### ## #######    ##    ####### ##   #### ####### ##   ##
    """
    return logo.__doc__
