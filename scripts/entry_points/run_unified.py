#!/usr/bin/env python3
"""
Quick wrapper to load .env manually and run unified ecosystem
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
from pathlib import Path

# Load .env file manually (no dotenv needed)
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, _, value = line.partition('=')
                value = value.strip('"').strip("'")
                os.environ[key] = value
    print(f"✅ Loaded {env_file}")

# Now import and run main()
from aureon_unified_ecosystem import main
main()

# Now import and run
import aureon_unified_ecosystem
