import json
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

def fetch_dividend_yield(symbol):
    try:
        ticker = yf.Ticker(symbol)
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
        yield_val = info.get("dividendYield") or 0
        if yield_val and 0 < float(yield_val) < 0.5:
            print(f"  {symbol}: yield(fallback)={float(yield_val)*100:.2f}%")
            return round(float(yield_val), 6)

        # 再試 trailingAnnualDividendYield
        trailing = info.get("trailingAnnualDividendYield") or 0
        if trailing and 0 < float(trailing) < 0.5:
            print(f"  {symbol}: trailing yield={float(trailing)*100:.2f}%")
            return round(float(trailing), 6)

        print(f"  {symbol}: no dividend data")
        return 0

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return 0

def main():
    print(f"Fetching dividend yields for {len(SYMBOLS)} symbols...")

    yields = {}
    success = 0
    failed = 0

    for symbol, market in SYMBOLS.items():
        yield_val = fetch_dividend_yield(symbol)
        yields[symbol] = yield_val

        if yield_val > 0:
            success += 1
        else:
            failed += 1

    version = "1.0.0"
    try:
        with open("dividends.json", "r") as f:
            existing = json.load(f)
            parts = existing.get("version", "1.0.0").split(".")
            parts[2] = str(int(parts[2]) + 1)
            version = ".".join(parts)
    except:
        pass

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

if __name__ == "__main__":
    main()
