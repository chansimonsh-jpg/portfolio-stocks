def fetch_dividend_yield(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # 用 dividendRate ÷ price 計算，最準確
        dividend_rate = info.get("dividendRate") or 0
        price = (
            info.get("regularMarketPrice") or
            info.get("currentPrice") or
            info.get("previousClose") or
            0
        )

        if dividend_rate and price and price > 0:
            result = dividend_rate / price
            print(f"  {symbol}: rate={dividend_rate}, price={price}, yield={result*100:.2f}%")
            return round(result, 6)

        # Fallback: 試用 dividendYield（已係小數格式）
        yield_val = info.get("dividendYield") or 0
        if yield_val and 0 < float(yield_val) < 1:
            print(f"  {symbol}: yield(fallback)={float(yield_val)*100:.2f}%")
            return round(float(yield_val), 6)

        print(f"  {symbol}: no dividend data")
        return 0

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return 0
