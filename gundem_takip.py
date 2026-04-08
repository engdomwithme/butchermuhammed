import os
import xml.etree.ElementTree as ET
from datetime import date, timedelta
import requests
import cloudscraper

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

# Cloudflare korumalı siteler için scraper
_scraper = cloudscraper.create_scraper()

CLOUDFLARE_SITELER = {"TRT Haber", "NTV", "CNN Türk", "Milliyet"}

# --- Tarih ve klasör hesapla ---
bugun = date.today()

gun_farki = (bugun.weekday() - 2) % 7  # 2 = Çarşamba
hafta_basi = bugun - timedelta(days=gun_farki)
hafta_sonu = hafta_basi + timedelta(days=6)

def tarih_str(d):
    AYLAR = {1:"ocak",2:"subat",3:"mart",4:"nisan",5:"mayis",6:"haziran",
              7:"temmuz",8:"agustos",9:"eylul",10:"ekim",11:"kasim",12:"aralik"}
    return f"{d.day}{AYLAR[d.month]}"

klasor_yolu = os.path.join("mertdmg", f"{tarih_str(hafta_basi)}-{tarih_str(hafta_sonu)}")
os.makedirs(klasor_yolu, exist_ok=True)

dosya_yolu = os.path.join(klasor_yolu, f"gundem_{tarih_str(bugun)}.md")
print(f"Klasör: {klasor_yolu}\nDosya: {dosya_yolu}")

# --- RSS'ten başlık çek ---
def rss_cek(url, site_adi, limit=15):
    basliklar = []
    try:
        if site_adi in CLOUDFLARE_SITELER:
            r = _scraper.get(url, headers=HEADERS, timeout=15)
        else:
            r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        for item in root.iter("item"):
            baslik = item.findtext("title", "").strip()
            if baslik and len(baslik) > 5:
                basliklar.append(baslik)
            if len(basliklar) >= limit:
                break
        print(f"  {site_adi}: {len(basliklar)} haber")
    except Exception as e:
        print(f"  {site_adi} hatası: {e}")
    return basliklar

# --- Mevcut trends bölümünü koru ---
def trends_bolumu_oku():
    if not os.path.exists(dosya_yolu):
        return "## 🔍 Google Türkiye Trendleri\n\n_Henüz güncellenmedi_\n"
    with open(dosya_yolu, encoding="utf-8") as f:
        icerik = f.read()
    # Trends bölümünü bul ve döndür
    baslangic = icerik.find("## 🔍 Google Türkiye Trendleri")
    if baslangic == -1:
        return "## 🔍 Google Türkiye Trendleri\n\n_Henüz güncellenmedi_\n"
    bitis = icerik.find("\n## ", baslangic + 1)
    if bitis == -1:
        return icerik[baslangic:]
    return icerik[baslangic:bitis]

print("Haberler çekiliyor...")
KAYNAKLAR = [
    ("TRT Haber",   "https://www.trthaber.com/sondakika_articles.rss"),
    ("Cumhuriyet",  "https://cumhuriyet.com.tr/rss/3"),
    ("CNN Türk",    "https://www.cnnturk.com/feed/rss/all/news"),
    ("Sabah",       "https://www.sabah.com.tr/rss/anasayfa.xml"),
    ("Hürriyet",    "https://www.hurriyet.com.tr/rss/anasayfa"),
    ("Milliyet",    "https://www.milliyet.com.tr/rss/rssNew/gundemRss.xml"),
    ("Sözcü",       "https://www.sozcu.com.tr/feeds-rss-category-gundem"),
    ("Haberturk",   "https://www.haberturk.com/rss"),
]

tum_haberler = {}
for site, url in KAYNAKLAR:
    tum_haberler[site] = rss_cek(url, site)

# --- Markdown oluştur ---
bugun_tr = bugun.strftime("%d.%m.%Y")
icerik = f"# Gündem Takip — {bugun_tr}\n\n"

icerik += trends_bolumu_oku() + "\n"

for site, haberler in tum_haberler.items():
    icerik += f"\n## 📰 {site}\n\n"
    if haberler:
        for h in haberler:
            icerik += f"- {h}\n"
    else:
        icerik += "_Veri alınamadı_\n"

icerik += f"\n---\n_Son güncelleme: {bugun_tr}_\n"

with open(dosya_yolu, "w", encoding="utf-8") as f:
    f.write(icerik)

print(f"\nDosya oluşturuldu: {dosya_yolu}")
print("Tamamlandı!")
