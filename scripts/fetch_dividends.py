import json
import time
import yfinance as yf
from datetime import datetime

SYMBOLS = {
    "AAPL": "US", "MSFT": "US", "GOOGL": "US", "AMZN": "US",
    "NVDA": "US", "META": "US", "TSLA": "US", "JPM": "US",
    "JNJ": "US", "V": "US", "WMT": "US", "XOM": "US",
    "MA": "US", "PG": "US", "HD": "US", "CVX": "US",
    "KO": "US", "PEP": "US", "COST": "US", "MRK": "US",
    "ABBV": "US", "OXY": "US", "DIS": "US", "MCD": "US",
    "SPY": "US", "VOO": "US", "QQQ": "US", "VTI": "US",
    "GLD": "US", "ARKK": "US", "IVV": "US", "VEA": "US",
    "VWO": "US", "AGG": "US",
    "0005.HK": "HK", "0700.HK": "HK", "9988.HK": "HK",
    "0941.HK": "HK", "1299.HK": "HK", "0388.HK": "HK",
    "2318.HK": "HK", "1211.HK": "HK", "3690.HK": "HK",
    "0883.HK": "HK", "1113.HK": "HK", "0001.HK": "HK",
    "0002.HK": "HK", "0003.HK": "HK", "0011.HK": "HK",
    "0016.HK": "HK", "0066.HK": "HK", "2020.HK": "HK",
    "SHEL.L": "UK", "AZN.L": "UK", "HSBA.L": "UK",
    "ULVR.L": "UK", "BP.L": "UK", "GSK.L": "UK",
    "RIO.L": "UK", "DGE.L": "UK", "BATS.L": "UK",
    "UKW.L": "UK", "BARC.L": "UK", "LLOY.L": "UK",
    "VOD.L": "UK",
    "D05.SI": "SEA", "O39.SI": "SEA", "U11.SI": "SEA",
    "Z74.SI": "SEA", "C6L.SI": "SEA",
    "BBCA.JK": "SEA", "BMRI.JK": "SEA", "TLKM.JK": "SEA",
    "MAYBANK.KL": "SEA", "CIMB.KL": "SEA",
}

# Yahoo Finance symbol overrides — some symbols use numeric codes instead of names
SYMBOL_OVERRIDES = {
    "MAYBANK.KL": "1155.KL",  # Malayan Banking Berhad
    "CIMB.KL": "1023.KL",     # CIMB Group Holdings Berhad
}

MAX_RETRIES = 3
RETRY_DELAY = 5       # seconds between retries on failure
REQUEST_DELAY = 1.5   # seconds between symbols (avoid rate limiting)


def fetch_dividend_yield(symbol):
    fetch_symbol = SYMBOL_OVERRIDES.get(symbol, symbol)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ticker = yf.Ticker(fetch_symbol)
            info = ticker.info

            dividend_rate = info.get("dividendRate") or 0
            price = (
                info.get("regularMarketPrice") or
                info.get("currentPrice") or
                info.get("previousClose") or
                0
            )

            # 英股特殊處理：price 係便士，需要除 100 轉英鎊
            is_uk = symbol.endswith(".L")
            if dividend_rate and price and float(price) > 0:
                p = float(price)
                if is_uk:
                    p = p / 100  # 便士轉英鎊
                result = float(dividend_rate) / p
                print(f"  {symbol}: rate={dividend_rate}, price={p:.2f}, yield={result*100:.2f}%")
                return round(result, 6)

            # Fallback: 用 dividendYield（ETF 通常只有呢個）
            # 正常股息率範圍 0%~15%，超出視為異常（常見 bug：yfinance 回傳百分比形式如 0.38 即 38%）
            yield_val = info.get("dividendYield") or 0
            if yield_val and 0 < float(yield_val) < 0.15:
                print(f"  {symbol}: yield(fallback)={float(yield_val)*100:.2f}%")
                return round(float(yield_val), 6)

            # 再試 trailingAnnualDividendYield
            trailing = info.get("trailingAnnualDividendYield") or 0
            if trailing and 0 < float(trailing) < 0.15:
                print(f"  {symbol}: trailing yield={float(trailing)*100:.2f}%")
                return round(float(trailing), 6)

            print(f"  {symbol}: no dividend data")
            return 0

        except Exception as e:
            print(f"  {symbol}: attempt {attempt}/{MAX_RETRIES} failed - {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                print(f"  {symbol}: giving up after {MAX_RETRIES} attempts")
                return None  # None = fetch failed, distinguish from "no dividend" (0)


def main():
    print(f"Fetching dividend yields for {len(SYMBOLS)} symbols...")

    # 讀取現有資料作為 fallback（fetch 失敗時保留舊數值）
    existing_yields = {}
    version = "1.0.0"
    try:
        with open("dividends.json", "r") as f:
            existing = json.load(f)
            existing_yields = existing.get("yields", {})
            parts = existing.get("version", "1.0.0").split(".")
            parts[2] = str(int(parts[2]) + 1)
            version = ".".join(parts)
    except Exception:
        pass

    yields = {}
    success = 0
    failed = 0
    errors = []

    for i, (symbol, market) in enumerate(SYMBOLS.items(), 1):
        yield_val = fetch_dividend_yield(symbol)

        if yield_val is None:
            # Fetch failed - 保留舊數值（如果有），否則 0
            yields[symbol] = existing_yields.get(symbol, 0)
            failed += 1
            errors.append(symbol)
        else:
            yields[symbol] = yield_val
            if yield_val > 0:
                success += 1
            else:
                failed += 1

        # 避免 rate limiting，每隻股票之間 delay
        if i < len(SYMBOLS):
            time.sleep(REQUEST_DELAY)

    output = {
        "version": version,
        "updatedAt": datetime.utcnow().strftime("%Y-%m-%d"),
        "totalSymbols": len(SYMBOLS),
        "withDividend": success,
        "yields": yields
    }

    with open("dividends.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone! {success} with dividend, {failed} without")
    print(f"Updated dividends.json to version {version}")

    if errors:
        print(f"\n⚠️  Failed to fetch (kept old values): {', '.join(errors)}")
        # Exit with error code if too many failures (helps detect systemic issues)
        if len(errors) > len(SYMBOLS) * 0.3:  # >30% failed
            print(f"\n❌ Too many failures ({len(errors)}/{len(SYMBOLS)}), failing the job")
            exit(1)


if __name__ == "__main__":
    main()
