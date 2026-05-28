#!/usr/bin/env python3
"""
🔮 DuangDee — AI ดูดวงฟรี 8 ฟีเจอร์ (Phase 2 — cached + ads-ready)
"""

import json, os, subprocess, random
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from cache import (
    init_db, get, set, get_daily, track_stats,
    get_stats, cache_size, MAJOR_ARCANA,
    ZODIAC_SIGNS, CHINESE_YEARS, BIRTHDAY_DAYS
)

app = Flask(__name__)

# ── Rate Limiting ────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Rate-limit specifically for LLM-calling endpoints
REALTIME_LIMIT = "5 per minute"  # phone, compatibility — unique inputs, always LLM
CACHED_LIMIT = "30 per minute"   # cached endpoints — cheap after first hit

# Init DB on startup
init_db()

# ── Config ──────────────────────────────────────────
ANTHROPIC_KEY = None
DEEPSEEK_KEY = None

for envpath in [os.path.expanduser("~/.hermes/.env"), ".env"]:
    if os.path.exists(envpath):
        with open(envpath) as f:
            for line in f:
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    ANTHROPIC_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("DEEPSEEK_API_KEY="):
                    DEEPSEEK_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")

# ── LLM Client ───────────────────────────────────
# ── LLM Helper ──────────────────────────────────────
def ask_llm(system_prompt, user_prompt):
    """DeepSeek API call (fast, cheap, Thai-friendly)."""
    if DEEPSEEK_KEY:
        try:
            payload = json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.8
            })
            # Write payload to temp file to avoid arg limit
            tmpfile = "/tmp/_duangdee_llm.json"
            with open(tmpfile, "w") as f:
                f.write(payload)
            
            resp = subprocess.run(["curl", "-s",
                "https://api.deepseek.com/v1/chat/completions",
                "-H", f"Authorization: Bearer {DEEPSEEK_KEY}",
                "-H", "Content-Type: application/json",
                "-d", f"@{tmpfile}"
            ], capture_output=True, text=True, timeout=30)
            
            data = json.loads(resp.stdout)
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"LLM error: {e}")
    return None


# ── API Endpoints ───────────────────────────────────

@app.route("/")
def index():
    return render_template("index_new.html")

@app.route("/classic")
def index_classic():
    return render_template("index.html")


@app.route("/api/tarot", methods=["POST"])
@limiter.limit(CACHED_LIMIT)
def tarot():
    """Pick 1 random tarot card + cached AI reading."""
    card = random.choice(MAJOR_ARCANA)
    track_stats("tarot")

    # Try cache first
    reading, _ = get_daily("tarot", card["key"])
    if reading:
        return jsonify({"card": card, "reading": reading, "cached": True})

    # Fallback: LLM call
    system = """คุณเป็นหมอดูไพ่ยิปซีที่มีชื่อเสียง พูดจาเป็นกันเองแบบคนไทย 
    ตอบด้วยภาษาไทยเท่านั้น แบ่งคำทำนายเป็น: 
    1. ความหมายของไพ่ 2. การงาน/การเรียน 3. การเงิน 4. ความรัก 5. คำแนะนำ"""

    prompt = f"ทำนายดวงด้วยไพ่ยิปซี: {card['th']} ({card['name']})\nความหมายหลัก: {card.get('meaning', '')}\n\nทำนายดวงประจำวันนี้ของผู้ที่เลือกไพ่ใบนี้"

    reading = ask_llm(system, prompt) or f"คุณได้ไพ่ **{card['th']}** ({card['name']})\n\n✨ {card.get('meaning', '')}\n\nวันนี้เป็นวันแห่งโอกาส จงเปิดใจรับสิ่งใหม่ๆ ที่จะเข้ามา!"

    # Cache for rest of day
    set("tarot", reading, card["key"], type="daily")

    return jsonify({"card": card, "reading": reading, "cached": False})


