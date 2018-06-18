'''
    Created on Fri June 15, 2018
    Author: Macingo
    Description: Market Making on DDEX

    !!! README before execution!
    1. This program is using 0x protocol v1.0 proxy
    2. It may be obsolete after late July 2018 with the deployment of 0x protocol v2.0
    3. Before using, please enable proxy through DDEX interface

'''

import requests
import json
import time
from datetime import datetime
from web3.auto import w3
from eth_account.messages import defunct_hash_message

# Preload some configration
# Warning: this approach is not 100% safe, use at your own risk

###############################Fire Wall####################################################
############################################################################################
address= ''
private_key=''
############################################################################################
###############################Fire Wall####################################################

address = str(address).lower() # the server side only recognize the lower case
cPair = 'ZRX-ETH'
endpoint = 'https://api.ddex.io/v2'


# Get time in milliseconds from current Date
def dt_to_ms(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return int(delta.total_seconds() * 1000)


# Hydro Authentication based on timestamp
def hydro_auth():
    # Set current date time
    now = datetime.utcnow()
    timeinms = str(dt_to_ms(now))
    message = 'HYDRO-AUTHENTICATION@' + timeinms
    # Hydro-Authentication: {Address}#{Message}#{Signature}
    signature = buildUnsignedOrder(message)
    headers = {'content-type': 'application/json', 'Hydro-Authentication': address + '#' + message + '#' + signature}
    return headers


# Sign Unsigned Order (text)
def buildUnsignedOrder(message):
    message_hash = defunct_hash_message(text=message)
    signed_msg = w3.eth.account.signHash(message_hash, private_key=private_key)
    signed_msg = signed_msg.signature
    signature = w3.toHex(signed_msg)
    return signature


# Sign Signed Order (hexstr)
def buildsignedOrder(orderId):
    message_hashOrder = defunct_hash_message(hexstr=orderId)
    signed_msgOrder = w3.eth.account.signHash(message_hashOrder, private_key=private_key)
    signed_msgOrder = signed_msgOrder.signature
    signatureOrder = w3.toHex(signed_msgOrder)
    return signatureOrder


# Get highest bid price (ZRX-ETH)
def getBid(cPair):
    r = requests.get(endpoint + '/markets/' + cPair + '/ticker')
    return r.json()['data']['ticker']['bid']


# Get lowest ask price (ZRX-ETH)
def getAsk(cPair):
    r = requests.get(endpoint + '/markets/' + cPair + '/ticker')
    return r.json()['data']['ticker']['ask']


# Get last traded price (ZRX-ETH)
def getLastPrice(cPair):
    r = requests.get(endpoint + '/markets/' + cPair + '/ticker')
    return r.json()['data']['ticker']['price']


# Get spread between lowest-ask and highest-bid (ZRX-ETH)
def getSpread(cPair):
    return getAsk(cPair) - getBid(cPair)


# Get price decimal (ZRX-ETH)
def getPriceDecimal(cPair):
    r = requests.get(endpoint + '/markets/' + cPair)
    return r.json()['data']['market']['priceDecimals']


# Get amount decimal (ZRX-ETH)
def getAmountDecimal(cPair):
    r = requests.get(endpoint + '/markets/' + cPair)
    return r.json()['data']['market']['amountDecimals']


# Place a single Buy/ Sell execution
def placeLimitOrder(side, amount, price):
    # build unsigned order
    unsigned_payload = {
        "amount": amount,
        "price": price,
        "side": side,
        "marketId": cPair
    }
    unsigned_payload = requests.post(endpoint + '/orders/build', data=json.dumps(unsigned_payload), headers=hydro_auth())
    # print('unsigned: ', unsigned_payload.json()['data']['feeAmount'])
    # build signed order
    order = json.loads(unsigned_payload.content)
    orderId = order['data']['order']['id']
    signatureOrder = buildsignedOrder(orderId)
    payload_order = {
        "orderId": orderId,
        "signature": signatureOrder
    }
    requests.post(endpoint + '/orders', data=json.dumps(payload_order), headers=hydro_auth())


# Cancel an existing order (orderId)
def cancelOrder(orderId):
    requests.delete(endpoint + '/orders/' + orderId, headers=hydro_auth())


# Cancel all the orders currently existing
def cancelOrders():
    r = requests.get(endpoint + '/orders', headers=hydro_auth())
    all_orders = r.json()['data']['orders']
    for order in all_orders:
        cancelOrder(order['id'])


# Batch execution at time = t ~[1, T]
def batchLimitOrder():
    level = 0.00001
    target_buy_price = float(getLastPrice(cPair)) - level
    target_sell_price = float(getLastPrice(cPair)) + 2*level
    for i in range(5):
        placeLimitOrder('buy', '1', str(target_buy_price))
        placeLimitOrder('sell', '1', str(target_sell_price))
        target_buy_price -= level
        target_sell_price += 2*level



# Calculate the middle price based on volume
def getMidPrice(cPair):
    r = requests.get(endpoint + '/markets/' + cPair + '/orderbook?level=3')  # level=3 --> all the order info

    all_bids = r.json()['data']['orderBook']['bids']
    bid_price = 0.0
    bid_amount = 0.0
    for bid in all_bids:
        bid_price += float(bid['price']) * float(bid['amount'])
        bid_amount += float(bid['amount'])

    all_asks = r.json()['data']['orderBook']['asks']
    ask_price = 0.0
    ask_amount = 0.0
    for ask in all_asks:
        ask_price += float(ask['price']) * float(ask['amount'])
        ask_amount += float(ask['amount'])

    avg_ask = ask_price / ask_amount
    avg_bid = bid_price / bid_amount
    #
    # print('avg_ask', avg_ask)
    # print('avg_bid', avg_bid)
    return (avg_ask + avg_bid) / 2


# Start market making bot
def start():
    print("--- DDEX Market Making <0x v1.0> ---")  # as of June 15, 2018
    print('Trade Account: %s' %address)
    print('Trade Pair: %s\n' %cPair)


# Main
start()
# placeLimitOrder('sell', '1', '0.0024')
# placeLimitOrder('buy', '0.11', '0.00014')
# batchLimitOrder()
# time.sleep(2)
# cancelOrders()



































