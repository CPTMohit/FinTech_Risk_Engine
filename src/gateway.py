"""
Angel One SmartAPI Gateway Module
Handles authentication and connection management
"""

try:
    from SmartApi import SmartConnect
except ImportError as e:
    print(f"SmartAPI Import Error: {e}")
    SmartConnect = None
except Exception as e:
    print(f"SmartAPI Unexpected Error: {e}")
    SmartConnect = None
    
import pyotp


class AngelOneDataGateway:
    """Gateway for Angel One SmartAPI connection and authentication"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        # Initialize the official Angel One SmartConnect instance
        if SmartConnect is not None:
            self.smart_conn = SmartConnect(api_key=self.api_key)
        else:
            self.smart_conn = None
        self.is_connected = False
        
    def authenticate(self, client_code, password, totp_secret):
        """Generates an encrypted session token via Angel One SmartAPI."""
        try:
            if self.smart_conn is None:
                return False, "SmartAPI library not available"
            # Generate the time-based 6-digit OTP code programmatically
            token_2fa = pyotp.TOTP(totp_secret).now() if totp_secret else ""
            
            # Request session from Angel One auth servers
            session_data = self.smart_conn.generateSession(client_code, password, token_2fa)
            
            if session_data.get('status') == True:
                self.is_connected = True
                return True, "Session tokens generated successfully."
            else:
                error_msg = session_data.get('message', 'Unknown Auth Error')
                return False, f"Angel One Reject: {error_msg}"
                
        except Exception as e:
            return False, f"Gateway Exception: {str(e)}"
