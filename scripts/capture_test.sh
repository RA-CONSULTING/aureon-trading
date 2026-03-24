#!/bin/bash
# Capture all output to a file we can read

echo "Running test..." > test_output.txt
python3 test_why_no_trades.py >> test_output.txt 2>&1
echo "" >> test_output.txt
echo "Exit code: $?" >> test_output.txt
echo "" >> test_output.txt
echo "Test complete. Output saved to test_output.txt"
cat test_output.txt
