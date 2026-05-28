#!/usr/bin/env python3
"""
Pre-generate cached horoscope content at 5 AM daily.
Run via cron: 0 5 * * * python3 /home/bill/horoscope_app/pre_generate.py

Generates:
  - 12 zodiac signs (daily)
  - 12 chinese zodiac years (daily)
  - 22 major arcana tarot cards (daily)
  - 7 birthday personality readings (permanent, once)
  - 28 siamsi love readings (permanent, once)
  - 8 yam coin readings (permanent, once)

Uses DeepSeek API for LLM generation.
"""
import json, sys, os, time, random
from datetime import date

# Add project dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cache import (
    init_db, get_daily, set, ZODIAC_SIGNS, CHINESE_YEARS,
    BIRTHDAY_DAYS, MAJOR_ARCANA
)

import openai

# Load API key from .env files (same as app.py)
DEEPSEEK_KEY = ""
for envpath in [os.path.expanduser("~/.hermes/.env"), ".env"]:
    if os.path.exists(envpath):
        with open(envpath) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    DEEPSEEK_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")

# DeepSeek API
client = openai.OpenAI(
    api_key=DEEPSEEK_KEY,
    base_url="https://api.deepseek.com/v1"
)

MODEL = "deepseek-chat"  # cheapest model

def ask_llm(system, prompt):
    """Call DeepSeek API with retries."""
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=800
            )
            return resp.choices[0].message.content
        except Exception as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                print(f"❌ LLM error after 3 retries: {e}")
                return None

# === System prompts (Thai) ===

ZODIAC_SYSTEM = """คุณคือหมอดูผู้เชี่ยวชาญด้านโหราศาสตร์ไทย
เขียนคำทำนายรายวันเป็นภาษาไทย สไตล์เป็นกันเอง อบอุ่น
โครงสร้าง: 
1. ดวงวันนี้โดยรวม (1-2 ประโยค)
2. 💰 การงาน/การเงิน (1-2 ประโยค)
3. 💕 ความรัก (1-2 ประโยค)
4. 🍀 เคล็ดลับเสริมดวง (1 ประโยค)
รวมประมาณ 150-200 คำ"""

CHINESE_SYSTEM = """คุณคือหมอดูผู้เชี่ยวชาญด้านนักษัตรจีน
เขียนคำทำนายรายวันเป็นภาษาไทย สไตล์สบายๆ เข้าถึงง่าย
โครงสร้าง:
1. พลังงานวันนี้ (1 ประโยค)
2. 🤝 การงาน/สังคม (1-2 ประโยค)
3. 💚 ความสัมพันธ์ (1-2 ประโยค)
4. 🎯 สิ่งควรระวัง (1 ประโยค)
รวมประมาณ 150-200 คำ"""

TAROT_SYSTEM = """คุณคือหมอดูไพ่ยิปซีผู้เชี่ยวชาญ
เขียนคำทำนายจากการเปิดไพ่ 1 ใบ เป็นภาษาไทย สไตล์ลึกลับน่าค้นหา
โครงสร้าง:
1. ความหมายของไพ่ที่ปรากฏ (1 ประโยค)
2. 🃏 สิ่งที่ควรรู้วันนี้ (2-3 ประโยค)
3. 🌟 พลังบวกที่เข้ามา (1-2 ประโยค)
4. ⚠️ ข้อควรระวัง (1 ประโยค)
รวมประมาณ 150-200 คำ"""

BIRTHDAY_SYSTEM = """คุณคือหมอดูผู้เชี่ยวชาญด้านวันเกิด 7 วัน
เขียนวิเคราะห์นิสัยคนเกิดแต่ละวันเป็นภาษาไทย สไตล์สนุก อ่านเพลิน
โครงสร้าง:
1. 🌟 ลักษณะเด่น (2 ประโยค)
2. 💪 จุดแข็ง (2 ข้อ)
3. ⚠️ จุดอ่อน (1 ข้อ)
4. 💕 ความรัก (1 ประโยค)
5. 💼 การงานที่เหมาะ (1 ประโยค)
ใช้ emoji และภาษาที่อ่านสนุก"""

SIAMSI_SYSTEM = """คุณคือหมอดูเซียมซีวัดดังในไทย
เขียนคำทำนายเซียมซีเป็นภาษาไทย สไตล์ให้กำลังใจ
โครงสร้าง:
1. ใบเซียมซีหมายเลข X (1 ประโยค)
2. 💕 ด้านความรัก (2-3 ประโยค)
3. 🍀 คำแนะนำ (1 ประโยค)
รวมประมาณ 120-180 คำ"""

YAM_SYSTEM = """คุณคือหมอดูจับยาม 3 เหรียญ
เขียนคำทำนายจากผลการเสี่ยงทายเป็นภาษาไทย สไตล์กระชับ ตรงประเด็น
โครงสร้าง:
1. ผลการเสี่ยงทาย (1 ประโยค)
2. 📖 คำทำนาย (2-3 ประโยค)
3. 🎯 ข้อแนะนำ (1 ประโยค)
รวมประมาณ 120-180 คำ"""


