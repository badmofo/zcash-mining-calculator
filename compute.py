# requires python3 and access to a zcash node

import requests
import sys
import collections
import decimal
import urllib.parse
import simplejson as json

def extract_auth_from_url(url):
    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
    user_password, host_port = urllib.parse.splituser(netloc)
    user, password = urllib.parse.splitpasswd(user_password) if user_password else (None, None)
    return user, password, urllib.parse.urlunsplit([scheme, host_port, path, query, fragment])

class JsonRpcException(Exception):
    pass

class JsonRpcProxy(object):
    def __init__(self, url, verify=True):
        username, password, url = extract_auth_from_url(url)
        self.url = url
        self.session = requests.session()
        self.session.verify = verify
        if not verify:
            requests.packages.urllib3.disable_warnings()
        if username:
            self.session.auth = (username, password)
        self.n = 1

    def __getattr__(self, name):
        def f(*args):
            data = {
                'jsonrpc': '2.0',
                'method': name,
                'params': args,
                'id': self.n
            }
            self.n += 1
            r = self.session.post(self.url, data=json.dumps(data))
            r.raise_for_status()
            r = json.loads(r.text, parse_float=decimal.Decimal, object_pairs_hook=collections.OrderedDict)
            if r.get('error'):
                raise JsonRpcException(r['error'])
            return r['result']
        return f

node_rpc_url = sys.argv[1]
service = JsonRpcProxy(node_rpc_url)
info = service.getmininginfo()
height = info['blocks']
top = service.getblock(service.getblockhash(height))
net_hash = service.getnetworkhashps(72)
top_minus_72 = service.getblock(service.getblockhash(height - 72))
block_time = (top['time'] - top_minus_72['time']) / 72
miner_subsidy = service.getblocksubsidy(100)['miner']
poloniex = requests.get('https://poloniex.com/public?command=returnTicker').json()
from decimal import Decimal
data = {
        'height': height,
        'minerSubsidy': miner_subsidy,
        'zecPriceBtc': Decimal(poloniex['BTC_ZEC']['last']),
        'btcPriceUsd': Decimal(poloniex['USDT_BTC']['last']),
        'netHash': net_hash,
        'blockTime': block_time,
}
print('zecStats = ' + json.dumps(data) + ';')