#here there will be 3 functions the first would be to login the second would be to get the kline data and the third would be to place order 
#then there would be orders to cancel order or cancel all orders get balance and get assets etc
import requests
import time
import requests
import creds
import urllib.parse
import hashlib
import hmac
import base64

# Read Kraken API key and secret stored in environment variables
api_url = "https://api.kraken.com"
api_key = creds.api
api_sec = creds.secret

def kraken_request(uri_path, data, api_key, api_sec):
    headers = {}
    headers['API-Key'] = api_key
    # get_kraken_signature() as defined in the 'Authentication' section
    headers['API-Sign'] = get_kraken_signature(uri_path, data, api_sec)             
    req = requests.post((api_url + uri_path), headers=headers, data=data)
    return req

def get_kraken_signature(urlpath, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def OHLCdata():
    resp = requests.get('https://api.kraken.com/0/public/OHLC?pair=ETHUSD')
    return resp.json()

def cancel_all_orders():
    resp = kraken_request('/0/private/CancelAll', {
    "nonce": str(int(1000*time.time()))
    }, api_key, api_sec)
    return resp.json()

def account_balance():
    resp = kraken_request('/0/private/Balance', {
    "nonce": str(int(1000*time.time()))
}, api_key, api_sec)
    return resp.json()

def cancel_orders():
    resp = kraken_request('/0/private/CancelOrder', {
    "nonce": str(int(1000*time.time())),
    "txid": "OG5V2Y-RYKVL-DT3V3B"
}, api_key, api_sec)
    return resp.json()
def place_order():
    b = kraken_request('/0/private/AddOrder', {
    "nonce": str(int(1000*time.time())),
    "ordertype": "limit",
    "type": "buy",
    "volume": 1,
    "pair": "XBTUSD",
    "price": 27500
}, api_key, api_sec)
    return b.json()
    


t=place_order()
d=account_balance()
a=OHLCdata()
c=cancel_all_orders()
print(t)








