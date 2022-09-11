"""
signing_bitshares.py
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

BitShares ECDSA for Login, Buy, Sell, Cancel, Transfer, Issue, Reserve
"""


# DISABLE SELECT PYLINT TESTS
# pylint: disable=too-many-statements, too-many-locals, too-many-branches
# pylint: disable=too-many-arguments, broad-except, invalid-name
# pylint: disable=too-many-nested-blocks, bad-continuation, bad-whitespace
# pylint: disable=too-many-lines, import-error
# FIXME this script is forked with legacy pylint issues, but live tested/works!
# FIXME very techical with considerable dev hours to achieve pylint 10/10

# =======================================================================
VERSION = "Bitshares manualSIGNING 0.00000010"
# =======================================================================

DEV = False

# STANDARD PYTHON MODULES
from time import time, ctime, mktime, strptime
from multiprocessing import Process, Value  # encapsulate processes
from decimal import Decimal as decimal  # higher precision than float
from json import dumps as json_dumps  # serialize object to string
from json import loads as json_loads  # deserialize string to object
from collections import OrderedDict
from traceback import format_exc  # stack trace in terminal
from datetime import datetime
from calendar import timegm
from getpass import getpass  # hidden input()
from random import shuffle
from pprint import pprint  # pretty printing
import math
import sys
import os

# STANDARD CONVERSION UTILITIES
from binascii import hexlify  # binary text to hexidecimal
from binascii import unhexlify  # hexidecimal to binary text
from zlib import decompress  # aka gzip inflate; only used for logo
from hashlib import sha256  # message digest algorithm
from hashlib import new as hashlib_new  # access algorithm library
from struct import pack  # convert to string representation of C struct
from struct import unpack, unpack_from  # convert back to PY variable

# NON STANDARD MODULES WHICH REQUIRE INSTALLATION
from websocket import create_connection as wss  # handshake to node
from secp256k1 import PrivateKey as secp256k1_PrivateKey  # class
from secp256k1 import PublicKey as secp256k1_PublicKey  # class
from secp256k1 import ffi as secp256k1_ffi  # compiled ffi object
from secp256k1 import lib as secp256k1_lib  # library
from ecdsa import numbertheory as ecdsa_numbertheory  # largest import
from ecdsa import VerifyingKey as ecdsa_VerifyingKey  # class
from ecdsa import SigningKey as ecdsa_SigningKey  # class
from ecdsa import SECP256k1 as ecdsa_SECP256k1  # curve
from ecdsa import util as ecdsa_util  # module
from ecdsa import der as ecdsa_der  # module

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.config import configure
from GPG.nodes import bitshares_nodes

# GLOBAL CONSTANTS
GATE = configure()["gate"]
PREFIX = configure()["gate"]["uia"]["chain"]["prefix"]
ID = configure()["gate"]["uia"]["chain"]["id"]

" PRINT CONTROL "


def blockPrint():
    # temporarily disable printing
    sys.stdout = open(os.devnull, "w")


def enablePrint():
    # re-enable printing
    sys.stdout = sys.__stdout__


def trace(e):
    # print stack trace upon exception
    msg = str(type(e).__name__) + "\n"
    msg += str(e.args) + "\n"
    msg += str(format_exc()) + "\n"
    print(msg)


" GLOBALS "


def sample_orders():

    global order1, order2, order3
    nodes = [
        "wss://chicago.bitshares.apasia.tech/ws",
        "wss://new-york.bitshares.apasia.tech/ws",
        "wss://seattle.bitshares.apasia.tech/ws",
        "wss://us-ny.bitshares.apasia.tech/ws",
        "wss://us-la.bitshares.apasia.tech/ws",
    ]
    # the sample orders below do not require currency id and precision in the header
    # it is also ok to just pass "BTS" as "1.3.0" and 5
    header = {
        "asset_id": "1.3.0",
        "asset_precision": 5,
        "account_id": "1.2.x",
        "account_name": "",
        "wif": "",
    }
    order = {
        "header": header,
        "nodes": nodes,
    }
    order1 = dict(order)
    order2 = dict(order)
    order3 = dict(order)
    order4 = dict(order)
    order5 = dict(order)
    # login
    order1["edicts"] = [{"op": "login"}]
    # cancel all
    order2["edicts"] = [
        {"op": "cancel", "ids": ["1.7.X"]},  # cancel all
        # or cancel specific order numbers:
        # {'op':'cancel',
        #'ids':['1.7.101','1.7.102','1.7.103']},
    ]
    # transfer
    order3["edicts"] = [
        {"op": "transfer", "amount": 0, "to_account_id": "1.2.x", "memo": "",}
    ]
    # issue asset
    order4["edicts"] = [
        {"op": "issue", "amount": 0, "to_account_id": "1.2.x", "memo": "",}
    ]
    # reserve asset
    order5["edicts"] = [{"op": "reserve", "amount": 0}]
    # limit and call orders require additional currency id and precision keys in header
    header = {
        "asset_id": "1.3.0",
        "currency_id": "1.3.861",
        "asset_precision": 5,
        "currency_precision": 8,
        "account_id": "1.2.x",
        "account_name": "",
        "wif": "",
    }
    order = {
        "header": header,
        "nodes": nodes,
    }
    # place two limit orders
    order6 = dict(order)
    order7 = dict(order)
    order6["edicts"] = [
        {"op": "buy", "amount": 10.0, "price": 0.00000100, "expiration": 0,},
        {"op": "sell", "amount": 30.0, "price": 0.00000150, "expiration": 0,},
    ]
    # call order update
    order7["edicts"] = [{"op": "call", "debt": 0, "collateral": 0,}]


def global_variables():

    global info

    info = {"id": 1}


def global_constants():

    global OP_IDS, OP_NAMES, TYPES, SATOSHI, SIXSIG
    global BASE58, HEXDIGITS, ISO8601, END_OF_TIME
    # bitsharesbase/operationids.py
    OP_IDS = {
        "Transfer": 0,
        "Limit_order_create": 1,
        "Limit_order_cancel": 2,
        "Call_order_update": 3,
        "Asset_issue": 14,
        "Asset_reserve": 15,
    }
    # swap keys/values to index names by number
    OP_NAMES = {v: k for k, v in OP_IDS.items()}   
    # bitsharesbase/objecttypes.py used by ObjectId() to confirm a.b.c
    TYPES = {
        "account": 2,
        "asset": 3,
        "limit_order": 7,
    }  # 1.2.x  # 1.3.x  # 1.7.x
    # base58 encoding and decoding; this is alphabet defined:
    BASE58 = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    # hex encoding and decoding
    HEXDIGITS = "0123456789abcdefABCDEF"
    # ISO8601 timeformat; 'graphene time'
    ISO8601 = "%Y-%m-%dT%H:%M:%S%Z"
    # MAX is 4294967295; year 2106 due to 4 byte unsigned integer
    END_OF_TIME = 4 * 10 ** 9  # about 75 years in future
    # very little
    SATOSHI = decimal(0.00000001)
    # almost 1
    SIXSIG = decimal(0.999999)


def control_panel():

    global HANDSHAKE_TIMEOUT, PROCESS_TIMEOUT, AUTOSCALE, BTS_FEES
    global KILL_OR_FILL, ATTEMPTS, JOIN, LIMIT, DUST

    " advanced user controls to alter execution behaviors "
    # timeout during websocket handshake; default 4 seconds
    HANDSHAKE_TIMEOUT = 4
    # multiprocessing handler lifespan, default 20 seconds
    PROCESS_TIMEOUT = 20
    # default False for persistent limit orders
    KILL_OR_FILL = False
    # default True scales elements of oversize gross order to means
    AUTOSCALE = True
    # default True to never spend last 2 bitshares
    BTS_FEES = True
    # multiprocessing incarnations, default 3 attempts
    ATTEMPTS = 1
    # prevent extreme number of AI generated edicts; default 20
    LIMIT = 20
    # default True to execute order in primary script process
    JOIN = True
    # ignore orders value less than ~X bitshares; 0 to disable
    DUST = 0


" COLOR TERMINAL "


def it(style, text):

    emphasis = {
        "red": 91,
        "green": 92,
        "yellow": 93,
        "blue": 94,
        "purple": 95,
        "cyan": 96,
    }

    return ("\033[%sm" % emphasis[style]) + str(text) + "\033[0m"


" REMOTE PROCEDURE CALLS TO PUBLIC API NODES"


def wss_handshake():

    # create a wss handshake in less than X seconds, else try again
    print(it("purple", "wss_handshake - node list is hard coded"))
    print("in production use latencyTEST.py to generate list")
    global ws, nodes  # the websocket is created and node list shuffled

    shuffle(nodes)
    handshake = 999
    while handshake > HANDSHAKE_TIMEOUT:
        try:
            try:
                ws.close  # attempt to close open stale connection
                print(it("purple", "connection terminated"))
            except Exception:
                pass
            start = time()
            nodes.append(nodes.pop(0))  # rotate list
            node = nodes[0]
            print(it("purple", "connecting:"), node)
            ws = wss(node, timeout=HANDSHAKE_TIMEOUT)
            handshake = time() - start
        except Exception:
            continue
    print(it("purple", "connected:"), node, ws)
    print("elapsed %.3f sec" % (time() - start))