@app.route("/api/yam", methods=["POST"])
@limiter.limit(CACHED_LIMIT)
def yam():
    """3-coin toss → cached AI reading."""
    coins = [random.choice(["หัว", "ก้อย"]) for _ in range(3)]
    key = "".join(c[0] for c in coins)  # "HHH", "HHK", etc.
    track_stats("yam")

    # Try permanent cache
    reading, _ = get("yam", key)
    if reading:
        return jsonify({"coins": coins, "pattern": key, "reading": reading, "cached": True})

    # Fallback: LLM call
    system = """คุณเป็นหมอดูจับยามผู้เชี่ยวชาญ ตอบด้วยภาษาไทย ใช้โทนเป็นกันเอง 
    แบ่งคำทำนายเป็น: ความหมายของยาม, การงาน, การเงิน, ความรัก, คำแนะนำ"""

    prompt = f"ผลการเสี่ยงทายจับยาม 3 เหรียญ: {', '.join(coins)} (เรียงจากซ้ายไปขวา)\nรูปแบบ: {key}\n\nทำนายดวงชะตาจากผลยามนี้"

    reading = ask_llm(system, prompt) or f"🎲 ผลยาม: {' • '.join(coins)}\n\nรูปแบบ **{key}**\n\nวันนี้เป็นวันที่ดีสำหรับการเริ่มต้นสิ่งใหม่ โชคลาภกำลังมาเยือน!"

    set("yam", reading, key, type="permanent")

    return jsonify({"coins": coins, "pattern": key, "reading": reading, "cached": False})


@app.route("/api/phone", methods=["POST"])
@limiter.limit(REALTIME_LIMIT)
def phone():
    """Phone number numerology analysis."""
    number = request.json.get("number", "").strip()
    if not number or len(number) < 9:
        return jsonify({"error": "กรุณากรอกเบอร์โทร 10 หลัก"}), 400
    
    # Simple numerology calculation
    digits = [int(d) for d in number if d.isdigit()]
    total = sum(digits)
    while total > 9:
        total = sum(int(d) for d in str(total))
    
    system = """คุณเป็นผู้เชี่ยวชาญด้าน numerology และการวิเคราะห์เบอร์โทร 
    ตอบด้วยภาษาไทย แบ่งเป็น: ผลรวมตัวเลข, ความหมาย, ผลดี, ข้อควรระวัง, คำแนะนำ"""
    
    prompt = f"เบอร์โทร: {number}\nผลรวมตัวเลข: {total}\n\nวิเคราะห์ดวงจากเบอร์โทรนี้ ตามหลัก numerology"
    
    reading = ask_llm(system, prompt) or f"📱 เบอร์: {number}\n🔢 ผลรวม: **{total}**\n\nเบอร์นี้มีพลังด้านการสื่อสารและการเข้าสังคม เหมาะกับงานที่ต้องพบปะผู้คน!"
    
    return jsonify({"number": number, "sum": total, "reading": reading})


@app.route("/api/compatibility", methods=["POST"])
@limiter.limit(REALTIME_LIMIT)
def compatibility():
    """Love compatibility check."""
    p1 = request.json.get("person1", "")
    p2 = request.json.get("person2", "")
    
    system = """คุณเป็นที่ปรึกษาความรักและผู้เชี่ยวชาญด้านดวงสมพงษ์ 
    ตอบด้วยภาษาไทย แบ่งเป็น: ภาพรวม, จุดแข็ง, จุดที่ต้องปรับ, คำแนะนำ"""
    
    prompt = f"วิเคราะห์ดวงสมพงษ์ระหว่างคู่รัก:\nคนที่ 1: {p1}\nคนที่ 2: {p2}\n\nทำนายความเข้ากันได้และอนาคตความสัมพันธ์"
    
    reading = ask_llm(system, prompt) or f"💕 **{p1}** & **{p2}**\n\nคุณทั้งคู่มีดวงที่ส่งเสริมกัน! เข้ากันได้ดีมาก โดยเฉพาะเรื่องการสื่อสารและการเข้าอกเข้าใจกัน ❤️"
    
    return jsonify({"person1": p1, "person2": p2, "reading": reading})


