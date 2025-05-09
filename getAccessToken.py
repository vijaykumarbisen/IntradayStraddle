from fyers_apiv3 import fyersModel
import webbrowser

"""
In order to get started with Fyers API we would like you to do the following things first.
1. Checkout our API docs :   https://myapi.fyers.in/docsv3
2. Create an APP using our API dashboard :   https://myapi.fyers.in/dashboard/

Once you have created an APP you can start using the below SDK 
"""

#### Generate an authcode and then make a request to generate an accessToken (Login Flow)

"""
1. Input parameters
"""
redirect_uri= "https://www.google.com"  ## redircet_uri you entered while creating APP.
client_id = "6B4ZMQL1YX-100"                       ## Client_id here refers to APP_ID of the created app
secret_key = "9GTEXEILT2"                          ## app_secret key which you got after creating the app 
grant_type = "authorization_code"                  ## The grant_type always has to be "authorization_code"
response_type = "code"                             ## The response_type always has to be "code"
state = "sample"                                   ##  The state field here acts as a session manager. you will be sent with the state field after successfull generation of auth_code 


# ### Connect to the sessionModel object here with the required input parameters
appSession = fyersModel.SessionModel(client_id = client_id, redirect_uri = redirect_uri,response_type=response_type,state=state,secret_key=secret_key,grant_type=grant_type)

# # ## Make  a request to generate_authcode object this will return a login url which you need to open in your browser from where you can get the generated auth_code 
generateTokenUrl = appSession.generate_authcode()

# """There are two method to get the Login url if  you are not automating the login flow
# 1. Just by printing the variable name 
# 2. There is a library named as webbrowser which will then open the url for you without the hasel of copy pasting
# both the methods are mentioned below"""
print((generateTokenUrl))  
webbrowser.open(generateTokenUrl,new=1)

"""
run the code firstly upto this after you generate the auth_code comment the above code and start executing the below code """
##########################################################################################################################

### After succesfull login the user can copy the generated auth_code over here and make the request to generate the accessToken 
#auth_code = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiI2QjRaTVFMMVlYIiwidXVpZCI6ImZkMjA4NGNmNTZiNTRmMTNhNGEyNWI5Y2Q1Mzg2OGMyIiwiaXBBZGRyIjoiIiwibm9uY2UiOiIiLCJzY29wZSI6IiIsImRpc3BsYXlfbmFtZSI6IlhWMDI2MTQiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiI2NzU5ZWUzMzBiMTgyYTZiODU4MThhMzY1MzhiYTliMTkyNmNmMDYxNDAwZWY1YjRjNTJlYWU3NiIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImF1ZCI6IltcImQ6MVwiLFwiZDoyXCIsXCJ4OjBcIixcIng6MVwiLFwieDoyXCJdIiwiZXhwIjoxNzQ2Mzk5OTc0LCJpYXQiOjE3NDYzNjk5NzQsImlzcyI6ImFwaS5sb2dpbi5meWVycy5pbiIsIm5iZiI6MTc0NjM2OTk3NCwic3ViIjoiYXV0aF9jb2RlIn0.Vx73qv5YzmffZNTQA0muT33gKqODXp_flRbNSFoZWeQ"
#appSession.set_token(auth_code)
# response = appSession.generate_token()
# with open("auth_code.txt", 'w') as file:
#         file.write(auth_code)
# ## There can be two cases over here you can successfully get the acccessToken over the request or you might get some error over here. so to avoid that have this in try except block
# try: 
#     access_token = response["access_token"]
#     print("access_token::",access_token)
# except Exception as e:
#     print(e,response)  ## This will help you in debugging then and there itself like what was the error and also you would be able to see the value you got in response variable. instead of getting key_error for unsuccessfull response.




