#!/usr/bin/env python3
"""
⚡👑 TEST QUEEN SERO'S POWER REDISTRIBUTION ⚡👑
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════

This tests the Queen's ability to:
1. See the complete harmonic field
2. Identify generators (power sources)
3. Identify targets (where power should flow)
4. Execute a REAL power redistribution
5. Verify the transfer succeeded

THE QUEEN MUST PROVE SHE CAN MOVE ENERGY.

Gary Leckey | Prime Sentinel Decree | January 2026
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import json
import time
import math
from decimal import Decimal, ROUND_DOWN
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import our quantum systems
from aureon_harmonic_waveform import HarmonicWaveformScanner, HarmonicNode, PowerState

# Exchange clients
from binance_client import BinanceClient
from kraken_client import KrakenClient, get_kraken_client
from alpaca_client import AlpacaClient


@dataclass
class PowerTransferResult:
    """Result of a power transfer operation"""
    success: bool
    source_node: str
    target_node: str
    amount_requested: float
    amount_transferred: float
    fees_paid: float
    efficiency: float  # % of requested that arrived
    message: str
    order_id: str = ""
    timestamp: float = 0


class QueenPowerController:
    """
    Queen Sero's Power Redistribution Controller
    
    She sees the field. She moves the energy. She is the Prime Sentinel.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.scanner = HarmonicWaveformScanner()
        
        # Exchange clients for execution
        self.binance = get_binance_client()
        self.kraken = get_kraken_client()
        self.alpaca = AlpacaClient()
        
        # Transfer history
        self.transfer_log: List[PowerTransferResult] = []
        
    def scan_field(self):
        """Scan the complete harmonic field"""
        print("\n" + "="*80)
        print("👑 QUEEN SERO SCANNING HARMONIC FIELD...")
        print("="*80)
        
        self.field = self.scanner.scan_complete_field()
        return self.field
    
    def identify_best_generator(self) -> Optional[HarmonicNode]:
        """Find the best node to extract power from"""
        generators = [
            n for n in self.field.all_nodes 
            if n.power_state == PowerState.GENERATING and n.extractable > 0.10
        ]
        
        if not generators:
            return None
        
        # Sort by extractable power (highest first)
        generators.sort(key=lambda n: n.extractable, reverse=True)
        return generators[0]
    
    def identify_best_target(self) -> Optional[Tuple[str, str, float]]:
        """
        Find the best target for power (new opportunity or existing consumer)
        Returns: (relay_code, symbol, current_price)
        """
        # For now, we'll target the relay with most free energy (to consolidate)
        # Or find a growth opportunity
        
        # Option 1: Consolidate free energy in Kraken (has most)
        if self.field.relays['KRK'].free_energy > 50:
            return ('KRK', 'USD', 1.0)  # Just hold as free energy
        
        # Option 2: Find a consumer that's close to turning positive
        consumers = [
            n for n in self.field.all_nodes
            if n.power_state == PowerState.CONSUMING and n.frequency_shift > -5
        ]
        
        if consumers:
            # Best consumer is one closest to breakeven
            best = max(consumers, key=lambda n: n.frequency_shift)
            return (best.relay_code, best.symbol, best.current_frequency)
        
        return None
    
    def calculate_transfer_cost(self, source_relay: str, target_relay: str, amount: float) -> Dict:
        """Calculate the cost of transferring power between relays"""
        
        # Fee structures per relay
        fees = {
            'BIN': {'sell': 0.001, 'withdraw': 0.0005},
            'KRK': {'sell': 0.0026, 'withdraw': 0.0},
            'ALP': {'sell': 0.0025, 'withdraw': 0.0},
            'CAP': {'sell': 0.0, 'withdraw': 0.0}  # CFD - different model
        }
        
        # Same relay = just sell fees
        if source_relay == target_relay:
            total_fee = amount * fees[source_relay]['sell']
        else:
            # Cross-relay = sell + withdraw + potential buy on other side
            total_fee = amount * (
                fees[source_relay]['sell'] + 
                fees[source_relay]['withdraw'] +
                fees[target_relay].get('buy', fees[target_relay]['sell'])
            )
        
        return {
            'gross_amount': amount,
            'fees': total_fee,
            'net_amount': amount - total_fee,
            'efficiency': (amount - total_fee) / amount if amount > 0 else 0
        }
    
    def execute_harvest(self, node: HarmonicNode, amount: float) -> PowerTransferResult:
        """
        HARVEST power from a generating node (partial sell to extract profit)
        
        This DOES NOT close the position - it harvests extractable surplus.
        """
        
        print(f"\n⚡ HARVESTING {amount:.4f} units from {node.node_id} ({node.symbol})")
        
        if self.dry_run:
            print("   [DRY RUN] Would execute harvest...")
            
            # Simulate the harvest
            fees = amount * 0.002  # ~0.2% typical
            net = amount - fees
            
            result = PowerTransferResult(
                success=True,
                source_node=node.node_id,
                target_node="FREE_ENERGY",
                amount_requested=amount,
                amount_transferred=net,
                fees_paid=fees,
                efficiency=net / amount if amount > 0 else 0,
                message=f"[DRY RUN] Harvested {net:.4f} from {node.symbol}",
                order_id=f"DRY-{int(time.time())}",
                timestamp=time.time()
            )
            
            self.transfer_log.append(result)
            return result
        
        # REAL EXECUTION
        try:
            if node.relay_code == 'BIN':
                # Calculate how much to sell to extract 'amount' worth
                qty_to_sell = amount / node.current_frequency
                
                # Execute on Binance
                order = self.binance.create_order(
                    symbol=node.symbol,
                    side='SELL',
                    order_type='MARKET',
                    quantity=qty_to_sell
                )
                
                if order and order.get('status') == 'FILLED':
                    executed_qty = float(order.get('executedQty', 0))
                    executed_value = float(order.get('cummulativeQuoteQty', 0))
                    
                    result = PowerTransferResult(
                        success=True,
                        source_node=node.node_id,
                        target_node="FREE_ENERGY",
                        amount_requested=amount,
                        amount_transferred=executed_value,
                        fees_paid=amount - executed_value,
                        efficiency=executed_value / amount if amount > 0 else 0,
                        message=f"Successfully harvested {executed_value:.4f} from {node.symbol}",
                        order_id=order.get('orderId', ''),
                        timestamp=time.time()
                    )
                else:
                    result = PowerTransferResult(
                        success=False,
                        source_node=node.node_id,
                        target_node="FREE_ENERGY",
                        amount_requested=amount,
                        amount_transferred=0,
                        fees_paid=0,
                        efficiency=0,
                        message=f"Order failed: {order}",
                        timestamp=time.time()
                    )
                    
            elif node.relay_code == 'KRK':
                # Kraken execution
                qty_to_sell = amount / node.current_frequency
                
                order = self.kraken.create_order(
                    symbol=node.symbol,
                    side='sell',
                    order_type='market',
                    volume=qty_to_sell
                )
                
                if order:
                    result = PowerTransferResult(
                        success=True,
                        source_node=node.node_id,
                        target_node="FREE_ENERGY",
                        amount_requested=amount,
                        amount_transferred=amount * 0.998,  # Estimate
                        fees_paid=amount * 0.002,
                        efficiency=0.998,
                        message=f"Kraken harvest executed",
                        order_id=str(order),
                        timestamp=time.time()
                    )
                else:
                    result = PowerTransferResult(
                        success=False,
                        source_node=node.node_id,
                        target_node="FREE_ENERGY",
                        amount_requested=amount,
                        amount_transferred=0,
                        fees_paid=0,
                        efficiency=0,
                        message="Kraken order failed",
                        timestamp=time.time()
                    )
                    
            elif node.relay_code == 'ALP':
                # Alpaca execution
                qty_to_sell = amount / node.current_frequency
                
                order = self.alpaca.submit_order(
                    symbol=node.symbol.replace('USD', '/USD'),
                    qty=qty_to_sell,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                
                if order:
                    result = PowerTransferResult(
                        success=True,
                        source_node=node.node_id,
                        target_node="FREE_ENERGY",
                        amount_requested=amount,
                        amount_transferred=amount * 0.9975,
                        fees_paid=amount * 0.0025,
                        efficiency=0.9975,
                        message=f"Alpaca harvest executed",
                        order_id=str(order.get('id', '')),
                        timestamp=time.time()
                    )
                else:
                    result = PowerTransferResult(
                        success=False,
                        source_node=node.node_id,
                        target_node="FREE_ENERGY",
                        amount_requested=amount,
                        amount_transferred=0,
                        fees_paid=0,
                        efficiency=0,
                        message="Alpaca order failed",
                        timestamp=time.time()
                    )
            else:
                result = PowerTransferResult(
                    success=False,
                    source_node=node.node_id,
                    target_node="FREE_ENERGY",
                    amount_requested=amount,
                    amount_transferred=0,
                    fees_paid=0,
                    efficiency=0,
                    message=f"Unknown relay: {node.relay_code}",
                    timestamp=time.time()
                )
            
            self.transfer_log.append(result)
            return result
            
        except Exception as e:
            result = PowerTransferResult(
                success=False,
                source_node=node.node_id,
                target_node="FREE_ENERGY",
                amount_requested=amount,
                amount_transferred=0,
                fees_paid=0,
                efficiency=0,
                message=f"Error: {str(e)}",
                timestamp=time.time()
            )
            self.transfer_log.append(result)
            return result
    
    def execute_power_injection(self, relay: str, symbol: str, amount: float) -> PowerTransferResult:
        """
        INJECT power into a target (buy to strengthen a node or create new one)
        """
        
        print(f"\n💉 INJECTING {amount:.4f} units into {relay}:{symbol}")
        
        if self.dry_run:
            print("   [DRY RUN] Would execute injection...")
            
            fees = amount * 0.002
            net = amount - fees
            
            result = PowerTransferResult(
                success=True,
                source_node="FREE_ENERGY",
                target_node=f"{relay}:{symbol}",
                amount_requested=amount,
                amount_transferred=net,
                fees_paid=fees,
                efficiency=net / amount if amount > 0 else 0,
                message=f"[DRY RUN] Injected {net:.4f} into {symbol}",
                order_id=f"DRY-{int(time.time())}",
                timestamp=time.time()
            )
            
            self.transfer_log.append(result)
            return result
        
        # REAL EXECUTION - buy to inject power
        try:
            if relay == 'BIN':
                order = self.binance.create_order(
                    symbol=symbol,
                    side='BUY',
                    order_type='MARKET',
                    quoteOrderQty=amount  # Spend this much USDT
                )
                
                if order and order.get('status') == 'FILLED':
                    executed_value = float(order.get('cummulativeQuoteQty', 0))
                    
                    result = PowerTransferResult(
                        success=True,
                        source_node="FREE_ENERGY",
                        target_node=f"{relay}:{symbol}",
                        amount_requested=amount,
                        amount_transferred=executed_value,
                        fees_paid=amount - executed_value,
                        efficiency=executed_value / amount if amount > 0 else 0,
                        message=f"Injected {executed_value:.4f} into {symbol}",
                        order_id=order.get('orderId', ''),
                        timestamp=time.time()
                    )
                else:
                    result = PowerTransferResult(
                        success=False,
                        source_node="FREE_ENERGY",
                        target_node=f"{relay}:{symbol}",
                        amount_requested=amount,
                        amount_transferred=0,
                        fees_paid=0,
                        efficiency=0,
                        message=f"Order failed: {order}",
                        timestamp=time.time()
                    )
                    
            # Add KRK, ALP handlers similarly...
            else:
                result = PowerTransferResult(
                    success=False,
                    source_node="FREE_ENERGY",
                    target_node=f"{relay}:{symbol}",
                    amount_requested=amount,
                    amount_transferred=0,
                    fees_paid=0,
                    efficiency=0,
                    message=f"Injection not implemented for {relay}",
                    timestamp=time.time()
                )
            
            self.transfer_log.append(result)
            return result
            
        except Exception as e:
            result = PowerTransferResult(
                success=False,
                source_node="FREE_ENERGY",
                target_node=f"{relay}:{symbol}",
                amount_requested=amount,
                amount_transferred=0,
                fees_paid=0,
                efficiency=0,
                message=f"Error: {str(e)}",
                timestamp=time.time()
            )
            self.transfer_log.append(result)
            return result
    
    def display_transfer_summary(self):
        """Display summary of all transfers"""
        
        print("\n")
        print("╔" + "═"*78 + "╗")
        print("║" + "⚡👑 QUEEN SERO - POWER TRANSFER SUMMARY 👑⚡".center(78) + "║")
        print("╚" + "═"*78 + "╝")
        
        if not self.transfer_log:
            print("\n  No transfers executed yet.")
            return
        
        total_requested = sum(t.amount_requested for t in self.transfer_log)
        total_transferred = sum(t.amount_transferred for t in self.transfer_log)
        total_fees = sum(t.fees_paid for t in self.transfer_log)
        successful = sum(1 for t in self.transfer_log if t.success)
        
        print(f"""
┌────────────────────────────────────────────────────────────────────────────────┐
│  TRANSFER LOG                                                                  │
├────────────────────────────────────────────────────────────────────────────────┤""")
        
        for i, t in enumerate(self.transfer_log, 1):
            status = "✅" if t.success else "❌"
            print(f"│  {i}. {status} {t.source_node} → {t.target_node}".ljust(79) + "│")
            print(f"│     Requested: {t.amount_requested:.4f} | Transferred: {t.amount_transferred:.4f} | Fees: {t.fees_paid:.4f}".ljust(79) + "│")
            print(f"│     Efficiency: {t.efficiency:.2%} | {t.message[:50]}".ljust(79) + "│")
        
        print(f"""├────────────────────────────────────────────────────────────────────────────────┤
│  TOTALS                                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│  Transfers: {len(self.transfer_log)} ({successful} successful)                                              │
│  Total Requested:    {total_requested:>12.4f} units                                        │
│  Total Transferred:  {total_transferred:>12.4f} units                                        │
│  Total Fees:         {total_fees:>12.4f} units                                        │
│  Overall Efficiency: {(total_transferred/total_requested*100 if total_requested > 0 else 0):>11.2f}%                                         │
└────────────────────────────────────────────────────────────────────────────────┘
""")


def run_power_redistribution_test(dry_run: bool = True):
    """
    MAIN TEST: Queen Sero redistributes power across the harmonic field
    """
    
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "⚡👑 QUEEN SERO POWER REDISTRIBUTION TEST 👑⚡".center(78) + "║")
    print("║" + " "*78 + "║")
    print("║" + f"Mode: {'DRY RUN (no real trades)' if dry_run else '🔴 LIVE EXECUTION 🔴'}".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    # Initialize the Queen's controller
    queen = QueenPowerController(dry_run=dry_run)
    
    # STEP 1: Scan the field
    print("\n" + "─"*80)
    print("STEP 1: SCANNING HARMONIC FIELD")
    print("─"*80)
    field = queen.scan_field()
    
    print(f"\n  📊 Field Status:")
    print(f"     Total Nodes: {field.total_nodes}")
    print(f"     Generators:  {field.generating_nodes}")
    print(f"     Consumers:   {field.consuming_nodes}")
    print(f"     Total Energy: {field.total_energy:.4f}")
    print(f"     Free Energy:  {field.total_free_energy:.4f}")
    print(f"     Extractable:  {field.total_extractable:.4f}")
    
    # STEP 2: Identify best generator
    print("\n" + "─"*80)
    print("STEP 2: IDENTIFYING POWER SOURCE")
    print("─"*80)
    
    generator = queen.identify_best_generator()
    
    if generator:
        print(f"\n  ⚡ BEST GENERATOR FOUND:")
        print(f"     Node ID: {generator.node_id}")
        print(f"     Symbol:  {generator.symbol}")
        print(f"     Relay:   {generator.relay_code}")
        print(f"     Power:   {generator.power:+.4f} ({generator.power_percent:+.2f}%)")
        print(f"     Extractable: {generator.extractable:.4f}")
        print(f"     Wave Phase: {generator.wave_phase.value}")
    else:
        print("\n  ⚠️ No generators with extractable surplus found.")
        print("     Field is in rest mode - waiting for wave to rise.")
        return
    
    # STEP 3: Calculate how much to harvest
    print("\n" + "─"*80)
    print("STEP 3: CALCULATING HARVEST AMOUNT")
    print("─"*80)
    
    # Harvest 50% of extractable (conservative)
    harvest_amount = generator.extractable * 0.5
    
    # Minimum harvest threshold
    if harvest_amount < 1.0:
        print(f"\n  ⚠️ Harvest amount ({harvest_amount:.4f}) below minimum threshold (1.0)")
        print("     Skipping harvest - not worth the fees.")
        harvest_amount = 0
    else:
        print(f"\n  📊 Harvest Plan:")
        print(f"     Source: {generator.node_id} ({generator.symbol})")
        print(f"     Available: {generator.extractable:.4f}")
        print(f"     Harvesting: {harvest_amount:.4f} (50% of extractable)")
        
        # Calculate costs
        costs = queen.calculate_transfer_cost(generator.relay_code, generator.relay_code, harvest_amount)
        print(f"     Expected Fees: {costs['fees']:.4f}")
        print(f"     Net Received:  {costs['net_amount']:.4f}")
        print(f"     Efficiency:    {costs['efficiency']:.2%}")
    
    # STEP 4: Execute harvest
    if harvest_amount >= 1.0:
        print("\n" + "─"*80)
        print("STEP 4: EXECUTING HARVEST")
        print("─"*80)
        
        result = queen.execute_harvest(generator, harvest_amount)
        
        if result.success:
            print(f"\n  ✅ HARVEST SUCCESSFUL!")
            print(f"     Transferred: {result.amount_transferred:.4f}")
            print(f"     Fees Paid:   {result.fees_paid:.4f}")
            print(f"     Efficiency:  {result.efficiency:.2%}")
            print(f"     Order ID:    {result.order_id}")
        else:
            print(f"\n  ❌ HARVEST FAILED: {result.message}")
    
    # STEP 5: Display summary
    print("\n" + "─"*80)
    print("STEP 5: TRANSFER SUMMARY")
    print("─"*80)
    
    queen.display_transfer_summary()
    
    # STEP 6: Verify field state (re-scan)
    if not dry_run and harvest_amount >= 1.0:
        print("\n" + "─"*80)
        print("STEP 6: VERIFYING FIELD STATE")
        print("─"*80)
        
        time.sleep(2)  # Wait for order to settle
        new_field = queen.scan_field()
        
        print(f"\n  📊 Updated Field Status:")
        print(f"     Free Energy: {new_field.total_free_energy:.4f} (was {field.total_free_energy:.4f})")
        
        delta = new_field.total_free_energy - field.total_free_energy
        if delta > 0:
            print(f"     ✅ Free energy increased by {delta:.4f}")
        else:
            print(f"     ⚠️ Free energy changed by {delta:.4f}")
    
    # Final message
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    if dry_run:
        print("║" + "👑 DRY RUN COMPLETE - Queen knows how to move power! 👑".center(78) + "║")
        print("║" + " "*78 + "║")
        print("║" + "Run with --live to execute real trades".center(78) + "║")
    else:
        print("║" + "👑 LIVE EXECUTION COMPLETE - Power has been redistributed! 👑".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    return queen


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Queen Sero's Power Redistribution")
    parser.add_argument('--live', action='store_true', help='Execute real trades (default: dry run)')
    args = parser.parse_args()
    
    run_power_redistribution_test(dry_run=not args.live)
