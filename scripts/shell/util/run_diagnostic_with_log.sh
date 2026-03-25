#!/bin/bash
# Run diagnostic and save output to file

echo "Running diagnostic..."
python3 diagnose_system.py 2>&1 | tee diagnostic_output.log
echo ""
echo "Diagnostic saved to: diagnostic_output.log"
echo ""
echo "===== DIAGNOSTIC OUTPUT ====="
cat diagnostic_output.log