def wss_query(params):

    # this definition will place all remote procedure calls (RPC)
    for _ in range(10):
        try:
            # print(it('purple','RPC ' + params[0]), it('cyan',params[1]))
            # this is the 4 part format of EVERY rpc request
            # params format is ["location", "object", []]
            query = json_dumps(
                {"method": "call", "params": params, "jsonrpc": "2.0", "id": 1,}
            )
            # print(query)
            # ws is the websocket connection created by wss_handshake()
            # we will use this connection to send query and receive json
            ws.send(query)
            ret = json_loads(ws.recv())
            try:
                ret = ret["result"]  # if there is result key take it
            except Exception:
                pass
            # print(ret)
            # print('elapsed %.3f sec' % (time() - start))
            return ret
        except Exception as e:
            try:  # attempt to terminate the connection
                ws.close()
            except Exception:
                pass
            trace(e)  # tell me what happened
            # switch nodes
            wss_handshake()
    raise


def rpc_block_number():
    return wss_query(["database", "get_dynamic_global_properties", []])


def rpc_account_id():
    # given an account name return an account id
    ret = wss_query(["database", "lookup_accounts", [account_name, 1]])
    return ret[0][1]


def rpc_fees():
    # returns fee for limit order create and cancel without 10^precision
    # also call orders
    query = [
        "database",
        "get_required_fees",
        [
            [
                ["1", {"from": str(account_id)}],
                ["2", {"from": str(account_id)}],
                ["3", {"from": str(account_id)}],
                ["0", {"from": str(account_id)}],
                ["14", {"from": str(account_id)}],
                ["15", {"from": str(account_id)}],
            ],
            "1.3.0",
        ],
    ]
    ret = wss_query(query)
    create = ret[0]["amount"]
    cancel = ret[1]["amount"]
    call = ret[2]["amount"]
    transfer = ret[3]["amount"]
    issue = ret[4]["amount"]
    reserve = ret[5]["amount"]

    return {
        "create": create,
        "cancel": cancel,
        "call": call,
        "transfer": transfer,
        "issue": issue,
        "reserve": reserve,
    }


def rpc_balances():

    balances = wss_query(
        [
            "database",
            "get_named_account_balances",
            [account_name, [currency_id, asset_id, "1.3.0"]],
        ]
    )

    # print(balances)
    for balance in balances:
        if balance["asset_id"] == currency_id:
            currency = decimal(balance["amount"]) / 10 ** currency_precision
        if balance["asset_id"] == asset_id:
            assets = decimal(balance["amount"]) / 10 ** asset_precision
        if balance["asset_id"] == "1.3.0":
            bitshares = decimal(balance["amount"]) / 10 ** 5

    # print(currency, assets, bitshares)
    return currency, assets, bitshares


def rpc_open_orders():
    # return a list of open orders, for one account, in one market
    ret = wss_query(["database", "get_full_accounts", [[account_name], "false"]])
    try:
        limit_orders = ret[0][1]["limit_orders"]
    except Exception:
        limit_orders = []
    market = [currency_id, asset_id]
    orders = []
    for order in limit_orders:
        base_id = order["sell_price"]["base"]["asset_id"]
        quote_id = order["sell_price"]["quote"]["asset_id"]
        if (base_id in market) and (quote_id in market):
            orders.append(order["id"])
    return orders


def rpc_key_reference(public_key):

    return wss_query(["database", "get_key_references", [[public_key]]])


def rpc_get_transaction_hex_without_sig(tx):
    # use this to verify the manually serialized tx buffer

    print("rpc_tx_hex_sig")
    pprint(tx)

    ret = wss_query(["database", "get_transaction_hex_without_sig", [tx]])

    if DEV:
        print(ret)
    return bytes(ret, "utf-8")


def rpc_broadcast_transaction(tx):
    # upload the signed transaction to the blockchain
    ret = wss_query(["network_broadcast", "broadcast_transaction", [tx]])
    if ret is None:
        print(it("yellow", "*************************************"))
        print("manualSIGNING" + it("red", " has placed your order"))
        print(it("yellow", "*************************************"))
        return tx
    pprint(ret)
    return ret


" DATE FORMATTING "


def to_iso_date(unix):
    return datetime.utcfromtimestamp(int(unix)).isoformat()


def from_iso_date(iso):
    return int(timegm(strptime(f"{iso}UTC", ISO8601)))


" GRAPHENEBASE TYPES "  # graphenebase/types.py


def types_README():
    # graphenebase types use python "dunder" / "magic" methods
    # these are a little abstract and under documented; to elucidate:
    # bytes() is a "built in" function like str(), int(), list()
    # it returns byte strings like: b'\x00\x00\x00'
    # these methods will redefine the type of byte string
    # returned by the "built in" bytes() in global space
    # but only when bytes() is called on an object that has passed
    # through a class with a "magic" __bytes__ method
    # these methods are used to serialize OrderDicts of various elements
    # graphenebase  __str__() methods have been removed
    # as they are unused for limit order operations
    # Set() has been merged into Array()
    # Bool() has been merged into Uint8()
    # Varint32() has been merged into both Id() and Array()
    'consider the following "magic method" example'
    # this would have no effect on the way bytes() normally behaves
    class normal:
        def __init__(self, d):
            self.data = int(d)

        def __bytes__(self):
            return bytes(self.data)

    # this redifines bytes() in global to pack unsigned 8 bit integers
    # but only in the case of bytes(Uint8(x))

    class Uint8:
        def __init__(self, d):
            self.data = int(d)

        def __bytes__(self):
            return pack("<B", self.data)

    # this is a definition method to accomplish the same "magic"

    def bytes_Uint8(data):
        return pack("<B", int(data))

    # apply each of these methods to x=3 to show what happens
    x = 3
    print(bytes(x))
    print(bytes(normal(x)))
    print(bytes(Uint8(x)))
    print(bytes_Uint8(x))
    """
    # >>>
    # b'\x00\x00\x00'
    # b'\x00\x00\x00'
    # b'\x03'
    # b'\x03'
    """


class ObjectId:

    # encodes a.b.c object ids - serializes the *instance* only!
    def __init__(self, object_str, type_verify=None):
        # if after splitting a.b.c there are 3 pieces:
        if len(object_str.split(".")) == 3:
            # assign those three pieces to a, b, and c
            a, b, c = object_str.split(".")
            # assure they are integers
            self.a = int(a)
            self.b = int(b)
            self.c = int(c)
            # serialize the c element; the "instance"
            self.instance = Id(self.c)
            self.abc = object_str
            # 1.2.x:account, 1.3.x:asset, or 1.7.x:limit
            if type_verify:
                assert TYPES[type_verify] == int(b), (
                    # except raise error showing mismatch
                    "Object id does not match object type! "
                    + "Excpected %d, got %d" % (TYPES[type_verify], int(b))
                )
        else:
            raise Exception("Object id is invalid")

    def __bytes__(self):
        # b'\x00\x00\x00' of serialized c element; the "instance"
        return bytes(self.instance)


class Id:
    # serializes the c element of "a.b.c" types
    # merged with Varint32()

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return bytes(varint(self.data))


class Array:
    # serializes lists as byte strings
    # merged with Set() and Varint32()

    def __init__(self, d):
        self.data = d
        self.length = len(self.data)

    def __bytes__(self):
        return bytes(varint(self.length)) + b"".join([bytes(a) for a in self.data])


class Uint8:
    # byte string of 8 bit unsigned integers
    # merged with Bool()

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return pack("<B", self.data)


class Uint16:
    # byte string of 16 bit unsigned integers

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return pack("<H", self.data)


class Uint32:
    # byte string of 32 bit unsigned integers

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return pack("<I", self.data)


class Int64:
    # byte string of 64 bit unsigned integers

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return pack("<q", self.data)


class Optional:
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        if not bool(self.data):
            return bytes(Uint8(0))
        else:
            return (
                bytes(Bool(1)) + bytes(self.data)
                if bytes(self.data)
                else bytes(Uint8(0))
            )

    def __str__(self):
        return str(self.data)

    def isempty(self):
        if self.data is None:
            return True
        return not bool(bytes(self.data)) if bool(str(self.data)) else True


class Signature:
    # used to disable bytes() method on Signatures in OrderedDicts

    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        return self.data  # note does NOT return bytes(self.data)


class PointInTime:
    # used to pack ISO8601 time as 4 byte unix epoch integer as bytes

    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        return pack("<I", from_iso_date(self.data))


class Static_variant:
    def __init__(self, d, type_id):
        self.data = d
        self.type_id = type_id

    def __bytes__(self):
        return varint(self.type_id) + bytes(self.data)

    def __str__(self):
        return json_dumps([self.type_id, self.data.json()])


" VARINT "


def varint(n):
    # varint encoding normally saves memory on smaller numbers
    # yet retains ability to represent numbers of any magnitude
    data = b""
    while n >= 0x80:
        data += bytes([(n & 0x7F) | 0x80])
        n >>= 7
    data += bytes([n])
    return data


" BASE 58 ENCODE, DECODE, AND CHECK "  # graphenebase/base58.py


