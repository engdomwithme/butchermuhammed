#!/usr/bin/env python3
"""Google Trends verisi çeken script — pytrends kullanır"""

from pytrends.request import TrendReq
from datetime import datetime
import os
import re

ay_tr = {1:'ocak',2:'subat',3:'mart',4:'nisan',5:'mayis',6:'haziran',
         7:'temmuz',8:'agustos',9:'eylul',10:'ekim',11:'kasim',12:'aralik'}

ay_no = {v: k for k, v in ay_tr.items()}

bugun = datetime.now()
tarih_str = f"{bugun.day}{ay_tr[bugun.month]}"

mertdmg_path = "mertdmg"

def parse_folder_date(folder_name):
    """Klasör adından başlangıç tarihini parse eder (örn. '18mart-24mart' -> date(2026,3,18))"""
    m = re.match(r'(\d+)([a-z]+)', folder_name)
    if not m:
        return None
    try:
        gun = int(m.group(1))
        ay = ay_no.get(m.group(2))
        if ay is None:
            return None
        yil = bugun.year
        from datetime import date
        return date(yil, ay, gun)
    except (ValueError, KeyError):
        return None

# Aktif haftayı bul: tarih aralığına göre eşleşen klasörü seç
folders = [f for f in os.listdir(mertdmg_path)
           if os.path.isdir(os.path.join(mertdmg_path, f))
           and re.match(r'\d+[a-z]+-\d+[a-z]+', f)]

bugun_date = bugun.date()
active_folder = None

# Tarih aralığı içinde olan klasörü bul
for folder in folders:
    parts = folder.split('-', 1)
    if len(parts) != 2:
        continue
    start = parse_folder_date(parts[0])
    end = parse_folder_date(parts[1])
    if start and end:
        # Ay geçişi varsa end yılını bir artır gerekirse
        if end < start:
            from datetime import date
            end = date(end.year + (1 if end.month < start.month else 0), end.month, end.day)
        if start <= bugun_date <= end:
            active_folder = folder
            break

# Bulunamazsa en son tarihli klasörü seç (fallback)
if not active_folder:
    dated_folders = [(parse_folder_date(f.split('-')[0]), f) for f in folders]
    dated_folders = [(d, f) for d, f in dated_folders if d is not None]
    if dated_folders:
        active_folder = sorted(dated_folders, reverse=True)[0][1]

if not active_folder:
    print(f"HATA: {tarih_str} için aktif klasör bulunamadı. Mevcut klasörler: {folders}")
    exit(1)

print(f"Aktif klasör: {active_folder}")
output_path = f"{mertdmg_path}/{active_folder}/trends/trends_{tarih_str}.md"

# Zaten varsa atla
if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
    print(f"Zaten mevcut: {output_path}, atlanıyor.")
    exit(0)

pytrends = TrendReq(hl='tr-TR', tz=-180, timeout=(10, 25), retries=3, backoff_factor=0.5)

# Gerçek zamanlı trending aramaları çek (TR)
trending_df = pytrends.realtime_trending_searches(pn='TR')

md_lines = [
    f"# Google Trends — {bugun.day} {ay_tr[bugun.month].capitalize()} {bugun.year}",
    f"",
    f"*Kaynak: Google Trends (pytrends realtime) | {bugun.strftime('%Y-%m-%d %H:%M')} UTC*",
    f"",
    f"## Günün Trend Aramaları",
    f""
]

# Başlık sütununu bul
title_col = 'title' if 'title' in trending_df.columns else trending_df.columns[0]
for i, term in enumerate(trending_df[title_col].tolist()[:50], 1):
    md_lines.append(f"{i}. {term}")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

print(f"✅ {len(trending_df)} trend yazıldı: {output_path}")
