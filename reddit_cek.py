import os
import requests
import feedparser
from datetime import date, timedelta

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GundemBot/1.0)"}

bugun = date.today()
gun_farki = (bugun.weekday() - 2) % 7  # 2 = Çarşamba
hafta_basi = bugun - timedelta(days=gun_farki)
hafta_sonu = hafta_basi + timedelta(days=6)

AYLAR = {1:"ocak",2:"subat",3:"mart",4:"nisan",5:"mayis",6:"haziran",
          7:"temmuz",8:"agustos",9:"eylul",10:"ekim",11:"kasim",12:"aralik"}

def tarih_str(d):
    return f"{d.day}{AYLAR[d.month]}"

hafta_klasoru = os.path.join("mertdmg", f"{tarih_str(hafta_basi)}-{tarih_str(hafta_sonu)}")
reddit_klasoru = os.path.join(hafta_klasoru, "reddit")
os.makedirs(reddit_klasoru, exist_ok=True)

def reddit_rss_cek(subreddit, limit=25):
    postlar = []
    try:
        url = f"https://www.reddit.com/r/{subreddit}/top.rss?t=day"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)

        if feed.bozo and not feed.entries:
            raise ValueError(f"RSS parse hatası: {feed.bozo_exception}")

        for entry in feed.entries[:limit]:
            baslik = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            yazar = entry.get("author", "").strip()
            if yazar.startswith("/u/"):
                yazar = yazar[3:]

            postlar.append({
                "baslik": baslik,
                "url": link,
                "yazar": yazar,
            })

        print(f"  r/{subreddit}: {len(postlar)} post (RSS)")
    except Exception as e:
        print(f"  r/{subreddit} RSS hatası: {e}")
    return postlar

def markdown_olustur(subreddit, postlar):
    bugun_tr = bugun.strftime("%d.%m.%Y")
    icerik = f"# r/{subreddit} Gündem — {bugun_tr}\n\n"
    if postlar:
        for i, p in enumerate(postlar, 1):
            satir = f"{i}. [{p['baslik']}]({p['url']})"
            if p.get("yazar"):
                satir += f" — u/{p['yazar']}"
            icerik += satir + "\n"
    else:
        icerik += "_Veri alınamadı_\n"
    icerik += f"\n---\n_Son güncelleme: {bugun_tr}_\n"
    return icerik

tarih = tarih_str(bugun)
bugun_tr = bugun.strftime("%d.%m.%Y")

print(f"Klasör: {reddit_klasoru}")
print("Reddit RSS verileri çekiliyor...")

turkey_postlar = reddit_rss_cek("Turkey")
dosya = os.path.join(reddit_klasoru, f"turkey_{tarih}.md")
with open(dosya, "w", encoding="utf-8") as f:
    f.write(markdown_olustur("Turkey", turkey_postlar))
print(f"Dosya oluşturuldu: {dosya}")

print("Tamamlandı!")
