"""
Coğrafi Konum Yardımcı Modülü
GPS koordinatlarını işler ve reverse geocoding yapar.
"""

import time
import functools


# Basit bir cache decorator
def simple_cache(maxsize=128):
    """Basit bellek içi cache."""
    cache = {}

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            if len(cache) < maxsize:
                cache[key] = result
            return result
        return wrapper
    return decorator


@simple_cache(maxsize=256)
def reverse_geocode(latitude, longitude):
    """
    Koordinatları adres bilgisine dönüştürür.
    Nominatim API kullanır (rate limit: 1 istek/saniye).
    """
    try:
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut, GeocoderServiceError

        geolocator = Nominatim(
            user_agent="exif_metadata_analyzer/1.0",
            timeout=5
        )

        # Rate limiting
        time.sleep(1)

        location = geolocator.reverse(
            f"{latitude}, {longitude}",
            language='tr',
            exactly_one=True
        )

        if location:
            address = location.raw.get('address', {})
            return {
                'full_address': location.address,
                'country': address.get('country', ''),
                'city': address.get('city', address.get('town', address.get('village', ''))),
                'state': address.get('state', ''),
                'district': address.get('suburb', address.get('district', '')),
                'road': address.get('road', ''),
                'postcode': address.get('postcode', ''),
                'success': True
            }
        else:
            return {'success': False, 'error': 'Adres bulunamadı'}

    except ImportError:
        return {'success': False, 'error': 'geopy kütüphanesi yüklü değil'}
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        return {'success': False, 'error': f'Geocoding hatası: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Beklenmeyen hata: {str(e)}'}


def format_coordinates(lat, lon, fmt='dms'):
    """
    Koordinatları farklı formatlarda gösterir.
    
    Args:
        lat: Enlem (ondalık derece)
        lon: Boylam (ondalık derece)
        fmt: Format tipi - 'dd' (ondalık), 'dms' (derece/dakika/saniye)
    """
    if fmt == 'dd':
        return f"{lat:.6f}°, {lon:.6f}°"
    elif fmt == 'dms':
        lat_dms = _decimal_to_dms(abs(lat))
        lon_dms = _decimal_to_dms(abs(lon))
        lat_dir = 'N' if lat >= 0 else 'S'
        lon_dir = 'E' if lon >= 0 else 'W'
        return (
            f"{lat_dms[0]}°{lat_dms[1]}'{lat_dms[2]:.2f}\"{lat_dir}, "
            f"{lon_dms[0]}°{lon_dms[1]}'{lon_dms[2]:.2f}\"{lon_dir}"
        )
    return f"{lat}, {lon}"


def _decimal_to_dms(decimal_degrees):
    """Ondalık dereceyi DMS (Derece, Dakika, Saniye) formatına çevirir."""
    degrees = int(decimal_degrees)
    minutes_full = (decimal_degrees - degrees) * 60
    minutes = int(minutes_full)
    seconds = (minutes_full - minutes) * 60
    return (degrees, minutes, seconds)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    İki koordinat arasındaki mesafeyi hesaplar (Haversine formülü).
    Sonuç kilometre cinsindendir.
    """
    import math

    R = 6371  # Dünya'nın yarıçapı (km)

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 2)


def get_map_bounds(locations):
    """
    Birden fazla konum için harita sınırlarını hesaplar.
    
    Args:
        locations: [(lat, lon), ...] listesi
    
    Returns:
        [[min_lat, min_lon], [max_lat, max_lon]]
    """
    if not locations:
        return None

    lats = [loc[0] for loc in locations]
    lons = [loc[1] for loc in locations]

    padding = 0.01  # ~1 km padding
    return [
        [min(lats) - padding, min(lons) - padding],
        [max(lats) + padding, max(lons) + padding]
    ]
