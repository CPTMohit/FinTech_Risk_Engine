from datetime import datetime
NSE_HOLIDAYS_2026 = [
    "2026-01-26",
    "2026-03-04",
    "2026-03-27",
    "2026-04-02",
    "2026-04-14",
    "2026-05-01",
    "2026-08-15",
    "2026-10-02",
    "2026-11-12",
    "2026-12-25"
]
def get_market_status():
    
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    if today in NSE_HOLIDAYS_2026:

        return False, "MARKET CLOSED - NSE HOLIDAY"
    
    weekday = now.weekday()
    current_time = now.strftime("%H:%M")

    if weekday >= 5:
        return False, "MARKET CLOSED - WEEKEND"

    if current_time < "09:15":
        return False, "PRE-MARKET"

    if current_time > "15:30":
        return False, "MARKET CLOSED"

    return True, "MARKET OPEN"
