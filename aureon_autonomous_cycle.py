from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import json
import time
import sys
import random
from capital_client import CapitalClient

# ==========================================
# 🔄 AUREON AUTONOMOUS CYCLE (Infinite Loop)
# ==========================================
# Phase 1: Energy Scan (Balance Check)
# Phase 2: Quantum Selection (Target Acquisition)
# Phase 3: Deployment (Buy Execution)
# Phase 4: Harvest Watch (PnL Monitoring)
# Phase 5: Kinetic Strike (Sell Execution)
# ==========================================

# Configuration
TARGET_ASSET = "COPPER"
TRADE_SIZE = 0.01  # Safe size for small balance
PROFIT_TARGET_GBP = 0.02  # Low threshold for rapid cycling demo
MIN_BALANCE_THRESHOLD = 20.0  # GBP
LOOP_DELAY = 10  # Seconds

# Logging Personas
def log_queen(msg):
    print(f"👑 [QUEEN] {msg}")
    sys.stdout.flush()

def log_auris(msg):
    print(f"⚕️ [DR. AURIS] {msg}")
    sys.stdout.flush()

def log_sniper(msg):
    print(f"🎯 [SNIPER] {msg}")
    sys.stdout.flush()

def log_system(msg):
    print(f"🖥️ [SYSTEM] {msg}")
    sys.stdout.flush()

def log_profit(msg):
    print(f"💰 [PROFIT GATE] {msg}")
    sys.stdout.flush()

class AutonomousAgent:
    def __init__(self):
        self.client = CapitalClient()
        self.active_deal_id = None
        self.start_balance = 0.0
        
    def connect(self):
        if not (self.client.enabled and self.client.cst):
            log_system("CRITICAL: Uplink Failed.")
            return False
        log_system("✅ Uplink Enforced. Shared Session Active.")
        return True

    def get_energy(self):
        """Phase 1: Energy Scan"""
        try:
            balances = self.client.get_account_balance()
            gbp_energy = balances.get('GBP', 0.0)
            return gbp_energy
        except Exception as e:
            log_system(f"Energy Scan Error: {e}")
            return 0.0

    def scan_reality(self):
        """Phase 2: Quantum Selection"""
        log_queen("Scanning reality branches for opportunity...")
        
        # In a full version, this would check multiple assets.
        # For this cycle, we focus on the proven timeline: COPPER.
        
        ticker = self.client.get_ticker(TARGET_ASSET)
        price = ticker.get('price', 0)
        
        if price > 0:
            log_auris(f"Harmonics detected on {TARGET_ASSET} @ {price}")
            return True, price
        else:
            log_auris(f"Void detected. {TARGET_ASSET} is silent.")
            return False, 0

    def deploy_capital(self, price):
        """Phase 3: Deployment (Buy)"""
        log_queen(f"Authorizing deployment of capital into {TARGET_ASSET}...")
        
        # Double check we don't already have one (redundancy)
        positions = self.client.get_positions()
        if positions:
            log_system("⚠️ Hold fire. Existing timeline detected.")
            self.active_deal_id = positions[0]['position']['dealId']
            return True

        res = self.client.place_market_order(TARGET_ASSET, "BUY", TRADE_SIZE)
        
        if 'dealReference' in res:
            log_sniper(f"Capital Deployed. Deal Ref: {res['dealReference']}")
            log_system("Confirming position establishment...")
            
            # Wait for confirmation/fill
            confirmed = False
            for _ in range(5):
                time.sleep(1)
                positions = self.client.get_positions()
                if positions:
                    self.active_deal_id = positions[0]['position']['dealId']
                    log_system(f"✅ Position Confirmed: {self.active_deal_id}")
                    confirmed = True
                    break
            
            return confirmed
        else:
            log_system(f"❌ Deployment Failed: {res}")
            return False

    def monitor_harvest(self):
        """Phase 4: Harvest Watch"""
        if not self.active_deal_id:
            return "NO_TARGET"

        positions = self.client.get_positions()
        target_pos = next((p for p in positions if p['position']['dealId'] == self.active_deal_id), None)
        
        if not target_pos:
            log_system("⚠️ Target lost contact. Assuming closed.")
            self.active_deal_id = None
            return "LOST"

        upl = float(target_pos['position']['upl'])
        market = target_pos['market']
        
        log_profit(f"Monitoring {market['epic']} | UnPnL: £{upl:.2f} | Target: >£{PROFIT_TARGET_GBP}")
        
        if upl >= PROFIT_TARGET_GBP:
            return "RIPE"
        elif upl < -2.0: # Safety valve (Stop Loss)
            return "ROTTEN"
        else:
            return "GROWING"

    def execute_kill(self):
        """Phase 5: Kinetic Strike (Sell)"""
        log_queen("Profit target acquired. EXECUTE.")
        log_sniper(f"Locking target {self.active_deal_id}...")
        
        res = self.client._request('DELETE', f'/positions/{self.active_deal_id}')
        
        if res.status_code == 200:
            log_sniper("💥 BOOM. Kill confirmed.")
            self.active_deal_id = None
            return True
        else:
            log_sniper(f"❌ Missed shot. Retrying. {res.text}")
            return False

    def run(self):
        if not self.connect():
            return
            
        print("\n🔄 ENABLED: INFINITE PROFIT CYCLE")
        print("Press Ctrl+C to stop the machine.\n")

        self.start_balance = self.get_energy()
        log_system(f"Initial Energy: £{self.start_balance:.2f}")

        try:
            while True:
                energy = self.get_energy()
                positions = self.client.get_positions()
                
                # === STATE: HOLDING ===
                if positions:
                    log_system(f"Current State: HOLDING ({len(positions)} active)")
                    self.active_deal_id = positions[0]['position']['dealId']
                    
                    status = self.monitor_harvest()
                    
                    if status == "RIPE":
                        log_auris("Harmonic peak reached. Collapsing wave function.")
                        self.execute_kill()
                        
                        # Energy Audit
                        new_energy = self.get_energy()
                        diff = new_energy - self.start_balance
                        log_profit(f"Cycle Complete. Net System Change: £{diff:+.2f}")
                        
                    elif status == "ROTTEN":
                        log_queen("Rot detected. Purging timeline.")
                        self.execute_kill()
                    else:
                        log_queen("Patience. The timeline must mature.")
                        time.sleep(LOOP_DELAY)
                        
                # === STATE: HUNTING ===
                else:
                    log_system("Current State: HUNTING")
                    
                    if energy < MIN_BALANCE_THRESHOLD:
                        log_system(f"⚠️ Low Energy (£{energy}). Buying capability compromised.")
                        time.sleep(30)
                        continue
                        
                    valid, price = self.scan_reality()
                    if valid:
                        success = self.deploy_capital(price)
                        if success:
                            log_queen("Timeline anchored. Resetting cycle.")
                        else:
                            log_system("Deployment failed. Retrying shortly.")
                            time.sleep(5)
                    else:
                        time.sleep(10)
                
                time.sleep(2)

        except KeyboardInterrupt:
            log_system("🛑 Manual Override. Safety Systems Engaged.")

if __name__ == "__main__":
    agent = AutonomousAgent()
    agent.run()
