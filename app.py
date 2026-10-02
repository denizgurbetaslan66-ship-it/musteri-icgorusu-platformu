"""AI Destekli Müşteri İçgörüsü & Ses Analiz Platformu (Streamlit arayüzü)."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analysis import (
    CATEGORIES, DATA_PATH, RECOMMENDATIONS, SENTIMENT_COLORS, SENTIMENT_ORDER,
    build_word_counters, category_report, executive_summary, load_data,
    normalize_text, sentiment_kpis, top_words,
)

st.set_page_config(
    page_title="Müşteri İçgörüsü Platformu", page_icon="📊", layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1400px;}
.hero {padding: 1.6rem 1.8rem; border-radius: 18px; margin-bottom: 1.2rem;
  background: linear-gradient(120deg, #1e1b4b 0%, #312e81 45%, #0e7490 100%);}
.hero h1 {margin: 0; font-size: 1.9rem; color: #fff;}
.hero p {margin: .4rem 0 0; color: #c7d2fe; font-size: 1rem;}
.kpi {background: #161b2e; border: 1px solid #263052; border-radius: 14px; padding: 1rem 1.2rem;}
.kpi .l {color: #94a3b8; font-size: .8rem; text-transform: uppercase; letter-spacing: .06em;}
.kpi .v {font-size: 1.9rem; font-weight: 700; color: #f1f5f9; line-height: 1.3;}
.kpi .s {color: #64748b; font-size: .8rem;}
.issue {background: #161b2e; border: 1px solid #263052; border-left: 5px solid var(--c);
  border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: .8rem;}
.issue .t {font-weight: 700; color: #f1f5f9; font-size: 1.05rem;}
.issue .m {color: #94a3b8; font-size: .9rem; margin: .2rem 0 .5rem;}
.issue .a {color: #cbd5e1; font-size: .92rem;}
.badge {display: inline-block; padding: .1rem .6rem; border-radius: 999px; font-size: .75rem;
  font-weight: 700; color: #0b1020; background: var(--c); margin-left: .5rem;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

RISK_COLORS = {"Yüksek": "#ef4444", "Orta": "#f59e0b", "Düşük": "#22c55e"}


@st.cache_data(show_spinner="Veri seti yükleniyor ve analiz ediliyor…")
def get_data(drop_dupes: bool):
    return load_data(DATA_PATH, drop_duplicates=drop_dupes)


@st.cache_data(show_spinner=False)
def get_counters(drop_dupes: bool):
    return build_word_counters(get_data(drop_dupes))


def style(fig, height=380):
    fig.update_layout(
        template="plotly_dark", height=height, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=40, b=10),
        legend_title_text="",
    )
    return fig


def kpi(label, value, sub=""):
    return f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div><div class="s">{sub}</div></div>'


def fmt(n):
    return f"{n:,}".replace(",", ".")


# ---------------------------------------------------------------- Sidebar
st.sidebar.header("🎛️ Filtreler")
drop_dupes = st.sidebar.toggle("Tekrarlayan yorumları çıkar", value=False,
                               help="Aynı metin ve aynı etikete sahip yinelenen kayıtları kaldırır.")
try:
    data = get_data(drop_dupes)
    counters = get_counters(drop_dupes)
except (FileNotFoundError, ValueError) as exc:
    st.error(f"Veri yüklenemedi: {exc}")
    st.stop()

sel_sent = st.sidebar.multiselect("Duygu", SENTIMENT_ORDER, default=SENTIMENT_ORDER)
sel_cat = st.sidebar.multiselect("Kategori", CATEGORIES, default=CATEGORIES)
max_len = int(data["Kelime Sayısı"].max())
len_range = st.sidebar.slider("Yorum uzunluğu (kelime)", 1, max_len, (1, max_len))
query = st.sidebar.text_input("🔍 Yorumlarda ara", placeholder="ör. kargo, iade, kalite")
st.sidebar.caption("Arama büyük/küçük harf ve Türkçe karakterlerden bağımsızdır.")

df = data[
    data["Duygu"].isin(sel_sent) & data["Kategori"].isin(sel_cat)
    & data["Kelime Sayısı"].between(*len_range)
]
q = normalize_text(query)
if q:
    df = df[df["_norm"].str.contains(q, regex=False)]

st.sidebar.divider()
st.sidebar.metric("Filtrelenen / Toplam", f"{fmt(len(df))} / {fmt(len(data))}")

# ---------------------------------------------------------------- Hero + KPI
st.markdown(
    '<div class="hero"><h1>📊 AI Destekli Müşteri İçgörüsü & Ses Analiz Platformu</h1>'
    "<p>E-ticaret müşteri yorumlarını analiz ederek yöneticilere veri odaklı karar desteği sunar.</p></div>",
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("Seçili filtrelerle eşleşen yorum bulunamadı. Lütfen filtreleri genişletin.")
    st.stop()

k = sentiment_kpis(df)
cols = st.columns(5)
cards = [
    ("Toplam Yorum", fmt(k["toplam"]), "filtrelenmiş kayıt"),
    ("Pozitif", f"%{k['pozitif_oran']}", f"{fmt(k['pozitif'])} yorum"),
    ("Negatif", f"%{k['negatif_oran']}", f"{fmt(k['negatif'])} şikayet"),
    ("Net Duygu Skoru", f"{k['net_skor']:+}", "pozitif % − negatif %"),
    ("Ort. Yorum Uzunluğu", f"{k['ort_kelime']}", "kelime"),
]
for col, c in zip(cols, cards):
    col.markdown(kpi(*c), unsafe_allow_html=True)
st.write("")

tab_overview, tab_exec, tab_words, tab_explorer, tab_about = st.tabs(
    ["📈 Genel Bakış", "🚨 Yönetici Raporu", "🔤 Kelime Analizi", "🔎 Yorum Gezgini", "ℹ️ Hakkında"]
)

# ---------------------------------------------------------------- Genel Bakış
with tab_overview:
    c1, c2 = st.columns([1, 2])
    with c1:
        pie = px.pie(df, names="Duygu", hole=0.55, color="Duygu", color_discrete_map=SENTIMENT_COLORS,
                     category_orders={"Duygu": SENTIMENT_ORDER}, title="Duygu Dağılımı")
        pie.update_traces(textinfo="percent+label")
        st.plotly_chart(style(pie), width="stretch")
    with c2:
        mode = st.radio("Gösterim", ["Adet", "Yüzde"], horizontal=True, label_visibility="collapsed")
        grp = df.groupby(["Kategori", "Duygu"]).size().reset_index(name="Adet")
        if mode == "Yüzde":
            grp["Adet"] = 100 * grp["Adet"] / grp.groupby("Kategori")["Adet"].transform("sum")
        bar = px.bar(grp, x="Kategori", y="Adet", color="Duygu", barmode="group",
                     color_discrete_map=SENTIMENT_COLORS, category_orders={"Duygu": SENTIMENT_ORDER},
                     title="Kategorilere Göre Müşteri Duygu Dağılımı",
                     labels={"Adet": "Yorum Sayısı" if mode == "Adet" else "Yüzde (%)"})
        st.plotly_chart(style(bar), width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        heat = (df.groupby(["Kategori", "Duygu"]).size().unstack(fill_value=0)
                .reindex(columns=SENTIMENT_ORDER, fill_value=0))
        heat = heat.div(heat.sum(axis=1), axis=0).mul(100).round(1)
        fig = px.imshow(heat, text_auto=".1f", aspect="auto", color_continuous_scale="Viridis",
                        title="Kategori İçi Duygu Oranı (%)")
        st.plotly_chart(style(fig), width="stretch")
    with c4:
        hist = px.histogram(df, x="Kelime Sayısı", color="Duygu", nbins=40, barmode="overlay",
                            opacity=0.7, color_discrete_map=SENTIMENT_COLORS,
                            category_orders={"Duygu": SENTIMENT_ORDER}, title="Yorum Uzunluğu Dağılımı")
        st.plotly_chart(style(hist), width="stretch")

# ---------------------------------------------------------------- Yönetici Raporu
with tab_exec:
    st.subheader("📋 Yönetici İçgörü Raporu (Kritik Sorunlar)")
    rep = category_report(df)
    if k["negatif"] == 0:
        st.success("Seçili filtrelerde olumsuz yorum bulunmuyor. 🎉")
    else:
        for _, r in rep.head(3).iterrows():
            if r["Negatif"] == 0:
                continue
            color = RISK_COLORS[r["Risk"]]
            st.markdown(
                f'<div class="issue" style="--c:{color}"><div class="t">⚠️ {r["Kategori"]}'
                f'<span class="badge" style="--c:{color}">Risk: {r["Risk"]}</span></div>'
                f'<div class="m">{fmt(int(r["Negatif"]))} olumsuz yorum · kategori içi %{r["Negatif Oran (%)"]} · '
                f'toplam şikayetlerin %{r["Negatif Payı (%)"]}\'i</div>'
                f'<div class="a">💡 {RECOMMENDATIONS[r["Kategori"]]}</div></div>',
                unsafe_allow_html=True,
            )
        neg = rep[rep["Negatif"] > 0]
        fig = px.bar(neg.sort_values("Negatif"), x="Negatif", y="Kategori", orientation="h",
                     color="Risk", color_discrete_map=RISK_COLORS, text="Negatif",
                     title="Kategorilere Göre Olumsuz Yorum Sayısı")
        st.plotly_chart(style(fig, 320), width="stretch")
    st.markdown("**Kategori Bazlı Detay Tablosu**")
    st.dataframe(rep, hide_index=True, width="stretch")
    st.caption("Risk seviyesi: kategori negatif oranı, genel negatif orana göre ≥1,5× ise Yüksek, ≥1× ise Orta, aksi halde Düşük.")
    st.download_button("⬇️ Yönetici özetini indir (.md)", executive_summary(df),
                       file_name="yonetici_ozeti.md", mime="text/markdown")

# ---------------------------------------------------------------- Kelime Analizi
with tab_words:
    cc1, cc2 = st.columns([2, 1])
    word_sent = cc1.radio("Duygu", SENTIMENT_ORDER, horizontal=True, key="ws")
    n_words = cc2.slider("Kelime sayısı", 5, 40, 20)
    cats = sel_cat or CATEGORIES
    tw = top_words(counters, word_sent, cats, n_words)
    if tw.empty:
        st.info("Bu seçim için kelime bulunamadı.")
    else:
        fig = px.bar(tw.iloc[::-1], x="Adet", y="Kelime", orientation="h",
                     color_discrete_sequence=[SENTIMENT_COLORS[word_sent]],
                     title=f"En Sık Geçen Kelimeler — {word_sent} Yorumlar")
        st.plotly_chart(style(fig, max(380, 22 * len(tw) + 100)), width="stretch")
    st.caption("Kelimeler aksansız/küçük harfe çevrilmiş halde gösterilir; sık kullanılan dolgu kelimeleri ayıklanmıştır. "
               "Bu sekme Kategori filtresine uyar.")

# ---------------------------------------------------------------- Yorum Gezgini
with tab_explorer:
    st.subheader("Yorumları İncele")
    show = df[["Yorum", "Duygu", "Kategori", "Kelime Sayısı"]]
    st.caption(f"{fmt(len(show))} yorumdan ilk 1.000 tanesi gösteriliyor. İndirme tüm filtrelenmiş veriyi içerir.")
    st.dataframe(show.head(1000), hide_index=True, width="stretch", height=480,
                 column_config={"Yorum": st.column_config.TextColumn(width="large")})
    st.download_button("⬇️ Filtrelenmiş veriyi indir (.csv)", show.to_csv(index=False).encode("utf-8-sig"),
                       file_name="filtrelenmis_yorumlar.csv", mime="text/csv")

# ---------------------------------------------------------------- Hakkında
with tab_about:
    st.markdown(f"""
### Proje Hakkında
Bu platform, e-ticaret müşteri yorumlarını **duygu (pozitif / negatif / nötr)** ve **konu kategorisi** bazında analiz eder.

**Veri seti:** {fmt(len(data))} yorum (`{DATA_PATH.name}`).

**Metodoloji**
1. Metinler Türkçe uyumlu olarak normalleştirilir (`İ/ı` ve aksan sorunları giderilir).
2. Her yorum, kategori anahtar kelimelerinin isabet sayısına göre bir konuya atanır (kural tabanlı).
3. Negatif yorumlar kategori bazında risk skoruyla raporlanır.

**Sınırlılıklar:** Kategorizasyon anahtar kelime tabanlıdır; ironi veya çok konulu yorumlarda hata payı vardır.
Duygu etiketleri veri setinden gelir, model tarafından tahmin edilmez.
""")
