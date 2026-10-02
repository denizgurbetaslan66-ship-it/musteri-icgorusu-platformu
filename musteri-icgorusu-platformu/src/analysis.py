"""Veri yükleme, metin normalleştirme, kategorizasyon ve raporlama fonksiyonları.

Bu modül Streamlit'ten bağımsızdır; bu sayede birim testleri kolayca yazılabilir.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "e-ticaret_yorumlari_temizlenmis.xlsx"

TEXT_COL = "yorumlar"
LABEL_COL = "duygu"
GENERAL = "Genel Memnuniyet"

SENTIMENT_ORDER = ["Pozitif", "Negatif", "Nötr"]
SENTIMENT_COLORS = {"Pozitif": "#22c55e", "Negatif": "#ef4444", "Nötr": "#94a3b8"}
_SENTIMENT_MAP = {"pozitif": "Pozitif", "negatif": "Negatif", "notr": "Nötr"}

# Anahtar kelimeler normalleştirilmiş (küçük harf, aksansız) biçimdedir.
# Eşleşme kelime BAŞINDA yapılır (ör. "gecik" -> gecikti, gecikme, geciktirdi).
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Teslimat ve Kargo": [
        "kargo", "gecik", "teslim", "kurye", "ulas", "paket", "dagitim", "gonderi",
    ],
    "Fiyat ve Ücret": [
        "pahali", "ucuz", "indirim", "fiyat", "kampanya", "ucret", "para", "butce", "kupon",
    ],
    "Ürün Kalitesi": [
        "kalite", "bozuk", "bozul", "kirik", "sahte", "defolu", "calismiyor", "calismad",
        "ariza", "yirtik", "kopt", "sorunlu", "hasarli", "dikis",
    ],
    "Müşteri Hizmetleri": [
        "iade", "musteri hizmet", "muhatap", "degisim", "ilgilen", "ilgisiz", "destek",
        "iletisim", "satici", "cevap",
    ],
}
_PATTERNS = {
    cat: r"\b(?:" + "|".join(re.escape(k) for k in kws) + ")"
    for cat, kws in CATEGORY_KEYWORDS.items()
}
CATEGORIES = [*CATEGORY_KEYWORDS, GENERAL]

RECOMMENDATIONS = {
    "Teslimat ve Kargo": "Kargo firması SLA'larını gözden geçirin; gecikme bildirimi ve kargo takip deneyimini iyileştirin.",
    "Fiyat ve Ücret": "Fiyat algısını ve kampanya iletişimini inceleyin; rakip fiyat analizi ve kupon stratejisi değerlendirin.",
    "Ürün Kalitesi": "Tedarikçi kalite kontrolünü, defolu ürün oranını ve ürün açıklamasının gerçeğe uygunluğunu denetleyin.",
    "Müşteri Hizmetleri": "İade/değişim sürecini sadeleştirin, ilk yanıt süresini kısaltın ve destek ekibi eğitimlerini gözden geçirin.",
    GENERAL: "Genel deneyimi izlemeye devam edin; beden/ölçü rehberi ve ürün sayfası iyileştirmelerini değerlendirin.",
}

STOPWORDS = {
    "bir", "ile", "icin", "ama", "cok", "daha", "gibi", "olan", "olarak", "kadar", "sonra",
    "her", "bile", "ise", "biraz", "bunu", "bana", "beni", "bence", "sadece", "fakat", "hem",
    "veya", "sey", "ben", "sen", "ancak", "hic", "urun", "urunu", "urunun", "den", "dan",
    "bunun", "ondan", "sana", "oldu", "olmus", "olur", "var", "gore",
}
_TOKEN = re.compile(r"[a-z]{3,}")


def normalize_text(text) -> str:
    """Türkçe uyumlu normalleştirme: küçük harf, aksansız, tek boşluk.

    'İADE' -> 'iade', 'ulaşmadı' -> 'ulasmadi', 'i̇ade' (birleşik nokta) -> 'iade'.
    Python'un ``str.lower()`` fonksiyonu 'İ' harfini 'i̇' yaptığı için özel işlenir.
    """
    if text is None or (not isinstance(text, str) and pd.isna(text)):
        return ""
    s = str(text).replace("İ", "i").replace("I", "ı").lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).replace("ı", "i")
    return re.sub(r"\s+", " ", s).strip()


def categorize(norm: pd.Series) -> pd.Series:
    """Normalleştirilmiş yorumları anahtar kelime isabet sayısına göre kategorilere ayırır.

    En çok isabet alan kategori seçilir; eşitlikte CATEGORY_KEYWORDS sırası belirleyicidir.
    Hiç isabet yoksa 'Genel Memnuniyet' atanır.
    """
    counts = pd.DataFrame({c: norm.str.count(p) for c, p in _PATTERNS.items()}, index=norm.index)
    best = counts.idxmax(axis=1)
    return best.where(counts.max(axis=1) > 0, GENERAL)


def load_data(path: str | Path = DATA_PATH, drop_duplicates: bool = False) -> pd.DataFrame:
    """Yorum veri setini okur, temizler ve zenginleştirir."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Veri dosyası bulunamadı: {path}")
    raw = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)
    missing = {TEXT_COL, LABEL_COL} - set(raw.columns)
    if missing:
        raise ValueError(f"Veri setinde beklenen sütunlar yok: {sorted(missing)}")

    df = raw[[TEXT_COL, LABEL_COL]].dropna().copy()
    df["Yorum"] = df[TEXT_COL].astype(str).str.strip()
    df = df[df["Yorum"] != ""]
    df["Duygu"] = df[LABEL_COL].map(lambda v: _SENTIMENT_MAP.get(normalize_text(v)))
    df = df.dropna(subset=["Duygu"])
    if drop_duplicates:
        df = df.drop_duplicates(subset=["Yorum", "Duygu"])
    df["_norm"] = df["Yorum"].map(normalize_text)
    df["Kategori"] = categorize(df["_norm"])
    df["Kelime Sayısı"] = df["_norm"].str.split().str.len().astype(int)
    return df[["Yorum", "Duygu", "Kategori", "Kelime Sayısı", "_norm"]].reset_index(drop=True)


