#!/bin/bash
while true; do
    echo "Generating probability batch..."
    python3 generate_live_probability_batch.py
    echo "Sleeping for 60 seconds..."
    sleep 60
done
