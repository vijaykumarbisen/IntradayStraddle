from fyers_apiv3 import fyersModel
from datetime import datetime, timedelta
import time


# Nifty 50 spot index symbol for NSE
symbol = "NSE:NIFTY50-INDEX"

client_id = "6B4ZMQL1YX-100"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCb0YzM3VZZ3R2QVNZbVVnUlJIZ1pyMENlM1pyX1ZTeWY4a3Q3bFU1R2UxVVN3cUZwdFV0NExwTmdwbmpuS2IxanNXRC1FWC1zUEVkR0x6OWxHbTgtbnNhWjQ2NkllR2dFODEwSXkwaHVENlJlTDUtST0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiI2NzU5ZWUzMzBiMTgyYTZiODU4MThhMzY1MzhiYTliMTkyNmNmMDYxNDAwZWY1YjRjNTJlYWU3NiIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFYwMjYxNCIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ2NDA1MDAwLCJpYXQiOjE3NDYzNzAwMzAsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NjM3MDAzMCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.xYxL_-Yl_2ukRue5IDwtOHvMpLk46f3ZRTqSNVG-XQE"
# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, token=access_token,is_async=False, log_path="")

data = {
    "symbol":"NSE:SBIN-EQ",
    "resolution":"1",
    "date_format":"1",
    "range_from":"2025-05-02",
    "range_to":"2025-05-02",
    "cont_flag":"1"
}

response = fyers.history(data=data)
print(response)

# Display data
if response['s'] == 'ok':
    candles = response['candles']
    for c in candles[:5]:  # print first 5 entries
        print(f"Time: {datetime.fromtimestamp(c[0])}, Open: {c[1]}, High: {c[2]}, Low: {c[3]}, Close: {c[4]}, Volume: {c[5]}")
else:
    print("Error:", response)