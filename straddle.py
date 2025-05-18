import time
from datetime import datetime
import pytz
from fyers_apiv3 import fyersModel
import requests
from retry import retry

redirect_uri= "https://www.google.com"  ## redircet_uri you entered while creating APP.
client_id = "6B4ZMQL1YX-100"                       ## Client_id here refers to APP_ID of the created app
secret_key = "9GTEXEILT2"                          ## app_secret key which you got after creating the app 
grant_type = "authorization_code"                  ## The grant_type always has to be "authorization_code"
response_type = "code"                             ## The response_type always has to be "code"
state = "sample"                                   ##  The state field here acts as a session manager. you will be sent with the state field after successfull generation of auth_code 

appSession = fyersModel.SessionModel(client_id = client_id, redirect_uri = redirect_uri,response_type=response_type,state=state,secret_key=secret_key,grant_type=grant_type)
with open('auth_code.txt', 'r') as file:
        auth_code = file.read().strip()

print("auth_code::",auth_code)       
appSession.set_token(auth_code)
response = appSession.generate_token()

## There can be two cases over here you can successfully get the acccessToken over the request or you might get some error over here. so to avoid that have this in try except block
try: 
    access_token = response["access_token"]
except Exception as e:
    print(e,response)  ## This will help you in debugging then and there itself like what was the error and also you would be able to see the value you got in response variable. instead of getting key_error for unsuccessfull response.

## Once you have generated accessToken now we can call multiple trading related or data related apis after that in order to do so we need to first initialize the fyerModel object with all the requried params.
"""
fyerModel object takes following values as arguments
1. accessToken : this is the one which you received from above 
2. client_id : this is basically the app_id for the particular app you logged into
"""
# === Configuration ===
CLIENT_ID = client_id
ACCESS_TOKEN = access_token
MTM_SL1 = -2400
MTM_SL2 = -5000
ENTRY_TIME = "09:25"
EXIT_TIME = "15:00"
RECHECK_INTERVAL = 2  # seconds
POSITION_SIZE = 75  # Number of lots
UNDERLYING = "NSE:NIFTY50-INDEX"
EXPIRY_DATE = 25522 
RETRY_LIMIT = 3

profit_lock = 0
mtm_threshold = 2400
lock_increment = 500
max_mtm = 0
profit_lock = 0


# === Initialize Fyers ===
fyers = fyersModel.FyersModel(client_id=CLIENT_ID, token=ACCESS_TOKEN)

# === Helper Functions ===

def get_nifty_spot():
    data = {"symbols": "NSE:NIFTY50-INDEX"}
    response = fyers.quotes(data)
    return response['d'][0]['v']['lp']

def get_atm_strike():
    # spot_price = get_nifty_spot()
    # atm_strike = round(spot_price / 50) * 50
    # return atm_strike
    quote = fyers.quotes({"symbols": UNDERLYING})
    ltp = quote['d'][0]['v']['lp']
    atm_strike = round(ltp / 50) * 50
    return atm_strike

# === UTILITY ===

def get_current_week_expiry():
    today = datetime.date.today()
    weekday = today.weekday()
    print("today:",today)
    expiry_day = today + datetime.timedelta(days=(3 - weekday) % 7)  # Thursday
    print(expiry_day)
   
    expiry_str = expiry_day.strftime("%y%m%d").upper()
    formatted = expiry_day.strftime("%y") + str(int(expiry_day.strftime("%m"))) + expiry_day.strftime("%d")
    
    print(formatted)
    return formatted

def get_option_symbols(atm_strike):
    # Replace 'YYYYMMDD' with the actual expiry date in YYYYMMDD format
    expiry = EXPIRY_DATE
    ce_symbol = f"NSE:NIFTY{expiry}{atm_strike}CE"
    pe_symbol = f"NSE:NIFTY{expiry}{atm_strike}PE"
    return ce_symbol,pe_symbol

def place_order(symbol, qty, side):
    print("symbol:",symbol)
    order_data = {
        "symbol": symbol,
        "qty": qty,
        "type": 2,  # Market Order
        "side": side,  # 1 = Buy, -1 = Sell
        "productType": "INTRADAY",
        "limitPrice": 0,
        "stopPrice": 0,
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": False,
        "stopLoss": 0,
        "takeProfit": 0
    }
    response = fyers.place_order(order_data)
    print(response)
    return response

def place_straddle(atm_strike):
    ce_symbol,pe_symbol = get_option_symbols(atm_strike)
    place_order(ce_symbol, POSITION_SIZE, -1)  # Sell CE
    place_order(pe_symbol, POSITION_SIZE, -1)  # Sell PE

# Retry on exceptions like requests.ConnectionError, requests.Timeout, etc.
@retry(tries=3, delay=2, backoff=2, exceptions=(requests.exceptions.RequestException,))
def get_positions():
    response = fyers.positions()
    
    if response.get("code") != 200:
        raise requests.exceptions.RequestException(f"Failed with status code: {response.get("code")}")
    return response['netPositions']

def calculate_mtm():
    positions = get_positions()
    mtm = 0
    for pos in positions:
        if 'NIFTY' in pos['symbol']:
            mtm += pos['pl']
    return mtm

def close_all_positions():
    positions = get_positions()
    for pos in positions:
        if 'NIFTY' in pos['symbol']:
            side = 1 if pos['netQty'] < 0 else -1
            place_order(pos['symbol'], abs(pos['netQty']), side)

def get_profit_lock(mtm):
    global max_mtm, profit_lock
    if mtm > max_mtm:
            max_mtm = mtm
            if max_mtm >= mtm_threshold:
                profit_lock = ((max_mtm - mtm_threshold) // lock_increment + 1) * lock_increment
                print("profit_lock::",profit_lock)

# === Main Strategy ===

def run_strategy():
    ist = pytz.timezone('Asia/Kolkata')
    straddle_entered = True
    reentry_done = False
    #current_sl = MTM_SL1
    if not reentry_done:
        current_sl = MTM_SL1
    else: 
        current_sl = MTM_SL2

    print("current_sl::",current_sl)
    while True:
        now = datetime.now(ist)
        current_time = now.strftime("%H:%M")
        print("current_time::",current_time)
        if current_time>= ENTRY_TIME and not straddle_entered:
        #if not straddle_entered:
            atm_strike = get_atm_strike()
            place_straddle(atm_strike)
            straddle_entered = True
            print(f"First straddle entered at {current_time}")

        if straddle_entered:
            mtm = calculate_mtm()
            print(f"Current MTM: ₹{mtm}")
            print(f"MAX MTM: ₹{max_mtm}")
            print(f"profit_lock: ₹{profit_lock}")
            print(f"current_sl: ₹{current_sl}")

            get_profit_lock(mtm)

            if mtm < profit_lock and profit_lock > 0:
                print(f"MTM dropped below profit lock ({mtm} < {profit_lock}). Exiting positions.")
                print("close position")
                close_all_positions()
                break

            if mtm <= current_sl:
                close_all_positions()
                print(f"MTM SL of ₹{current_sl} hit at {current_time}. Positions closed.")

                if not reentry_done:
                    time.sleep(2)
                    atm_strike = get_atm_strike()
                    place_straddle(atm_strike)
                    reentry_done = True
                    current_sl = MTM_SL2
                    print(f"Second straddle entered at {current_time}")
                else:
                    break

        if current_time >= EXIT_TIME:
            close_all_positions()
            print(f"Market close at {current_time}. All positions closed.")
            break

        time.sleep(RECHECK_INTERVAL)

# === Execute Strategy ===
run_strategy()