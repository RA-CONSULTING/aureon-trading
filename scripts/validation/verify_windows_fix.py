#!/usr/bin/env python3
"""
Quick verification that Windows fixes are in place
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys

def check_file(filepath, expected_function):
    """Check if a file uses the expected safe print function"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if safe_print is defined
        has_safe_print = 'def safe_print(' in content
        
        # Count regular print vs safe_print (excluding builtins.print inside safe_print)
        import re
        # Match print( but not safe_print( or builtins.print(
        regular_prints = len(re.findall(r'(?<!safe_)(?<!builtins\.)print\(', content))
        safe_prints = content.count('safe_print(')
        
        print(f"\n📄 {filepath}")
        print(f"   {'✅' if has_safe_print else '❌'} Has safe_print() definition: {has_safe_print}")
        print(f"   {'✅' if regular_prints == 0 else '⚠️ '} Regular print() calls: {regular_prints}")
        print(f"   {'✅' if safe_prints > 0 else '❌'} Safe print() calls: {safe_prints}")
        
        return has_safe_print and regular_prints == 0
    except Exception as e:
        print(f"\n❌ {filepath}: Error reading file: {e}")
        return False

print("="*80)
print("🔍 WINDOWS FIX VERIFICATION")
print("="*80)

files_to_check = [
    'micro_profit_labyrinth.py',
    'aureon_command_center.py',
    'aureon_game_launcher.py'
]

all_good = True
for filepath in files_to_check:
    if not check_file(filepath, 'safe_print'):
        all_good = False

print("\n" + "="*80)
if all_good:
    print("✅ ALL FILES HAVE WINDOWS FIX APPLIED!")
    print("   You can safely run: python aureon_game_launcher.py")
else:
    print("⚠️  SOME FILES NEED FIXING!")
    print("   Run: git pull origin main")
print("="*80)

sys.exit(0 if all_good else 1)
