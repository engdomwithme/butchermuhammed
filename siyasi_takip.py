"""
Siyasi takip — Üç kategori:
  1. Parti Liderleri & Sözcüler
  2. Partilerin Resmi Hesapları
  3. Bakanlar Kurulu
Nitter RSS üzerinden çeker. Günlük çalışır.
"""

import os
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta, datetime

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GundemBot/1.0)"}

NITTER_INSTANCES = [
    "nitter.privacydev.net",
    "nitter.poast.org",
    "nitter.lucabased.space",
    "nitter.net",
]

AYLAR = {1:"ocak",2:"subat",3:"mart",4:"nisan",5:"mayis",6:"haziran",
          7:"temmuz",8:"agustos",9:"eylul",10:"ekim",11:"kasim",12:"aralik"}

bugun = date.today()
gun_farki = (bugun.weekday() - 2) % 7
hafta_basi = bugun - timedelta(days=gun_farki)
hafta_sonu = hafta_basi + timedelta(days=6)

def tarih_str(d):
    return f"{d.day}{AYLAR[d.month]}"

hafta_klasoru = os.path.join("mertdmg", f"{tarih_str(hafta_basi)}-{tarih_str(hafta_sonu)}")
siyasi_klasoru = os.path.join(hafta_klasoru, "siyasi")
os.makedirs(siyasi_klasoru, exist_ok=True)

# ── Kategori 1: Parti Liderleri & Sözcüler ───────────────────────────────────

PARTI_LIDERLERI = [
    # CHP
    {"isim": "Özgür Özel",           "unvan": "Genel Başkan",     "parti": "CHP",           "twitter": "eczozgurozel"},
    {"isim": "Ekrem İmamoğlu",       "unvan": "İBB / Tutuklu",   "parti": "CHP",           "twitter": "ekrem_imamoglu"},
    # AKP
    {"isim": "Recep Tayyip Erdoğan", "unvan": "Genel Başkan",     "parti": "AKP",           "twitter": "RTErdogan"},
    {"isim": "Ömer Çelik",           "unvan": "Sözcü",            "parti": "AKP",           "twitter": "omerrcelik"},
    # Yeniden Refah
    {"isim": "Fatih Erbakan",        "unvan": "Genel Başkan",     "parti": "Yeniden Refah", "twitter": "erbakanfatih"},
    {"isim": "Suat Kılıç",           "unvan": "GBY / Sözcü",     "parti": "Yeniden Refah", "twitter": "suatkilic"},
    # DEM Parti
    {"isim": "Tülay Hatimoğulları",  "unvan": "Eş GB",            "parti": "DEM Parti",     "twitter": "TulayHatim"},
    {"isim": "Tuncer Bakırhan",      "unvan": "Eş GB",            "parti": "DEM Parti",     "twitter": "tuncerbakirhan"},
    # MHP
    {"isim": "Devlet Bahçeli",       "unvan": "Genel Başkan",     "parti": "MHP",           "twitter": "dbdevletbahceli"},
    {"isim": "İsmet Büyükataman",    "unvan": "Sözcü",            "parti": "MHP",           "twitter": "buyukataman"},
    # İYİ Parti
    {"isim": "Müsavat Dervişoğlu",   "unvan": "Genel Başkan",     "parti": "İYİ Parti",     "twitter": "MDervisogluTR"},
    {"isim": "Buğra Kavuncu",        "unvan": "Sözcü",            "parti": "İYİ Parti",     "twitter": "SBugraKavuncu"},
    # Zafer
    {"isim": "Ümit Özdağ",           "unvan": "Genel Başkan",     "parti": "Zafer",         "twitter": "umitozdag"},
    {"isim": "Azmi Karamahmutoğlu",  "unvan": "Sözcü",            "parti": "Zafer",         "twitter": "AzmiKaramahmut"},
    # Saadet
    {"isim": "Mahmut Arıkan",        "unvan": "Genel Başkan",     "parti": "Saadet",        "twitter": "mahmutarikansp"},
    {"isim": "Birol Aydın",          "unvan": "Sözcü",            "parti": "Saadet",        "twitter": "birolaydinSP"},
]

# ── Kategori 2: Partilerin Resmi Hesapları ───────────────────────────────────

