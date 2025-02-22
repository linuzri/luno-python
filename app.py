import os
import time
from luno_python.client import Client

# Replace with your actual API key and secret
API_KEY = 'm12o71yP5nqf4-LHx-o9tbH_XaC9LCpc49ckhygcAeM'
API_SECRET = 'm12o71yP5nqf4-LHx-o9tbH_XaC9LCpc49ckhygcAeM'

if __name__ == '__main__':
    c = Client(api_key_id=API_KEY, api_key_secret=API_SECRET)

    res = c.get_tickers()
    print(res)
    time.sleep(0.5)

    res = c.get_ticker(pair='XBTZAR')
    print(res)
    time.sleep(0.5)

    res = c.get_order_book(pair='XBTZAR')
    print(res)
    time.sleep(0.5)

    since = int(time.time()*1000)-24*60*59*1000
    res = c.list_trades(pair='XBTZAR', since=since)
    print(res)
    time.sleep(0.5)

    res = c.get_candles(pair='XBTZAR', since=since, duration=300)
    print(res)
    time.sleep(0.5)

    res = c.get_balances()
    print(res)
    time.sleep(0.5)

    aid = ''
    if res['balance']:
        aid = res['balance'][0]['account_id']

    if aid:
        res = c.list_transactions(id=aid, min_row=1, max_row=10)
        print(res)
        time.sleep(0.5)

    if aid:
        res = c.list_pending_transactions(id=aid)
        print(res)
        time.sleep(0.5)

    res = c.list_orders()
    print(res)
    time.sleep(0.5)

    res = c.list_user_trades(pair='XBTZAR')
    print(res)
    time.sleep(0.5)

    res = c.get_fee_info(pair='XBTZAR')
    print(res)
    time.sleep(0.5)

    res = c.get_funding_address(asset='XBT')
    print(res)
    time.sleep(0.5)

    # Commenting out the withdrawal API call section
    # res = c.list_withdrawals()
    # print(res)
    # time.sleep(0.5)

    # wid = ''
    # if res['withdrawals']:
    #     wid = res['withdrawals'][0]['id']

    # if wid:
    #     res = c.get_withdrawal(id=wid)
    #     print(res)
    #     time.sleep(0.5)
