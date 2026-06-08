import urllib.request
import re
import zipfile
import io
import os

req = urllib.request.Request('https://exiftool.org/', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')
match = re.search(r'href="(exiftool-\d+\.\d+\.zip)"', html)
if match:
    url = 'https://exiftool.org/' + match.group(1)
    print('Downloading', url)
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})).read()))
    z.extractall('bin')
    print('Extracted.')
    for root, dirs, files in os.walk('bin'):
        for f in files:
            if f.startswith('exiftool') and f.endswith('.exe'):
                src = os.path.join(root, f)
                dst = os.path.join('bin', 'exiftool.exe')
                if src != dst:
                    if os.path.exists(dst): os.remove(dst)
                    os.rename(src, dst)
                print('Success: bin/exiftool.exe created.')
else:
    print('Could not find zip link in HTML')
