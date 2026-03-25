#!/usr/bin/env python3
"""Fix the if __name__ block in orca_complete_kill_cycle.py"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
with open("orca_complete_kill_cycle.py", "r") as f:
    lines = f.readlines()

# Find the line with "def _run_main():"
run_main_line = None
for i, line in enumerate(lines):
    if "def _run_main():" in line:
        run_main_line = i
        break

if run_main_line:
    # Remove the _run_main function definition and its docstring
    # Find the end of the function definition block (before the if __name__ block starts using it)
    lines_to_keep = []
    in_run_main = False
    skip_next_comment = False
    
    for i, line in enumerate(lines):
        if i == run_main_line:
            in_run_main = True
            skip_next_comment = True
            continue
        
        if in_run_main and skip_next_comment and '"""' in line:
            skip_next_comment = False
            continue
        
        if in_run_main and ("try:" in line or "# 👑" in line):
            # Found the actual start of Queen awakening logic
            in_run_main = False
        
        if not in_run_main or i < run_main_line:
            lines_to_keep.append(line)
    
    # Now fix the if __name__ block - replace the _run_main() call with the actual logic
    final_lines = []
    skip_until_except = False
    
    for i, line in enumerate(lines_to_keep):
        if "_run_main()" in line:
            # Replace with the Queen awakening logic
            final_lines.append("        # 👑 WAKE THE QUEEN (Runs in background thread) 👑\n")
            skip_until_except = True
            continue
        
        if skip_until_except and "except KeyboardInterrupt:" in line:
            skip_until_except = False
        
        if not skip_until_except:
            final_lines.append(line)
    
    with open("orca_complete_kill_cycle.py", "w") as f:
        f.writelines(final_lines)
    
    print("✅ Fixed orca_complete_kill_cycle.py")
else:
    print("❌ Could not find _run_main function")
