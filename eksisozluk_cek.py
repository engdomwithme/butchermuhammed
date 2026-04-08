import os
import cloudscraper
from bs4 import BeautifulSoup
from datetime import date, timedelta

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

bugun = date.today()
gun_farki = (bugun.weekday() - 2) % 7  # 2 = Çarşamba
hafta_basi = bugun - timedelta(days=gun_farki)
hafta_sonu = hafta_basi + timedelta(days=6)

AYLAR = {1:"ocak",2:"subat",3:"mart",4:"nisan",5:"mayis",6:"haziran",
          7:"temmuz",8:"agustos",9:"eylul",10:"ekim",11:"kasim",12:"aralik"}

def tarih_str(d):
    return f"{d.day}{AYLAR[d.month]}"

hafta_klasoru = os.path.join("mertdmg", f"{tarih_str(hafta_basi)}-{tarih_str(hafta_sonu)}")
klasor_yolu = os.path.join(hafta_klasoru, "eksisozluk")
os.makedirs(klasor_yolu, exist_ok=True)

dosya_yolu = os.path.join(klasor_yolu, f"eksisozluk_{tarih_str(bugun)}.md")
print(f"Klasör: {klasor_yolu}\nDosya: {dosya_yolu}")

scraper = cloudscraper.create_scraper()

def eksisozluk_gundem_cek():
    basliklar = []
    try:
        r = scraper.get("https://eksisozluk.com/?tab=gündem", headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.select("ul.topic-list li a"):
            metin = item.get_text(strip=True)
            if metin:
                basliklar.append(metin)
        print(f"  Ekşi Sözlük: {len(basliklar)} başlık")
    except Exception as e:
        print(f"  Ekşi Sözlük hatası: {e}")
    return basliklar

print("Ekşi Sözlük gündem çekiliyor...")
basliklar = eksisozluk_gundem_cek()

bugun_tr = bugun.strftime("%d.%m.%Y")
icerik = f"# Ekşi Sözlük Gündem — {bugun_tr}\n\n"

if basliklar:
    for i, b in enumerate(basliklar, 1):
        icerik += f"{i}. {b}\n"
else:
    icerik += "_Veri alınamadı_\n"

icerik += f"\n---\n_Son güncelleme: {bugun_tr}_\n"

with open(dosya_yolu, "w", encoding="utf-8") as f:
    f.write(icerik)

print(f"\nDosya oluşturuldu: {dosya_yolu}")
print("Tamamlandı!")