class Base58(object):

    """
    This class serves as an abstraction layer
    to deal with base58 encoded strings
    and their corresponding hex and binary representation
    """

    def __init__(self, data, prefix=PREFIX):

        print(it("green", "Base58"))
        print(it("blue", data))
        self._prefix = prefix
        if all(c in HEXDIGITS for c in data):
            self._hex = data
        elif data[0] in ["5", "6"]:
            self._hex = base58CheckDecode(data)
        elif data[0] in ["K", "L"]:
            self._hex = base58CheckDecode(data)[:-2]
        elif data[: len(self._prefix)] == self._prefix:
            self._hex = gphBase58CheckDecode(data[len(self._prefix) :])
        else:
            raise ValueError("Error loading Base58 object")

    def __format__(self, _format):

        if _format.upper() != PREFIX:
            print("Format %s unkown. You've been warned!\n" % _format)
        return _format.upper() + str(self)

    def __repr__(self):  # hex string of data
        return self._hex

    def __str__(self):  # base58 string of data
        return gphBase58CheckEncode(self._hex)

    def __bytes__(self):  # raw bytes of data
        return unhexlify(self._hex)


def base58decode(base58_str):
    print(it("green", "base58decode"))
    base58_text = bytes(base58_str, "ascii")
    n = 0
    leading_zeroes_count = 0
    for b in base58_text:
        n = n * 58 + BASE58.find(b)
        if n == 0:
            leading_zeroes_count += 1
    res = bytearray()
    while n >= 256:
        div, mod = divmod(n, 256)
        res.insert(0, mod)
        n = div
    res.insert(0, n)
    return hexlify(bytearray(1) * leading_zeroes_count + res).decode("ascii")


def base58encode(hexstring):
    print(it("green", "base58encode"))
    byteseq = bytes(unhexlify(bytes(hexstring, "ascii")))
    n = 0
    leading_zeroes_count = 0
    for c in byteseq:
        n = n * 256 + c
        if n == 0:
            leading_zeroes_count += 1
    res = bytearray()
    while n >= 58:
        div, mod = divmod(n, 58)
        res.insert(0, BASE58[mod])
        n = div
    res.insert(0, BASE58[n])
    ret = (BASE58[:1] * leading_zeroes_count + res).decode("ascii")

    # public_key = 'BTS' + str(ret)
    # print(it('purple',public_key), "public key")

    print("len(ret)", len(ret))
    return ret


def ripemd160(s):
    # 160-bit cryptographic hash function
    ripemd160 = hashlib_new("ripemd160")  # import the library
    ripemd160.update(unhexlify(s))
    ret = ripemd160.digest()
    print("use hashlib to perform a ripemd160 message digest")
    print(ret)
    return ret


def doublesha256(s):
    # double sha256 cryptographic hash function
    ret = sha256(sha256(unhexlify(s)).digest()).digest()
    print("use hashlib to perform a double sha256 message digest")
    print(ret)
    return ret


def base58CheckEncode(version, payload):

    print(it("green", "base58CheckEncode"))
    print(payload, version)
    s = ("%.2x" % version) + payload
    print(s)
    checksum = doublesha256(s)[:4]
    result = s + hexlify(checksum).decode("ascii")
    return base58encode(result)


def gphBase58CheckEncode(s):
    print(it("yellow", "gphBase58CheckEncode"))
    print(s)
    checksum = ripemd160(s)[:4]
    result = s + hexlify(checksum).decode("ascii")
    return base58encode(result)


def base58CheckDecode(s):
    print(it("green", "base58CheckDecode"))
    print(s)
    s = unhexlify(base58decode(s))
    dec = hexlify(s[:-4]).decode("ascii")
    checksum = doublesha256(dec)[:4]
    assert s[-4:] == checksum
    return dec[2:]


def gphBase58CheckDecode(s):
    print(it("yellow", "gphBase58CheckDecode"))
    print(s)
    s = unhexlify(base58decode(s))
    dec = hexlify(s[:-4]).decode("ascii")
    checksum = ripemd160(dec)[:4]
    assert s[-4:] == checksum
    return dec


" ADDRESS AND KEYS "


class Address(object):  # cropped litepresence2019

    """
    Example :: Address("BTSFN9r6VYzBK8EKtMewfNbfiGCr56pHDBFi")
    """

    # graphenebase/account.py

    def __init__(self, address=None, pubkey=None, prefix=PREFIX):
        print(it("red", "Address"), "pubkey", pubkey)
        self.prefix = prefix
        self._pubkey = Base58(pubkey, prefix=prefix)
        self._address = None


class PublicKey(Address):  # graphenebase/account.py

    """
    This class deals with Public Keys and inherits ``Address``.

    :param str pk: Base58 encoded public key
    :param str prefix: Network prefix (defaults to ``BTS``)
    """

    def __init__(self, pk, prefix=PREFIX):

        global authenticated

        print(it("red", "PublicKey"))
        self.prefix = prefix
        self._pk = Base58(pk, prefix=prefix)
        self.address = Address(pubkey=pk, prefix=prefix)
        self.pubkey = self._pk

        public_key = prefix + str(self._pk)

        if login and (len(public_key) == 53):
            try:
                public_key = prefix + str(self._pk)
                print(public_key)
                print(len(public_key))
                account = rpc_key_reference(public_key)
                print(account[0][0])
                print(account_id)
                if str(account[0][0]) == str(account_id):
                    authenticated = True
                print("authenticated:", authenticated)
            except Exception:
                pass

    def _derive_y_from_x(self, x, is_even):
        print(it("purple", "           y^2 = x^3 + ax + b          "))
        print(self, x)
        """ Derive y point from x point """
        curve = ecdsa_SECP256k1.curve
        a, b, p = curve.a(), curve.b(), curve.p()
        alpha = (pow(x, 3, p) + a * x + b) % p
        beta = ecdsa_numbertheory.square_root_mod_prime(alpha, p)
        if (beta % 2) == is_even:
            beta = p - beta
        print(beta)
        return beta

    def compressed(self):
        print("PublicKey.compressed")
        """ Derive compressed public key """
        order = ecdsa_SECP256k1.generator.order()
        p = ecdsa_VerifyingKey.from_string(
            bytes(self), curve=ecdsa_SECP256k1
        ).pubkey.point
        x_str = ecdsa_util.number_to_string(p.x(), order)
        return hexlify(bytes(chr(2 + (p.y() & 1)), "ascii") + x_str).decode(
            "ascii"
        )

    def unCompressed(self):
        print("PublicKey.unCompressed")
        """ Derive uncompressed key """
        public_key = repr(self._pk)
        prefix = public_key[:2]
        if prefix == "04":
            return public_key
        assert prefix in ["02", "03"]
        x = int(public_key[2:], 16)
        y = self._derive_y_from_x(x, (prefix == "02"))
        return "04" + "%064x" % x + "%064x" % y

    def point(self):
        """ Return the point for the public key """
        string = unhexlify(self.unCompressed())
        return ecdsa_VerifyingKey.from_string(
            string[1:], curve=ecdsa_SECP256k1
        ).pubkey.point

    def __repr__(self):
        # print('PublicKey.__repr__')
        """ Gives the hex representation of the Graphene public key. """
        return repr(self._pk)

    def __format__(self, _format):
        # print('PublicKey.__format__')
        """ Formats the instance of:doc:`Base58 <base58>
        ` according to ``_format`` """
        return format(self._pk, _format)

    def __bytes__(self):
        # print('PublicKey.__bytes__')
        """ Returns the raw public key (has length 33)"""
        return bytes(self._pk)


class PrivateKey(PublicKey):  # merged litepresence2019

    # Bitshares(MIT) graphenebase/account.py
    # Bitshares(MIT) bitsharesbase/account.py

    """ Derives the compressed and uncompressed public keys and
        constructs two instances of ``PublicKey``:
    """

    def __init__(self, wif=None, prefix=PREFIX):

        print(prefix)
        print(it("red", "PrivateKey"))
        print(PublicKey)
        if wif is None:
            import os

            self._wif = Base58(hexlify(os.urandom(32)).decode("ascii"))
        elif isinstance(wif, Base58):
            self._wif = wif
        else:
            self._wif = Base58(wif)
        # compress pubkeys only
        self._pubkeyhex, self._pubkeyuncompressedhex = self.compressedpubkey()
        self.pubkey = PublicKey(self._pubkeyhex, prefix=prefix)
        self.uncompressed = PublicKey(self._pubkeyuncompressedhex, prefix=prefix)
        self.uncompressed.address = Address(
            pubkey=self._pubkeyuncompressedhex, prefix=prefix
        )
        self.address = Address(pubkey=self._pubkeyhex, prefix=prefix)

    def compressedpubkey(self):
        print("PrivateKey.compressedpubkey")
        """ Derive uncompressed public key """
        secret = unhexlify(repr(self._wif))
        order = ecdsa_SigningKey.from_string(
            secret, curve=ecdsa_SECP256k1
        ).curve.generator.order()
        p = ecdsa_SigningKey.from_string(
            secret, curve=ecdsa_SECP256k1
        ).verifying_key.pubkey.point
        x_str = ecdsa_util.number_to_string(p.x(), order)
        y_str = ecdsa_util.number_to_string(p.y(), order)
        compressed = hexlify(chr(2 + (p.y() & 1)).encode("ascii") + x_str).decode(
            "ascii"
        )
        uncompressed = hexlify(chr(4).encode("ascii") + x_str + y_str).decode("ascii")
        return [compressed, uncompressed]

    def __bytes__(self):
        # print('PrivateKey.__bytes__')
        """ Returns the raw private key """
        return bytes(self._wif)


" SERIALIZATION "


class GrapheneObject(object):  # Bitshares(MIT) graphenebase/objects.py
    def __init__(self, data=None):
        self.data = data

    def __bytes__(self):
        # encodes data into wire format'
        if self.data is None:
            return bytes()
        b = b""
        for name, value in self.data.items():
            b += bytes(value, "utf-8") if isinstance(value, str) else bytes(value)
        return b


