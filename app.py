"""
Görüntü Metadata (EXIF) Analizi ve Coğrafi Konum Haritalama
Flask Web Uygulaması
Pillow bağımlılığı olmadan çalışır.
"""

import os
import io
import json
import csv
import uuid
import base64
from datetime import datetime

from flask import (
    Flask, render_template, request, jsonify,
    send_file, Response, send_from_directory
)
from werkzeug.utils import secure_filename

from exif_analyzer import ExifAnalyzer, make_serializable
from geo_utils import reverse_geocode, format_coordinates

# Flask uygulaması
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB
# Vercel Serverless ortamı kontrolü
if os.environ.get('VERCEL'):
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
else:
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

# Upload klasörünü oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Desteklenen dosya uzantıları
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'heic', 'heif'}

# Oturum bazlı analiz sonuçlarını sakla
analysis_results = {}


def allowed_file(filename):
    """Dosya uzantısının geçerli olup olmadığını kontrol eder."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Ana sayfa."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_and_analyze():
    """Görüntü yükleme ve EXIF analizi."""
    if 'file' not in request.files:
        return jsonify({'error': 'Dosya bulunamadı'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Desteklenmeyen dosya formatı. Desteklenen: JPG, PNG, TIFF, WEBP, HEIC'}), 400

    try:
        # Güvenli dosya adı oluştur
        original_name = file.filename
        ext = original_name.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)

        # Dosyayı kaydet
        file.save(file_path)

        # EXIF analizi yap
        analyzer = ExifAnalyzer(file_path)
        result = analyzer.analyze()

        # Thumbnail: EXIF gömülü thumbnail veya orijinal dosyayı kullan
        thumbnail_b64 = None
        embedded_thumb = analyzer.get_embedded_thumbnail()
        if embedded_thumb:
            thumbnail_b64 = base64.b64encode(embedded_thumb).decode('utf-8')
        else:
            # Orijinal dosyayı base64 olarak gönder (max 2MB)
            if os.path.getsize(file_path) < 2 * 1024 * 1024:
                with open(file_path, 'rb') as f:
                    thumbnail_b64 = base64.b64encode(f.read()).decode('utf-8')

        # GPS bilgisi varsa reverse geocoding yap
        address_info = None
        if result.get('gps', {}).get('has_location'):
            lat = result['gps']['latitude']
            lon = result['gps']['longitude']
            address_info = reverse_geocode(lat, lon)

            # Koordinat formatları
            result['gps']['formatted_dd'] = format_coordinates(lat, lon, 'dd')
            result['gps']['formatted_dms'] = format_coordinates(lat, lon, 'dms')

        # Sonucu serileştirilebilir yap
        result = make_serializable(result)

        # Sonuç ID'si oluştur
        result_id = uuid.uuid4().hex[:12]
        analysis_results[result_id] = {
            'result': result,
            'file_path': file_path,
            'file_name': unique_name,
            'original_name': original_name,
            'timestamp': datetime.now().isoformat()
        }

        response = {
            'success': True,
            'result_id': result_id,
            'original_name': original_name,
            'metadata': result,
            'thumbnail': thumbnail_b64,
            'thumbnail_ext': ext if ext in ('jpg', 'jpeg') else 'jpeg',
            'image_url': f'/api/image/{result_id}',
            'address': address_info,
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': f'Analiz hatası: {str(e)}'}), 500


@app.route('/api/export/<result_id>/<format_type>')
def export_metadata(result_id, format_type):
    """Metadata'yı dışa aktarır."""
    if result_id not in analysis_results:
        return jsonify({'error': 'Sonuç bulunamadı'}), 404

    data = analysis_results[result_id]
    result = data['result']
    original_name = data['original_name']
    base_name = os.path.splitext(original_name)[0]

    if format_type == 'json':
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        return Response(
            json_str,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment;filename={base_name}_metadata.json'}
        )

    elif format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Kategori', 'Alan', 'Değer'])

        for category, fields in result.items():
            if isinstance(fields, dict):
                for field, value in fields.items():
                    writer.writerow([category, field, str(value)])
            else:
                writer.writerow([category, '', str(fields)])

        csv_content = output.getvalue()
        return Response(
            csv_content,
            mimetype='text/csv; charset=utf-8',
            headers={
                'Content-Disposition': f'attachment;filename={base_name}_metadata.csv',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )

    else:
        return jsonify({'error': 'Geçersiz format. json veya csv kullanın.'}), 400


@app.route('/api/image/<result_id>')
def get_image(result_id):
    """Orijinal görüntüyü döndürür."""
    if result_id not in analysis_results:
        return jsonify({'error': 'Sonuç bulunamadı'}), 404

    data = analysis_results[result_id]
    file_path = data['file_path']

    if os.path.exists(file_path):
        return send_file(file_path)
    return jsonify({'error': 'Dosya bulunamadı'}), 404


@app.route('/api/batch-upload', methods=['POST'])
def batch_upload():
    """Çoklu dosya yükleme ve analiz."""
    files = request.files.getlist('files')

    if not files:
        return jsonify({'error': 'Dosya bulunamadı'}), 400

    results = []
    for file in files:
        if file.filename and allowed_file(file.filename):
            try:
                original_name = file.filename
                ext = original_name.rsplit('.', 1)[1].lower()
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                file.save(file_path)

                analyzer = ExifAnalyzer(file_path)
                result = analyzer.analyze()

                # Thumbnail
                thumbnail_b64 = None
                embedded_thumb = analyzer.get_embedded_thumbnail()
                if embedded_thumb:
                    thumbnail_b64 = base64.b64encode(embedded_thumb).decode('utf-8')

                result = make_serializable(result)

                result_id = uuid.uuid4().hex[:12]
                analysis_results[result_id] = {
                    'result': result,
                    'file_path': file_path,
                    'file_name': unique_name,
                    'original_name': original_name,
                    'timestamp': datetime.now().isoformat()
                }

                # Adres
                address_info = None
                if result.get('gps', {}).get('has_location'):
                    lat = result['gps']['latitude']
                    lon = result['gps']['longitude']
                    address_info = reverse_geocode(lat, lon)

                results.append({
                    'success': True,
                    'result_id': result_id,
                    'original_name': original_name,
                    'metadata': result,
                    'thumbnail': thumbnail_b64,
                    'image_url': f'/api/image/{result_id}',
                    'address': address_info,
                })
            except Exception as e:
                results.append({
                    'success': False,
                    'original_name': file.filename,
                    'error': str(e)
                })

    return jsonify({'results': results, 'total': len(results)})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  📸 EXIF Metadata Analizi ve Coğrafi Konum Haritalama")
    print("="*60)
    print(f"  🌐 http://localhost:5000")
    print(f"  📁 Yükleme klasörü: {app.config['UPLOAD_FOLDER']}")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
