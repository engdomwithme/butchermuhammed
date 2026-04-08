"""
Twitter/X Türkiye Trendleri — trends24.in/turkey/ üzerinden çeker.
Her çalışmada mertdmg/<hafta_klasoru>/twitter_trends_<tarih>.md dosyasını oluşturur.
"""

import os
import time
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

AYLAR = {1:"ocak",2:"subat",3:"mart",4:"nisan",5:"mayis",6:"haziran",
          7:"temmuz",8:"agustos",9:"eylul",10:"ekim",11:"kasim",12:"aralik"}

bugun = date.today()
gun_farki = (bugun.weekday() - 2) % 7  # Çarşamba başlangıcı
hafta_basi = bugun - timedelta(days=gun_farki)
hafta_sonu = hafta_basi + timedelta(days=6)

def tarih_str(d):
    return f"{d.day}{AYLAR[d.month]}"

hafta_klasoru = os.path.join("mertdmg", f"{tarih_str(hafta_basi)}-{tarih_str(hafta_sonu)}")
os.makedirs(hafta_klasoru, exist_ok=True)


def trends24_cek(limit=50):
    """trends24.in/turkey/ sitesinden güncel Twitter trendlerini çeker."""
    url = "https://trends24.in/turkey/"
    trendler = []
    for deneme in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content.decode("utf-8", errors="replace"), "html.parser")

            # Saatlik trend kartları — en güncel kart ilk sırada
            kart = soup.select_one("ol.trend-card__list")
            if kart:
                for li in kart.select("li")[:limit]:
                    a = li.select_one("a")
                    if a:
                        metin = a.get_text(strip=True)
                        # Tweet sayısı varsa al
                        sayi_el = li.select_one("span.tweet-count")
                        sayi = sayi_el.get_text(strip=True) if sayi_el else ""
                        trendler.append({"trend": metin, "sayi": sayi})

            if trendler:
                print(f"  trends24: {len(trendler)} trend")
                return trendler

            # Alternatif: tüm trend-card'lardan birleştir
            kartlar = soup.select("ol.trend-card__list")
            for k in kartlar[:1]:
                for li in k.select("li")[:limit]:
                    a = li.select_one("a")
                    if a:
                        metin = a.get_text(strip=True)
                        sayi_el = li.select_one("span.tweet-count")
                        sayi = sayi_el.get_text(strip=True) if sayi_el else ""
                        trendler.append({"trend": metin, "sayi": sayi})
            if trendler:
                print(f"  trends24 (alt): {len(trendler)} trend")
                return trendler

            print(f"  trends24: boş yanıt (deneme {deneme+1})")
        except Exception as e:
            print(f"  trends24 hata (deneme {deneme+1}): {e}")
        time.sleep(2 ** deneme)

    return []


def markdown_olustur(trendler):
    bugun_tr = bugun.strftime("%d.%m.%Y")
    icerik = f"# Twitter/X Türkiye Trendleri — {bugun_tr}\n\n"
    if trendler:
        for i, t in enumerate(trendler, 1):
            satir = f"{i}. {t['trend']}"
            if t.get("sayi"):
                satir += f" — {t['sayi']}"
            icerik += satir + "\n"
    else:
        icerik += "_Veri alınamadı_\n"
    icerik += f"\n---\n_Kaynak: trends24.in/turkey/ — {bugun_tr}_\n"
    return icerik


print(f"Klasör: {hafta_klasoru}")
print("Twitter trendleri çekiliyor...")

trendler = trends24_cek()

tarih = tarih_str(bugun)
dosya = os.path.join(hafta_klasoru, f"twitter_trends_{tarih}.md")
with open(dosya, "w", encoding="utf-8") as f:
    f.write(markdown_olustur(trendler))

print(f"Dosya oluşturuldu: {dosya}")
print("Tamamlandı!")