class Asset(GrapheneObject):  # bitsharesbase/objects.py
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and not kwargs:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("amount", Int64(kwargs["amount"])),
                        ("asset_id", ObjectId(kwargs["asset_id"], "asset"),),
                    ]
                )
            )


class Operation:  # refactored  litepresence2019

    "class GPHOperation():"
    # Bitshares(MIT) graphenebase/objects.py
    "class Operation(GPHOperation):"
    # Bitshares(MIT) bitsharesbase/objects.py

    def __init__(self, op):

        if not (isinstance(op, list)):
            raise ValueError("expecting op to be a list")
        if len(op) != 2:
            raise ValueError("expecting op to be two items")
        if not (isinstance(op[0], int)):
            raise ValueError("expecting op[0] to be integer")

        self.opId = op[0]
        name = OP_NAMES[self.opId]
        self.name = name[0].upper() + name[1:]

        if op[0] == 0:
            self.op = Transfer(op[1])
        if op[0] == 1:
            self.op = Limit_order_create(op[1])
        if op[0] == 2:
            self.op = Limit_order_cancel(op[1])
        if op[0] == 3:
            self.op = Call_order_update(op[1])
        if op[0] == 14:
            self.op = Asset_issue(op[1])
        if op[0] == 15:
            self.op = Asset_reserve(op[1])

    def __bytes__(self):
        print(it("yellow", "GPHOperation.__bytes__"))
        return bytes(Id(self.opId)) + bytes(self.op)


class Extension(Array):  # /bitsharesbase/objects.py
    def __init__(self, *args, **kwargs):
        a = []
        self.json = dict(kwargs)
        for arg in args:
            if isinstance(arg, dict):
                self.json |= arg

        for index, extension in enumerate(self.sorted_options):
            name = extension[0]
            klass = extension[1]
            a.extend(
                Static_variant(klass(value), index)
                for key, value in self.json.items()
                if key.lower() == name.lower()
            )

        super().__init__(a)

    def __str__(self):
        """ We overload the __str__ function because the json
            representation is different for extensions
        """
        return json_dumps(self.json)


class Signed_Transaction(GrapheneObject):  # merged litepresence2019

    # Bitshares(MIT) graphenebase/signedtransactions.py
    # Bitshares(MIT) bitsharesbase/signedtransactions.py

    def __init__(self, *args, **kwargs):
        print(it("red", "Signed_Transaction"))
        print(
            """ Create a signed transaction and
                offer method to create the signature

            (see ``getBlockParams``)
            :param num refNum: parameter ref_block_num
            :param num refPrefix: parameter ref_block_prefix
            :param str expiration: expiration date
            :param Array operations:  array of operations
        """
        )
        print("args, kwargs", args, kwargs)
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and not kwargs:
                kwargs = args[0]
            if (
                "extensions" not in kwargs
                or "extensions" in kwargs
                and not kwargs.get("extensions")
            ):
                kwargs["extensions"] = Array([])
            if "signatures" not in kwargs:
                kwargs["signatures"] = Array([])
            else:
                kwargs["signatures"] = Array(
                    [Signature(unhexlify(a)) for a in kwargs["signatures"]]
                )

            if "operations" in kwargs:
                opklass = self.getOperationKlass()
                if all(not isinstance(a, opklass) for a in kwargs["operations"]):
                    kwargs["operations"] = Array(
                        [opklass(a) for a in kwargs["operations"]]
                    )
                else:
                    kwargs["operations"] = Array(kwargs["operations"])

            super().__init__(
                OrderedDict(
                    [
                        ("ref_block_num", Uint16(kwargs["ref_block_num"]),),
                        ("ref_block_prefix", Uint32(kwargs["ref_block_prefix"]),),
                        ("expiration", PointInTime(kwargs["expiration"]),),
                        ("operations", kwargs["operations"]),
                        ("extensions", kwargs["extensions"]),
                        ("signatures", kwargs["signatures"]),
                    ]
                )
            )

    @property
    def id(self):
        print("Signed_Transaction.id")
        """
        The transaction id of this transaction
        """
        # Store signatures temporarily
        sigs = self.data["signatures"]
        self.data.pop("signatures", None)
        # Generage Hash of the seriliazed version
        h = sha256(bytes(self)).digest()
        # Recover signatures
        self.data["signatures"] = sigs
        # Return properly truncated tx hash
        return hexlify(h[:20]).decode("ascii")

    def getOperationKlass(self):
        print("Signed_Transaction.get_operationKlass")
        return Operation

    def derSigToHexSig(self, s):
        print("Signed_Transaction.derSigToHexSig")
        s, junk = ecdsa_der.remove_sequence(unhexlify(s))
        if junk:
            log.debug("JUNK: %s", hexlify(junk).decode("ascii"))
        assert junk == b""
        x, s = ecdsa_der.remove_integer(s)
        y, s = ecdsa_der.remove_integer(s)
        return "%064x%064x" % (x, y)

    def deriveDigest(self, chain):
        print("Signed_Transaction.deriveDigest")
        print(self, chain)
        # Do not serialize signatures
        sigs = self.data["signatures"]
        self.data["signatures"] = []
        # Get message to sign
        #   bytes(self) will give the wire formated data according to
        #   GrapheneObject and the data given in __init__()
        self.message = unhexlify(ID) + bytes(self)
        self.digest = sha256(self.message).digest()
        # restore signatures
        self.data["signatures"] = sigs

    def verify(self, pubkeys=[], chain=PREFIX):
        print(it("green", "###############################################"))
        print("Signed_Transaction.verify")
        print(it("green", "self, pubkeys, chain"), self, pubkeys, chain)

        self.deriveDigest(chain)
        print(it("green", "self"))
        print(self)
        signatures = self.data["signatures"].data
        print(it("green", "signatures"))
        print(signatures)
        pubKeysFound = []

        for signature in signatures:
            p = verify_message(self.message, bytes(signature))
            phex = hexlify(p).decode("ascii")
            print("")
            print("")
            print(it("green", "phex"))
            print(it("green", phex))
            print(it("cyan", "len(phex)"), len(str(phex)))
            print("")
            print("")
            pubKeysFound.append(phex)

        for pubkey in pubkeys:

            print(it("green", "for pubkey in pubkeys:"))
            print(it("green", "************ pubkey ************"))
            print(it("blue", "repr(pubkey)"))
            print(repr(pubkey))

            print(it("cyan", "len(pubkey)"), len(str(pubkey)))
            print("")
            if not isinstance(pubkey, PublicKey):
                raise Exception("Pubkeys must be array of 'PublicKey'")

            k = pubkey.unCompressed()[2:]

            print(it("green", ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"))
            print(it("yellow", "k"))
            print(k)
            print(it("cyan", "len(k)"), len(str(k)))
            print(it("yellow", "pubKeysFound"))
            print(pubKeysFound)
            print(it("cyan", "len(pubKeysFound[0])"), len(pubKeysFound[0]))
            print("")
            print(it("green", ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"))

            if k not in pubKeysFound and repr(pubkey) not in pubKeysFound:
                print(
                    it(
                        "blue",
                        "if k not in pubKeysFound and repr(pubkey) "
                        + "not in pubKeysFound:",
                    )
                )
                k = PublicKey(PublicKey(k).compressed())
                f = format(k, PREFIX)  # chain_params["prefix"]) # 'BTS'
                print("")
                print(it("red", "FIXME"))
                raise Exception(f"Signature for {f} missing!")

        return pubKeysFound

    def sign(self, wifkeys, chain=PREFIX):
        print("Signed_Transaction.sign")
        """
        Sign the transaction with the provided private keys.
        """
        self.deriveDigest(chain)

        # Get Unique private keys
        self.privkeys = []
        [self.privkeys.append(item) for item in wifkeys if item not in self.privkeys]

        # Sign the message with every private key given!
        sigs = []
        for wif in self.privkeys:
            signature = sign_message(self.message, wif)
            sigs.append(Signature(signature))

        self.data["signatures"] = Array(sigs)
        return self


class Limit_order_create(GrapheneObject):  # bitsharesbase/operations.py
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and not kwargs:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("fee", Asset(kwargs["fee"])),
                        ("seller", ObjectId(kwargs["seller"], "account"),),
                        ("amount_to_sell", Asset(kwargs["amount_to_sell"]),),
                        ("min_to_receive", Asset(kwargs["min_to_receive"]),),
                        ("expiration", PointInTime(kwargs["expiration"]),),
                        ("fill_or_kill", Uint8(kwargs["fill_or_kill"])),
                        ("extensions", Array([])),
                    ]
                )
            )


class Call_order_update(GrapheneObject):
    """
    /bitsharesbase/operations.py
    """

    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and not kwargs:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("fee", Asset(kwargs["fee"])),
                        (
                            "funding_account",
                            ObjectId(kwargs["funding_account"], "account"),
                        ),
                        ("delta_collateral", Asset(kwargs["delta_collateral"])),
                        ("delta_debt", Asset(kwargs["delta_debt"])),
                        ("extensions", CallOrderExtension(kwargs["extensions"])),
                    ]
                )
            )


class CallOrderExtension(Extension):
    """
    /bitsharesbase/objects.py
    """

    def tcr(self):
        return Uint16(self) if self else None

    sorted_options = [("target_collateral_ratio", tcr)]


