"""
nodes.py
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

public api endpoints

SECURITY ADVISORY: best to use a "personal node" in production
"""


def eosio_nodes():
    """
    EOSIO https rest api endpoints tested MAY 2020
    """
    # alternatively you can use single private node in list
    # if using more than 1 node it is best to use at least 5
    return ["https://api.eosdetroit.io"]
   
    # "https://api.tokenika.io",
    # "https://api1.eosasia.one",
    # "https://eos.greymass.com",
    # "https://api.eosdetroit.io",
    # "https://bp.cryptolions.io",
    # "https://mainnet.eoscannon.io",
    # "https://user-api.eoseoul.io",
    # "https://node.eosflare.io",
    # "https://api.eossweden.se",
    # "https://eosbp.atticlab.net",
    # "https://node1.eosphere.io",
    # "https://node2.eosphere.io",



def bitshares_nodes():
    """
    Bitshares websocket endpoints tested JAN 2021
    """
    # alternatively you can use single private node in list
    # if using more than 1 node it is best to use at least 5
    return [
        "wss://newyork.bitshares.im/ws", 
        "wss://api.bts.mobi/wss", 
        "wss://node1.deex.exchange/ws", 
        "wss://api.dex.trading/wss", 
        "wss://eu.nodes.bitshares.ws/wss", 
        "wss://nexus01.co.uk/ws", 
        "wss://public.xbts.io/wss", 
        "wss://node.xbts.io/ws", 
        "wss://api.bitshares.bhuz.info/ws", 
        "wss://dex.iobanker.com/wss", 
        "wss://cloud.xbts.io/ws", 
        "wss://node.market.rudex.org/wss", 
        "wss://btsws.roelandp.nl/ws", 
        "wss://api.cnvote.vip:888/wss", 
        "wss://api.gbacenter.org", 
        "wss://api.weaccount.cn/wss", 
        "wss://ws.gdex.top/wss", 
        "wss://bts.open.icowallet.net/ws", 
        "wss://singapore.bitshares.im", 
        "wss://api.61bts.com", 
        "wss://freedom.bts123.cc:15138/wss", 
        "wss://api.btsgo.net/wss",
    ]



def eosio_universe():
    """
    all public api endpoints I could find; some in this list do not connect though
    """
    # https://github.com/greymass/anchor/blob/
    #    c29b5665083c854f0d7b27281587cfb3b2ffb398/nodes.md
    return [
        "https://api.tokenika.io",
        "https://api1.eosasia.one",
        "https://eos.greymass.com",  # operated by greymass
        "https://mainnet.eoscalgary.io",  # operated by EOS Cafe
        "https://api.eosnewyork.io",  # operated by EOS New York
        "https://api.eosdetroit.io",  # operated by EOS Detroit
        "http://api.hkeos.com",  # operated by HK EOS
        "https://bp.cryptolions.io",  # operated by CryptoLions
        "http://dc1.eosemerge.io:8888",  # operated by EOS Emerge Poland
        "https://dc1.eosemerge.io:5443",  # operated by EOS Emerge Poland
        "https://api1.eosdublin.io",  # operated by EOS Dublin
        "https://api2.eosdublin.io",  # operated by EOS Dublin
        "https://mainnet.eoscannon.io",  # operated by EOS Cannon
        "https://eos-api.privex.io",  # operated by Privex
        "https://eosapi.blockmatrix.network",  # operated by Block Matrix
        "https://user-api.eoseoul.io",  # operated by EOSeoul
        "https://api.eos.bitspace.no",  # operated by Bitspace
        "https://node.eosflare.io",  # operated by EOS Flare
        "https://api-eos.blckchnd.com",  # operated by BLCKCHND
        "https://mainnet.eosimpera.com",  # operated by EOS IMPERA
        "https://api.franceos.fr",  # operated by franceos
        "http://api.cypherglass.com",  # operated by Cypherglass
        "https://api.eossweden.se",  # operated by Sw/eden
        "https://nodes.eos42.io",  # operated by EOS42
        "http://api-mainnet.starteos.io",  # operated by Starteos
        "https://eosbp.atticlab.net",  # opeated by AtticLab
        "https://api1.eosdublin.io",  # operated by eosDublin
        "https://node1.eosphere.io",  # operated by EOSphere
        "https://node2.eosphere.io",  # operated by EOSphere
    ]


def unit_test_nodes():
    """
    print the list of nodes in use by the Gateway
    """
    print("bitshares nodes\n", bitshares_nodes(), "\n\n")
    print("bitshares nodes\n", eosio_nodes(), "\n\n")


if __name__ == "__main__":

    unit_test_nodes()
