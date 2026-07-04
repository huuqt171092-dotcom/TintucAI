"""
AI News Daily Bot
------------------
Lấy tin tức AI mới nhất (24h qua) từ các nguồn RSS uy tín, tóm tắt bằng
Claude API, rồi gửi kết quả vào Telegram của bạn.

Không dùng Facebook vì:
- Facebook không cho phép bot tự động đăng nhập / cào News Feed cá nhân
  (vi phạm điều khoản dịch vụ, có thể bị khóa tài khoản).
- Graph API chính thức chỉ đọc được nội dung Page/Group bạn quản lý,
  không đọc được News Feed cá nhân.

Cách chạy thử trên máy của bạn:
    pip install -r requirements.txt
    export TELEGRAM_BOT_TOKEN="xxx"
    export TELEGRAM_CHAT_ID="xxx"
    export ANTHROPIC_API_KEY="xxx"   # tùy chọn, để tóm tắt hay hơn
    python ai_news_bot.py

Xem README.md để biết cách lấy các giá trị trên và cách cho chạy
tự động mỗi ngày miễn phí bằng GitHub Actions.
"""

import os
import sys
import time
import requests
import feedparser
from datetime import datetime, timedelta, timezone

# ---------- Cấu hình nguồn tin ----------
RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://news.google.com/rss/search?q=AI%20artificial%20intelligence&hl=en-US&gl=US&ceid=US:en",
]

HOURS_LOOKBACK = 24  # chỉ lấy tin trong N giờ gần nhất
MAX_ITEMS = 15        # giới hạn số tin đưa vào tóm tắt

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


def fetch_recent_entries():
    """Lấy các bài viết mới trong HOURS_LOOKBACK giờ qua từ mọi feed."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)
    entries = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[warn] Không đọc được feed {url}: {e}")
            continue

        for e in feed.entries:
            published = None
            for key in ("published_parsed", "updated_parsed"):
                if getattr(e, key, None):
                    published = datetime(*e[key][:6], tzinfo=timezone.utc)
                    break
            if published is None or published < cutoff:
                continue

            entries.append({
                "title": e.get("title", "").strip(),
                "link": e.get("link", "").strip(),
                "summary": e.get("summary", "")[:500],
                "source": feed.feed.get("title", url),
                "published": published,
            })

    # Mới nhất trước, giới hạn số lượng
    entries.sort(key=lambda x: x["published"], reverse=True)
    return entries[:MAX_ITEMS]


def summarize_with_claude(entries):
    """Dùng Claude API để tóm tắt gọn các tin thành bản tin ngắn."""
    if not entries:
        return "Hôm nay không có tin AI mới đáng chú ý."

    raw_text = "\n\n".join(
        f"- {e['title']} ({e['source']})\n  {e['summary']}\n  {e['link']}"
        for e in entries
    )

    if not ANTHROPIC_API_KEY:
        # Không có API key -> chỉ liệt kê gọn, không tóm tắt bằng AI
        lines = [f"📰 *{e['title']}*\n{e['source']} — {e['link']}" for e in entries]
        return "🗞 Tin AI hôm nay:\n\n" + "\n\n".join(lines)

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 800,
                "messages": [{
                    "role": "user",
                    "content": (
                        "Tóm tắt các tin tức AI dưới đây thành một bản tin ngắn "
                        "gọn bằng tiếng Việt, nhóm theo chủ đề, mỗi tin 1-2 câu, "
                        "kèm link nguồn. Định dạng Markdown đơn giản (dùng * cho in đậm):\n\n"
                        + raw_text
                    ),
                }],
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return "".join(
            block.get("text", "") for block in data.get("content", [])
            if block.get("type") == "text"
        ).strip() or "Không tạo được bản tóm tắt."
    except Exception as e:
        print(f"[warn] Lỗi khi gọi Claude API: {e}")
        lines = [f"📰 *{e['title']}*\n{e['source']} — {e['link']}" for e in entries]
        return "🗞 Tin AI hôm nay (chưa tóm tắt được):\n\n" + "\n\n".join(lines)


def send_to_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[error] Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID.")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Telegram giới hạn ~4096 ký tự/tin nhắn -> chia nhỏ nếu cần
    chunks = [text[i:i + 3500] for i in range(0, len(text), 3500)] or [text]

    for chunk in chunks:
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        })
        if r.status_code != 200:
            print(f"[error] Gửi Telegram thất bại: {r.status_code} {r.text}")
        time.sleep(1)


def main():
    today = datetime.now().strftime("%d/%m/%Y")
    entries = fetch_recent_entries()
    summary = summarize_with_claude(entries)
    message = f"🤖 *Bản tin AI ngày {today}*\n\n{summary}"
    send_to_telegram(message)
    print("Đã gửi bản tin thành công.")


if __name__ == "__main__":
    main()