@app.route("/api/siamsi", methods=["POST"])
@limiter.limit(CACHED_LIMIT)
def siamsi():
    """Love fortune stick — cached permanent."""
    number = random.randint(1, 28)
    track_stats("siamsi")

    # Try permanent cache
    reading, _ = get("siamsi", str(number))
    if reading:
        return jsonify({"number": number, "reading": reading, "cached": True})

    # Fallback
    system = """คุณเป็นหมอดูเซียมซีผู้เชี่ยวชาญด้านความรัก ตอบด้วยภาษาไทย 
    ทำนายเป็นข้อๆ สั้นๆ กระชับ: เนื้อคู่, อุปสรรค, คำแนะนำ, ฤกษ์ดี"""

    prompt = f"ใบเซียมซีหมายเลข {number} (จาก 28 ใบ) เกี่ยวกับความรัก\n\nทำนายความรักจากเซียมซีใบนี้"

    reading = ask_llm(system, prompt) or f"🏮 เซียมซีใบที่ **{number}**\n\n✨ เนื้อคู่ของคุณอยู่ไม่ไกล มองหาคนที่ทำให้คุณยิ้มได้ทุกวัน ความรักกำลังจะเบ่งบานในไม่ช้า!"

    set("siamsi", reading, str(number), type="permanent")

    return jsonify({"number": number, "reading": reading, "cached": False})


@app.route("/api/birthday", methods=["POST"])
@limiter.limit(CACHED_LIMIT)
def birthday():
    """Personality by birthday — cached permanent."""
    day = request.json.get("day", "").strip()

    DAYS_TH = {
        "จันทร์": "Monday", "อังคาร": "Tuesday", "พุธ": "Wednesday",
        "พฤหัสบดี": "Thursday", "ศุกร์": "Friday", "เสาร์": "Saturday", "อาทิตย์": "Sunday"
    }

    if day not in DAYS_TH:
        return jsonify({"error": "กรุณาเลือกวันเกิด"}), 400

    track_stats("birthday")

    # Try permanent cache
    reading, _ = get("birthday", day)
    if reading:
        return jsonify({"day": day, "reading": reading, "cached": True})

    # Fallback
    system = """คุณเป็นนักพยากรณ์ผู้เชี่ยวชาญด้านบุคลิกภาพตามวันเกิด ตอบด้วยภาษาไทย 
    แบ่งเป็น: ลักษณะนิสัย, จุดเด่น, จุดที่ควรพัฒนา, อาชีพที่เหมาะ, คำแนะนำ"""

    prompt = f"วันเกิด: วัน{day} ({DAYS_TH[day]})\n\nวิเคราะห์บุคลิกภาพและนิสัยตามวันเกิด"

    reading = ask_llm(system, prompt) or f"🌟 คนเกิดวัน**{day}**\n\nคุณเป็นคนมีเสน่ห์ พูดจาดี เข้ากับคนง่าย มีความเป็นผู้นำตามธรรมชาติ!"

    set("birthday", reading, day, type="permanent")

    return jsonify({"day": day, "reading": reading, "cached": False})


@app.route("/api/zodiac", methods=["POST"])
@limiter.limit(CACHED_LIMIT)
def zodiac():
    """Daily zodiac reading — cached daily."""
    sign = request.json.get("sign", "").strip()

    if sign not in ZODIAC_SIGNS:
        return jsonify({"error": "กรุณาเลือกราศี"}), 400

    today = datetime.now().strftime("%d/%m/%Y")
    track_stats("zodiac")

    # Try today's cache
    reading, _ = get_daily("zodiac", sign)
    if reading:
        return jsonify({"sign": sign, "date": today, "reading": reading, "cached": True})

    # Fallback
    system = """คุณเป็นนักโหราศาสตร์ผู้เชี่ยวชาญ ตอบด้วยภาษาไทย 
    ทำนายดวงรายวัน แบ่งเป็น: ภาพรวม, การงาน, การเงิน, ความรัก, สุขภาพ, เลขนำโชค, สีมงคล"""

    prompt = f"ดูดวงรายวัน ราศี{sign} วันที่ {today}\n\nทำนายดวงชะตาประจำวันนี้"

    reading = ask_llm(system, prompt) or f"♈ ราศี**{sign}** — {today}\n\n✨ วันนี้เป็นวันที่ดี! มีเกณฑ์ได้รับข่าวดีจากการงาน การเงินราบรื่น มีโชคจากคนใกล้ตัว\n🔢 เลขนำโชค: {random.randint(10,99)}\n🎨 สีมงคล: {'แดง' if random.random()>0.5 else 'เขียว'}"

    set("zodiac", reading, sign, type="daily")

    return jsonify({"sign": sign, "date": today, "reading": reading, "cached": False})


