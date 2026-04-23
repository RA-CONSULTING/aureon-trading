#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test harmonic field node population"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from aureon_harmonic_liquid_aluminium import HarmonicLiquidAluminiumField
    
    print("🔩 Testing Harmonic Liquid Aluminium Field\n")
    
    # Create field
    field = HarmonicLiquidAluminiumField()
    print(f"✅ Field created: {field.cycle_count} cycles\n")
    
    # Add test positions (simulating what dashboard does)
    test_positions = [
        {'symbol': 'SHIBUSD', 'exchange': 'binance', 'quantity': 934990, 'avgCost': 0.000026, 'currentPrice': 0.00000689},
        {'symbol': 'TRXUSD', 'exchange': 'binance', 'quantity': 1500, 'avgCost': 0.15, 'currentPrice': 0.28390},
        {'symbol': 'TUSD', 'exchange': 'binance', 'quantity': 100, 'avgCost': 1.0, 'currentPrice': 0.00796},
        {'symbol': 'BSXUSD', 'exchange': 'binance', 'quantity': 500, 'avgCost': 2.5, 'currentPrice': 1.25},
        {'symbol': 'LPTUSD', 'exchange': 'binance', 'quantity': 10, 'avgCost': 15.0, 'currentPrice': 2.715},
    ]
    
    print("📝 Adding positions to field...")
    for pos in test_positions:
        node = field.add_or_update_node(
            exchange=pos['exchange'],
            symbol=pos['symbol'],
            current_price=pos['currentPrice'],
            entry_price=pos['avgCost'],
            quantity=pos['quantity']
        )
        print(f"  ✅ {pos['symbol']}: freq={node.frequency:.2f}Hz, amp={node.amplitude:.4f}, energy={node.energy:.2f}")
    
    print(f"\n📊 Field Status:")
    print(f"  Total Nodes: {len(field.nodes)}")
    print(f"  Total Layers: {len(field.layers)}")
    
    # Capture snapshot
    snapshot = field.capture_snapshot()
    print(f"\n📸 Snapshot Captured:")
    print(f"  Cycle: {snapshot.cycle}")
    print(f"  Total Nodes: {snapshot.total_nodes}")
    print(f"  Total Energy: {snapshot.total_energy:.2f}")
    print(f"  Global Frequency: {snapshot.global_frequency:.2f} Hz")
    print(f"  Total Value: ${snapshot.total_value_usd:,.2f}")
    print(f"  Total P&L: ${snapshot.total_pnl_usd:+,.2f}")
    
    # Test to_dict()
    snapshot_dict = snapshot.to_dict()
    print(f"\n🔍 Snapshot Dict:")
    print(f"  Keys: {list(snapshot_dict.keys())}")
    print(f"  Global Nodes: {snapshot_dict['global']['total_nodes']}")
    print(f"  Layers: {list(snapshot_dict['layers'].keys())}")
    
    # Check each layer
    for layer_name, layer_data in snapshot_dict['layers'].items():
        print(f"\n  Layer '{layer_name}':")
        print(f"    Nodes: {layer_data['total_nodes']}")
        print(f"    Frequency: {layer_data['base_frequency']:.2f} Hz")
        print(f"    Energy: {layer_data['total_energy']:.2f}")
    
    print("\n✅ Harmonic field is working correctly!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