def generate_zodiac():
    """Generate all 12 zodiac signs for today."""
    today = date.today()
    count = 0
    for sign in ZODIAC_SIGNS:
        # Skip if already cached today
        val, _ = get_daily("zodiac", sign)
        if val:
            continue
        
        prompt = f"ทำนายดวงรายวันสำหรับราศี{sign} วันที่ {today.strftime('%d/%m/%Y')}"
        reading = ask_llm(ZODIAC_SYSTEM, prompt)
        if reading:
            set("zodiac", reading, sign, type="daily")
            count += 1
            time.sleep(0.3)  # Rate limit
    
    print(f"♈ Zodiac: {count}/12 generated")
    return count


def generate_chinese():
    """Generate all 12 chinese zodiac for today."""
    today = date.today()
    count = 0
    for year in CHINESE_YEARS:
        val, _ = get_daily("chinese", year)
        if val:
            continue
        
        prompt = f"ทำนายดวงรายวันสำหรับปีนักษัตร {year} วันที่ {today.strftime('%d/%m/%Y')}"
        reading = ask_llm(CHINESE_SYSTEM, prompt)
        if reading:
            set("chinese", reading, year, type="daily")
            count += 1
            time.sleep(0.3)
    
    print(f"🐉 Chinese zodiac: {count}/12 generated")
    return count


def generate_tarot():
    """Generate all 22 major arcana for today."""
    today = date.today()
    count = 0
    for card in MAJOR_ARCANA:
        val, _ = get_daily("tarot", card["key"])
        if val:
            continue
        
        prompt = f"ทำนายดวงจากการเปิดไพ่ {card['name']} ({card['th']})"
        reading = ask_llm(TAROT_SYSTEM, prompt)
        if reading:
            set("tarot", reading, card["key"], type="daily")
            count += 1
            time.sleep(0.3)
    
    print(f"🃏 Tarot: {count}/22 generated")
    return count


def generate_birthday():
    """Generate 7 birthday personality readings (permanent)."""
    count = 0
    for day in BIRTHDAY_DAYS:
        val, _ = get_daily("birthday", day)  # check if exists at all
        if val:
            continue
        
        # Use permanent cache — check without date filter
        from cache import get
        val, _ = get("birthday", day)
        if val:
            continue
        
        prompt = f"วิเคราะห์นิสัยคนเกิดวัน{day}"
        reading = ask_llm(BIRTHDAY_SYSTEM, prompt)
        if reading:
            set("birthday", reading, day, type="permanent")
            count += 1
            time.sleep(0.3)
    
    print(f"👶 Birthday: {count}/7 generated")
    return count


def generate_siamsi():
    """Generate 28 siamsi love readings (permanent)."""
    count = 0
    for num in range(1, 29):
        from cache import get
        val, _ = get("siamsi", str(num))
        if val:
            continue
        
        prompt = f"คำทำนายเซียมซีความรัก ใบที่ {num}"
        reading = ask_llm(SIAMSI_SYSTEM, prompt)
        if reading:
            set("siamsi", reading, str(num), type="permanent")
            count += 1
            time.sleep(0.3)
    
    print(f"🏮 Siamsi: {count}/28 generated")
    return count


def generate_yam():
    """Generate 8 coin flip results (permanent)."""
    from cache import get
    
    coin_results = [
        ("หัว", "หัว", "หัว"),
        ("หัว", "หัว", "ก้อย"),
        ("หัว", "ก้อย", "หัว"),
        ("หัว", "ก้อย", "ก้อย"),
        ("ก้อย", "หัว", "หัว"),
        ("ก้อย", "หัว", "ก้อย"),
        ("ก้อย", "ก้อย", "หัว"),
        ("ก้อย", "ก้อย", "ก้อย"),
    ]
    
    count = 0
    for coins in coin_results:
        key = "".join(c[0] for c in coins)  # "HHH", "HHK", etc.
        val, _ = get("yam", key)
        if val:
            continue
        
        prompt = f"เสี่ยงทายจับยาม 3 เหรียญ ได้ผล: {coins[0]}, {coins[1]}, {coins[2]}"
        reading = ask_llm(YAM_SYSTEM, prompt)
        if reading:
            set("yam", reading, key, type="permanent")
            count += 1
            time.sleep(0.3)
    
    print(f"🎲 Yam: {count}/8 generated")
    return count


def generate_all():
    init_db()
    
    print(f"🔮 Pre-generating horoscope content for {date.today()}...")
    print()
    
    # Phase 1: Daily content (most important)
    n1 = generate_zodiac()
    n2 = generate_chinese()
    n3 = generate_tarot()
    
    # Phase 2: Permanent content (only if missing)
    n4 = generate_birthday()
    n5 = generate_siamsi()
    n6 = generate_yam()
    
    total = n1 + n2 + n3 + n4 + n5 + n6
    print()
    print(f"✅ Done! {total} readings generated/cached.")
    
    from cache import cache_size
    count, size = cache_size()
    print(f"📊 Cache: {count} entries ({size/1024:.1f} KB)")
    
    return total


if __name__ == "__main__":
    generate_all()
