import pandas as pd
import datetime as dt
import time
from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
#from straddle import EXPIRY_DATE

redirect_uri= "https://www.google.com"  ## redircet_uri you entered while creating APP.
client_id = "6B4ZMQL1YX-100"                       ## Client_id here refers to APP_ID of the created app
secret_key = "9GTEXEILT2"                          ## app_secret key which you got after creating the app
grant_type = "authorization_code"                  ## The grant_type always has to be "authorization_code"
response_type = "code"                             ## The response_type always has to be "code"
state = "sample"                                   ##  The state field here acts as a session manager. you will be sent with the state field after successfull generation of auth_code

appSession = fyersModel.SessionModel(client_id = client_id, redirect_uri = redirect_uri,response_type=response_type,state=state,secret_key=secret_key,grant_type=grant_type)
# with open('auth_code.txt', 'r') as file:
#         auth_code = file.read().strip()
#
# print("auth_code::",auth_code)
auth_code = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiI2QjRaTVFMMVlYIiwidXVpZCI6IjRiNDliYzczYTkxMTRjZWE4YmNhNDcxNTEyYzU5NjEzIiwiaXBBZGRyIjoiIiwibm9uY2UiOiIiLCJzY29wZSI6IiIsImRpc3BsYXlfbmFtZSI6IlhWMDI2MTQiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiIyYTRhZTBlN2FhYzM4ZjA2NmFmMTdiNDkzZDVmZjg4OTViYzkxYTVjMDk0NzgyNTRjZmI5Nzk3OSIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImF1ZCI6IltcImQ6MVwiLFwiZDoyXCIsXCJ4OjBcIixcIng6MVwiLFwieDoyXCJdIiwiZXhwIjoxNzc1NDM3Mjk5LCJpYXQiOjE3NzU0MDcyOTksImlzcyI6ImFwaS5sb2dpbi5meWVycy5pbiIsIm5iZiI6MTc3NTQwNzI5OSwic3ViIjoiYXV0aF9jb2RlIn0.6CCKIs-YD4WbffmMCWtFmWYc7VUTDGyY6Yw1ZfWZsZs"
appSession.set_token(auth_code)
response = appSession.generate_token()

## There can be two cases over here you can successfully get the acccessToken over the request or you might get some error over here. so to avoid that have this in try except block
try:
    access_token = response["access_token"]
except Exception as e:
    print(e,response)  ## This will help you in debugging then and there itself like what was the error and also you would be able to see the value you got in response variable. instead of getting key_error for unsuccessfull response.
print("here 1")
# === Configuration ===
CLIENT_ID = client_id
ACCESS_TOKEN = access_token

SYMBOL = "NSE:NIFTY50-INDEX"
LOT_SIZE = 260
EXPIRY_DATE = "26407"
MAX_STRADDLES = 3
# MAX_LOSS = -10000
# PROFIT_TRIGGER = 7000
# LOCK_PROFIT_BASE = 500
# INCREMENT = 3000

MAX_LOSS = -10000
PROFIT_TRIGGER = 2000
LOCK_PROFIT_BASE = 100
INCREMENT = 700

straddle_count = 0
trading_active = True

positions = []
ltp_data = {}
entry_done = False
locked_profit = None
peak_profit = 0



CE_SYMBOL = None
PE_SYMBOL =  None
previous_bias = None
ltp_data = {}
fyers_socket = None
last_processed_candle = None


# === Initialize Fyers ===
fyers = fyersModel.FyersModel(client_id=CLIENT_ID, token=ACCESS_TOKEN)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

