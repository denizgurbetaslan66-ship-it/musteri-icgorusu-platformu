AI Destekli Müşteri İçgörüsü & Ses Analiz Platformu

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.50%2B-FF4B4B?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-interaktif-3F4F75?logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

E-ticaret müşteri yorumlarını **duygu** ve **konu kategorisi** bazında analiz eden, yöneticilere
karar desteği sunan interaktif bir veri analitiği panelidir.

> 73.392 Türkçe müşteri yorumu · 5 konu kategorisi · otomatik risk skoru · tek tıkla yönetici özeti

<!-- Ekran görüntüsünü docs/screenshot.png olarak ekleyip aşağıdaki satırın yorumunu kaldırabilirsiniz -->
<!-- ![Dashboard](docs/screenshot.png) -->

 Özellikler

| Bölüm | Açıklama |
|---|---|
| **Genel Bakış** | Duygu dağılımı (donut), kategori bazlı karşılaştırma (adet/yüzde), ısı haritası, yorum uzunluğu dağılımı |
| **Yönetici Raporu** | En kritik 3 sorun alanı, risk seviyesi (Yüksek/Orta/Düşük), aksiyon önerileri, indirilebilir `.md` özet |
| **Kelime Analizi** | Duyguya ve kategoriye göre en sık geçen kelimeler |
| **Yorum Gezgini** | Filtrelenebilir yorum tablosu ve CSV dışa aktarma |
| **Filtreler** | Duygu, kategori, yorum uzunluğu, Türkçe karakterden bağımsız serbest metin arama, tekrarlayan yorumları çıkarma |

 Metodoloji

1. **Türkçe uyumlu normalleştirme:** `İ/ı` dönüşümü, aksan temizleme ve boşluk düzeltme.
   Böylece `ulaşmadı`, `ulasmadi` ve `İADE` gibi yazımların hepsi doğru eşleşir.
2. **Kural tabanlı kategorizasyon:** Her yorum, kategori anahtar kelimelerinin isabet sayısına göre
   *Teslimat ve Kargo, Fiyat ve Ücret, Ürün Kalitesi, Müşteri Hizmetleri* veya *Genel Memnuniyet* kategorisine atanır.
3. **Risk skoru:** Kategorinin negatif oranı, genel negatif orana bölünür; ≥ 1,5 ise **Yüksek**, ≥ 1 ise **Orta**, aksi halde **Düşük**.

### Örnek bulgular (tüm veri seti)

| Kategori | Yorum | Negatif oran | Risk |
|---|---:|---:|---|
| Müşteri Hizmetleri | 2.203 | %47,3 | 🔴 Yüksek |
| Ürün Kalitesi | 6.723 | %17,4 | 🟠 Orta |
| Genel Memnuniyet | 50.049 | %15,4 | 🟢 Düşük |
| Fiyat ve Ücret | 8.237 | %14,0 | 🟢 Düşük |
| Teslimat ve Kargo | 6.180 | %12,6 | 🟢 Düşük |

Genel dağılım: **%81,9 pozitif · %16,2 negatif · %1,9 nötr**.

Kurulum

```bash
git clone https://github.com/<kullanici-adi>/<repo-adi>.git
cd <repo-adi>

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Uygulama `http://localhost:8501` adresinde açılır. İlk açılışta veri seti analiz edilir ve önbelleğe alınır.

 Testler

```bash
pip install -r requirements-dev.txt
pytest -q
```

Proje Yapısı

```
.
├── app.py                  # Streamlit arayüzü
├── src/
│   └── analysis.py         # Veri yükleme, normalleştirme, kategorizasyon, raporlama
├── tests/
│   └── test_analysis.py    # Birim testleri
├── data/
│   └── e-ticaret_yorumlari_temizlenmis.xlsx
├── .streamlit/config.toml  # Tema ayarları
├── .github/workflows/ci.yml
├── requirements.txt
└── LICENSE
```


 Sınırlılıklar

- Kategorizasyon anahtar kelime tabanlıdır; ironi veya birden fazla konuyu içeren yorumlarda hata payı vardır.
- Duygu etiketleri veri setinden gelir; bu projede model ile tahmin edilmez.
- Veri setinde yaklaşık 4.700 birebir tekrar eden kayıt bulunur; yan menüden çıkarılabilir.

 Yol Haritası

-  Makine öğrenmesi tabanlı duygu ve konu sınıflandırması (ör. BERTurk)
-  Zaman serisi trend analizi (tarih sütunu eklendiğinde)
-  Kendi CSV/Excel dosyanı yükleme desteği

Sistem Görselleri:
<img width="1600" height="757" alt="image" src="https://github.com/user-attachments/assets/8286747d-fda0-424e-8163-52292254745a" />



