# Bot tin tức Gemini & Claude hàng ngày → Telegram

Mỗi ngày tự động lấy tin về tính năng mới của **Google Gemini** và
**Anthropic Claude** (48h qua) từ các nguồn tiếng Việt và quốc tế uy tín,
tóm tắt lại bằng tiếng Việt qua Gemini API, rồi gửi vào Telegram của bạn —
hoàn toàn miễn phí, không cần điện thoại phải mở app hay máy tính phải bật.

## Bước 1: Tạo Telegram Bot (2 phút)

1. Mở Telegram, tìm **@BotFather**, gõ `/newbot`, đặt tên tùy ý.
2. BotFather sẽ trả về một **token** dạng `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`
   → đây là `TELEGRAM_BOT_TOKEN`.
3. Nhắn bất kỳ tin gì cho bot vừa tạo (để bot "biết" bạn).
4. Mở trình duyệt vào:
   `https://api.telegram.org/bot<TOKEN_CỦA_BẠN>/getUpdates`
   Tìm số trong `"chat":{"id": ...}` → đây là `TELEGRAM_CHAT_ID`.

## Bước 2: (Tùy chọn) Lấy Gemini API key

Để bản tóm tắt mượt và thông minh hơn (thay vì chỉ liệt kê tin):
1. Vào https://aistudio.google.com/apikey
2. Đăng nhập bằng tài khoản Google, bấm **Create API key**.
3. Copy key hiện ra (dạng `AIzaSy...`) → đây là `GEMINI_API_KEY`.
4. Gemini API có gói miễn phí (giới hạn số lượt gọi/ngày) — dùng 1 lần/ngày
   cho bot này là thoải mái nằm trong hạn mức miễn phí.

Nếu không có key, bot vẫn chạy bình thường, chỉ là sẽ liệt kê tin gọn
thay vì tóm tắt bằng AI.

## Bước 3: Thêm Secrets vào GitHub

1. Vào repo của bạn → **Settings → Secrets and variables → Actions**.
2. Bấm **New repository secret**, thêm lần lượt:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `GEMINI_API_KEY` (nếu có)

## Bước 4: Thiết lập chạy tự động mỗi ngày (GitHub Actions — miễn phí)

1. Upload các file: `ai_news_bot.py`, `requirements.txt`, và thư mục
   `.github/workflows/daily-ai-news.yml` lên repo.
2. Workflow sẽ tự chạy mỗi ngày lúc 7:00 sáng giờ Việt Nam.
   Muốn đổi giờ → sửa dòng `cron` trong file
   `.github/workflows/daily-ai-news.yml` (giờ tính theo UTC).
3. Muốn test ngay: vào tab **Actions** trên GitHub → chọn workflow
   "Daily Gemini News to Telegram" → **Run workflow**.

## Chạy thử trên máy cá nhân (không cần GitHub)

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="xxx"
export TELEGRAM_CHAT_ID="xxx"
export GEMINI_API_KEY="xxx"   # tùy chọn
python ai_news_bot.py
```

## Vì sao không lấy tin trực tiếp từ Facebook?

Facebook không cho phép bot tự động đăng nhập và "cào" News Feed cá nhân
— vi phạm điều khoản dịch vụ và có thể khiến tài khoản bị khóa. API
chính thức của Facebook (Graph API) cũng chỉ đọc được nội dung Page/Group
bạn quản lý, không đọc được News Feed cá nhân của bạn. Vì vậy bot này
lấy tin trực tiếp từ các trang báo công nghệ uy tín — vừa an toàn vừa
ổn định hơn nhiều so với việc scrape Facebook.

## Nguồn tin hiện tại

Nguồn tiếng Việt:
- **GenK - chuyên mục AI** (`genk.vn/rss/ai.rss`)
- **VnExpress Khoa học công nghệ**
- **Tinh Tế**
- **Google News tiếng Việt** (tìm "Gemini OR Claude AI")

Nguồn quốc tế (được Gemini dịch và tóm tắt sang tiếng Việt):
- **TechCrunch** (chuyên mục AI)
- **VentureBeat** (chuyên mục AI)
- **The Verge** (chuyên mục AI)
- **Google News tiếng Anh** (tìm "Gemini OR Claude AI feature")

Tất cả các nguồn trên đều được lọc lại theo từ khóa liên quan đến Gemini
và Claude (`TOPIC_KEYWORDS` trong code) để chỉ giữ tin thực sự liên quan.

## Tùy biến

- Thêm/bớt nguồn tin: sửa danh sách `RSS_FEEDS` trong `ai_news_bot.py`.
- Thêm/bớt từ khóa lọc: sửa danh sách `TOPIC_KEYWORDS` (ví dụ thêm "veo",
  "imagen", "notebooklm" nếu muốn bắt luôn tin về các sản phẩm liên quan).
- Đổi số giờ lấy tin: sửa `HOURS_LOOKBACK` (mặc định 48 giờ).
- Đổi số lượng tin tối đa: sửa `MAX_ITEMS`.
- Đổi model Gemini dùng để tóm tắt: sửa `GEMINI_MODEL` (mặc định
  `gemini-2.5-flash`, nhanh và miễn phí trong hạn mức).
