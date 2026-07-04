Bot tin tức AI hàng ngày → Telegram
Mỗi ngày tự động lấy tin AI mới nhất (24h qua) từ các trang tin tiếng Việt
uy tín (GenK, VnExpress, Tinh Tế, Google News tiếng Việt), tóm tắt bằng
Claude, rồi gửi vào Telegram của bạn — hoàn toàn miễn phí, không cần điện
thoại phải mở app hay máy tính phải bật.
Bước 1: Tạo Telegram Bot (2 phút)
Mở Telegram, tìm @BotFather, gõ `/newbot`, đặt tên tùy ý.
BotFather sẽ trả về một token dạng `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`
→ đây là `TELEGRAM_BOT_TOKEN`.
Nhắn bất kỳ tin gì cho bot vừa tạo (để bot "biết" bạn).
Mở trình duyệt vào:
`https://api.telegram.org/bot<TOKEN_CỦA_BẠN>/getUpdates`
Tìm số trong `"chat":{"id": ...}` → đây là `TELEGRAM_CHAT_ID`.
Bước 2: (Tùy chọn) Lấy Anthropic API key
Nếu muốn bản tóm tắt mượt và thông minh hơn (thay vì chỉ liệt kê tin):
Vào https://console.anthropic.com/ → tạo API key → đây là `ANTHROPIC_API_KEY`.
Nếu không có key, bot vẫn chạy bình thường, chỉ là sẽ liệt kê tin gọn
thay vì tóm tắt bằng AI.
Bước 3: Thiết lập chạy tự động mỗi ngày (GitHub Actions — miễn phí)
Tạo một repo GitHub mới (private cũng được), upload toàn bộ các file
trong thư mục này (`ai_news_bot.py`, `requirements.txt`, thư mục `.github/`).
Vào repo → Settings → Secrets and variables → Actions → New repository secret,
thêm 3 secret:
`TELEGRAM_BOT_TOKEN`
`TELEGRAM_CHAT_ID`
`ANTHROPIC_API_KEY` (nếu có)
Xong! Workflow sẽ tự chạy mỗi ngày lúc 7:00 sáng giờ Việt Nam.
Muốn đổi giờ → sửa dòng `cron` trong file
`.github/workflows/daily-ai-news.yml` (giờ tính theo UTC).
Muốn test ngay: vào tab Actions trên GitHub → chọn workflow
"Daily AI News to Telegram" → Run workflow.
Chạy thử trên máy cá nhân (không cần GitHub)
```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="xxx"
export TELEGRAM_CHAT_ID="xxx"
export ANTHROPIC_API_KEY="xxx"   # tùy chọn
python ai_news_bot.py
```
Vì sao không lấy tin trực tiếp từ Facebook?
Facebook không cho phép bot tự động đăng nhập và "cào" News Feed cá nhân
— vi phạm điều khoản dịch vụ và có thể khiến tài khoản bị khóa. API
chính thức của Facebook (Graph API) cũng chỉ đọc được nội dung Page/Group
bạn quản lý, không đọc được News Feed cá nhân của bạn. Vì vậy bot này
lấy tin trực tiếp từ các trang báo công nghệ uy tín — vừa an toàn vừa
ổn định hơn nhiều so với việc scrape Facebook.
Nguồn tin hiện tại
GenK - chuyên mục AI (`genk.vn/rss/ai.rss`) — lấy toàn bộ tin, đã chuyên về AI.
VnExpress Khoa học công nghệ — lọc theo từ khóa AI trước khi đưa vào bản tin.
Tinh Tế — lọc theo từ khóa AI trước khi đưa vào bản tin.
Google News tiếng Việt (tìm "AI trí tuệ nhân tạo") — lấy toàn bộ tin.
Tùy biến
Thêm/bớt nguồn tin: sửa danh sách `RSS_FEEDS` trong `ai_news_bot.py`. Mỗi
mục có dạng `(url, is_dedicated)` — đặt `is_dedicated=True` nếu nguồn đã
chuyên về AI, `False` nếu là nguồn công nghệ nói chung cần lọc từ khóa.
Thêm/bớt từ khóa lọc AI: sửa danh sách `AI_KEYWORDS`.
Đổi số giờ lấy tin: sửa `HOURS_LOOKBACK`.
Đổi số lượng tin tối đa: sửa `MAX_ITEMS`.
