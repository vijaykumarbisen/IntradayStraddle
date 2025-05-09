import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta, time
import matplotlib.pyplot as plt
from fyers_apiv3 import fyersModel

# FYERS API Setup
FYERS_CLIENT_ID = '6B4ZMQL1YX'
FYERS_ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCb0YzM3VZZ3R2QVNZbVVnUlJIZ1pyMENlM1pyX1ZTeWY4a3Q3bFU1R2UxVVN3cUZwdFV0NExwTmdwbmpuS2IxanNXRC1FWC1zUEVkR0x6OWxHbTgtbnNhWjQ2NkllR2dFODEwSXkwaHVENlJlTDUtST0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiI2NzU5ZWUzMzBiMTgyYTZiODU4MThhMzY1MzhiYTliMTkyNmNmMDYxNDAwZWY1YjRjNTJlYWU3NiIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFYwMjYxNCIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ2NDA1MDAwLCJpYXQiOjE3NDYzNzAwMzAsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NjM3MDAzMCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.xYxL_-Yl_2ukRue5IDwtOHvMpLk46f3ZRTqSNVG-XQE'  # You get this from your login process

fyers = fyersModel.FyersModel(client_id=FYERS_CLIENT_ID, token=FYERS_ACCESS_TOKEN,is_async=False, log_path="")

def fetch_spot_data(symbol: str, date: str):
    """
    Fetch 1-minute spot data from Fyers API for Nifty on a given date.
    symbol = NSE:NIFTY50-INDEX
    """
    
    data = {
    "symbol":symbol,
    "resolution":"1",
    "date_format":"1",
    "range_from":"2025-05-02",
    "range_to":"2025-05-02",
    "cont_flag":"1"
    }

    response = fyers.history(data=data)
    data = response


    if data.get("s") == "ok":
        df = pd.DataFrame(data["candles"], columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit='s')
        return df
    else:
        print("Error fetching data:", data)
        return None

# Load Options Data from CSV
def load_options_data(call_file, put_file):
    ce_df = pd.read_csv(call_file, parse_dates=["timestamp"])
    print("ce_df::",ce_df)
    pe_df = pd.read_csv(put_file, parse_dates=["timestamp"])
    ce_df.set_index("timestamp", inplace=True)
    pe_df.set_index("timestamp", inplace=True)
    return ce_df, pe_df

# Backtest Function
def backtest_intraday_straddle(spot_df, ce_df, pe_df, entry_time="09:20:00", exit_time="15:15:00"):
    results = []
    # days = spot_df.index.normalize().unique()
    days = spot_df.index
    print("days::",days)
    for day in days:
        try:
            print("day::",day)
            entry_dt = pd.to_datetime(f"{day.date()} {entry_time}")
            exit_dt = pd.to_datetime(f"{day.date()} {exit_time}")
            if entry_dt not in spot_df.index:
                continue

            spot_price = spot_df.loc[entry_dt]["open"]
            atm_strike = round(spot_price / 50) * 50

            # Filter relevant time slice
            ce_day = ce_df.loc[entry_dt:exit_dt]
            pe_day = pe_df.loc[entry_dt:exit_dt]

            ce_entry = ce_day.iloc[0]["open"]
            pe_entry = pe_day.iloc[0]["open"]

            ce_exit = ce_day.iloc[-1]["close"]
            pe_exit = pe_day.iloc[-1]["close"]

            profit = (ce_exit - ce_entry) + (pe_exit - pe_entry)
            results.append({
                "date": day.date(),
                "spot": spot_price,
                "atm_strike": atm_strike,
                "ce_entry": ce_entry,
                "ce_exit": ce_exit,
                "pe_entry": pe_entry,
                "pe_exit": pe_exit,
                "pnl": profit
            })

        except Exception as e:
            print(f"Error on {day}: {e}")
            continue

    return pd.DataFrame(results)

# === MAIN ===
if __name__ == "__main__":
    # Example Usage
    spot_symbol = "NSE:NIFTY50-INDEX"
    date = "2025-05-02"  # example

    # Fetch spot data from Fyers
    spot_df = fetch_spot_data(spot_symbol, date)
    print("nifty spot_df::",spot_df)

    # Load options data (replace with your actual file paths)
    call_csv = "data/23400CE_08May2025.csv"
    put_csv = "data/23400PE_08May2025.csv"
    
    ce_df, pe_df = load_options_data(call_csv, put_csv)
    print("call_csv::",ce_df)
    # Run backtest
    result_df = backtest_intraday_straddle(spot_df, ce_df, pe_df)
    print(result_df)

    # Plot PnL
    if not result_df.empty:
        result_df.set_index("date")["pnl"].plot(title="Intraday Straddle PnL", marker='o')
        plt.axhline(0, color='red', linestyle='--')
        plt.show()