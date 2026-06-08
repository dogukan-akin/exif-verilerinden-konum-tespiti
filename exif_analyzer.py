"""
EXIF Metadata Analiz Modülü
Görüntü dosyalarından EXIF metadata bilgilerini çıkarır ve düzenler.
Pillow yerine sadece exifread kullanır (Python 3.15 uyumluluğu için).
"""

import os
import struct
import re
from datetime import datetime
import exifread


class ExifAnalyzer:
    """Görüntü dosyalarından EXIF metadata analizi yapan sınıf."""

    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.heif'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    def __init__(self, file_path):
        self.file_path = file_path
        self.metadata = {}
        self.gps_data = {}

    def validate_file(self):
        """Dosya doğrulama."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {self.file_path}")

        file_size = os.path.getsize(self.file_path)
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"Dosya boyutu çok büyük: {file_size / (1024*1024):.1f} MB (Max: 50 MB)")

        ext = os.path.splitext(self.file_path)[1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Desteklenmeyen dosya formatı: {ext}")

        return True

    def analyze(self):
        """Ana analiz fonksiyonu - tüm metadata'yı çıkarır."""
        self.validate_file()

        # Temel dosya bilgileri
        self._extract_file_info()

        # exifread ile detaylı EXIF
        self._extract_exifread_data()
        
        # XMP'den alternatif metadata taraması (WhatsApp vb. bazı OS kaydetmelerinde kalabilen veriler)
        self._extract_xmp_fallback()

        # Görüntü boyutlarını EXIF'ten çıkar
        self._extract_image_dimensions()

        # GPS verilerini işle
        self._process_gps_data()

        return self._format_result()

    def _extract_file_info(self):
        """Temel dosya bilgilerini çıkarır."""
        file_size = os.path.getsize(self.file_path)
        ext = os.path.splitext(self.file_path)[1].lower()

        format_map = {
            '.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG',
            '.tiff': 'TIFF', '.tif': 'TIFF', '.webp': 'WebP',
            '.heic': 'HEIC', '.heif': 'HEIF'
        }

        self.metadata['image_info'] = {
            'file_name': os.path.basename(self.file_path),
            'file_size': file_size,
            'format': format_map.get(ext, ext.upper()),
        }

    def _extract_image_dimensions(self):
        """EXIF veya dosya başlığından görüntü boyutlarını çıkarır."""
        # EXIF'ten boyutları al
        image_details = self.metadata.get('image_details', {})
        width = None
        height = None

        for key, val in image_details.items():
            key_lower = key.lower()
            if 'width' in key_lower or 'imagewidth' in key_lower.replace(' ', ''):
                try:
                    width = int(val)
                except (ValueError, TypeError):
                    pass
            elif 'height' in key_lower or 'imageheight' in key_lower.replace(' ', '') or 'imagelength' in key_lower.replace(' ', ''):
                try:
                    height = int(val)
                except (ValueError, TypeError):
                    pass

        # EXIF ExifImageWidth/ExifImageHeight'tan al
        settings = self.metadata.get('settings', {})
        for key, val in settings.items():
            key_lower = key.lower()
            if 'exifimagewidth' in key_lower.replace(' ', '') and width is None:
                try:
                    width = int(val)
                except (ValueError, TypeError):
                    pass
            elif 'exifimageheight' in key_lower.replace(' ', '') and height is None:
                try:
                    height = int(val)
                except (ValueError, TypeError):
                    pass

        # Dosya başlığından boyut okuma
        if width is None or height is None:
            dims = self._read_dimensions_from_header()
            if dims:
                width = width or dims[0]
                height = height or dims[1]

        if width and height:
            self.metadata['image_info']['width'] = width
            self.metadata['image_info']['height'] = height

    def _read_dimensions_from_header(self):
        """Dosya başlığından görüntü boyutlarını okur."""
        try:
            with open(self.file_path, 'rb') as f:
                header = f.read(30)

                # JPEG
                if header[:2] == b'\xff\xd8':
                    return self._get_jpeg_dimensions()

                # PNG
                if header[:8] == b'\x89PNG\r\n\x1a\n':
                    width = struct.unpack('>I', header[16:20])[0]
                    height = struct.unpack('>I', header[20:24])[0]
                    return (width, height)

        except Exception:
            pass
        return None

    def _get_jpeg_dimensions(self):
        """JPEG dosyasından boyutları okur."""
        try:
            with open(self.file_path, 'rb') as f:
                f.read(2)  # SOI marker skip
                while True:
                    marker = f.read(2)
                    if len(marker) < 2:
                        break
                    if marker[0] != 0xFF:
                        break
                    marker_type = marker[1]

                    # SOF markers (Start of Frame)
                    if marker_type in (0xC0, 0xC1, 0xC2, 0xC3):
                        f.read(3)  # length + precision
                        height = struct.unpack('>H', f.read(2))[0]
                        width = struct.unpack('>H', f.read(2))[0]
                        return (width, height)

                    # Skip marker
                    length = struct.unpack('>H', f.read(2))[0]
                    f.read(length - 2)
        except Exception:
            pass
        return None

    def _extract_exifread_data(self):
        """exifread kütüphanesi ile detaylı EXIF verilerini çıkarır."""
        try:
            with open(self.file_path, 'rb') as f:
                tags = exifread.process_file(f, details=True)

            for tag_name, tag_value in tags.items():
                category, field = self._categorize_tag(str(tag_name))
                if category not in self.metadata:
                    self.metadata[category] = {}
                self.metadata[category][field] = str(tag_value)
        except Exception as e:
            if 'exifread_error' not in self.metadata:
                self.metadata['exifread_error'] = str(e)

    def _categorize_tag(self, tag_name):
        """EXIF etiketini kategoriye ayırır."""
        tag_lower = tag_name.lower()

        if 'gps' in tag_lower:
            return 'gps', tag_name.replace('GPS ', '')
        elif any(k in tag_lower for k in ['make', 'model', 'lens', 'body']):
            return 'camera', tag_name.replace('Image ', '').replace('EXIF ', '')
        elif any(k in tag_lower for k in ['iso', 'aperture', 'exposure', 'focal', 'fnumber',
                                           'shutter', 'brightness', 'metering']):
            return 'settings', tag_name.replace('EXIF ', '')
        elif any(k in tag_lower for k in ['date', 'time', 'offset']):
            return 'datetime', tag_name.replace('EXIF ', '').replace('Image ', '')
        elif any(k in tag_lower for k in ['flash', 'white', 'scene', 'light', 'sensing']):
            return 'advanced', tag_name.replace('EXIF ', '')
        elif any(k in tag_lower for k in ['software', 'processing', 'version']):
            return 'software', tag_name.replace('Image ', '').replace('EXIF ', '')
        elif any(k in tag_lower for k in ['width', 'height', 'resolution', 'pixel',
                                           'orientation', 'color', 'compression', 'quality']):
            return 'image_details', tag_name.replace('Image ', '').replace('EXIF ', '')
        elif 'thumbnail' in tag_lower:
            return 'thumbnail', tag_name.replace('Thumbnail ', '')
        else:
            return 'other', tag_name

    def _extract_xmp_fallback(self):
        """Standard EXIF bulunamazsa raw dosya üzerinden XMP XML taraması yapar."""
        try:
            with open(self.file_path, 'rb') as f:
                content = f.read()
            
            # XMP tag'leri aranıyor
            # GPSLatitude, GPSLongitude bulmaya çalış
            lat_match = re.search(rb'exif:GPSLatitude[=">]+([^<"\s]+)', content)
            lon_match = re.search(rb'exif:GPSLongitude[=">]+([^<"\s]+)', content)
            
            if lat_match and lon_match:
                if 'gps' not in self.metadata:
                    self.metadata['gps'] = {}
                
                lat_str = lat_match.group(1).decode('utf-8', errors='ignore')
                lon_str = lon_match.group(1).decode('utf-8', errors='ignore')
                
                # Eğer daha önce exifread ile bulunmadıysa XMP'den yaz
                if 'GPSLatitude' not in self.metadata['gps']:
                    self.metadata['gps']['GPSLatitude'] = lat_str
                if 'GPSLongitude' not in self.metadata['gps']:
                    self.metadata['gps']['GPSLongitude'] = lon_str
                    
            # Make/Model taraması
            make_match = re.search(rb'tiff:Make[=">]+([^<"\s]+)', content)
            model_match = re.search(rb'tiff:Model[=">]+([^<"\s]+)', content)
            
            if make_match or model_match:
                if 'camera' not in self.metadata:
                    self.metadata['camera'] = {}
                if make_match and 'Make' not in self.metadata['camera']:
                    self.metadata['camera']['Make'] = make_match.group(1).decode('utf-8', errors='ignore')
                if model_match and 'Model' not in self.metadata['camera']:
                    self.metadata['camera']['Model'] = model_match.group(1).decode('utf-8', errors='ignore')
                    
        except Exception as e:
            pass

    def _process_gps_data(self):
        """GPS verilerini işler ve koordinatlara dönüştürür."""
        gps_info = self.metadata.get('gps', {})

        if not gps_info:
            self.gps_data = {'has_location': False}
            return

        lat = self._extract_coordinate(gps_info, 'GPSLatitude', 'GPSLatitudeRef')
        lon = self._extract_coordinate(gps_info, 'GPSLongitude', 'GPSLongitudeRef')

        if lat is not None and lon is not None:
            self.gps_data = {
                'latitude': lat,
                'longitude': lon,
                'altitude': self._extract_altitude(gps_info),
                'has_location': True
            }
        else:
            self.gps_data = {'has_location': False}

    def _extract_coordinate(self, gps_info, coord_key, ref_key):
        """GPS koordinatını DMS'den ondalık dereceye dönüştürür."""
        coord_value = None
        ref_value = None

        # Farklı key formatlarını dene
        for key in [coord_key, coord_key.replace('GPS', '')]:
            if key in gps_info:
                coord_value = gps_info[key]
                break

        for key in [ref_key, ref_key.replace('GPS', '')]:
            if key in gps_info:
                ref_value = gps_info[key]
                break

        if coord_value is None:
            return None

        try:
            # XMP'den gelen string formatı: "41,0.01N" veya "41.0123"
            if isinstance(coord_value, str) and not coord_value.startswith('['):
                coord_str = coord_value.strip()
                # Zaten ondalık sayıysa
                if re.match(r'^-?\d+\.\d+$', coord_str):
                    return float(coord_str)
                # DMS formatındaysa: "41,30.5N" veya "41,30,15.5N"
                parts = re.split(r'[,NnSsEeWw\s]', coord_str)
                parts = [p for p in parts if p]
                if len(parts) >= 1:
                    degrees = float(parts[0])
                    minutes = float(parts[1]) if len(parts) > 1 else 0.0
                    seconds = float(parts[2]) if len(parts) > 2 else 0.0
                    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
                    if 'S' in coord_str.upper() or 'W' in coord_str.upper():
                        decimal = -decimal
                    return round(decimal, 6)

            # exifread formatı: "[deg, min, sec]"
            coord_str = str(coord_value).strip('[]')
            parts = [p.strip() for p in coord_str.split(',')]
            if len(parts) == 3:
                degrees = self._parse_rational(parts[0])
                minutes = self._parse_rational(parts[1])
                seconds = self._parse_rational(parts[2])
            else:
                # Sadece ondalık varsa
                if len(parts) == 1:
                    decimal = self._parse_rational(parts[0])
                else:
                    return None

            if len(parts) == 3:
                decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

            ref_str = str(ref_value).strip().upper() if ref_value else 'N'
            if ref_str in ('S', 'W'):
                decimal = -decimal

            return round(decimal, 6)
        except (ValueError, TypeError, IndexError, ZeroDivisionError):
            return None

    def _parse_rational(self, value_str):
        """Rasyonel sayı formatını (ör. '41/1') ondalık sayıya çevirir."""
        value_str = str(value_str).strip()
        if '/' in value_str:
            parts = value_str.split('/')
            numerator = float(parts[0])
            denominator = float(parts[1])
            if denominator == 0:
                return 0.0
            return numerator / denominator
        return float(value_str)

    def _extract_altitude(self, gps_info):
        """GPS yükseklik bilgisini çıkarır."""
        alt_value = None
        for key in ['GPSAltitude', 'Altitude']:
            if key in gps_info:
                alt_value = gps_info[key]
                break

        if alt_value is None:
            return None

        try:
            return round(self._parse_rational(str(alt_value)), 1)
        except (ValueError, TypeError):
            return None

    def _format_result(self):
        """Sonuçları düzenli bir formatta döndürür."""
        result = {
            'file_info': self.metadata.get('image_info', {}),
            'camera': self.metadata.get('camera', {}),
            'settings': self.metadata.get('settings', {}),
            'datetime': self.metadata.get('datetime', {}),
            'image_details': self.metadata.get('image_details', {}),
            'gps_raw': self.metadata.get('gps', {}),
            'gps': self.gps_data,
            'advanced': self.metadata.get('advanced', {}),
            'software': self.metadata.get('software', {}),
            'other': self.metadata.get('other', {}),
        }

        # Boş kategorileri temizle
        result = {k: v for k, v in result.items() if v}

        return result

    def get_embedded_thumbnail(self):
        """EXIF'teki gömülü thumbnail'ı çıkarır (byte data olarak)."""
        try:
            with open(self.file_path, 'rb') as f:
                tags = exifread.process_file(f)

            if 'JPEGThumbnail' in tags:
                return tags['JPEGThumbnail']
            elif 'TIFFThumbnail' in tags:
                return tags['TIFFThumbnail']
        except Exception:
            pass
        return None


def make_serializable(obj):
    """Nesneleri JSON serileştirilebilir yapar."""
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, bytes):
        try:
            return obj.decode('utf-8', errors='ignore')
        except Exception:
            return str(obj)
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    elif hasattr(obj, 'numerator') and hasattr(obj, 'denominator'):
        try:
            if obj.denominator == 0:
                return 0
            return float(obj.numerator) / float(obj.denominator)
        except Exception:
            return str(obj)
    else:
        return str(obj)
