#!/bin/bash
# 🌍⚡ CoinAPI Setup Script ⚡🌍
# Run this once your API key is activated

echo "🔧 Setting up CoinAPI integration..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    touch .env
fi

# Check if COINAPI_KEY already exists
if grep -q "COINAPI_KEY" .env; then
    echo "⚠️  COINAPI_KEY already exists in .env"
    echo "   Current value: $(grep COINAPI_KEY .env)"
    read -p "   Replace it? (y/n): " replace
    if [ "$replace" != "y" ]; then
        echo "   Skipping..."
        exit 0
    fi
    # Remove old key
    sed -i '/COINAPI_KEY/d' .env
fi

# Get API key from user
echo ""
echo "📋 Go to https://www.coinapi.io/market-data-api/pricing"
echo "   1. Copy your API Key from the dashboard"
echo "   2. Paste it below"
echo ""
read -p "Enter your CoinAPI key: " api_key

if [ -z "$api_key" ]; then
    echo "❌ No key provided. Exiting."
    exit 1
fi

# Add to .env
echo "COINAPI_KEY=$api_key" >> .env
echo "ENABLE_COINAPI=1" >> .env

echo ""
echo "✅ CoinAPI key saved to .env"
echo ""

# Test the key
echo "🧪 Testing API key..."
export COINAPI_KEY="$api_key"

python3 << 'PYEOF'
import os
import requests

api_key = os.getenv('COINAPI_KEY')
url = 'https://rest.coinapi.io/v1/exchanges'
headers = {'X-CoinAPI-Key': api_key, 'Accept': 'application/json'}

try:
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f'\n✅ API Key is VALID!')
        print(f'📊 {len(data)} exchanges available')
        print(f'\nSample exchanges:')
        for exc in data[:5]:
            print(f'   • {exc.get("exchange_id")} - {exc.get("name", "Unknown")}')
        print(f'\n🚀 Ready to detect anomalies!')
    elif response.status_code == 401:
        print(f'\n❌ API Key INVALID or not activated yet')
        print(f'   Wait a few minutes after key creation')
        print(f'   Or check the key format in your CoinAPI dashboard')
    else:
        print(f'\n⚠️  Unexpected response: {response.status_code}')
        print(f'   {response.text[:200]}')
except Exception as e:
    print(f'\n❌ Error testing key: {e}')
PYEOF

echo ""
echo "📚 Next steps:"
echo "   1. If key is valid, you're ready to go!"
echo "   2. Run: python test_coinapi_integration.py"
echo "   3. Run: python aureon_unified_ecosystem.py (with ENABLE_COINAPI=1)"
echo ""
echo "💡 Configuration:"
echo "   • Scans every 5 minutes"
echo "   • Analyzes 3-5 symbols per scan"
echo "   • Free tier: 100 requests/day"
echo "   • ~288 potential scans/day"
echo ""