def calculate_supertrend(df, period=7, multiplier=3):
    df = df.copy()

    # ATR
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))

    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(period).mean()

    # Bands
    df['upperband'] = ((df['high'] + df['low']) / 2) + (multiplier * df['ATR'])
    df['lowerband'] = ((df['high'] + df['low']) / 2) - (multiplier * df['ATR'])

    # Supertrend
    df['supertrend'] = True  # True = Bullish, False = Bearish

    for i in range(1, len(df)):
        if df['close'][i] > df['upperband'][i-1]:
            df.at[i, 'supertrend'] = True
        elif df['close'][i] < df['lowerband'][i-1]:
            df.at[i, 'supertrend'] = False
        else:
            df.at[i, 'supertrend'] = df['supertrend'][i-1]

            if df['supertrend'][i] and df['lowerband'][i] < df['lowerband'][i-1]:
                df.at[i, 'lowerband'] = df['lowerband'][i-1]

            if not df['supertrend'][i] and df['upperband'][i] > df['upperband'][i-1]:
                df.at[i, 'upperband'] = df['upperband'][i-1]

    return df

def get_candle_data():
    data = {
        "symbol": SYMBOL,
        "resolution": "5",
        "date_format": "1",
        "range_from": "2026-03-19",
        "range_to": "2026-03-20",
        "cont_flag": "1"
    }

    res = fyers.history(data)
    df = pd.DataFrame(res['candles'], columns=['ts','open','high','low','close','volume'])

    df['datetime'] = pd.to_datetime(df['ts'], unit='s',  utc=True)
    df['datetime'] = df['datetime'].dt.tz_convert('Asia/Kolkata')

    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
    df['sma'] = SMAIndicator(df['close'], window=50).sma_indicator()

    df = calculate_supertrend(df, period=7, multiplier=3)
    #print("df:", df)
    return df


def is_full_straddle_active(position):
    return (
        position is not None and
        position["ce"]["active"] and
        position["pe"]["active"]
    )

#backtesting loop function
def run_backtest():
    global previous_bias, straddle_count, trading_active

    df = get_bias_for_day()

    entry_done = False

    for i in range(len(df)):
        row = df.iloc[i]

        candle_time = row['datetime']
        time_ist = candle_time.strftime('%H:%M:%S')

        current_bias = row['bias']

        print(f"{time_ist} | Bias: {current_bias}")

        # 🔥 ENTRY AT 09:25
        if not entry_done and time_ist >= "09:25:00":
            print("🚀 Entering First Straddle at 09:25")
            if not entry_done and time_ist == "09:25:00":
                print("🚀 Entering Straddle")

                price = row['close']  # 🔥 THIS IS THE FIX
                place_straddle(price)

                entry_done = True

        # 🔥 SKIP NA
        if current_bias == "NA":
            continue

        # 🔥 INITIALIZE BIAS
        if previous_bias is None:
            previous_bias = current_bias
            continue

        # 🔻 Flip → Exit PE
        if previous_bias == "BULLISH" and current_bias == "BEARISH":
            print("🔻 Exit PE")

        # 🔺 Flip → Exit CE
        elif previous_bias == "BEARISH" and current_bias == "BULLISH":
            print("🔺 Exit CE")

        previous_bias = current_bias

#def get_bias_for_day(test_date=None):
def get_bias_for_day(test_date):
    df = get_candle_data()
    #test_date="2026-04-02"
    # 🔥 Use custom date if provided
    print("test_date::",test_date)

    if test_date:
        target_date = pd.to_datetime(test_date).date()
    else:
        target_date = dt.date.today()

    # Filter for that date
    df_day = df[df['datetime'].dt.date == target_date].copy()

    df_day = df_day.sort_values(by='datetime')

    df_day['bias'] = "NA"


    bullish = (
            (df_day['rsi'] > 60) &
            (df_day['close'] > df_day['sma']) &
            (df_day['supertrend'] == True)
    )

    bearish = (
            (df_day['rsi'] < 40) &
            (df_day['close'] < df_day['sma']) &
            (df_day['supertrend'] == False)
    )

    df_day.loc[bullish, 'bias'] = "BULLISH"
    df_day.loc[bearish, 'bias'] = "BEARISH"

    # 🔥 Track previous bias
    df_day['prev_bias'] = df_day['bias'].shift(1)
    print("printing **** df_day *******")
    print( df_day[['datetime','open','high', 'close', 'rsi', 'sma', 'supertrend', 'prev_bias', 'bias']])
    return df_day[['datetime','open','high', 'close', 'rsi', 'sma', 'supertrend', 'prev_bias', 'bias']]

