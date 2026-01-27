from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
from binance.client import Client
from dotenv import load_dotenv
from collections import Counter


def load_client() -> Client:
    load_dotenv()
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    if not api_key or not api_secret:
        raise RuntimeError("Missing BINANCE_API_KEY / BINANCE_API_SECRET env vars")
    return Client(api_key, api_secret)


def extract_trade_groups(permissions):
    if not permissions:
        return set()
    return {p for p in permissions if p.startswith('TRD_GRP_')}


def main():
    try:
        client = load_client()
        account = client.get_account()
        trade_groups = extract_trade_groups(account.get('permissions'))

        if not trade_groups:
            print("This account has no TRD_GRP permissions; Binance UK likely disabled trading.")
            return

        print(f"Account Type: {account.get('accountType', 'Unknown')}")
        print(f"Can Trade: {account.get('canTrade')}")
        print(f"Assigned Trade Groups: {', '.join(sorted(trade_groups))}")

        info = client.get_exchange_info()
        symbols = info.get('symbols', [])
        print(f"\nTotal Symbols on Exchange: {len(symbols)}")

        allowed = []
        for symbol in symbols:
            if symbol.get('status') != 'TRADING':
                continue
            if not symbol.get('isSpotTradingAllowed', False):
                continue
            permission_sets = symbol.get('permissionSets') or []
            if not permission_sets:
                continue

            # UK retail access is defined by matching Trade Groups.
            if any(trade_groups.intersection({p for p in perm if p.startswith('TRD_GRP_')}) for perm in permission_sets):
                allowed.append(symbol)

        if not allowed:
            print("\nNo spot symbols matched the account's trade groups. Binance UK may have disabled all trading.")
            return

        print(f"\nSpot Symbols Allowed for this Account: {len(allowed)}")

        quote_counts = Counter(sym['quoteAsset'] for sym in allowed)
        print("\nTop Quote Assets:")
        for quote, count in quote_counts.most_common(10):
            print(f"  {quote}: {count} pairs")

        focus_quotes = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB', 'GBP', 'EUR']
        print("\nKey Quote Coverage:")
        for fq in focus_quotes:
            print(f"  {fq}: {quote_counts.get(fq, 0)} pairs")

        # Show a few concrete tickers per fiat/major quote so we know what's tradable.
        def sample_pairs(quote, limit=5):
            picks = [sym['symbol'] for sym in allowed if sym['quoteAsset'] == quote][:limit]
            return ', '.join(picks) if picks else 'None'

        print("\nSample Pairs:")
        for quote in ['USDT', 'GBP', 'EUR', 'BTC']:
            print(f"  {quote}: {sample_pairs(quote)}")

    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
