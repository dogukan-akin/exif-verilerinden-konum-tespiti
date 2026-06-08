# 📸 Görüntü Metadata (EXIF) Analizi ve Coğrafi Konum Haritalama

## Ürün Gereksinim Dokümanı (PRD)

---

## 1. Proje Özeti

Bu proje, kullanıcıların fotoğraf dosyalarını yükleyerek EXIF metadata bilgilerini detaylı şekilde analiz etmelerini ve fotoğrafın çekildiği coğrafi konumu interaktif bir harita üzerinde görselleştirmelerini sağlayan bir **Python web uygulaması**dır.

## 2. Problem Tanımı

- Kullanıcılar fotoğraflarının hangi cihazla, ne zaman, hangi ayarlarla çekildiğini kolayca göremiyorlar.
- Fotoğraflardaki GPS bilgisini çıkarmak ve harita üzerinde göstermek teknik bilgi gerektiriyor.
- Mevcut araçlar genellikle ya sadece metadata gösteriyor ya da sadece konum haritalama yapıyor; ikisini birleştiren modern bir arayüz eksik.

## 3. Hedef Kitle

- Fotoğrafçılar (amatör ve profesyonel)
- Dijital adli bilişim uzmanları
- Gizlilik bilinçli kullanıcılar (fotoğraflarındaki metadata'yı kontrol etmek isteyenler)
- Gazeteciler ve araştırmacılar
- Genel kullanıcılar

## 4. Temel Özellikler

### 4.1 Görüntü Yükleme
- **Sürükle-bırak** ile dosya yükleme
- **Dosya seçici** ile yükleme
- Desteklenen formatlar: JPEG, JPG, PNG, TIFF, WEBP, HEIC
- Çoklu dosya yükleme desteği
- Dosya boyutu limiti: 50 MB

### 4.2 EXIF Metadata Analizi
- **Kamera Bilgileri**: Marka, model, lens bilgisi
- **Çekim Ayarları**: ISO, diyafram (f-stop), enstantane hızı, odak uzaklığı
- **Tarih/Saat Bilgileri**: Çekim tarihi, düzenleme tarihi, dijitalleştirme tarihi
- **Görüntü Bilgileri**: Çözünürlük, boyut, renk derinliği, yönelim (orientation)
- **GPS Bilgileri**: Enlem, boylam, yükseklik, hız, yön
- **Yazılım Bilgileri**: Düzenleme yazılımı, işletim sistemi
- **Gelişmiş Bilgiler**: Flash durumu, beyaz dengesi, ölçüm modu, sahne tipi
- Metadata'sız alanlar için uyarı gösterimi

### 4.3 Coğrafi Konum Haritalama
- **İnteraktif harita** (Leaflet.js) üzerinde konum gösterimi
- Çoklu fotoğraf için tüm konumları tek haritada gösterme
- Konum bilgisi olmayan fotoğraflar için bilgilendirme mesajı
- Farklı harita katmanları (sokak, uydu, topografik)
- Marker üzerine tıklayınca fotoğraf önizleme ve detay gösterimi
- Koordinatların adres bilgisine dönüştürülmesi (Reverse Geocoding)

### 4.4 Veri Dışa Aktarma
- Metadata'yı **JSON** formatında dışa aktarma
- Metadata'yı **CSV** formatında dışa aktarma
- Metadata'yı **PDF rapor** olarak dışa aktarma

### 4.5 Görüntü Önizleme
- Yüklenen görselin küçük resim (thumbnail) önizlemesi
- EXIF yönelim bilgisine göre otomatik döndürme
- Fotoğraf galerisi görünümü (çoklu yükleme için)

## 5. Teknik Mimari

### 5.1 Backend (Python)
- **Framework**: Flask 3.x
- **EXIF Okuma**: Pillow (PIL), exifread
- **GPS İşleme**: Koordinat dönüştürme (DMS → DD)
- **Reverse Geocoding**: Nominatim (OpenStreetMap) API
- **Dosya İşleme**: Güvenli dosya yükleme, geçici dosya yönetimi

### 5.2 Frontend
- **HTML5 / CSS3 / JavaScript** (Vanilla)
- **Harita**: Leaflet.js (OpenStreetMap tiles)
- **Tasarım**: Modern, koyu tema, glassmorphism, mikro-animasyonlar
- **Responsive**: Mobil uyumlu tasarım
- **Font**: Inter (Google Fonts)

### 5.3 Proje Yapısı
```
proje/
├── prd.md                    # Bu doküman
├── app.py                    # Flask ana uygulama
├── requirements.txt          # Python bağımlılıkları
├── exif_analyzer.py          # EXIF analiz modülü
├── geo_utils.py              # Coğrafi konum yardımcı fonksiyonları
├── templates/
│   └── index.html            # Ana sayfa şablonu
├── static/
│   ├── css/
│   │   └── style.css         # Ana stil dosyası
│   ├── js/
│   │   └── app.js            # Frontend mantığı
│   └── uploads/              # Geçici yükleme dizini
└── README.md                 # Kurulum ve kullanım kılavuzu
```

## 6. API Endpointleri

| Metot | Endpoint              | Açıklama                          |
|-------|-----------------------|-----------------------------------|
| GET   | `/`                   | Ana sayfa                         |
| POST  | `/api/upload`         | Görüntü yükleme ve analiz        |
| POST  | `/api/analyze`        | EXIF metadata çıkarma            |
| GET   | `/api/export/<format>`| Metadata dışa aktarma (json/csv) |
| GET   | `/api/thumbnail/<id>` | Küçük resim getirme              |

## 7. UI/UX Gereksinimleri

### 7.1 Tasarım İlkeleri
- **Koyu tema** varsayılan olarak
- **Glassmorphism** efektleri ile modern görünüm
- **Gradient** arka planlar ve buton renkleri
- **Smooth animasyonlar** (geçişler, hover efektleri)
- **Sürükle-bırak** alanı belirgin ve kullanıcı dostu

### 7.2 Sayfa Bölümleri
1. **Header**: Logo, proje adı, kısa açıklama
2. **Yükleme Alanı**: Sürükle-bırak + dosya seçici
3. **Metadata Paneli**: Kategorilere ayrılmış metadata tablosu
4. **Harita Paneli**: İnteraktif Leaflet harita
5. **Dışa Aktarma**: JSON/CSV indirme butonları
6. **Footer**: Telif hakkı, teknoloji bilgisi

### 7.3 Renk Paleti
- **Arka Plan**: `#0a0a1a` → `#1a1a2e` (gradient)
- **Kart Arka Plan**: `rgba(255, 255, 255, 0.05)` (glassmorphism)
- **Birincil Renk**: `#6c63ff` (mor/indigo)
- **İkincil Renk**: `#00d4aa` (turkuaz)
- **Vurgu Renk**: `#ff6b6b` (mercan kırmızı)
- **Metin**: `#e0e0e0` (açık gri)
- **Başarı**: `#4ecdc4`
- **Uyarı**: `#ffe66d`

## 8. Performans Gereksinimleri

- Görüntü yükleme ve analiz süresi: < 3 saniye (10 MB altı dosyalar için)
- Harita yükleme süresi: < 1 saniye
- Eşzamanlı kullanıcı desteği: 10+ (geliştirme ortamı için)
- Maksimum dosya boyutu: 50 MB

## 9. Güvenlik

- Dosya tipi doğrulama (sadece izin verilen formatlar)
- Dosya adı sanitizasyonu
- Yükleme dizini izolasyonu
- XSS koruması
- Geçici dosyaların otomatik temizlenmesi

## 10. Kurulum ve Çalıştırma

```bash
# 1. Bağımlılıkları yükle
pip install -r requirements.txt

# 2. Uygulamayı başlat
python app.py

# 3. Tarayıcıda aç
# http://localhost:5000
```

## 11. Gelecek Geliştirmeler (v2.0)

- [ ] Toplu fotoğraf analizi ve karşılaştırma
- [ ] EXIF metadata düzenleme/silme
- [ ] Fotoğraf zaman çizelgesi görünümü
- [ ] Rota haritalama (çoklu GPS noktaları birleştirme)
- [ ] Fotoğraf benzerlik analizi
- [ ] API anahtarı ile kimlik doğrulama
- [ ] Docker desteği
- [ ] Bulut depolama entegrasyonu (S3, GCS)

## 12. Başarı Kriterleri

- [x] Kullanıcı fotoğraf yükleyebilmeli
- [x] Tüm EXIF metadata alanları doğru şekilde çıkarılabilmeli
- [x] GPS bilgisi olan fotoğraflar haritada gösterilmeli
- [x] Metadata JSON/CSV olarak dışa aktarılabilmeli
- [x] Arayüz modern ve kullanıcı dostu olmalı
- [x] Responsive tasarım (mobil uyumlu) olmalı

---

**Versiyon**: 1.0  
**Tarih**: 2026-06-08  
**Yazar**: AI Assistant  
**Durum**: Onaylandı ✅