PARTI_HESAPLARI = [
    {"isim": "CHP",           "unvan": "Resmi Hesap", "parti": "CHP",           "twitter": "herkesicinCHP"},
    {"isim": "AKP",           "unvan": "Resmi Hesap", "parti": "AKP",           "twitter": "Akparti"},
    {"isim": "Yeniden Refah", "unvan": "Resmi Hesap", "parti": "Yeniden Refah", "twitter": "rprefahpartisi"},
    {"isim": "DEM Parti",     "unvan": "Resmi Hesap", "parti": "DEM Parti",     "twitter": "DEMGenelMerkezi"},
    {"isim": "MHP",           "unvan": "Resmi Hesap", "parti": "MHP",           "twitter": "MHP_Bilgi"},
    {"isim": "İYİ Parti",     "unvan": "Resmi Hesap", "parti": "İYİ Parti",     "twitter": "iyiparti"},
    {"isim": "Zafer",         "unvan": "Resmi Hesap", "parti": "Zafer",         "twitter": "zaferpartisi"},
    {"isim": "Saadet",        "unvan": "Resmi Hesap", "parti": "Saadet",        "twitter": "SaadetPartisi"},
]

# ── Kategori 3: Bakanlar Kurulu ──────────────────────────────────────────────

BAKANLAR = [
    {"isim": "Recep Tayyip Erdoğan",  "unvan": "Cumhurbaşkanı",                   "twitter": "RTErdogan"},
    {"isim": "Cevdet Yılmaz",         "unvan": "Cumhurbaşkanı Yardımcısı",        "twitter": "_cevdetyilmaz"},
    {"isim": "Akın Gürlek",           "unvan": "Adalet Bakanı",                   "twitter": "abakingurlek"},
    {"isim": "Mustafa Çiftçi",        "unvan": "İçişleri Bakanı",                 "twitter": "mustafaciftcitr"},
    {"isim": "Hakan Fidan",           "unvan": "Dışişleri Bakanı",                "twitter": "HakanFidan"},
    {"isim": "Mehmet Şimşek",         "unvan": "Hazine ve Maliye Bakanı",         "twitter": "memetsimsek"},
    {"isim": "Yusuf Tekin",           "unvan": "Millî Eğitim Bakanı",             "twitter": "Yusuf__Tekin"},
    {"isim": "Kemal Memişoğlu",       "unvan": "Sağlık Bakanı",                   "twitter": "drmemisoglu"},
    {"isim": "Abdulkadir Uraloğlu",   "unvan": "Ulaştırma Bakanı",                "twitter": "a_uraloglu"},
    {"isim": "Alparslan Bayraktar",   "unvan": "Enerji Bakanı",                   "twitter": "aBayraktar1"},
    {"isim": "İbrahim Yumaklı",       "unvan": "Tarım ve Orman Bakanı",           "twitter": "ibrahimyumakli"},
    {"isim": "Murat Kurum",           "unvan": "Çevre ve Şehircilik Bakanı",      "twitter": "murat_kurum"},
    {"isim": "Mehmet Nuri Ersoy",     "unvan": "Kültür ve Turizm Bakanı",         "twitter": "MehmetNuriErsoy"},
    {"isim": "Osman Aşkın Bak",       "unvan": "Gençlik ve Spor Bakanı",          "twitter": "OA_BAK"},
    {"isim": "Mahinur Özdemir Göktaş","unvan": "Aile ve Sosyal Hizmetler Bakanı", "twitter": "MahinurOzdemir"},
    {"isim": "Vedat Işıkhan",         "unvan": "Çalışma Bakanı",                  "twitter": "isikhanvedat"},
    {"isim": "Mehmet Fatih Kacır",    "unvan": "Sanayi ve Teknoloji Bakanı",      "twitter": "mfatihkacir"},
    {"isim": "Ömer Bolat",            "unvan": "Ticaret Bakanı",                  "twitter": "omerbolatTR"},
    {"isim": "Yaşar Güler",           "unvan": "Millî Savunma Bakanı",            "twitter": "YasarGulermsb"},
]

# ── Nitter RSS çekme ─────────────────────────────────────────────────────────

