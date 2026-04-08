#!/bin/bash
# Batch download script for Schumann resonance historical data
# Usage: bash download_schumann_batch.sh

DATA_DIR="/mnt/okcomputer/output/ionospheric_data/schumann"
mkdir -p "$DATA_DIR"

# Base URL pattern
BASE_URL="https://ljnpynnorwveqpsgkxws.supabase.co/storage/v1/object/public/sonograms"

# Function to download a specific timestamp
download_schumann() {
    local date_str=$1
    local time_str=$2

    # URL format: earth-resonance-YYYY-MM-DDTHH-MM-SS-MSZ.jpg
    url="${BASE_URL}/earth-resonance-${date_str}T${time_str}-000Z.jpg"
    output="${DATA_DIR}/schumann_${date_str}_${time_str}.jpg"

    # Download with curl
    curl -s -L --max-time 10 "$url" -o "$output"

    # Check if valid (size > 50KB)
    if [ -f "$output" ]; then
        size=$(stat -f%z "$output" 2>/dev/null || stat -c%s "$output" 2>/dev/null)
        if [ "$size" -gt 50000 ]; then
            echo "✓ Downloaded: $date_str $time_str (${size} bytes)"
        else
            rm "$output"
            echo "✗ Failed: $date_str $time_str (too small)"
        fi
    else
        echo "✗ Failed: $date_str $time_str (no file)"
    fi
}

# Download recent data (last 24 hours)
echo "Downloading recent Schumann data..."
echo "===================================="

# Current time (UTC)
CURRENT_DATE=$(date -u +%Y-%m-%d)

# Download every 10 minutes for the last 24 hours
for hour in {0..23}; do
    for minute in 00 10 20 30 40 50; do
        HOUR_STR=$(printf "%02d" $hour)
        TIME_STR="${HOUR_STR}-${minute}-00"
        download_schumann "$CURRENT_DATE" "$TIME_STR"
    done
done

echo ""
echo "===================================="
echo "Download complete!"
echo "Files saved to: $DATA_DIR"
ls -la "$DATA_DIR" | wc -l
echo "sonograms downloaded"
