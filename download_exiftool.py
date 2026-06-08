import urllib.request
import re
import zipfile
import os

print('Finding latest ExifTool version...')
req = urllib.request.Request('https://exiftool.org/', headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    # Find something like exiftool-13.06_32.zip or exiftool-13.06_64.zip
    matches = re.findall(r'href="([^"]+\.zip)"', html)
    zip_url = None
    for m in matches:
        if 'exiftool-' in m and ('_64' in m or '_32' in m or 'exiftool-' in m):
            zip_url = 'https://exiftool.org/' + m
            break
            
    if not zip_url:
        print("Could not find zip url in matches:", matches)
        exit(1)
        
    print('Downloading:', zip_url)
    zip_path = 'exiftool.zip'
    urllib.request.urlretrieve(zip_url, zip_path)

    print('Extracting...')
    if not os.path.exists('bin'):
        os.makedirs('bin')
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall('bin')

    print('Locating executable...')
    for root, dirs, files in os.walk('bin'):
        for file in files:
            if file.startswith('exiftool') and file.endswith('.exe'):
                src = os.path.join(root, file)
                dst = os.path.join('bin', 'exiftool.exe')
                if src != dst:
                    os.rename(src, dst)
                print(f'ExifTool installed to {dst}')
                break
                
    if os.path.exists(zip_path):
        os.remove(zip_path)

except Exception as e:
    print("Error:", e)
    exit(1)
