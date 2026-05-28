# 🔮 DuangDee — AI ดูดวงฟรี 8 ศาสตร์

เว็บดูดวง AI ภาษาไทย 8 ฟีเจอร์ ต้นทุน ~฿7/เดือน  
ดูสด: [https://duangdee.onrender.com](https://duangdee.onrender.com)

## ✨ ฟีเจอร์

- 🃏 ไพ่ยิปซี (22 ใบ)
- 🎲 จับยาม (3 เหรียญ)
- ♈ ดูดวง 12 ราศี
- 🐉 ดูดวง 12 นักษัตร
- 📱 วิเคราะห์เบอร์มือถือ
- 💕 ตรวจดวงสมพงษ์
- 🏮 เซียมซีความรัก
- 👶 นิสัยตามวันเกิด

## 🏗️ Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python + Flask + Gunicorn |
| AI | DeepSeek API |
| Cache | SQLite (3-tier: daily/permanent/realtime) |
| Frontend | Vanilla HTML/CSS/JS (dark gold theme) |
| Ads | Google AdSense + Shopee Affiliate |
| Hosting | Render (free tier) |

## 🚀 Deploy

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "🔮 DuangDee v1.0"
git remote add origin https://github.com/YOUR_USER/duangdee.git
git push -u origin main
```

### 2. Deploy to Render

1. [Render.com](https://render.com) → New Web Service
2. Connect GitHub repo
3. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
4. Environment Variables:
   - `DEEPSEEK_API_KEY` = `sk-xxxxxxxx`
5. Deploy → ได้ URL `duangdee.onrender.com` 🎉

### 3. ตั้งค่าโฆษณา

**Google AdSense:**
- สมัครที่ [adsense.google.com](https://adsense.google.com)
- เปลี่ยน `ca-pub-XXXXXXXXXXXXXXXX` ใน `index.html` เป็น publisher ID ของคุณ
- เปลี่ยน `data-ad-slot` เป็น ad unit ID

**Shopee Affiliate:**
- สมัครที่ [affiliate.shopee.co.th](https://affiliate.shopee.co.th)
- เปลี่ยน `https://shope.ee/XXXXXXXXXXXXXXXXX` เป็นลิงก์ affiliate

### 4. Pre-Generate Cache (Cron)

```bash
# Render มี cron job service หรือใช้ UptimeRobot ping:
# https://duangdee.onrender.com/api/stats
# ทุก 5 นาที เพื่อกัน server หลับ

# หรือรัน pre_generate.py เองทุกเที่ยงคืน:
python3 pre_generate.py
```

## 💰 ต้นทุน

| รายการ | ต่อเดือน |
|--------|---------|
| Render hosting | 🆓 ฿0 |
| DeepSeek API | ~฿7 |
| Domain (optional) | ~฿30 |
| **รวม** | **~฿7-37** |

## 📊 รายได้ (ประมาณการ)

| ช่องทาง | CPM/CPA | วิว/เดือน | รายได้/เดือน |
|---------|---------|----------|-------------|
| **Google AdSense** | ฿20-50 CPM | 10,000 | ฿200-500 |
| **Shopee Affiliate** | ฿10-50/sale | 1-2% conv | ฿50-500 |
| **ขายโฆษณาตรง** | ฿500-2,000/เดือน | — | ฿500-2,000 |
| *10,000 วิว* | | | *~฿1,000-3,000* |
| *100,000 วิว* | | | *~฿10,000-30,000* |

## 🔒 Security

- ✅ Rate limiting (Flask-Limiter)
- ✅ Security headers
- ✅ API key server-side only
- ✅ Input validation
- ✅ Error handling
- ✅ No debug mode in production

## 📁 Project Structure

```
horoscope_app/
├── app.py              # Flask + 8 API endpoints
├── cache.py            # SQLite 3-tier cache system
├── pre_generate.py     # Daily content generator (cron)
├── requirements.txt    # Python dependencies
├── Procfile            # Render deployment
├── render.yaml         # Render Blueprint
├── .gitignore
├── cache.db            # Auto-created on first run
└── templates/
    └── index.html      # Full UI + AdSense + SEO
```