def get_atm_strike(price):
    return round(price / 50) * 50

def calculate_mtm_from_df(position, row):
    total = 0.0

    # CE
    if position["ce"]["active"]:
        total += (position["ce"]["entry"] - row['close_ce']) * LOT_SIZE
    else:
        total += (position["ce"]["entry"] - position["ce"]["exit"]) * LOT_SIZE

    # PE
    if position["pe"]["active"]:
        total += (position["pe"]["entry"] - row['close_pe']) * LOT_SIZE
    else:
        total += (position["pe"]["entry"] - position["pe"]["exit"]) * LOT_SIZE

    return total

def check_1_to_4_df(row):
    ce = row['close_ce']
    pe = row['close_pe']

    if ce == 0 or pe == 0:
        return False

    ratio = max(ce, pe) / min(ce, pe)

    return ratio >= 4

def close_position(position, opt_row):
    pnl = 0.0

    # CE
    if position["ce"]["active"]:
        exit_price = opt_row['close_ce']
        pnl += (position["ce"]["entry"] - exit_price) * LOT_SIZE
    else:
        pnl += (position["ce"]["entry"] - position["ce"]["exit"]) * LOT_SIZE

    # PE
    if position["pe"]["active"]:
        exit_price = opt_row['close_pe']
        pnl += (position["pe"]["entry"] - exit_price) * LOT_SIZE
    else:
        pnl += (position["pe"]["entry"] - position["pe"]["exit"]) * LOT_SIZE

    return pnl

