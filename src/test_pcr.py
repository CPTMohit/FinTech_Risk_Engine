# src/test_pcr.py
from SmartApi import SmartConnect
import pyotp

API_KEY = "3xK955MH"
CLIENT_CODE = "AACI729341"
PIN = "0912"
TOTP_SECRET = "ZG4AT5YV6GPJQNPPVHLESN5JZI"

smart = SmartConnect(api_key=API_KEY)

totp = pyotp.TOTP(TOTP_SECRET).now()

smart.generateSession(
    CLIENT_CODE,
    PIN,
    totp
)

data = smart.putCallRatio()

print(type(data))
print(data.keys())

print(data)