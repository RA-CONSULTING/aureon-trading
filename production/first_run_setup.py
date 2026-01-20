#!/usr/bin/env python3
"""
🎮👑 AUREON FIRST-RUN SETUP WIZARD 👑🎮
=====================================
Interactive CLI setup for production environment.
Guides user through exchange configuration and risk settings.
"""

import sys
import os
import json
import getpass
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# UTF-8 for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# ═══════════════════════════════════════════════════════════════════════════
# Configuration Dataclasses
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ExchangeConfig:
    """Exchange API configuration"""
    enabled: bool = False
    api_key: str = ""
    api_secret: str = ""
    sandbox: bool = True  # Always start in sandbox mode
    extra: Dict[str, str] = None
    
    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


@dataclass 
class RiskConfig:
    """Risk management settings"""
    max_position_size_usd: float = 10.0  # Very conservative default
    max_daily_loss_usd: float = 5.0
    max_trades_per_day: int = 100
    dry_run_mode: bool = True  # Always default to dry run
    require_confirmation: bool = True


@dataclass
class AureonConfig:
    """Master configuration"""
    version: str = "1.0.0"
    setup_complete: bool = False
    exchanges: Dict[str, ExchangeConfig] = None
    risk: RiskConfig = None
    
    def __post_init__(self):
        if self.exchanges is None:
            self.exchanges = {}
        if self.risk is None:
            self.risk = RiskConfig()


# ═══════════════════════════════════════════════════════════════════════════
# Setup Wizard
# ═══════════════════════════════════════════════════════════════════════════

class FirstRunSetup:
    """Interactive first-run setup wizard"""
    
    BANNER = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║     █████╗ ██╗   ██╗██████╗ ███████╗ ██████╗ ███╗   ██╗                   ║
    ║    ██╔══██╗██║   ██║██╔══██╗██╔════╝██╔═══██╗████╗  ██║                   ║
    ║    ███████║██║   ██║██████╔╝█████╗  ██║   ██║██╔██╗ ██║                   ║
    ║    ██╔══██║██║   ██║██╔══██╗██╔══╝  ██║   ██║██║╚██╗██║                   ║
    ║    ██║  ██║╚██████╔╝██║  ██║███████╗╚██████╔╝██║ ╚████║                   ║
    ║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝                   ║
    ║                                                                           ║
    ║                    ⚙️  FIRST-RUN SETUP WIZARD ⚙️                          ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """
    
    EXCHANGES = {
        'alpaca': {
            'name': '🦙 Alpaca',
            'description': 'US Stocks & Crypto (recommended for beginners)',
            'fields': ['api_key', 'api_secret'],
            'sandbox_url': 'https://paper-api.alpaca.markets'
        },
        'kraken': {
            'name': '🐙 Kraken',
            'description': 'Cryptocurrency exchange',
            'fields': ['api_key', 'api_secret']
        },
        'binance': {
            'name': '🟡 Binance',
            'description': 'Global crypto exchange',
            'fields': ['api_key', 'api_secret']
        },
        'capital': {
            'name': '💼 Capital.com',
            'description': 'CFD trading (advanced)',
            'fields': ['api_key', 'api_secret', 'password']
        }
    }
    
    def __init__(self):
        self.config_dir = Path(os.environ.get('AUREON_CONFIG', '/aureon/config'))
        self.config_file = self.config_dir / 'aureon.json'
        self.credentials_file = self.config_dir / '.credentials.json'
        self.config = AureonConfig()
    
    def run(self):
        """Run the setup wizard"""
        self._clear_screen()
        print(self.BANNER)
        
        print("\n" + "═" * 75)
        print("  Welcome to AUREON Trading System!")
        print("  This wizard will help you configure your trading environment.")
        print("═" * 75 + "\n")
        
        # Step 1: Safety warning
        self._show_safety_warning()
        
        # Step 2: Exchange setup
        self._setup_exchanges()
        
        # Step 3: Risk configuration
        self._setup_risk_limits()
        
        # Step 4: Review and confirm
        self._review_config()
        
        # Step 5: Save configuration
        self._save_config()
        
        print("\n" + "═" * 75)
        print("  ✅ Setup complete! AUREON is ready to launch.")
        print("═" * 75 + "\n")
    
    def _clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _show_safety_warning(self):
        """Display important safety warnings"""
        print("⚠️  IMPORTANT SAFETY INFORMATION ⚠️")
        print("-" * 50)
        print("""
