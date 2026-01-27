#!/usr/bin/env python3
"""
AUREON Credential Manager
Securely stores API keys in Windows Credential Manager
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import keyring
import json

SERVICE_NAME = "AUREON_Trading"

class CredentialManager:
    """Manages API credentials using Windows Credential Manager"""
    
    EXCHANGES = ['binance', 'kraken', 'alpaca', 'capital']
    
    def __init__(self):
        self.service = SERVICE_NAME
    
    def has_credentials(self) -> bool:
        """Check if any credentials are stored"""
        for exchange in self.EXCHANGES:
            if self.get_credentials(exchange):
                return True
        return False
    
    def get_credentials(self, exchange: str) -> dict | None:
        """Get credentials for an exchange from keychain"""
        try:
            creds_json = keyring.get_password(self.service, exchange)
            if creds_json:
                return json.loads(creds_json)
        except Exception as e:
            print(f"Error getting credentials for {exchange}: {e}")
        return None
    
    def save_credentials(self, exchange: str, api_key: str, api_secret: str, **extra) -> bool:
        """Save credentials to keychain"""
        try:
            creds = {
                'api_key': api_key,
                'api_secret': api_secret,
                **extra
            }
            keyring.set_password(self.service, exchange, json.dumps(creds))
            return True
        except Exception as e:
            print(f"Error saving credentials for {exchange}: {e}")
            return False
    
    def delete_credentials(self, exchange: str) -> bool:
        """Delete credentials from keychain"""
        try:
            keyring.delete_password(self.service, exchange)
            return True
        except Exception as e:
            print(f"Error deleting credentials for {exchange}: {e}")
            return False
    
    def get_all_exchanges_status(self) -> dict:
        """Get status of all exchanges"""
        return {
            exchange: self.get_credentials(exchange) is not None
            for exchange in self.EXCHANGES
        }


# Test the credential manager
if __name__ == '__main__':
    cm = CredentialManager()
    print("Credential Manager Test")
    print("-" * 40)
    
    status = cm.get_all_exchanges_status()
    for exchange, has_creds in status.items():
        icon = "✅" if has_creds else "❌"
        print(f"{icon} {exchange.capitalize()}")