def nitter_rss_cek(twitter_handle, limit=5):
    for instance in NITTER_INSTANCES:
        url = f"https://{instance}/{twitter_handle}/rss"
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            tweetler = []
            for item in root.iter("item"):
                baslik = item.findtext("title", "").strip()
                link   = item.findtext("link", "").strip()
                tarih_raw = item.findtext("pubDate", "").strip()
                try:
                    dt = datetime.strptime(tarih_raw, "%a, %d %b %Y %H:%M:%S %z")
                    tarih_fmt = dt.strftime("%d.%m.%Y %H:%M")
                except Exception:
                    tarih_fmt = tarih_raw[:16] if tarih_raw else ""
                if baslik and "R to @" not in baslik:
                    tweetler.append({"metin": baslik, "link": link, "tarih": tarih_fmt})
                if len(tweetler) >= limit:
                    break
            if tweetler:
                return tweetler, instance
        except Exception:
            pass
    return [], None


def _cek(kisi):
    tweetler, instance = nitter_rss_cek(kisi["twitter"])
    return kisi, tweetler, instance


# ── Paralel çekme ─────────────────────────────────────────────────────────────

def paralel_cek(liste, etiket):
    print(f"\n{etiket} ({len(liste)} hesap) çekiliyor...")
    sonuclar_dict = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_cek, kisi): kisi for kisi in liste}
        for future in as_completed(futures):
            kisi, tweetler, instance = future.result()
            sonuclar_dict[kisi["twitter"]] = (kisi, tweetler, instance)
            durum = f"✓ [{instance}]" if tweetler else "✗"
            print(f"  {durum} @{kisi['twitter']} — {kisi['isim']}")
    return [sonuclar_dict[k["twitter"]] for k in liste]


# ── Markdown bölümü ──────────────────────────────────────────────────────────

def bolum_yaz(baslik, sonuclar, grup_alani=None):
    icerik = f"## {baslik}\n\n"
    if grup_alani:
        gruplar = {}
        for kisi, tweetler, instance in sonuclar:
            g = kisi.get(grup_alani, "—")
            gruplar.setdefault(g, []).append((kisi, tweetler, instance))
        for grup, kisiler in gruplar.items():
            icerik += f"### {grup}\n\n"
            for kisi, tweetler, instance in kisiler:
                icerik += f"#### {kisi['isim']} _{kisi['unvan']}_\n\n"
                if tweetler:
                    for t in tweetler:
                        satir = f"- **{t['tarih']}** — {t['metin']}"
                        if t.get("link"):
                            satir += f" [→]({t['link']})"
                        icerik += satir + "\n"
                else:
                    icerik += "_Tweet alınamadı_\n"
                icerik += "\n"
    else:
        for kisi, tweetler, instance in sonuclar:
            icerik += f"### {kisi['isim']} _{kisi['unvan']}_\n\n"
            if tweetler:
                for t in tweetler:
                    satir = f"- **{t['tarih']}** — {t['metin']}"
                    if t.get("link"):
                        satir += f" [→]({t['link']})"
                    icerik += satir + "\n"
            else:
                icerik += "_Tweet alınamadı_\n"
            icerik += "\n"
    return icerik


# ── Ana akış ─────────────────────────────────────────────────────────────────

print(f"Klasör: {siyasi_klasoru}")

sonuc_liderler  = paralel_cek(PARTI_LIDERLERI, "Kategori 1 — Parti Liderleri & Sözcüler")
sonuc_hesaplar  = paralel_cek(PARTI_HESAPLARI, "Kategori 2 — Parti Resmi Hesapları")
sonuc_bakanlar  = paralel_cek(BAKANLAR,        "Kategori 3 — Bakanlar Kurulu")

bugun_tr = bugun.strftime("%d.%m.%Y")
icerik  = f"# Siyasi Takip — {bugun_tr}\n\n"
icerik += bolum_yaz("Parti Liderleri & Sözcüler", sonuc_liderler, grup_alani="parti")
icerik += bolum_yaz("Parti Resmi Hesapları", sonuc_hesaplar, grup_alani="parti")
icerik += bolum_yaz("Bakanlar Kurulu", sonuc_bakanlar)
icerik += f"---\n_Son güncelleme: {bugun_tr}_\n"

tarih = tarih_str(bugun)
dosya = os.path.join(siyasi_klasoru, f"siyasi_{tarih}.md")
with open(dosya, "w", encoding="utf-8") as f:
    f.write(icerik)

print(f"\nDosya oluşturuldu: {dosya}")
print("Tamamlandı!")
