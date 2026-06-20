
from SmartApi import SmartConnect
import pyotp
API_KEY = "3xK955MH"
CLIENT_CODE = "AACI729341"
PIN = "0912"
TOTP_SECRET = "ZG4AT5YV6GPJQNPPVHLESN5JZI"


smartApi = SmartConnect(api_key=API_KEY)

totp = pyotp.TOTP(TOTP_SECRET).now()

smartApi.generateSession(
    CLIENT_CODE,
    PIN,
    totp
)

result = smartApi.searchScrip(
    "NFO",
    "NIFTY24DEC2924000"
)

print(result)