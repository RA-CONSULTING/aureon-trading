# Manual Data Collection Guide

## 30-Day Ionospheric Data Collection

Since automated downloads are timing out, here's how to manually collect data:

### Method 1: Browser Automation (Recommended)

Use a browser extension or script to automatically download images:

1. **Schumann Resonance Data**
   - URL: https://schumannresonancedata.com/
   - Frequency: Every 10 minutes
   - Action: Download the sonogram image each time it updates
   - Save to: `/mnt/okcomputer/output/ionospheric_data/schumann/`
   - Filename format: `schumann_YYYY-MM-DD_HH-MM-SS.jpg`

2. **Space Weather Data**
   - URL: https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json
   - Frequency: Every hour
   - Action: Download JSON file
   - Save to: `/mnt/okcomputer/output/ionospheric_data/analysis/`
   - Filename format: `kp_index_YYYYMMDD_HHMMSS.json`

### Method 2: Python Script with Selenium

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def collect_schumann():
    driver = webdriver.Chrome()
    driver.get("https://schumannresonancedata.com/")

    # Find and click download button
    download_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
    download_btn.click()

    time.sleep(2)
    driver.quit()

# Run every 10 minutes
while True:
    collect_schumann()
    time.sleep(600)
```

### Method 3: wget/curl with Retry

```bash
#!/bin/bash

DATA_DIR="/mnt/okcomputer/output/ionospheric_data"

while true; do
    TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)

    # Try to download with retries
    for i in {1..5}; do
        curl -L -o "$DATA_DIR/schumann/schumann_$TIMESTAMP.jpg"              "https://schumannresonancedata.com/sonogram/current" && break
        sleep 10
    done

    sleep 600  # 10 minutes
done
```

### Method 4: Contact Data Providers

Request historical data directly from:
- Space Observing System (Tomsk): Contact through schumannresonancedata.com
- NOAA NCEI: Request archival data via https://www.ncei.noaa.gov/contact
- GIRO: Request via https://giro.uml.edu/

### Data Collection Checklist

- [ ] Set up data directory structure
- [ ] Configure download script
- [ ] Test downloads (single file)
- [ ] Start continuous collection
- [ ] Monitor for 24 hours
- [ ] Verify data quality
- [ ] Continue for 30 days
- [ ] Run analysis pipeline

### Expected Data Volume

- Schumann: ~4,320 images (30 days × 144/day)
- Space Weather: ~720 JSON files (30 days × 24/day)
- Total: ~25 GB

### After 30 Days

Run the analysis:
```bash
python3 /mnt/okcomputer/output/ionospheric_data/analyze_data.py
```