def run_single_day_backtest(test_date, expiry):
    global previous_bias

    exit_reference = None
    exit_candle_index = None
    exit_type = None
    monitor_after_3 = False
    total_pnl = 0.0

    # RESET STATE
    previous_bias = None
    straddle_count = 0
    position = None

    last_strike = None
    entry_spot = None
    last_reentry_spot = None
    first_loss_trigger_done = False

    df_spot = get_bias_for_day(test_date)

    print(f"\n📅 Backtesting for {test_date}\n")

    for i in range(len(df_spot)):
        row = df_spot.iloc[i]

        dt_obj = row['datetime']
        time_ist = dt_obj.strftime('%H:%M:%S')

        # 🔥 ENTRY AT 09:20
        if time_ist == "09:20:00" and position is None:
            position = enter_straddle(row, expiry)
            entry_spot = row['close']
            last_reentry_spot = entry_spot
            straddle_count += 1
            continue

        if position is None:
            continue

        # 🔥 GET OPTION ROW
        opt_df = position['df']
        opt_row = opt_df[opt_df['datetime'] == dt_obj]
        # if opt_row.empty:
        #     continue

        opt_row = opt_row.iloc[0].to_dict()


        running_mtm = calculate_mtm_from_df(position, opt_row)
        net_mtm = total_pnl + running_mtm

        print(f"{time_ist} | Running MTM: {running_mtm} | Net PnL: {net_mtm}")
        if (
                net_mtm <= -6000 and
                not monitor_after_3  and
                straddle_count < MAX_STRADDLES
        ):

            new_strike = round(row['close'] / 50) * 50

            # ❗ Avoid same strike re-entry
            if new_strike == last_strike:
                print("⚠️ Same strike — skipping re-entry")
            else:
                print("🔻 Loss Trigger Hit → Re-enter New Straddle")

                # 🔥 BOOK PNL
                closed_pnl = close_position(position, opt_row)
                total_pnl += closed_pnl

                print(f"💰 Booked PnL: {closed_pnl}")
                print(f"📊 Total PnL: {total_pnl}")

                # 🔁 NEW ENTRY
                position = enter_straddle(row, expiry)
                last_reentry_spot = row['close']

                if position is None:
                    continue

                last_strike = position["strike"]
                straddle_count += 1

                continue



        # ❌ MAX LOSS
        if net_mtm <= -10000:
            print("❌ Max Loss Hit → Exit All")
            pnl = close_position(position, opt_row)
            total_pnl += pnl
            print(f"Final PnL: {total_pnl}")
            break

        # 🔥 SPOT MOVE CALCULATION
        current_spot = row['close']
        if last_reentry_spot is None:
            last_reentry_spot = current_spot
        spot_move = abs(current_spot - last_reentry_spot)

        print(f"Spot Move: {spot_move} | Entry Spot: {entry_spot}")

        # =========================================
        # 🔻 FIRST LOSS TRIGGER (-6000)
        # =========================================
        if (
                not first_loss_trigger_done and
                net_mtm <= -6000 and
                spot_move >= 50 and
                straddle_count < MAX_STRADDLES
        ):

            print("🔻 First -6000 Loss + 50 Move → Re-entry")

            # 🔥 BOOK PNL
            closed_pnl = close_position(position, opt_row)
            total_pnl += closed_pnl

            print(f"💰 Booked PnL: {closed_pnl}")
            print(f"📊 Total PnL: {total_pnl}")

            # NEW ENTRY
            position = enter_straddle(row, expiry)
            last_reentry_spot = row['close']

            if position is None:
                continue

            straddle_count += 1

            # UPDATE TRACKERS
            first_loss_trigger_done = True
            last_reentry_spot = current_spot

            continue

        # =========================================
        # 🔁 SUBSEQUENT RE-ENTRY (EVERY 50 MOVE)
        # =========================================
        if (
                first_loss_trigger_done and
                spot_move >= 50 and
                net_mtm > -6000 and
                net_mtm > MAX_LOSS and
                straddle_count < MAX_STRADDLES
        ):

            print("🔁 50 Move Re-entry (Post -1500 Recovery Zone)")

            # 🔥 BOOK PNL
            closed_pnl = close_position(position, opt_row)
            total_pnl += closed_pnl

            print(f"💰 Booked PnL: {closed_pnl}")
            print(f"📊 Total PnL: {total_pnl}")

            # NEW ENTRY
            position = enter_straddle(row, expiry)
            last_reentry_spot = row['close']
            if position is None:
                continue

            straddle_count += 1

            # UPDATE SPOT TRACKING
            last_reentry_spot = current_spot

            continue

        # 🔁 1:4 RE-ENTRY
        if (
                is_full_straddle_active(position) and
                exit_reference is None and
                check_1_to_4_df(opt_row) and
                straddle_count < 3
        ):
            print("⚡ 1:4 Re-entry Triggered")

            # Close both legs first
            position["ce"]["exit"] = opt_row['close_ce']
            position["pe"]["exit"] = opt_row['close_pe']

            position["ce"]["active"] = False
            position["pe"]["active"] = False

            print("🔁 Closing current straddle")

            # New entry
            position = enter_straddle(row, expiry)
            last_reentry_spot = row['close']
            last_strike = position["strike"]
            straddle_count += 1

            continue

        # 🔥 BIAS LOGIC
        current_bias = row['bias']

        if current_bias == "NA":
            continue

        if previous_bias is None:
            previous_bias = current_bias
            continue

        if time_ist >= "15:00:00" and position is not None:
            print("⏰ 15:00 Exit All")
            pnl = close_position(position, opt_row)
            total_pnl += pnl
            print(f"Final PnL: {total_pnl}")

            # Exit CE
            if position["ce"]["active"]:
                position["ce"]["exit"] = opt_row['close_ce']
                position["ce"]["active"] = False
                print(f"CE EXIT at {position['ce']['exit']}")

            # Exit PE
            if position["pe"]["active"]:
                position["pe"]["exit"] = opt_row['close_pe']
                position["pe"]["active"] = False
                print(f"PE EXIT at {position['pe']['exit']}")

            break  # 🔥 STOP BACKTEST HERE
            # =========================================

            # MTM
        mtm = calculate_mtm_from_df(position, opt_row)

        # 🔻 Bullish → Bearish
        if previous_bias == "BULLISH" and current_bias == "BEARISH":
            if position["pe"]["active"]:
                position["pe"]["exit"] = opt_row['close_pe']
                position["pe"]["active"] = False

                print(f"🔻 PE EXIT at {opt_row['close_pe']}")

                exit_reference = row['open']
                exit_candle_index = i
                exit_type = "PE"
                monitor_after_3 = True

        # 🔺 Bearish → Bullish
        if previous_bias == "BEARISH" and current_bias == "BULLISH":
            if position["ce"]["active"]:
                position["ce"]["exit"] = opt_row['close_ce']
                position["ce"]["active"] = False

                print(f"🔺 CE EXIT at {opt_row['close_ce']}")
                exit_reference = row['open']
                exit_candle_index = i
                exit_type = "CE"
                monitor_after_3 = True

        previous_bias = current_bias

        # 🔥 CHECK 3rd CANDLE CONDITION
        if monitor_after_3:

            candles_passed = i - exit_candle_index
            # print(f"[CHECK] i={i}, exit_i={exit_candle_index}, passed={candles_passed}")
            # We want 3rd candle AFTER exit candle
            if candles_passed >= 3:
                print(f"⏳ Checking 3rd candle condition...row['close']...exit_reference", row['close'], exit_reference)
                print(f"[TRACKING ACTIVE] ExitIdx={exit_candle_index}, CurrentIdx={i}")
                condition_met = False

                # 🔺 CE exit → bullish expectation → price should go UP
                if exit_type == "CE" and row['close'] < exit_reference:
                    condition_met = True

                # 🔻 PE exit → bearish expectation → price should go DOWN
                elif exit_type == "PE" and row['close'] > exit_reference:
                    condition_met = True

                if condition_met:
                    print("🚀 Condition Met → Exit All + New Entry")

                    closed_pnl = close_position(position, opt_row)
                    total_pnl += closed_pnl

                    print(f"💰 Booked PnL: {closed_pnl}")
                    print(f"📊 Total PnL: {total_pnl}")

                    position = enter_straddle(row, expiry)
                    last_reentry_spot = row['close']
                    last_reentry_spot = entry_spot
                    straddle_count += 1

                    # RESET
                    exit_reference = None
                    exit_candle_index = None
                    exit_type = None
                    monitor_after_3 = False

                    continue


