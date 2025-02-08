def run_add_asset(add_asset):
    """비공개 자산 추가 함수. main.py의 `add_asset()`을 호출"""
    """아래는 추가 예시"""
    add_asset("stock", "Stocks", "AAPL", 46, "USD", 1)
    add_asset("cash", "Cash", "", 69476, "KRW", 1, 1)
    add_asset("cash", "Cash", "", 10899.87, "USD", 1, 1)
    add_asset("stock", "Stocks", "005930.KS", 200, "KRW", 1)
    add_asset("stock", "Commodities", "411060.KS", 300, "KRW", 1)