def build_word_counters(df: pd.DataFrame) -> dict[tuple[str, str], Counter]:
    """(duygu, kategori) çiftleri için kelime frekanslarını hesaplar."""
    out: dict[tuple[str, str], Counter] = {}
    for key, grp in df.groupby(["Duygu", "Kategori"]):
        c: Counter = Counter()
        for text in grp["_norm"]:
            c.update(w for w in _TOKEN.findall(text) if w not in STOPWORDS)
        out[key] = c
    return out


def top_words(counters, sentiment: str, categories: list[str], n: int = 20) -> pd.DataFrame:
    total: Counter = Counter()
    for (s, k), c in counters.items():
        if s == sentiment and k in categories:
            total.update(c)
    return pd.DataFrame(total.most_common(n), columns=["Kelime", "Adet"])


def sentiment_kpis(df: pd.DataFrame) -> dict:
    n = len(df)
    counts = df["Duygu"].value_counts()
    pos, neg, neu = (int(counts.get(s, 0)) for s in SENTIMENT_ORDER)
    pct = lambda x: round(100 * x / n, 1) if n else 0.0  # noqa: E731
    return {
        "toplam": n, "pozitif": pos, "negatif": neg, "notr": neu,
        "pozitif_oran": pct(pos), "negatif_oran": pct(neg), "notr_oran": pct(neu),
        "net_skor": round(pct(pos) - pct(neg), 1),
        "ort_kelime": round(float(df["Kelime Sayısı"].mean()), 1) if n else 0.0,
    }


def risk_level(rate: float, overall_rate: float) -> str:
    """Kategori negatif oranını genel negatif orana göre Yüksek/Orta/Düşük olarak etiketler."""
    if overall_rate <= 0:
        return "Düşük"
    ratio = rate / overall_rate
    return "Yüksek" if ratio >= 1.5 else "Orta" if ratio >= 1.0 else "Düşük"


def category_report(df: pd.DataFrame) -> pd.DataFrame:
    """Kategori bazında yönetici raporu tablosu (negatif şikayet önceliğine göre sıralı)."""
    cols = ["Kategori", "Toplam", "Negatif", "Pozitif", "Nötr", "Negatif Oran (%)", "Negatif Payı (%)", "Risk"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    ct = pd.crosstab(df["Kategori"], df["Duygu"]).reindex(columns=SENTIMENT_ORDER, fill_value=0)
    ct["Toplam"] = ct.sum(axis=1)
    total_neg = ct["Negatif"].sum()
    overall = 100 * total_neg / ct["Toplam"].sum()
    ct["Negatif Oran (%)"] = (100 * ct["Negatif"] / ct["Toplam"]).round(1)
    ct["Negatif Payı (%)"] = (100 * ct["Negatif"] / total_neg).round(1) if total_neg else 0.0
    ct["Risk"] = ct["Negatif Oran (%)"].map(lambda r: risk_level(r, overall))
    return ct.reset_index().sort_values("Negatif", ascending=False)[cols].reset_index(drop=True)


def executive_summary(df: pd.DataFrame, top: int = 3) -> str:
    """Seçili veri için Markdown biçiminde yönetici özeti üretir."""
    k = sentiment_kpis(df)
    rep = category_report(df)
    lines = [
        "# Müşteri İçgörüsü Yönetici Özeti", "",
        f"- **Toplam yorum:** {k['toplam']:,}".replace(",", "."),
        f"- **Pozitif:** %{k['pozitif_oran']} · **Negatif:** %{k['negatif_oran']} · **Nötr:** %{k['notr_oran']}",
        f"- **Net duygu skoru:** {k['net_skor']:+}", "", "## Öncelikli Sorun Alanları", "",
    ]
    for i, r in rep.head(top).iterrows():
        if r["Negatif"] == 0:
            continue
        lines += [
            f"{i + 1}. **{r['Kategori']}** — {r['Negatif']} olumsuz yorum "
            f"(kategori içi %{r['Negatif Oran (%)']}, toplam şikayetlerin %{r['Negatif Payı (%)']}'i), risk: {r['Risk']}",
            f"   - Öneri: {RECOMMENDATIONS[r['Kategori']]}",
        ]
    return "\n".join(lines) + "\n"
