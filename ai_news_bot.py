"""
Gemini & Claude Feature News Daily Bot
---------------------------------------
Lấy tin tức về tính năng mới của Google Gemini và Anthropic Claude (48h qua)
từ các nguồn uy tín (cả tiếng Việt và quốc tế), tóm tắt lại bằng tiếng Việt
qua Gemini API, rồi gửi vào Telegram của bạn.

Không dùng Facebook vì:
- Facebook không cho phép bot tự động đăng nhập / cào News Feed cá nhân
  (vi phạm điều khoản dịch vụ, có thể bị khóa tài khoản).
- Graph API chính thức chỉ đọc được nội dung Page/Group bạn quản lý,
  không đọc được News Feed cá nhân.

Cách chạy thử trên máy của bạn:
    pip install -r requirements.txt
    export TELEGRAM_BOT_TOKEN="xxx"
    export TELEGRAM_CHAT_ID="xxx"
    export GEMINI_API_KEY="xxx"   # tùy chọn, để tóm tắt hay hơn
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
# Mỗi mục: (url_feed, da_chuyen_ve_AI)
# - da_chuyen_ve_AI=True  -> feed đã chuyên về AI, chỉ cần lọc từ khóa Gemini/Claude
# - da_chuyen_ve_AI=False -> feed công nghệ nói chung, lọc từ khóa Gemini/Claude
RSS_FEEDS = [
    # Nguồn tiếng Việt
    ("https://genk.vn/rss/ai.rss", True),
    ("https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss", False),
    ("https://tinhte.vn/rss/", False),
    ("https://news.google.com/rss/search?q=Gemini%20OR%20Claude%20AI&hl=vi&gl=VN&ceid=VN:vi", True),
    # Nguồn quốc tế uy tín (sẽ được Gemini dịch và tóm tắt sang tiếng Việt)
    ("https://techcrunch.com/category/artificial-intelligence/feed/", True),
    ("https://venturebeat.com/category/ai/feed/", True),
    ("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", True),
    ("https://news.google.com/rss/search?q=Gemini%20OR%20Claude%20AI%20feature&hl=en-US&gl=US&ceid=US:en", True),
]

# Chỉ lấy tin có nhắc đến Gemini hoặc Claude (các sản phẩm AI liên quan)
TOPIC_KEYWORDS = [
    "gemini", "google ai", "google deepmind", "bard",
    "claude", "anthropic", "sonnet", "opus", "haiku",
]

HOURS_LOOKBACK = 48   # mở rộng lên 48h để có đủ tin (thay vì 24h)
MAX_ITEMS = 20         # lấy nhiều hơn để lọc, tóm tắt sẽ rút gọn còn ~10 tin


def is_topic_related(title, summary):
    text = f"{title} {summary}".lower()
    return any(kw in text for kw in TOPIC_KEYWORDS)


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-2.5-flash"


def fetch_recent_entries():
    """Lấy các bài viết mới trong HOURS_LOOKBACK giờ qua, chỉ giữ tin về Gemini/Claude."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)
    entries = []

    for url, _is_dedicated in RSS_FEEDS:
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

            title = e.get("title", "").strip()
            summary_raw = e.get("summary", "")[:500]

            if not is_topic_related(title, summary_raw):
                continue

            entries.append({
                "title": title,
                "link": e.get("link", "").strip(),
                "summary": summary_raw,
                "source": feed.feed.get("title", url),
                "published": published,
            })

    # Loại bỏ trùng lặp theo link, mới nhất trước, giới hạn số lượng
    seen_links = set()
    unique_entries = []
    for e in sorted(entries, key=lambda x: x["published"], reverse=True):
        if e["link"] in seen_links:
            continue
        seen_links.add(e["link"])
        unique_entries.append(e)

    return unique_entries[:MAX_ITEMS]


def summarize_with_gemini(entries):
    """Dùng Gemini API để tóm tắt thành bản tin ~10 tin bằng tiếng Việt."""
    if not entries:
        return "Hôm nay không có tin mới về Gemini hoặc Claude đáng chú ý."

    raw_text = "\n\n".join(
        f"- {e['title']} ({e['source']})\n  {e['summary']}\n  {e['link']}"
        for e in entries
    )

    if not GEMINI_API_KEY:
        lines = [f"📰 *{e['title']}*\n{e['source']} — {e['link']}" for e in entries]
        return "🗞 Tin về Gemini & Claude hôm nay:\n\n" + "\n\n".join(lines)

    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            headers={"content-type": "application/json"},
            params={"key": GEMINI_API_KEY},
            json={
                "contents": [{
                    "parts": [{
                        "text": (
                            "Bạn là biên tập viên công nghệ. Dưới đây là danh sách tin tức "
                            "thô (có thể bằng tiếng Anh hoặc tiếng Việt) về các tính năng, "
                            "cập nhật của Google Gemini và Anthropic Claude.\n\n"
                            "Hãy viết lại thành một bản tin khoảng 10 mục bằng TIẾNG VIỆT, "
                            "mỗi mục gồm:\n"
                            "1. Tiêu đề ngắn gọn (in đậm bằng *...*)\n"
                            "2. Tóm tắt 1-2 câu về tính năng/thông tin chính\n"
                            "3. Link nguồn ở cuối mỗi mục\n\n"
                            "Nhóm theo Gemini và Claude nếu có thể. Nếu số tin ít hơn 10, "
                            "cứ liệt kê hết những gì có, không cần bịa thêm tin. "
                            "Bỏ qua tin trùng lặp nội dung. Định dạng Markdown đơn giản:\n\n"
                            + raw_text
                        )
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 3000,
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            },
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Không có candidate nào trong phản hồi Gemini")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts).strip()
        return text or "Không tạo được bản tóm tắt."
    except Exception as e:
        print(f"[warn] Lỗi khi gọi Gemini API: {e}")
        lines = [f"📰 *{e['title']}*\n{e['source']} — {e['link']}" for e in entries]
        return "🗞 Tin về Gemini & Claude hôm nay (chưa tóm tắt được):\n\n" + "\n\n".join(lines)


def send_to_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[error] Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID.")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

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
    summary = summarize_with_gemini(entries)
    message = f"✨ *Bản tin Gemini & Claude ngày {today}*\n\n{summary}"
    send_to_telegram(message)
    print("Đã gửi bản tin thành công.")


if __name__ == "__main__":
    main()