def get_option_data(symbol, from_date, to_date):
    data = {
        "symbol": symbol,
        "resolution": "5",
        "date_format": "1",
        "range_from": from_date,
        "range_to": to_date,
        "cont_flag": "1"
    }

    res = fyers.history(data)
    # 🔥 DEBUG PRINT
    if res.get("s") != "ok":
        print(f"❌ No data for {symbol}")
        print("Response:", res)

    if "candles" not in res:
        print(f"❌ Missing candles for {symbol}")

    df = pd.DataFrame(res['candles'],
                      columns=['ts','open','high','low','close','volume'])

    df['datetime'] = pd.to_datetime(df['ts'], unit='s', utc=True)\
                        .dt.tz_convert('Asia/Kolkata')

    return df

def get_straddle_df(strike, expiry, date):
    ce_symbol = f"NSE:NIFTY{expiry}{strike}CE"
    pe_symbol = f"NSE:NIFTY{expiry}{strike}PE"
    print("expiry",expiry)
    print("date", date)
    print("strike", strike)
    from_date = date
    to_date = date

    ce_df = get_option_data(ce_symbol, from_date, to_date)
    pe_df = get_option_data(pe_symbol, from_date, to_date)

    # Merge on datetime
    df = pd.merge(
        ce_df[['datetime','close']],
        pe_df[['datetime','close']],
        on='datetime',
        suffixes=('_ce','_pe')
    )

    return df

