LAST_ALERT = None
from plyer import notification

LAST_ALERT = None

def send_desktop_alert(
    title,
    message
):

    notification.notify(
        title=title,
        message=message,
        timeout=10
    )