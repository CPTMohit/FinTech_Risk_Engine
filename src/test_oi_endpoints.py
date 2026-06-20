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

print("=" * 50)
print("PUT CALL RATIO")
print("=" * 50)

try:
    result = smart.putCallRatio()
    print(result)

except Exception as e:
    print("PCR ERROR:", e)

print("\n" + "=" * 50)
print("OPTION GREEK")
print("=" * 50)

try:

    result = smart.optionGreek(
    {
        "name": "NIFTY",
        "expirydate": "26JUN2026"
    }
)

    print(result)

except Exception as e:
    print("OPTION GREEK ERROR:", e)

print("\n" + "=" * 50)
print("OI BUILDUP")
print("=" * 50)

try:

    result = smart.oIBuildup(
    {
        "name": "NIFTY",
        "expirytype": "NEAR"
    }
)   

    print(result)

except Exception as e:
    print("OI BUILDUP ERROR:", e)

print("\n" + "=" * 50)
print("OI DATA")
print("=" * 50)

try:

    result = smart.getOIData(
        {
            "exchange": "NFO",
            "tradingsymbol": "NIFTY24DEC2924000CE",
            "symboltoken": "61748"
        }
    )

    print(result)

except Exception as e:
    print("OI DATA ERROR:", e)