class Limit_order_cancel(GrapheneObject):  # bitsharesbase/operations.py
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and not kwargs:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("fee", Asset(kwargs["fee"])),
                        (
                            "fee_paying_account",
                            ObjectId(kwargs["fee_paying_account"], "account"),
                        ),
                        ("order", ObjectId(kwargs["order"], "limit_order"),),
                        ("extensions", Array([])),
                    ]
                )
            )


class Transfer(GrapheneObject):
    def __init__(self, *args, **kwargs):
        # Allow for overwrite of prefix
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and not kwargs:
                kwargs = args[0]
            prefix = kwargs.get("prefix", PREFIX)
            if "memo" in kwargs and kwargs["memo"]:
                if isinstance(kwargs["memo"], dict):
                    kwargs["memo"]["prefix"] = prefix
                    memo = Optional(Memo(**kwargs["memo"]))
                else:
                    memo = Optional(Memo(kwargs["memo"]))
            else:
                memo = Optional(None)
            super().__init__(
                OrderedDict(
                    [
                        ("fee", Asset(kwargs["fee"])),
                        ("from", ObjectId(kwargs["from"], "account")),
                        ("to", ObjectId(kwargs["to"], "account")),
                        ("amount", Asset(kwargs["amount"])),
                        ("memo", memo),
                        ("extensions", Array([])),
                    ]
                )
            )


