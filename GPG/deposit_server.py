"""
deposit_server.py
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

Falcon API Server for Gateway Deposit Requests

    upon deposit offer address
    upon receipt issue UIA
"""

# DISABLE SELECT PYLINT TESTS
# pylint: disable=too-few-public-methods, no-self-use, too-many-function-args
# pylint: disable=bad-continuation

# STANDARD PYTHON MODULES
import time
from subprocess import call
from multiprocessing import Process
from json import dumps as json_dumps
from wsgiref.simple_server import make_server

# THIRD PARTY MODULES
from falcon import App, HTTP_200

# GRAPHENE PYTHON GATEWAY MODULES
from GPG.listener_eosio import listener_eosio
from GPG.listener_ripple import listener_ripple
from GPG.utilities import it, json_ipc, timestamp, line_number, milleseconds
from GPG.config import configure
from GPG.gateway_state import lock_address

# GLOBAL CONSTANTS
GATE = configure()["gate"]


class GatewayDepositServer:
    """
    Provide Webserver Public API for deposit gateway service
    """

    def on_get(self, req, resp):
        """
        When there is a get request made to the deposit server api
        User GET request includes the client_id's BitShares account_name
        Select a gateway wallet from list currently available; remove it from the list
        the available address list will be stored in a json_ipc text pipe
        Server RESPONSE is deposit address and timeout
        After timeout or deposit return address to text pipe list
        """
        # create a millesecond nonce to log this event
        nonce = milleseconds()
        # extract the incoming parameters to a dictionary
        data = dict(req.params)
        timestamp()
        line_number()
        print(it("red", "DEPOSIT SERVER RECEIVED A GET REQUEST"), "\n")
        call(["hostname", "-I"])
        print(data, "\n")
        client_id = data["client_id"]
        uia = data["uia_name"]
        # translate the incoming uia request to the appropriate network
        network = ""
        if uia == GATE["uia"]["xrp"]["asset_name"]:
            network = "xrp"
        elif uia == GATE["uia"]["eos"]["asset_name"]:
            network = "eos"
        print("network", network, "\n")
        if network in {"xrp", "eos"}:
            # lock an address until this transaction is complete
            gateway_idx = lock_address(network)
            print("gateway index", gateway_idx, "\n")
            if gateway_idx is not None:
                timestamp()
                line_number()
                deposit_address = GATE[network][gateway_idx]["public"]
                print("gateway address", deposit_address, "\n")
                confirm_time = {
                    "eos": 30,
                    "xrp": 2,
                }
                # format a response json
                msg = json_dumps(
                    {
                        "response": "success",
                        "server_time": nonce,
                        "deposit_address": deposit_address,
                        "gateway_timeout": "30 MINUTES",
                        "msg": (
                            f"Welcome {client_id}, please deposit your gateway issued "
                            + f"{network} asset, to the {uia} gateway 'deposit_address' "
                            + "in this response.  Make ONE transfer to this address, "
                            + "within the gateway_timeout specified. Transactions on "
                            + f"this network take about {confirm_time[network]} "
                            + "minutes to confirm."
                        ),
                    }
                )
                print(
                    it("red", f"STARTING {network} LISTENER TO ISSUE to {client_id}"),
                    "\n",
                )
                # dispatch the appropriate listener protocol
                listen = {"eos": listener_eosio, "xrp": listener_ripple}
                # in subprocess listen for payment from client_id to gateway[idx]
                # upon receipt issue asset, else timeout
                listener = Process(
                    target=listen[network],
                    args=(gateway_idx, None, "issue", client_id, nonce),
                )
                listener.start()
                print(f"{network}listener started", "\n")

            else:
                msg = json_dumps(
                    {
                        "response": "error",
                        "server_time": nonce,
                        "msg": f"all {uia} gateway addresses are in use, "
                        + "please try again later",
                    }
                )

        else:
            msg = json_dumps(
                {
                    "response": "error",
                    "server_time": nonce,
                    "msg": f"{uia} is an invalid gateway UIA, please try again",
                }
            )
        # log the response and build the response body with a data dictionary
        doc = f"{str(nonce)}_{uia}_{client_id}.txt"
        json_ipc(doc=doc, text=msg)
        time.sleep(5)  # allow some time for listener to start before offering address
        print(msg, "\n")
        resp.body = msg
        resp.status = HTTP_200


def api_server():
    """
    spawn a run forever api server instance and add routing information
    """
    app = App()
    app.add_route("/gateway", GatewayDepositServer())
    print(it("red", "INITIALIZING DEPOSIT SERVER"))
    print("serving http at")
    call(["hostname", "-I"])
    with make_server("", 8000, app) as httpd:
        httpd.serve_forever()
