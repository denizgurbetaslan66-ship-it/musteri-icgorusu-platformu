import pandas as pd
import pytest

from src.analysis import (
    DATA_PATH, GENERAL, categorize, category_report, executive_summary,
    load_data, normalize_text, risk_level, sentiment_kpis,
)


def test_normalize_turkish_chars():
    assert normalize_text("İADE Ulaşmadı") == "iade ulasmadi"
    assert normalize_text("i\u0307ade   talebi") == "iade talebi"
    assert normalize_text(None) == "" and normalize_text(float("nan")) == ""


@pytest.mark.parametrize("text,expected", [
    ("kargo çok geç geldi", "Teslimat ve Kargo"),
    ("Ürün Ulaşmadı", "Teslimat ve Kargo"),
    ("fiyatı çok pahalı", "Fiyat ve Ücret"),
    ("telefon 2 ayda bozuldu", "Ürün Kalitesi"),
    ("iade talebime cevap yok", "Müşteri Hizmetleri"),
    ("güzel bir tişört", GENERAL),
])
def test_categorize(text, expected):
    s = pd.Series([normalize_text(text)])
    assert categorize(s).iloc[0] == expected


def test_risk_level():
    assert risk_level(30, 15) == "Yüksek"
    assert risk_level(16, 15) == "Orta"
    assert risk_level(5, 15) == "Düşük"
    assert risk_level(5, 0) == "Düşük"


def test_empty_frames_do_not_crash():
    empty = pd.DataFrame(columns=["Yorum", "Duygu", "Kategori", "Kelime Sayısı", "_norm"])
    empty["Kelime Sayısı"] = empty["Kelime Sayısı"].astype(int)
    assert sentiment_kpis(empty)["toplam"] == 0
    assert category_report(empty).empty


@pytest.mark.skipif(not DATA_PATH.exists(), reason="veri dosyası yok")
def test_real_dataset():
    df = load_data()
    assert len(df) > 70000
    assert set(df["Duygu"]) <= {"Pozitif", "Negatif", "Nötr"}
    assert df["Kategori"].notna().all()
    assert "Yönetici" in executive_summary(df)
    assert round(category_report(df)["Negatif"].sum()) == (df["Duygu"] == "Negatif").sum()