class Asset_issue(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            prefix = kwargs.get("prefix", PREFIX)

            if len(args) == 1 and not kwargs:
                kwargs = args[0]
            if "memo" in kwargs and kwargs["memo"]:
                memo = Optional(Memo(prefix=prefix, **kwargs["memo"]))
            else:
                memo = Optional(None)
            super().__init__(
                OrderedDict(
                    [
                        ("fee", Asset(kwargs["fee"])),
                        ("issuer", ObjectId(kwargs["issuer"], "account")),
                        ("asset_to_issue", Asset(kwargs["asset_to_issue"])),
                        (
                            "issue_to_account",
                            ObjectId(kwargs["issue_to_account"], "account"),
                        ),
                        ("memo", memo),
                        ("extensions", Array([])),
                    ]
                )
            )


class Asset_reserve(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and not kwargs:
                kwargs = args[0]

            super().__init__(
                OrderedDict(
                    [
                        ("fee", Asset(kwargs["fee"])),
                        ("payer", ObjectId(kwargs["payer"], "account")),
                        ("amount_to_reserve", Asset(kwargs["amount_to_reserve"])),
                        ("extensions", Array([])),
                    ]
                )
            )


def verify_message(message, signature, hashfn=sha256):

    # graphenebase/ecdsa.py stripped of non-secp256k1 methods
    print(it("red", "verify_message...return phex"))
    # require message and signature to be bytes
    if not isinstance(message, bytes):
        message = bytes(message, "utf-8")
    if not isinstance(signature, bytes):
        signature = bytes(signature, "utf-8")

    digest = hashfn(message).digest()
    sig = signature[1:]
    # recover parameter only
    recoverParameter = bytearray(signature)[0] - 4 - 27
    # "bitwise or"; each bit of the output is 0
    # if the corresponding bit of x AND of y is 0, otherwise it's 1
    ALL_FLAGS = (
        secp256k1_lib.SECP256K1_CONTEXT_VERIFY | secp256k1_lib.SECP256K1_CONTEXT_SIGN
    )
    # ecdsa.PublicKey with additional functions to serialize
    # in uncompressed and compressed formats
    pub = secp256k1_PublicKey(flags=ALL_FLAGS)
    # recover raw signature
    sig = pub.ecdsa_recoverable_deserialize(sig, recoverParameter)
    # recover public key
    verifyPub = secp256k1_PublicKey(pub.ecdsa_recover(message, sig))
    # convert recoverable sig to normal sig
    normalSig = verifyPub.ecdsa_recoverable_convert(sig)
    # verify
    verifyPub.ecdsa_verify(message, normalSig)
    return verifyPub.serialize(compressed=True)


def isArgsThisClass(self, args):  # graphenebase/objects.py
    return len(args) == 1 and type(args[0]).__name__ == type(self).__name__


" PRIMARY TRANSACTION BACKBONE "


def build_transaction(order):
    # this performs incoming limit order api conversion
    # from human terms to graphene terms
    # humans speak:
    "account name, asset name, order number"
    "decimal amounts, rounded is just fine"
    "buy/sell/cancel"
    "amount of assets"
    "price in currency"

    # graphene speaks:
    "1.2.x, 1.3.x, 1.7.x"
    "only in integers"
    "create/cancel"
    "min_to_receive/10^receiving_precision"
    "amount_to_sell/10^selling_precision"

    # build_transaction speaks:
    "list of buy/sell/cancel human terms edicts any order in"
    "validated data request"
    "autoscale amounts if out of budget"
    "autoscale amounts if spending last bitshare"
    "bundled cancel/buy/sell transactions out; cancel first"
    "prevent inadvertent huge number of orders"
    "do not place orders for dust amounts"

    global account_id, account_name, currency_id, asset_id
    global currency_precision, asset_precision

    " VALIDATE INCOMING DATA "
    if not isinstance(order["edicts"], list):
        raise ValueError("order parameter must be list: %s" % order["edicts"])
    if not isinstance(order["nodes"], list):
        raise ValueError("order parameter must be list: %s" % order["nodes"])
    if not isinstance(order["header"], dict):
        raise ValueError("order parameter must be list: %s" % order["header"])
    # the location of the decimal place must be provided by order
    asset_precision = int(order["header"]["asset_precision"])
    # validate a.b.c identifiers of account id and asset ids
    asset_id = str(order["header"]["asset_id"])
    account_id = str(order["header"]["account_id"])
    account_name = str(order["header"]["account_name"])
    currency_precision = 5
    currency_id = "1.3.0"
    # perform checks on currency for limit and call orders
    if order["edicts"][0]["op"] in ["buy", "sell", "call"]:
        currency_precision = int(order["header"]["currency_precision"])
        currency_id = str(order["header"]["currency_id"])
    for i in [account_id, asset_id, currency_id]:
        try:
            a, b, c = i.split(".")
            int(a) == 1
            int(b) in [2, 3]
            int(c) == float(c)
        except Exception:
            raise ValueError("invalid object id %s" % i)

    " GATHER TRANSACTION HEADER DATA "
    # fetch block data via websocket request
    block = rpc_block_number()
    ref_block_num = block["head_block_number"] & 0xFFFF
    ref_block_prefix = unpack_from("<I", unhexlify(block["head_block_id"]), 4)[0]
    # fetch limit order create and cancel fee via websocket request
    fees = rpc_fees()
    # establish transaction expiration
    tx_expiration = to_iso_date(int(time() + 120))
    # initialize tx_operations list
    tx_operations = []

    " SORT INCOMING EDICTS BY TYPE AND CONVERT TO DECIMAL "
    buy_edicts = []
    sell_edicts = []
    cancel_edicts = []
    call_edicts = []
    issue_edicts = []
    reserve_edicts = []
    transfer_edicts = []
    if not login:
        for edict in order["edicts"]:
            if edict["op"] == "cancel":
                print(it("yellow", str({k: str(v) for k, v in edict.items()})))
                cancel_edicts.append(edict)
            elif edict["op"] == "buy":
                print(it("yellow", str({k: str(v) for k, v in edict.items()})))
                buy_edicts.append(edict)
            elif edict["op"] == "sell":
                print(it("yellow", str({k: str(v) for k, v in edict.items()})))
                sell_edicts.append(edict)
            elif edict["op"] == "call":
                print(it("yellow", str({k: str(v) for k, v in edict.items()})))
                call_edicts.append(edict)
            elif edict["op"] == "issue":
                print(it("yellow", str({k: str(v) for k, v in edict.items()})))
                issue_edicts.append(edict)
            elif edict["op"] == "reserve":
                print(it("yellow", str({k: str(v) for k, v in edict.items()})))
                reserve_edicts.append(edict)
            elif edict["op"] == "transfer":
                print(it("yellow", str({k: str(v) for k, v in edict.items()})))
                transfer_edicts.append(edict)

    for i in range(len(buy_edicts)):
        buy_edicts[i]["amount"] = decimal(buy_edicts[i]["amount"])
        buy_edicts[i]["price"] = decimal(buy_edicts[i]["price"])
    for i in range(len(sell_edicts)):
        sell_edicts[i]["amount"] = decimal(sell_edicts[i]["amount"])
        sell_edicts[i]["price"] = decimal(sell_edicts[i]["price"])
    if DEV:
        print("early edicts")
        edicts = cancel_edicts + buy_edicts + sell_edicts
        pprint(edicts)

    " TRANSLATE CANCEL ORDERS TO GRAPHENE "
    for edict in cancel_edicts:
        if "ids" not in edict.keys():
            edict["ids"] = ["1.7.X"]
        if "1.7.X" in edict["ids"]:  # the "cancel all" signal
            # for cancel all op, we collect all open orders in 1 market
            edict["ids"] = rpc_open_orders()
            print(it("yellow", str(edict)))
        for order_id in edict["ids"]:
            # confirm it is good 1.7.x format:
            order_id = str(order_id)
            a, b, c = order_id.split(".", 2)
            assert int(a) == 1
            assert int(b) == 7
            assert int(c) == float(c) > 0
            # create cancel fee ordered dictionary
            fee = OrderedDict([("amount", fees["cancel"]), ("asset_id", "1.3.0")])
            # create ordered operation dicitonary for this edict
            operation = [
                2,  # two means "Limit_order_cancel"
                OrderedDict(
                    [
                        ("fee", fee),
                        ("fee_paying_account", account_id),
                        ("order", order_id),
                        ("extensions", []),
                    ]
                ),
            ]
            # append the ordered dict to the tx operations list
            tx_operations.append(operation)
    if DEV:
        print("after cancel edicts")
        edicts = cancel_edicts + buy_edicts + sell_edicts
        pprint(edicts)

    " SCALE ORDER SIZE TO FUNDS ON HAND "
    if (AUTOSCALE or BTS_FEES) and not login:
        currency, assets, bitshares = rpc_balances()
        if AUTOSCALE and len(buy_edicts + sell_edicts):
            # autoscale buy edicts
            if len(buy_edicts):
                currency_value = 0
                # calculate total value of each amount in the order
                for i in range(len(buy_edicts)):
                    currency_value += buy_edicts[i]["amount"] * buy_edicts[i]["price"]
                # scale the order amounts to means
                scale = SIXSIG * currency / (currency_value + SATOSHI)
                if scale < 1:
                    print(
                        it("yellow", "ALERT: scaling buy edicts to means: %.3f" % scale)
                    )
                    for i in range(len(buy_edicts)):
                        buy_edicts[i]["amount"] *= scale
            # autoscale sell edicts
            if len(sell_edicts):
                asset_total = 0
                # calculate total amount in the order
                for i in range(len(sell_edicts)):
                    asset_total += sell_edicts[i]["amount"]
                scale = SIXSIG * assets / (asset_total + SATOSHI)
                # scale the order amounts to means
                if scale < 1:
                    print(
                        it(
                            "yellow",
                            "ALERT: scaling sell edicts to means: %.3f" % scale,
                        )
                    )
                    for i in range(len(sell_edicts)):
                        sell_edicts[i]["amount"] *= scale
        if DEV:
            print("after autoscale edicts")
            edicts = cancel_edicts + buy_edicts + sell_edicts
            pprint(edicts)

        " ALWAYS SAVE LAST 2 BITSHARES FOR FEES "
        if BTS_FEES and (
            len(buy_edicts + sell_edicts) and ("1.3.0" in [asset_id, currency_id])
        ):
            # print(bitshares, 'BTS balance')
            # when BTS is the currency don't spend the last 2
            if currency_id == "1.3.0" and len(buy_edicts):
                bts_value = 0
                # calculate total bts value of each amount in the order
                for i in range(len(buy_edicts)):
                    bts_value += buy_edicts[i]["amount"] * buy_edicts[i]["price"]
                # scale the order amounts to save last two bitshares
                scale = SIXSIG * max(0, (bitshares - 2)) / (bts_value + SATOSHI)
                if scale < 1:
                    print(
                        it("yellow", "ALERT: scaling buy edicts for fees: %.4f" % scale)
                    )
                    for i in range(len(buy_edicts)):
                        buy_edicts[i]["amount"] *= scale
            # when BTS is the asset don't sell the last 2
            if asset_id == "1.3.0" and len(sell_edicts):
                bts_total = 0
                # calculate total of each bts amount in the order
                for i in range(len(sell_edicts)):
                    bts_total += sell_edicts[i]["amount"]
                scale = SIXSIG * max(0, (bitshares - 2)) / (bts_total + SATOSHI)
                # scale the order amounts to save last two bitshares
                if scale < 1:
                    print(
                        it(
                            "yellow",
                            "ALERT: scaling sell edicts for fees: %.4f" % scale,
                        )
                    )
                    for i in range(len(sell_edicts)):
                        sell_edicts[i]["amount"] *= scale
    if DEV:
        print("after bts fee edicts")
        edicts = cancel_edicts + buy_edicts + sell_edicts
        pprint(edicts)
    # after scaling recombine buy and sell
    create_edicts = buy_edicts + sell_edicts

    " REMOVE DUST EDICTS "
    if DUST and len(create_edicts):
        ce = []
        dust = DUST * 100000 / 10 ** asset_precision
        for i in range(len(create_edicts)):
            if create_edicts[i]["amount"] > dust:
                ce.append(create_edicts[i])
            else:
                print(
                    it("red", "WARN: removing dust threshold %s order" % dust),
                    create_edicts[i],
                )
        create_edicts = ce[:]  # copy as new list
        del ce
    if DEV:
        print("after dust edicts")
        edicts = cancel_edicts + buy_edicts + sell_edicts
        pprint(edicts)

    " TRANSLATE LIMIT ORDERS TO GRAPHENE "
    for i in range(len(create_edicts)):
        price = create_edicts[i]["price"]
        amount = create_edicts[i]["amount"]
        op_exp = int(create_edicts[i]["expiration"])
        # convert zero expiration flag to "really far in future"
        if op_exp == 0:
            op_exp = END_OF_TIME
        op_expiration = to_iso_date(op_exp)
        # we'll use ordered dicts and put items in api specific order
        min_to_receive = OrderedDict({})
        amount_to_sell = OrderedDict({})
        # derive min_to_receive & amount_to_sell from price & amount
        # means SELLING currency RECEIVING assets
        if create_edicts[i]["op"] == "buy":
            min_to_receive["amount"] = int(amount * 10 ** asset_precision)
            min_to_receive["asset_id"] = asset_id
            amount_to_sell["amount"] = int(amount * price * 10 ** currency_precision)
            amount_to_sell["asset_id"] = currency_id
        # means SELLING assets RECEIVING currency
        if create_edicts[i]["op"] == "sell":
            min_to_receive["amount"] = int(amount * price * 10 ** currency_precision)
            min_to_receive["asset_id"] = currency_id
            amount_to_sell["amount"] = int(amount * 10 ** asset_precision)
            amount_to_sell["asset_id"] = asset_id
        # Limit_order_create fee ordered dictionary
        fee = OrderedDict([("amount", fees["create"]), ("asset_id", "1.3.0")])
        # create ordered dicitonary from each buy/sell operation
        operation = [
            1,
            OrderedDict(
                [
                    ("fee", fee),  # OrderedDict
                    ("seller", account_id),  # "a.b.c"
                    ("amount_to_sell", amount_to_sell),  # OrderedDict
                    ("min_to_receive", min_to_receive),  # OrderedDict
                    ("expiration", op_expiration),  # ISO8601
                    ("fill_or_kill", KILL_OR_FILL),  # bool
                    ("extensions", [],),  # always empty list for our purpose
                ]
            ),
        ]
        tx_operations.append(operation)
    if DEV:
        print("after limit order edicts")
        edicts = cancel_edicts + buy_edicts + sell_edicts
        pprint(edicts)

    " TRANSLATE CALL ORDERS TO GRAPHENE "
    for idx, call in enumerate(call_edicts):
        # convert to graphene amount, asset_id type
        delta_debt = OrderedDict(
            [
                ("amount", int(call["debt_delta"] * 10 ** asset_precision)),
                ("asset_id", asset_id),
            ]
        )
        delta_collateral = OrderedDict(
            [
                ("amount", int(call["collateral_delta"] * 10 ** currency_precision)),
                ("asset_id", currency_id),
            ]
        )
        # call fee ordered dictionary of graphene amount, asset_id
        fee = OrderedDict([("amount", fees["call"]), ("asset_id", "1.3.0")])
        # call ordered dictionary from each buy/sell operation
        operation = [
            3,
            OrderedDict(
                [
                    ("fee", fee),
                    ("funding_account", account_id),
                    ("delta_collateral", delta_collateral),
                    ("delta_debt", delta_debt),
                    (
                        "extensions",
                        OrderedDict(
                            [("target_collateral_ratio", int(1000 * call["tcr"]))]
                        ),
                    ),
                ]
            ),
        ]
        # add this op to our list of ops
        tx_operations.append(operation)

    " TRANSLATE TRANSFER ORDERS TO GRAPHENE "
    for idx, transfer in enumerate(transfer_edicts):
        # convert to graphene amount, asset_id type
        # class Transfer(GrapheneObject): # OPERATION ID 0 "transfer"
        fee = OrderedDict([("amount", fees["transfer"]), ("asset_id", "1.3.0")])
        graphene_amount = int(transfer["amount"] * 10 ** asset_precision)
        amount_dict = OrderedDict([("amount", graphene_amount), ("asset_id", asset_id)])
        # transfer ordered dictionary from each buy/sell operation
        operation = [
            0,
            OrderedDict(
                [
                    ("fee", fee),
                    ("from", account_id),
                    ("to", transfer["account_id"]),
                    ("amount", amount_dict),
                    # ("memo", transfer["memo"]), # FIXME memos are not yet implemented
                    ("extensions", []),
                ]
            ),
        ]
        tx_operations.append(operation)
    " TRANSLATE ISSUE ORDERS TO GRAPHENE "
    for idx, issue in enumerate(issue_edicts):
        # convert to graphene amount, asset_id type
        # class Asset_issue(GrapheneObject): # OPERATION ID 14 "asset_issue"
        fee = OrderedDict([("amount", fees["issue"]), ("asset_id", "1.3.0")])
        graphene_amount = issue["amount"] * 10 ** asset_precision
        amount_dict = OrderedDict([("amount", graphene_amount), ("asset_id", asset_id)])
        # issue ordered dictionary from each buy/sell operation
        operation = [
            14,
            OrderedDict(
                [
                    ("fee", fee),
                    ("issuer", account_id),
                    ("asset_to_issue", amount_dict),
                    ("issue_to_account", issue["account_id"]),
                    # ("memo", issue["memo"]), # FIXME memos are not yet implemented
                    ("extensions", []),
                ]
            ),
        ]
        tx_operations.append(operation)
    " TRANSLATE RESERVE ORDERS TO GRAPHENE "
    for idx, reserve in enumerate(reserve_edicts):
        # convert to graphene amount, asset_id type
        # class Asset_reserve(GrapheneObject): # OPERATION ID 15 "asset_reserve"
        fee = OrderedDict([("amount", fees["reserve"]), ("asset_id", "1.3.0")])
        graphene_amount = reserve["amount"] * 10 ** asset_precision
        amount_dict = OrderedDict([("amount", graphene_amount), ("asset_id", asset_id)])
        # reserve ordered dictionary from each buy/sell operation
        operation = [
            15,
            OrderedDict(
                [
                    ("fee", fee),
                    ("payer", account_id),
                    ("amount_to_reserve", amount_dict),
                    ("extensions", []),
                ]
            ),
        ]
        tx_operations.append(operation)
    if DEV:
        print("after call order edicts")
        edicts = cancel_edicts + buy_edicts + sell_edicts + call_edicts
        pprint(edicts)

    " TRANSLATE LOG IN TO DUMMY GRAPHENE CANCEL ORDER "
    if login:
        fee = OrderedDict([("amount", 0), ("asset_id", "1.3.0")])
        operation = [
            2,
            OrderedDict(
                [
                    ("fee", fee),
                    ("fee_paying_account", account_id),
                    ("order", "1.7.0"),
                    ("extensions", []),
                ]
            ),
        ]
        tx_operations.append(operation)
    # prevent inadvertent huge number of orders
    tx_operations = tx_operations[:LIMIT]
    # the tx is just a regular dictionary we will convert to json later
    # the operations themselves must still be an OrderedDict
    tx = {
        "ref_block_num": ref_block_num,
        "ref_block_prefix": ref_block_prefix,
        "expiration": tx_expiration,
        "operations": tx_operations,
        "signatures": [],
        "extensions": [],
    }
    if DEV:
        pprint(tx)
    return tx


def serialize_transaction(tx):
    """
    {"method":"call","params":[
        2,
        "get_required_signatures",
            [{"ref_block_num":0,
            "ref_block_prefix":0,
            "expiration":"1970-01-01T00:00:00",
            "operations":
                [[3,{
                "fee":{"amount":"48260","asset_id":"1.3.0"},
                "funding_account":"1.2.11111111",
                "delta_collateral":{"amount":"1","asset_id":"1.3.5650"},
                "delta_debt":{"amount":"0","asset_id":"1.3.5662"},
                "extensions":{"target_collateral_ratio":2000}}]],
                "extensions":[],"signatures":[]},
                ["BTS6upQe7upQe7upQe7upQe7upQe7upQe7upQe7upQe7upQe7upQe7"]]],
            "id":371}
    """

    if tx["operations"] == []:
        return tx, b""

    # gist.github.com/xeroc/9bda11add796b603d83eb4b41d38532b
    print(it("blue", "serialize_transaction"))
    print(it("yellow", "IF WE DO EVERYTHING RIGHT:"))
    print(it("green", "rpc_tx_hex = manual_tx_hex"))
    # RPC call for ordered dicts which are dumped by the query
    print(it("yellow", "get RPC tx hex..."))

    tx_ops = tx["operations"]
    for idx, _ in enumerate(tx_ops):
        if "memo" in tx_ops[idx][1].keys():
            if tx_ops[idx][1]["memo"] == "":
                tx_ops[idx][1] = {
                    k: v for k, v in tx_ops[idx][1].items() if k != "memo"
                }
    rpc_tx = dict(tx)
    rpc_tx["operations"] = tx_ops
    rpc_tx_hex = rpc_get_transaction_hex_without_sig(json_loads(json_dumps(rpc_tx)))
    print(it("yellow", "build manual tx hex..."))
    buf = b""  # create an empty byte string buffer
    # add block number, prefix, and tx expiration to the buffer
    buf += pack("<H", tx["ref_block_num"])  # 2 byte int
    buf += pack("<I", tx["ref_block_prefix"])  # 4 byte int
    buf += pack("<I", from_iso_date(tx["expiration"]))  # 4 byte int
    # add length of operations list to buffer
    buf += bytes(varint(len(tx["operations"])))
    # add the operations list to the buffer in graphene type fashion
    for op in tx["operations"]:
        # print(op[0])  # Int (1=create, 2=cancel)
        # print(op[1])  # OrderedDict of operations
        buf += varint(op[0])
        if op[0] == 0:
            buf += bytes(Transfer(op[1]))
        if op[0] == 1:
            buf += bytes(Limit_order_create(op[1]))
        if op[0] == 2:
            buf += bytes(Limit_order_cancel(op[1]))
        if op[0] == 3:
            buf += bytes(Call_order_update(op[1]))
        if op[0] == 14:
            buf += bytes(Asset_issue(op[1]))
        if op[0] == 15:
            buf += bytes(Asset_reserve(op[1]))

    # add legth of (empty) extensions list to buffer
    buf += bytes(varint(len(tx["extensions"])))  # effectively varint(0)
    # this the final manual transaction hex, which should match rpc
    manual_tx_hex = hexlify(buf)
    enablePrint()
    print(manual_tx_hex, "\n")
    blockPrint()
    print(it("red", "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"))
    print("   rpc_tx_hex:  ", rpc_tx_hex)
    print("manual_tx_hex:  ", manual_tx_hex)
    print(it("red", "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"))
    print(it("yellow", "assert (rpc_tx_hex == manual_tx_hex)"))
    assert rpc_tx_hex == manual_tx_hex, "Serialization Failed"
    print(it("green", "Serialization Success"))
    # prepend the chain ID to the buffer to create final serialized msg
    message = unhexlify(ID) + buf
    return tx, message


def sign_transaction(tx, message):

    # graphenebase/ecdsa.py
    # tools.ietf.org/html/rfc6979
    # @xeroc/steem-transaction-signing-in-a-nutshell
    # @dantheman/steem-and-bitshares-cryptographic-security-update

    # deterministic signatures retain the cryptographic
    # security features associated with digital signatures
    # but can be more easily implemented
    # since they do not need high-quality randomness

    # 1 in 4 signatures are randomly canonical; "normal form"
    # using the other three causes vulnerability to maleability attacks
    # as a metaphor; "require reduced fractions in simplest terms"
    def canonical(sig):
        sig = bytearray(sig)
        # 0x80 hex = 10000000 binary = 128 integer
        ret = (
            not (int(sig[0]) & 0x80)
            and not (sig[0] == 0 and not (int(sig[1]) & 0x80))
            and not (int(sig[32]) & 0x80)
            and not (sig[32] == 0 and not (int(sig[33]) & 0x80))
        )
        print(it("green", "canonical"), it("cyan", str(ret)))
        print(sig)
        return ret  # true/false

    # create fixed length representation of arbitrary length data
    # this will thoroughly obfuscate and compress the transaction
    # signing large data is computationally expensive and time consuming
    # the hash of the data is a relatively small
    # signing hash is more efficient than signing serialization
    digest = sha256(message).digest()
    print(digest)
    """
    ECDSA
    eliptical curve digital signature algorithm
    this is where the real hocus pocus lies
    all of the ordering, typing, serializing, and digesting
    culminates with the message meeting the wif
    """
    # 8 bit string representation of private key
    p = bytes(PrivateKey(wif))
    # create some arbitrary data used by the nonce generation
    ndata = secp256k1_ffi.new("const int *ndata")
    ndata[0] = 0  # it adds "\0x00", then "\0x00\0x00", etc..
    while True:  # repeat process until deterministic and cannonical
        ndata[0] += 1  # increment the arbitrary nonce
        # obtain compiled/binary private key from the wif
        privkey = secp256k1_PrivateKey(p, raw=True)
        print(it("red", str(privkey)))
        print(privkey)
        # create a new recoverable 65 byte ECDSA signature
        sig = secp256k1_ffi.new("secp256k1_ecdsa_recoverable_signature *")
        # parse a compact ECDSA signature (64 bytes + recovery id)
        # returns: 1 = deterministic; 0 = not deterministic
        deterministic = secp256k1_lib.secp256k1_ecdsa_sign_recoverable(
            privkey.ctx,  # initialized context object
            sig,  # array where signature is held
            digest,  # 32-byte message hash being signed
            privkey.private_key,  # 32-byte secret key
            secp256k1_ffi.NULL,  # default nonce function
            ndata,  # incrementing nonce data
        )
        if not deterministic:
            print("not deterministic, try again...")
            continue
        # we derive the recovery paramter
        # which simplifies the verification of the signature
        # it links the signature to a single unique public key
        # without this parameter, the back-end would need to test
        # for multiple public keys instead of just one
        signature, i = privkey.ecdsa_recoverable_serialize(sig)
        # we ensure that the signature is canonical; simplest form
        if canonical(signature):
            # add 4 and 27 to stay compatible with other protocols
            i += 4  # compressed
            i += 27  # compact
            # and have now obtained our signature
            break
    # having derived a valid canonical signature
    # we format it in its hexadecimal representation
    # and add it our transactions signatures
    # note that we do not only add the signature
    # but also the recover parameter
    # this kind of signature is then called "compact signature"
    signature = hexlify(pack("<B", i) + signature).decode("ascii")
    tx["signatures"].append(signature)
    print(it("blue", 'tx["signatures"].append(signature)'))
    print(signature)
    print("")
    enablePrint()
    print(tx, "\n")
    blockPrint()

    return tx


def verify_transaction(tx):
    # gist.github.com/xeroc/9bda11add796b603d83eb4b41d38532b
    # once you have derived your new tx including the signatures
    # verify your transaction and it's signature
    print(it("blue", "verify_transaction"))
    print(it("blue", "tx2 = Signed_Transaction(**tx)"))
    tx2 = Signed_Transaction(**tx)
    print(tx2)

    print(it("blue", 'tx2.deriveDigest("BTS")'))
    tx2.deriveDigest(PREFIX)

    print(it("blue", "pubkeys = [PrivateKey(wif).pubkey]"))
    pubkeys = [PrivateKey(wif).pubkey]
    print(pubkeys)

    print(it("blue", 'tx2.verify(pubkeys, "BTS")'))
    tx2.verify(pubkeys, PREFIX)

    return tx


" THE BROKER METHOD"


def broker(order):
    "broker(order) --> execute(signal, order)"
    # insistent timed multiprocess wrapper for authorized ops
    # covers all incoming buy/sell/cancel authenticated requests
    # if command does not execute in time: terminate and respawn
    # serves to force disconnect websockets if hung
    "up to ATTEMPTS chances; each PROCESS_TIMEOUT long: else abort"
    # signal is switched to 0 after execution to end the process

    global_constants()
    global_variables()
    control_panel()

    log_in = False
    if order["edicts"][0]["op"] == "login":
        log_in = True

    signal = Value("i", 0)
    auth = Value("i", 0)
    i = 0
    while (i < ATTEMPTS) and not signal.value:
        i += 1
        print("\nmanualSIGNING authentication attempt:", i, ctime(), "\n")
        child = Process(target=execute, args=(signal, log_in, auth, order))
        child.daemon = False
        child.start()
        if JOIN:  # means main script will not continue till child done
            child.join(PROCESS_TIMEOUT)
        # to parallel process a broker(order) see microDEX.py
    if log_in:
        if auth.value == 1:
            return True
        else:
            return False


def execute(signal, log_in, auth, order):

    global nodes, account_id, account_name, wif, login, authenticated

    login = log_in

    start = time()
    if not DEV:  # disable printing with DEV=False
        blockPrint()
    nodes = order["nodes"]
    account_id = order["header"]["account_id"]
    account_name = order["header"]["account_name"]
    wif = order["header"]["wif"]
    wss_handshake()

    if not DEV:
        enablePrint()
    try:
        tx = build_transaction(order)
    except Exception as e:
        trace(e)
    if len(tx["operations"]):  # if there are any orders
        if not DEV:  # disable printing with DEV=False
            blockPrint()
        authenticated = False
        # perform ecdsa on serialized transaction
        try:
            tx, message = serialize_transaction(tx)
        except Exception as e:
            trace(e)
        try:
            signed_tx = sign_transaction(tx, message)
            print(signed_tx)
        except Exception as e:
            trace(e)
        if login:
            # PublicKey.__init__ switches "authenticated"
            if not DEV:
                enablePrint()
            print("authenticated", authenticated)
            if authenticated:
                auth.value = 1
        else:
            signed_tx = verify_transaction(signed_tx)
            if not DEV:
                enablePrint()
            broadcasted_tx = rpc_broadcast_transaction(signed_tx)
    else:
        print(it("red", "manualSIGNING rejected your order"), order["edicts"], "\n")
    print("manualSIGNING process elapsed: %.3f sec" % (time() - start), "\n\n")
    signal.value = 1
    return None


def prototype_order(network):
    """
    each order will require a cached nodes list
    and a cached header with account and asset metadata
    """
    nodes = bitshares_nodes()
    header = {
        "asset_id": GATE["uia"][network]["asset_id"],
        "asset_precision": GATE["uia"][network]["asset_precision"],
        "account_id": GATE["uia"][network]["issuer_id"],
        "account_name": GATE["uia"][network]["issuer_public"],
        "wif": GATE["uia"][network]["issuer_private"],
    }
    order = {
        "header": header,
        "nodes": nodes,
    }
    return order


def issue(network, amount, account_id):
    """
    Put matching UIA.XZY in user's BitShares wallet upon deposit.
    """
    order = prototype_order(network)
    order["edicts"] = [{"op": "issue", "amount": amount, "account_id": account_id}]
    print(order["header"]["account_name"], order["header"]["asset_id"], order["edicts"])
    broker(order)


def reserve(network, amount):
    """
    Put matching UIA.XZY into the reserve pool upon withdrawal.
    """
    order = prototype_order(network)
    order["edicts"] = [{"op": "reserve", "amount": amount}]
    print(order["header"]["account_name"], order["header"]["asset_id"], order["edicts"])
    broker(order)


" IN SCRIPT DEMONSTRATION "


def log_in():

    global wif, account_name, account_id
    global order, order1, order2, order3, nodes

    print("\033c")  # clear terminal
    print("")
    print(it("green", "                                       y**2 = x**3 + 7"))
    print("************************************************************")
    print("")
    print(it("green", " manualSIGNING - BUY/SELL/CANCEL OPS v%.8f alpha" % VERSION))
    print("")
    print("************************************************************")
    print("")
    print("             given a buy/sell/cancel order and wif:")
    print("                  convert to graphene terms")
    print("                  serialize the transaction")
    print("                       perform ECDSA")
    print("                  broadcast to a public node")
    print("               use only standard python modules")
    print("              spell the rest out here concisely")
    print("")
    print("           if you input name and wif this script will:")
    print("")
    print(it("red", "          BUY 10 BTS with OPEN.BTC at 0.00000100"))
    print("")
    print(it("green", "              WITHOUT IMPORTING PYBITSHARES "))
    print("")
    print("enter account name (press ENTER for demo)")
    print("")
    account_name = input("account name: ")
    print("")
    print("lookup account_id...")
    print("")
    if account_name == "":
        account_name = "fd"  # some random acct
        print("using mock account for demo: %s" % account_name)
    nodes = order1["nodes"]
    # create a websocket connection
    wss_handshake()
    # convert account name to id via rpc request
    account_id = rpc_account_id()
    print(account_id)
    print("")
    # input wallet import format key for authentication
    wif = getpass(prompt="enter wif (press ENTER for demo): ")
    if not wif:
        # some random wif
        wif = "5JLw5dgQAx6rhZEgNN5C2ds1V47RweGshynFSWFbaMohsYsBvE8"
        print("using sample wallet import format (wif)")
        print(wif)
        print("")
        print(it("green", "BEGIN DEMO"))
        print("")
    # add wif, account_id, and account_name to sample order headers
    order1["header"]["wif"] = wif
    order1["header"]["account_id"] = account_id
    order1["header"]["account_name"] = account_name
    order2["header"]["wif"] = wif
    order2["header"]["account_id"] = account_id
    order2["header"]["account_name"] = account_name
    order3["header"]["wif"] = wif
    order3["header"]["account_id"] = account_id
    order3["header"]["account_name"] = account_name
    print(" 1:buy, 2:cancel, 3:authenticate ")
    select = 0
    while select not in [1, 2, 3]:
        select = int(input("1, 2, or 3? "))
    if select == 1:
        order = order1
    if select == 2:
        order = order2
    if select == 3:
        order = order3


def demo():
    # this is the backbone of events for the demo
    """
    receive order
    build graphene transaction
    serialize transaction
    sign transaction
    verify transaction
    broadcast transaction
    """

    try:
        print(it("purple", "======================================"))
        print(it("purple", "receive order                         "))
        print(it("purple", "======================================"))
        pprint(order)
        print("")
    except Exception as e:
        trace(e)

    try:
        print(it("purple", "======================================"))
        print(it("purple", "build graphene transaction from order "))
        print(it("purple", "======================================"))
        tx = build_transaction(order)
        pprint(tx)
        print("")
    except Exception as e:
        trace(e)
    if len(tx["operations"]):
        try:
            print(it("purple", "======================================"))
            print(it("purple", "serialize transaction bytes string    "))
            print(it("purple", "======================================"))
            tx, message = serialize_transaction(tx)
            pprint(tx)
            print("")
        except Exception as e:
            trace(e)

        try:
            print(it("purple", "======================================"))
            print(it("purple", "sign transaction with wif             "))
            print(it("purple", "======================================"))
            signed_tx = sign_transaction(tx, message)
            pprint(signed_tx)
            print("")
        except Exception as e:
            trace(e)

        try:
            print(it("purple", "======================================"))
            print(it("purple", "verify the signature on transaction   "))
            print(it("purple", "======================================"))
            signed_tx = verify_transaction(signed_tx)
            pprint(signed_tx)
            print("")
        except Exception as e:
            trace(e)

        try:
            print(it("purple", "======================================"))
            print(it("purple", "broadcast transaction                 "))
            print(it("purple", "======================================"))
            broadcasted_tx = rpc_broadcast_transaction(signed_tx)
            pprint(broadcasted_tx)
            print("")
        except Exception as e:
            trace(e)
    else:
        print("no operations to broadcast")

    try:
        ws.close()
        print(it("purple", "connection terminated"))
    except Exception as e:
        trace(e)
    print("")
    print("END")


def main():

    sample_orders()
    global_constants()
    global_variables()
    control_panel()
    log_in()
    demo()


if __name__ == "__main__":

    main()