def enter_straddle(row, expiry):
    price = row['close']
    strike = round(price / 50) * 50

    date_str = row['datetime'].strftime('%Y-%m-%d')

    df = get_straddle_df(strike, expiry, date_str)

    entry_time = row['datetime']

    entry_row = df[df['datetime'] == entry_time]

    if entry_row.empty:
        print("❌ No option data for entry time")
        return None

    ce_entry = entry_row['close_ce'].values[0]
    pe_entry = entry_row['close_pe'].values[0]

    print(f"\n🚀 ENTRY {entry_time.strftime('%H:%M:%S')}")
    print(f"Strike: {strike} | CE: {ce_entry} | PE: {pe_entry}")

    return {
        "strike": strike,

        "ce": {
            "entry": ce_entry,
            "active": True,
            "exit": None
        },

        "pe": {
            "entry": pe_entry,
            "active": True,
            "exit": None
        },

        "df": df
    }


def get_option_symbols():
    global CE_SYMBOL, PE_SYMBOL
    expiry = EXPIRY_DATE  # TODO: automate
    strike = get_atm_strike()
    CE_SYMBOL = f"NSE:NIFTY{expiry}{strike}CE"
    PE_SYMBOL = f"NSE:NIFTY{expiry}{strike}PE"
    print("Generated Symbols:", CE_SYMBOL, PE_SYMBOL)




def place_straddle(price):
    global CE_SYMBOL, PE_SYMBOL

    strike = get_atm_strike(price)
    expiry = EXPIRY_DATE  # TODO dynamic

    CE_SYMBOL = f"NSE:NIFTY{expiry}{strike}CE"
    PE_SYMBOL = f"NSE:NIFTY{expiry}{strike}PE"

    print(f"Selected Strike: {strike}")
    print(f"CE: {CE_SYMBOL}, PE: {PE_SYMBOL}")

def exit_leg(symbol):
    pos = fyers.positions()

    for p in pos['netPositions']:
        if p['symbol'] == symbol and p['netQty'] != 0:
            order = {
                "symbol": symbol,
                "qty": abs(p['netQty']),
                "type": 2,
                "side": 1 if p['netQty'] < 0 else -1,
                "productType": "INTRADAY",
                "limitPrice": 0,
                "stopPrice": 0,
                "validity": "DAY"
            }
            fyers.place_order(order)
            print(f"Exited {symbol}")

def process_bias_and_exit(df_day):
    global previous_bias

    for i in range(len(df_day)):
        row = df_day.iloc[i]

        current_bias = row['bias']
        time_ist = row['datetime'].strftime('%Y-%m-%d %H:%M:%S')

        print(f"{time_ist} | Bias: {current_bias}")

        if previous_bias == "BULLISH" and current_bias == "BEARISH":
            print("🔻 Bias Flip → Exit PE")
            exit_leg(PE_SYMBOL)

        elif previous_bias == "BEARISH" and current_bias == "BULLISH":
            print("🔺 Bias Flip → Exit CE")
            exit_leg(CE_SYMBOL)

        print("here 3")
        previous_bias = current_bias

def exit_all():
    pos = fyers.positions()

    for p in pos['netPositions']:
        if p['netQty'] != 0:
            order = {
                "symbol": p['symbol'],
                "qty": abs(p['netQty']),
                "type": 2,
                "side": 1 if p['netQty'] < 0 else -1,
                "productType": "INTRADAY",
                "limitPrice": 0,
                "stopPrice": 0,
                "validity": "DAY"
            }
            fyers.place_order(order)

    print("EXITED ALL")

def calculate_mtm():
    total = 0.0

    pos = fyers.positions()

    for p in pos['netPositions']:
        sym = p['symbol']
        qty = p['netQty']

        if sym in ltp_data:
            ltp = ltp_data[sym]
            total += (p['avgPrice'] - ltp) * qty

    return total

#PREMIUM CHECK 1:4
def check_1_to_4_condition():
    if CE_SYMBOL not in ltp_data or PE_SYMBOL not in ltp_data:
        return False

    ce_price = ltp_data[CE_SYMBOL]
    pe_price = ltp_data[PE_SYMBOL]

    if ce_price == 0 or pe_price == 0:
        return False

    ratio = max(ce_price, pe_price) / min(ce_price, pe_price)

    print(f"Premium Ratio: {ratio:.2f}")

    return ratio >= 4