@app.route("/api/chinese", methods=["POST"])
@limiter.limit(CACHED_LIMIT)
def chinese():
    """Chinese zodiac reading — cached daily."""
    years = {
        "ชวด": "หนู", "ฉลู": "วัว", "ขาล": "เสือ", "เถาะ": "กระต่าย",
        "มะโรง": "งูใหญ่", "มะเส็ง": "งูเล็ก", "มะเมีย": "ม้า", "มะแม": "แพะ",
        "วอก": "ลิง", "ระกา": "ไก่", "จอ": "หมา", "กุน": "หมู"
    }

    year = request.json.get("year", "").strip()

    if year not in years:
        return jsonify({"error": "กรุณาเลือกปีนักษัตร"}), 400

    today = datetime.now().strftime("%d/%m/%Y")
    track_stats("chinese")

    # Try today's cache
    reading, _ = get_daily("chinese", year)
    if reading:
        return jsonify({"year": year, "animal": years[year], "date": today, "reading": reading, "cached": True})

    # Fallback
    system = """คุณเป็นนักพยากรณ์ผู้เชี่ยวชาญด้านนักษัตรจีน ตอบด้วยภาษาไทย 
    แบ่งเป็น: ภาพรวม, การงาน, การเงิน, ความรัก, สุขภาพ, เลขนำโชค, ทิศมงคล"""

    prompt = f"ดูดวงนักษัตร ปี{year} ({years[year]}) วันที่ {today}\n\nทำนายดวงชะตาตามปีนักษัตร"

    reading = ask_llm(system, prompt) or f"🐭 ปี**{year}** ({years[year]}) — {today}\n\n✨ ดวงของคุณกำลัง上升! มีเกณฑ์ได้เลื่อนตำแหน่งหรือรับผิดชอบงานใหญ่ เตรียมตัวให้พร้อม!\n🔢 เลขนำโชค: {random.randint(10,99)}\n🧭 ทิศมงคล: {'ทิศเหนือ' if random.random()>0.5 else 'ทิศตะวันออก'}"

    set("chinese", reading, year, type="daily")

    return jsonify({"year": year, "animal": years[year], "date": today, "reading": reading, "cached": False})


# ── Stats API (for analytics/ad targeting) ───────

@app.route("/api/stats")
def stats():
    """Return usage stats and cache info."""
    return jsonify({
        "stats": get_stats(7),
        "cache": {"entries": cache_size()[0], "size_kb": round(cache_size()[1]/1024, 1)}
    })


# ── Security Headers ─────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# ── Error Handlers ───────────────────────────────
@app.errorhandler(429)
def ratelimit_error(e):
    return jsonify({"error": "ขออภัย คุณใช้บริการถี่เกินไป กรุณารอสักครู่แล้วลองใหม่ 🙏", "retry_after": e.description}), 429

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "ระบบขัดข้องชั่วคราว กรุณาลองใหม่ภายหลัง 🔮"}), 500


# ── Main ────────────────────────────────────────────
if __name__ == "__main__":
    print("🔮 DuangDee — AI ดูดวงฟรี 8 ฟีเจอร์")
    print("👉 http://localhost:8898")
    import sys
    # Production: gunicorn app:app (no debug, no app.run)
    # Dev: python app.py
    debug_mode = "--debug" in sys.argv
    app.run(host="0.0.0.0", port=8898, debug=debug_mode)
