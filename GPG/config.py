"""
config.py
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

Gateway Configuration Details
"""


def configure():
    """
    Manually input account details and gateway asset information here
    """
    # FIXME don't keep private keys in a config file:
    # should build encrypted "wallet", but this is outside of the scope of the task
    return {
        "test": {  # test client account is used only in unit tests
            "bts": {
                "id": "",  # bitshares account id
                "public": "",  # bitshares account name
                "private": "",  # wif
            },
            "eos": {"public": "", "private": "",},  # eosio account name  # wif
            "xrp": {"public": "", "private": "",},
        },
        "gate": {  # production gateway account details
            "uia": {  # dict of BitShares gateway uia's
                "chain": {
                    "prefix": "BTS",
                    # bitsharesbase/chains.py
                    "id": "4018"
                    + "d7844c78f6a6c41c6a552b898022310fc5dec06da467ee7905a8dad512c8",
                },
                "eos": {
                    "asset_id": "",  # "1.3.x"
                    "dynamic_id": "",  # "2.3.x"
                    "asset_name": "",  # all caps
                    "asset_precision": 0,  # int()
                    "issuer_id": "",  # "1.2.x"
                    "issuer_public": "",  # bitshares account name
                    "issuer_private": "",  # wif
                },
                "xrp": {
                    "asset_id": "",  # "1.3.x"
                    "dynamic_id": "",  # "2.3.x"
                    "asset_name": "",  # all caps
                    "asset_precision": 0,  # int()
                    "issuer_id": "",  # "1.2.x"
                    "issuer_public": "",  # bitshares account name
                    "issuer_private": "",  # wif
                },
            },
            "eos": [  # List of Eosio foreign chain gateway accounts, min 2
                {"public": "", "private": "",},  # eosio account name  # wif
                {"public": "", "private": "",},  # eosio account name  # wif
                {"public": "", "private": "",},  # eosio account name  # wif
                # etc.
            ],
            "xrp": [  # List of Ripple foreign chain gateway accounts, min 2
                {"public": "", "private": "",},
                {"public": "", "private": "",},
                {"public": "", "private": "",},
                # etc.
            ],
        },
    }
