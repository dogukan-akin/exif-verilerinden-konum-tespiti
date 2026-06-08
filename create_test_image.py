import piexif
from PIL import Image # Wait, Pillow isn't installed. I'll just download a pure raw valid JPEG and insert EXIF with piexif.
import urllib.request

# Download a tiny blank valid JPEG from internet
url = "https://upload.wikimedia.org/wikipedia/commons/c/ca/1x1.png" # wait, needs to be jpeg
url = "https://upload.wikimedia.org/wikipedia/commons/d/d1/1x1-white.jpg"
urllib.request.urlretrieve(url, 'test_base.jpg')

# Create EXIF data
gps_ifd = {
    piexif.GPSIFD.GPSLatitudeRef: 'N',
    piexif.GPSIFD.GPSLatitude: ((41, 1), (0, 1), (0, 1)), # 41 deg 0 min 0 sec
    piexif.GPSIFD.GPSLongitudeRef: 'E',
    piexif.GPSIFD.GPSLongitude: ((28, 1), (58, 1), (0, 1)), # 28 deg 58 min 0 sec (Istanbul)
}
exif_dict = {"0th": {}, "Exif": {}, "GPS": gps_ifd, "1st": {}, "thumbnail": None}
exif_bytes = piexif.dump(exif_dict)

piexif.insert(exif_bytes, 'test_base.jpg', 'test_gps.jpg')
print('test_gps.jpg created with GPS EXIF data.')
