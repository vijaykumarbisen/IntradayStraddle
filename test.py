from fyers_apiv3 import fyersModel
import time
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


# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, token=access_token,is_async=False, log_path="")

data = {
    "symbol":"NSE:SBIN-EQ",
    "resolution":"D",
    "date_format":"1",
    "range_from":"2025-05-02",
    "range_to":"2025-05-02",
    "cont_flag":"1"
}

response = fyers.history(data=data)
print(response)
max_mtm = 0
profit_lock = 0
mtm_threshold = 2400
lock_step = 500
lock_increment = 500
initial_lock = 500
def get_positions():
    response = fyers.positions()
    return response['netPositions']

def calculate_mtm():
    positions = get_positions()
    mtm = 0
    for pos in positions:
        if 'NIFTY' in pos['symbol']:
            mtm += pos['pl']

    for pos in positions:
        if 'NIFTY' in pos['symbol']:
            side = 1 if pos['netQty'] < 0 else -1
    return mtm

while True:

    mtm = calculate_mtm()
    mtm = 3500
    profit_lock = 0
    if mtm > max_mtm:
            max_mtm = mtm
            if max_mtm >= mtm_threshold:
                #profit_lock = (max_mtm // lock_step) * lock_step - (lock_step * ((max_mtm - mtm_threshold) // lock_step == 0))
                profit_lock = ((max_mtm - mtm_threshold) // lock_increment + 1) * lock_increment
                
    elif mtm < profit_lock and profit_lock > 0:
            print(f"MTM dropped below profit lock ({mtm} < {profit_lock}). Exiting positions.")
            print("close position")
            #exit_positions()
            #schedule.clear()  # Stop monitoring
    
    print("profit_lock::",profit_lock) 
    print("max_mtm::",max_mtm)
    time.sleep(1)