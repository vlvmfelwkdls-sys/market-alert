"""
글로벌 마켓 알림 - 카카오톡 자동 전송
GitHub Actions에서 매일 09:30(KST)에 자동 실행됩니다.
"""

import yfinance as yf
import requests
import json
import os
from datetime import datetime

# GitHub Secrets에서 토큰 읽기
ACCESS_TOKEN = os.environ.get("KAKAO_ACCESS_TOKEN", "")

TICKERS = {
    "SPY":     "S&P500",
    "QQQ":     "나스닥",
    "NVDA":    "NVDA",
    "AAPL":    "AAPL",
    "TSLA":    "TSLA",
    "BTC-USD": "BTC",
    "ETH-USD": "ETH",
}


def get_market_data():
    results = {}
    for ticker, name in TICKERS.items():
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            price = info.last_price
            prev  = info.previous_close
            if price and prev:
                chg_pct = (price - prev) / prev * 100
                results[name] = {"price": price, "chg_pct": chg_pct}
        except Exception:
            pass
    return results


def format_message(data):
    today = datetime.now().strftime("%m/%d")
    sign  = lambda v: "+" if v >= 0 else ""
    line  = lambda n, d: f"・{n}: ${d['price']:,.0f} ({sign(d['chg_pct'])}{d['chg_pct']:.2f}%)"

    lines = [f"📊 글로벌마켓 {today} 09:30\n"]

    stock_names = ["S&P500", "나스닥", "NVDA", "AAPL", "TSLA"]
    stock_lines = [line(n, data[n]) for n in stock_names if data.get(n)]
    if stock_lines:
        ups = sum(1 for n in stock_names if data.get(n) and data[n]["chg_pct"] >= 0)
        lines.append("📈 미국증시" if ups >= 3 else "📉 미국증시")
        lines.extend(stock_lines)

    lines.append("")

    crypto_names = ["BTC", "ETH"]
    crypto_lines = [line(n, data[n]) for n in crypto_names if data.get(n)]
    if crypto_lines:
        btc = data.get("BTC")
        lines.append("📈 코인" if btc and btc["chg_pct"] >= 0 else "📉 코인")
        lines.extend(crypto_lines)

    lines.append("\n⚠️ 투자는 본인 책임!")

    msg = "\n".join(lines)
    return msg[:197] + "..." if len(msg) > 200 else msg


def send_kakao(message: str):
    if not ACCESS_TOKEN:
        print("❌ KAKAO_ACCESS_TOKEN이 설정되지 않았습니다.")
        return
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    template = {
        "object_type": "text",
        "text": message,
        "link": {"web_url": "", "mobile_web_url": ""},
    }
    resp = requests.post(url, headers=headers, data={"template_object": json.dumps(template)})
    if resp.status_code == 200:
        print(f"✅ 카카오톡 전송 성공 [{datetime.now()}]")
    else:
        print(f"❌ 전송 실패: {resp.status_code} {resp.text}")


def main():
    print(f"[{datetime.now()}] 시장 데이터 조회 중...")
    data = get_market_data()
    msg  = format_message(data)
    print(f"--- 전송 메시지 ---\n{msg}\n-------------------")
    send_kakao(msg)


if __name__ == "__main__":
    main()
