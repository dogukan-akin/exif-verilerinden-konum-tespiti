# 📸 Görüntü Metadata (EXIF) Analizi ve Coğrafi Konum Haritalama

Fotoğraflarınızın EXIF metadata bilgilerini detaylı şekilde analiz edin ve çekildiği konumu interaktif bir harita üzerinde görüntüleyin.

## ✨ Özellikler

- 🖼️ **Sürükle-bırak** ile kolay dosya yükleme
- 📋 **Detaylı EXIF Analizi**: Kamera, çekim ayarları, tarih, GPS ve daha fazlası
- 🗺️ **İnteraktif Harita**: Leaflet.js ile konum görselleştirme (Koyu, Standart, Uydu katmanları)
- 📍 **Reverse Geocoding**: GPS koordinatlarını adres bilgisine dönüştürme
- 📥 **Dışa Aktarma**: JSON ve CSV formatlarında metadata indirme
- 🎨 **Modern Tasarım**: Koyu tema, glassmorphism, mikro-animasyonlar
- 📱 **Responsive**: Mobil uyumlu arayüz

## 🚀 Kurulum

```bash
# 1. Bağımlılıkları yükle
pip install -r requirements.txt

# 2. Uygulamayı başlat
python app.py

# 3. Tarayıcıda aç
# http://localhost:5000
```

## 📁 Proje Yapısı

```
proje/
├── app.py              # Flask ana uygulama
├── exif_analyzer.py    # EXIF analiz modülü
├── geo_utils.py        # Coğrafi konum yardımcıları
├── requirements.txt    # Python bağımlılıkları
├── prd.md              # Ürün gereksinim dokümanı
├── README.md           # Bu dosya
├── templates/
│   └── index.html      # Ana sayfa şablonu
└── static/
    ├── css/
    │   └── style.css   # Stil dosyası
    ├── js/
    │   └── app.js      # Frontend mantığı
    └── uploads/        # Geçici yükleme dizini
```

## 🛠️ Teknolojiler

| Katman   | Teknoloji                        |
|----------|----------------------------------|
| Backend  | Python 3.x, Flask                |
| EXIF     | Pillow, exifread                 |
| Geocoding| geopy (Nominatim/OpenStreetMap)  |
| Harita   | Leaflet.js                       |
| Frontend | HTML5, CSS3, Vanilla JavaScript  |

## 📸 Desteklenen Formatlar

JPG, JPEG, PNG, TIFF, WEBP, HEIC

## 📄 Lisans

MIT License
