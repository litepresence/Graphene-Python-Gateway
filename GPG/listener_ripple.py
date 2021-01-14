"""
listener_ripple.py
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

Ripple ledger Ops Listener

triggers:

    issue UIA upon deposited foreign coin
    reserve UIA upon confirmed withdrawal
"""

# DISABLE SELECT PYLINT TESTS
# pylint: disable=too-many-locals, too-many-nested-blocks, bare-except
# pylint: disable=too-many-function-args, too-many-branches

# STANDARD PYTHON MODULES
from json import dumps as json_dumps
import time

# THIRD PARTY MODULES
from requests import get

# GRAPHENE PYTHON GATEWAY MODULES
from config import configure
from signing_bitshares import issue, reserve
from gateway_state import unlock_address
from utilities import it, timestamp, line_number

# GLOBAL CONSTANTS
URL = "https://s1.ripple.com:51234/"
GATE = configure()["gate"]
DEPOSIT_TIMEOUT = 1800
DEPOSIT_PAUSE = 600


def get_validated_ledger():
    """
    ripple public api validated ledger
    :return int(ledger_index):
    """
    data = json_dumps({"method": "ledger", "params": [{"ledger_index": "validated"}]})
    ledger_index = get(URL, data=data).json()["result"]["ledger"]["ledger_index"]
    # print(ledger_index)
    return int(ledger_index)


def get_ledger(ledger):
    """
    ripple public api of a specific ledger
    """
    data = json_dumps(
        {
            "method": "ledger",
            "params": [{"ledger_index": ledger, "transactions": True, "expand": True}],
        }
    )
    ret = get(URL, data=data).json()["result"]["ledger"]["transactions"]

    ret = [tx for tx in ret if tx["TransactionType"] == "Payment"]
    ret = [tx for tx in ret if tx["metaData"]["TransactionResult"] == "tesSUCCESS"]

    # print(json_dumps(ret, sort_keys=True, indent=2))
    return ret


def verify_ripple_account(account):
    """
    ripple public api consensus of get_account() returns True or False on existance
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
    ret = get(URL, data=data).json()["result"]
    timestamp()
    line_number()
    print(ret, "\n")
    is_account = False
    if "account_data" in ret.keys():
        is_account = True
    return is_account


def listener_ripple(
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
    gateway = GATE["xrp"][account_idx]["public"]
    uia = GATE["uia"]["xrp"]["asset_name"]
    start_ledger_num = get_validated_ledger()
    checked_ledgers = [start_ledger_num]
    timestamp()
    line_number()
    print(f"nonce {nonce}", "Start ledger:", start_ledger_num, "\n")
    start = time.time()
    while 1:
        elapsed = time.time() - start
        if elapsed > DEPOSIT_TIMEOUT:
            print(f"nonce {nonce}", it("red", "XRP GATEWAY TIMEOUT"), gateway)
            # after timeout, release the address
            if issuer_action == "issue":
                unlock_address("ripple", account_idx, DEPOSIT_PAUSE)
            break
        # get the latest validated ledger number
        current_ledger = get_validated_ledger()
        # get the latest ledger number we checked
        max_checked_ledger = max(checked_ledgers)
        # if there are any new validated ledgers
        if current_ledger > max_checked_ledger + 1:
            # check every ledger from last check till now
            for ledger_num in range(max_checked_ledger + 1, current_ledger):
                print(
                    f"nonce {nonce}",
                    it("green", "Ripple Validated Ledger"),
                    it("yellow", ledger_num),
                    time.ctime()[11:19],
                )
                # get each new validated ledger
                transactions = get_ledger(ledger_num)
                # iterate through all transactions in the list of transactions
                for trx in transactions:
                    if not isinstance(trx["Amount"], dict):
                        # localize data from the transaction
                        amount = int(trx["Amount"]) / 10 ** 6  # convert drops to xrp
                        trx_from = trx["Account"]
                        trx_to = trx["Destination"]
                        # during unit testing
                        if issuer_action is None:
                            print(f"nonce {nonce}", ledger_num, trx, "\n")
                        # determine if it is a transfer to or from the gateway
                        if gateway in [trx_from, trx_to]:
                            timestamp()
                            line_number()
                            # establish gateway transfer direction
                            direction = "INCOMING"
                            if gateway == trx_from:
                                direction = "OUTGOING"
                            print(
                                f"nonce {nonce}",
                                it(
                                    "red",
                                    f"{direction} XRP GATEWAY TRANSFER DETECTED\n",
                                ),
                                f"amount {amount}\n",
                                f"from {trx_from}\n",
                                f"to {trx_to}\n",
                            )
                            # the client_id was assigned deposit gateway address
                            # issue UIA to client_id upon receipt of their foreign funds
                            if issuer_action == "issue" and trx_to == gateway:
                                print(
                                    f"nonce {nonce}",
                                    it(
                                        "red",
                                        f"ISSUING {amount} {uia} to {client_id}\n",
                                    ),
                                )
                                issue("xrp", amount, client_id)
                                # in subprocess unlock the deposit address after wait
                                delay = DEPOSIT_TIMEOUT - elapsed + DEPOSIT_PAUSE
                                unlock_address("xrp", account_idx, delay)
                                return  # but immediately kill the listener
                            # the parent process will soon send foreign funds to client_id
                            # reserve UIA upon hearing proof of this transfer
                            if issuer_action == "reserve" and trx_from == gateway:
                                print(
                                    f"nonce {nonce}",
                                    it("red", f"RESERVING {amount} {uia}\n"),
                                )
                                reserve("xrp", amount)
                                return  # kill the listener
                # append this ledger number to the list of checked numbers
                if ledger_num not in checked_ledgers:
                    checked_ledgers.append(ledger_num)


def main():
    """
    UNIT TEST listener demonstration
    """
    print("\033c")
    print(time.ctime())
    print("\nXRP Transaction Listener\n============================")
    listener_ripple()


if __name__ == "__main__":

    main()