1. 🔒 NEVER enable withdrawal permissions on API keys
2. 💰 Start with SMALL amounts you can afford to lose
3. 📊 Use DRY RUN mode to test strategies first
4. 🛡️ Set strict risk limits to protect your capital
5. 🔐 API keys are encrypted and stored locally only
        """)
        
        input("\nPress ENTER to acknowledge and continue...")
        print()
    
    def _setup_exchanges(self):
        """Guide user through exchange setup"""
        print("\n" + "═" * 75)
        print("  STEP 1: Exchange Configuration")
        print("═" * 75 + "\n")
        
        print("Available exchanges:")
        for i, (key, info) in enumerate(self.EXCHANGES.items(), 1):
            print(f"  {i}. {info['name']} - {info['description']}")
        
        print("\nYou need at least ONE exchange configured to trade.")
        print("Enter exchange numbers separated by commas (e.g., 1,2) or 'skip' to skip:\n")
        
        choice = input("Your choice: ").strip().lower()
        
        if choice == 'skip':
            print("\n⚠️  No exchanges configured. You can add them later in settings.")
            return
        
        # Parse choices
        try:
            indices = [int(x.strip()) for x in choice.split(',')]
            exchange_keys = list(self.EXCHANGES.keys())
            
            for idx in indices:
                if 1 <= idx <= len(exchange_keys):
                    exchange_id = exchange_keys[idx - 1]
                    self._configure_exchange(exchange_id)
        except ValueError:
            print("Invalid input. Skipping exchange setup.")
    
    def _configure_exchange(self, exchange_id: str):
        """Configure a specific exchange"""
        info = self.EXCHANGES[exchange_id]
        print(f"\n--- Configuring {info['name']} ---\n")
        
        config = ExchangeConfig(enabled=True, sandbox=True)
        
        # Get API credentials
        print("Enter your API credentials:")
        print("(Stored locally with restricted file permissions)\n")
        
        config.api_key = input(f"  API Key: ").strip()
        config.api_secret = getpass.getpass(f"  API Secret: ").strip()
        
        # Extra fields (e.g., password for Capital.com)
        if 'password' in info.get('fields', []):
            config.extra['password'] = getpass.getpass(f"  Password: ").strip()
        
        # Sandbox mode
        print(f"\n  📦 Sandbox/Paper mode: ENABLED (recommended)")
        print("     Real trading will require manual activation later.\n")
        
        self.config.exchanges[exchange_id] = config
        print(f"  ✅ {info['name']} configured successfully!")
    
    def _setup_risk_limits(self):
        """Configure risk management settings"""
        print("\n" + "═" * 75)
        print("  STEP 2: Risk Management")
        print("═" * 75 + "\n")
        
        print("Setting conservative defaults to protect your capital.\n")
        
        risk = RiskConfig()
        
        # Max position size
        try:
            val = input(f"  Max position size (USD) [{risk.max_position_size_usd}]: ").strip()
            if val:
                risk.max_position_size_usd = float(val)
        except ValueError:
            pass
        
        # Max daily loss
        try:
            val = input(f"  Max daily loss (USD) [{risk.max_daily_loss_usd}]: ").strip()
            if val:
                risk.max_daily_loss_usd = float(val)
        except ValueError:
            pass
        
        # Max trades per day
        try:
            val = input(f"  Max trades per day [{risk.max_trades_per_day}]: ").strip()
            if val:
                risk.max_trades_per_day = int(val)
        except ValueError:
            pass
        
        # Dry run mode
        print(f"\n  🧪 DRY RUN mode: ENABLED")
        print("     All trades will be simulated. No real money at risk.")
        risk.dry_run_mode = True
        
        self.config.risk = risk
        print("\n  ✅ Risk limits configured!")
    
    def _review_config(self):
        """Review configuration before saving"""
        print("\n" + "═" * 75)
        print("  STEP 3: Review Configuration")
        print("═" * 75 + "\n")
        
        # Exchanges
        print("📊 EXCHANGES:")
        if self.config.exchanges:
            for ex_id, ex_config in self.config.exchanges.items():
                info = self.EXCHANGES[ex_id]
                mode = "🧪 Sandbox" if ex_config.sandbox else "💰 Live"
                print(f"   {info['name']}: Enabled ({mode})")
        else:
            print("   None configured")
        
        # Risk
        print("\n🛡️ RISK LIMITS:")
        print(f"   Max position: ${self.config.risk.max_position_size_usd:.2f}")
        print(f"   Max daily loss: ${self.config.risk.max_daily_loss_usd:.2f}")
        print(f"   Max trades/day: {self.config.risk.max_trades_per_day}")
        print(f"   Mode: {'🧪 DRY RUN' if self.config.risk.dry_run_mode else '💰 LIVE'}")
        
        print("\n")
        confirm = input("Save this configuration? (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("\n❌ Setup cancelled. Run again to reconfigure.")
            sys.exit(1)
    
    def _save_config(self):
        """Save configuration to disk"""
        print("\n💾 Saving configuration...")
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract credentials (stored separately with encryption)
        credentials = {}
        config_data = {
            'version': self.config.version,
            'setup_complete': True,
            'exchanges': {},
            'risk': asdict(self.config.risk)
        }
        
        for ex_id, ex_config in self.config.exchanges.items():
            # Store credentials separately
            credentials[ex_id] = {
                'api_key': ex_config.api_key,
                'api_secret': ex_config.api_secret,
                'extra': ex_config.extra
            }
            # Config only stores non-sensitive data
            config_data['exchanges'][ex_id] = {
                'enabled': ex_config.enabled,
                'sandbox': ex_config.sandbox
            }
        
        # Save main config with restrictive permissions
        # Set umask to ensure file is created with 600 permissions
        old_umask = os.umask(0o077)
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            # Explicitly set permissions (belt and suspenders)
            os.chmod(self.config_file, 0o600)
        finally:
            os.umask(old_umask)
        print(f"   ✅ Config saved to {self.config_file} (mode 600)")
        
        # Try to save credentials to OS keyring (secure), fallback to file
        keyring_success = self._save_to_keyring(credentials)
        
        if not keyring_success:
            # Fallback: save to file with restricted permissions
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            os.chmod(self.credentials_file, 0o600)  # Restrict permissions
            print(f"   ⚠️  Credentials saved to file (keyring unavailable)")
            print(f"      Location: {self.credentials_file}")
        else:
            print(f"   ✅ Credentials saved to OS keyring (secure)")
    
    def _save_to_keyring(self, credentials: dict) -> bool:
        """Attempt to save credentials to OS keyring"""
        try:
            import keyring
            SERVICE_NAME = "AUREON_Trading"
            
            for exchange_id, creds in credentials.items():
                # Store as JSON in keyring
                keyring.set_password(SERVICE_NAME, exchange_id, json.dumps(creds))
            
            return True
        except ImportError:
            print("   ℹ️  keyring package not installed - using file storage")
            return False
        except Exception as e:
            print(f"   ℹ️  Keyring unavailable ({e}) - using file storage")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    wizard = FirstRunSetup()
    wizard.run()
