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
try:
    print("OPTION GREEK")
    print(
        smartApi.optionGreek({})
    )
except Exception as e:
    print("ERROR:", e)

try:
    print("OI BUILDUP")
    print(
        smartApi.oIBuildup({})
    )
except Exception as e:
    print("ERROR:", e)

try:
    print("OI DATA")
    print(
        smartApi.getOIData({})
    )
except Exception as e:
    print("ERROR:", e)