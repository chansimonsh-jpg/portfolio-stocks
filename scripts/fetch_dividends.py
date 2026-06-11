import json
import yfinance as yf
from datetime import datetime
import os

# 所有需要追蹤股息嘅股票
SYMBOLS = {
    # 美股
    "AAPL": "US", "MSFT": "US", "GOOGL": "US", "AMZN": "US",
    "NVDA": "US", "META": "US", "TSLA": "US", "JPM": "US",
    "JNJ": "US", "V": "US", "WMT": "US", "XOM": "US",
    "MA": "US", "PG": "US", "HD": "US", "CVX": "US",
    "KO": "US", "PEP": "US", "COST": "US", "MRK": "US",
    "ABBV": "US", "OXY": "US", "DIS": "US", "MCD": "US",
    # US ETF
    "SPY": "US", "VOO": "US", "QQQ": "US", "VTI": "US",
    "GLD": "US", "ARKK": "US", "IVV": "US", "VEA": "US",
    "VWO": "US", "AGG": "US",
    # 港股 (加 .HK suffix)
    "0005.HK": "HK", "0700.HK": "HK", "9988.HK": "HK",
    "0941.HK": "HK", "1299.HK": "HK", "0388.HK": "HK",
    "2318.HK": "HK", "1211.HK": "HK", "3690.HK": "HK",
    "0883.HK": "HK", "1113.HK": "HK", "0001.HK": "HK",
    "0002.HK": "HK", "0003.HK": "HK", "0011.HK": "HK",
    "0016.HK": "HK", "0066.HK": "HK", "2020.HK": "HK",
    # 英股 (加 .L suffix)
    "SHEL.L": "UK", "AZN.L": "UK", "HSBA.L": "UK",
    "ULVR.L": "UK", "BP.L": "UK", "GSK.L": "UK",
    "RIO.L": "UK", "DGE.L": "UK", "BATS.L": "UK",
    "UKW.L": "UK", "BARC.L": "UK", "LLOY.L": "UK",
    "VOD.L": "UK",
    # 東南亞
    "D05.SI": "SEA", "O39.SI": "SEA", "U11.SI": "SEA",
    "Z74.SI": "SEA", "C6L.SI": "SEA",
    "BBCA.JK": "SEA", "BMRI.JK": "SEA", "TLKM.JK": "SEA",
    "MAYBANK.KL": "SEA", "CIMB.KL": "SEA",
}

def fetch_dividend_yield(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 嘗試多個欄位
        yield_val = (
            info.get("dividendYield") or
            info.get("trailingAnnualDividendYield") or
            0
        )
        
        # 如果 dividendYield 係 None 或 0，試用 dividendRate / price 計算
        if not yield_val or yield_val == 0:
            dividend_rate = info.get("dividendRate") or 0
            price = info.get("regularMarketPrice") or info.get("currentPrice") or 0
            if dividend_rate and price:
                yield_val = dividend_rate / price
        
        return round(float(yield_val), 6) if yield_val else 0
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
            print(f"✓ {symbol}: {yield_val*100:.2f}%")
        else:
            failed += 1
            print(f"- {symbol}: no dividend")
    
    # 讀取現有 dividends.json 版本號
    version = "1.0.0"
    try:
        with open("dividends.json", "r") as f:
            existing = json.load(f)
            # 版本號遞增
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
    
    print(f"\n✅ Done! {success} with dividend, {failed} without")
    print(f"Updated dividends.json to version {version}")

if __name__ == "__main__":
    main()