#GET LATEST CLOSED CANDLE
def get_latest_closed_candle():
    df = get_bias_for_day()

    if df is None or len(df) < 2:
        return None

    # 🔥 Last row = current forming candle
    # 🔥 Second last = last CLOSED candle
    return df.iloc[-2]

def onmessage(message):
    global previous_bias, last_processed_candle, trading_active
    print("here in onmessage",message)
    # ✅ Store LTP
    if 'symbol' in message and 'ltp' in message:
        ltp_data[message['symbol']] = message['ltp']

    # Only proceed if both legs active
    if CE_SYMBOL is None or PE_SYMBOL is None:
        return

    if CE_SYMBOL not in ltp_data or PE_SYMBOL not in ltp_data:
        return
    # 🔥 Get last CLOSED candle
    candle = get_latest_closed_candle()
    if candle is None:
        return

    candle_time = candle['datetime']
    # 🔥 RUN ONLY ON NEW CANDLE
    if last_processed_candle == candle_time:
        return

    last_processed_candle = candle_time

    current_bias = candle['bias']

    # ✅ MTM Calculation
    mtm = calculate_mtm()
    print(f"MTM: {mtm}")

    if mtm <= MAX_LOSS:
        print("❌ Max Loss Hit → Stopping Trading")
        exit_all()
        trading_active = False
        fyers_socket.close()
        return

        # 🔥 1:4 CONDITION
    if trading_active and check_1_to_4_condition():
        print("⚡ 1:4 Condition Hit → Re-entering")

        exit_all()
        time.sleep(1)

        latest_price = candle['close']
        place_straddle(latest_price)
        return  # 🔥 IMPORTANT (avoid double execution)

    # ✅ Get latest bias
    #df_bias = get_bias_for_day()
    #latest = df_bias.iloc[-1]

    #current_bias = latest['bias']
    #time_ist = latest['datetime'].strftime('%H:%M:%S')
    time_ist = candle_time.strftime('%H:%M:%S')
    print(f"{time_ist} | previous_bias: {previous_bias}")
    print(f"{time_ist} | current_bias: {current_bias}")

    if previous_bias is None:
        print("⚡ Initial Bias Set:", current_bias)
        previous_bias = current_bias

    # 🔥 Bias Flip Logic
    if previous_bias == "BULLISH" and current_bias == "BEARISH":
        print("🔻 Exit PE (Bias Flip)")
        exit_leg(PE_SYMBOL)

    elif previous_bias == "BEARISH" and current_bias == "BULLISH":
        print("🔺 Exit CE (Bias Flip)")
        exit_leg(CE_SYMBOL)


def subscribe_symbols(symbols):
    global fyers_socket

    fyers_socket = data_ws.FyersDataSocket(
        access_token=ACCESS_TOKEN,
        log_path="",
        litemode=False,
        write_to_file=False,
        reconnect=True,
        on_connect=lambda: fyers_socket.subscribe(
            symbols=symbols,
            data_type="SymbolUpdate"
        ),
        on_message=onmessage
    )

    fyers_socket.connect()


##   MAIN LOOP
if __name__ == "__main__":

    #while True:
        now = dt.datetime.now().time()
        #bias = get_bias_for_day()
        #print("Bias:", bias)
        # Entry at 9:25
        #if now >= dt.time(9, 25) and CE_SYMBOL is None:
        #if CE_SYMBOL is None:
        #    print("🚀 Entering Straddle")
        #    place_straddle()
        run_single_day_backtest(
            test_date="2026-03-20",
            expiry=EXPIRY_DATE
             )
        # Exit at 3:00
        #if now >= dt.time(15, 0):
            #    print("⏰ Market Close Exit")
            #    exit_all()
        #    break

        time.sleep(1)
