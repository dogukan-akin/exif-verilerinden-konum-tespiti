/**
 * EXIF Metadata Analizi - Frontend Mantığı
 * 21st.dev ilhamlı premium UI bileşenleri
 * Spotlight Cards + Skeleton Loading + Animated Tabs + Download Toast
 */

// ---- Global State ----
const AppState = {
    currentResult: null,
    resultId: null,
    map: null,
    markers: [],
};

// ---- DOM Elements ----
const DOM = {
    uploadZone: document.getElementById('upload-zone'),
    fileInput: document.getElementById('file-input'),
    loadingOverlay: document.getElementById('loading-overlay'),
    resultsSection: document.getElementById('results-section'),
    uploadSection: document.getElementById('upload-section'),
    toastContainer: document.getElementById('toast-container'),
};

// ---- Initialization ----
document.addEventListener('DOMContentLoaded', () => {
    initUploadZone();
    initSpotlightCards();
});

// ---- Upload Zone ----
function initUploadZone() {
    const zone = DOM.uploadZone;
    const input = DOM.fileInput;

    // Tıklama ile dosya seçme
    zone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
            input.click();
        }
    });

    // Dosya seçildiğinde
    input.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFiles(e.target.files);
        }
    });

    // Drag & Drop
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    });
}

function triggerFileSelect() {
    DOM.fileInput.click();
}

// ============================================
// 21st.dev: SPOTLIGHT CARD EFFECT
// Mouse-following radial glow on cards
// ============================================
function initSpotlightCards() {
    document.addEventListener('mousemove', (e) => {
        const cards = document.querySelectorAll('.card, .stat-card');
        cards.forEach(card => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            card.style.setProperty('--spotlight-x', `${x}px`);
            card.style.setProperty('--spotlight-y', `${y}px`);
        });
    });

    // Spotlight CSS'i dinamik olarak ekle
    const style = document.createElement('style');
    style.textContent = `
        .card::after, .stat-card::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: radial-gradient(
                400px circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%),
                rgba(124, 106, 255, 0.04) 0%,
                transparent 60%
            );
            opacity: 0;
            transition: opacity 0.4s ease;
            pointer-events: none;
            z-index: 0;
        }
        .card:hover::after, .stat-card:hover::after {
            opacity: 1;
        }
        .card__header, .card__body, .card__header-badge {
            position: relative;
            z-index: 1;
        }
    `;
    document.head.appendChild(style);
}

// ---- File Handling ----
async function handleFiles(files) {
    if (files.length === 1) {
        await uploadAndAnalyze(files[0]);
    } else {
        await batchUpload(files);
    }
}

async function uploadAndAnalyze(file) {
    const validExts = ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'heic', 'heif'];
    const ext = file.name.split('.').pop().toLowerCase();

    if (!validExts.includes(ext)) {
        showToast('Desteklenmeyen dosya formatı!', 'error');
        return;
    }

    if (file.size > 50 * 1024 * 1024) {
        showToast('Dosya boyutu 50 MB sınırını aşıyor!', 'error');
        return;
    }

    showLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        // Yükleme tamamlandı, verileri göster
        document.getElementById('upload-zone').style.opacity = '1';
        const selectBtn = document.getElementById('select-file-btn');
        if (selectBtn) selectBtn.disabled = false;
        
        const skeleton = document.getElementById('processing-skeleton');
        if(skeleton) skeleton.style.display = 'none';

        if (data.success) {
            AppState.currentResult = data;
            AppState.resultId = data.result_id;
            displayResults(data);
            showToast('Analiz tamamlandı!', 'success');
        } else {
            showToast(data.error || 'Analiz sırasında hata oluştu.', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Sunucu bağlantı hatası!', 'error');
    } finally {
        showLoading(false);
    }
}

async function batchUpload(files) {
    showLoading(true);

    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file);
    }

    try {
        const response = await fetch('/api/batch-upload', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (data.results && data.results.length > 0) {
            const firstSuccess = data.results.find(r => r.success);
            if (firstSuccess) {
                AppState.currentResult = firstSuccess;
                AppState.resultId = firstSuccess.result_id;
                displayResults(firstSuccess);
            }
            showToast(`${data.total} dosya analiz edildi.`, 'success');
        }
    } catch (error) {
        console.error('Batch upload error:', error);
        showToast('Toplu yükleme hatası!', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// DISPLAY RESULTS
// ============================================
function displayResults(data) {
    DOM.uploadSection.style.display = 'none';
    DOM.resultsSection.classList.add('active');

    renderFileInfoBar(data);
    renderStats(data.metadata);
    renderPreview(data.thumbnail, data.image_url, data.thumbnail_ext);
    renderMetadataTabs(data.metadata);
    renderMap(data.metadata, data.address, data.thumbnail, data.original_name, data.image_url, data.thumbnail_ext);

    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Re-init spotlight for new cards
    setTimeout(() => initSpotlightCards(), 100);
}

// ============================================
// FILE INFO BAR
// ============================================
function renderFileInfoBar(data) {
    const bar = document.getElementById('file-info-bar');
    const fileInfo = data.metadata.file_info || {};

    const fileSize = formatFileSize(fileInfo.file_size || 0);
    const dims = fileInfo.width && fileInfo.height
        ? `${fileInfo.width} × ${fileInfo.height}`
        : '—';

    bar.innerHTML = `
        <div class="file-info-bar__left">
            <div class="file-info-bar__icon">📄</div>
            <div>
                <div class="file-info-bar__name">${escapeHtml(data.original_name)}</div>
                <div class="file-info-bar__meta">${fileSize} · ${dims} · ${fileInfo.format || '—'}</div>
            </div>
        </div>
        <div class="file-info-bar__actions">
            <button class="btn btn--secondary" onclick="exportMetadata('json')" id="export-json-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                JSON
            </button>
            <button class="btn btn--secondary" onclick="exportMetadata('csv')" id="export-csv-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                CSV
            </button>
            <button class="btn btn--new" onclick="resetApp()" id="new-analysis-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Yeni Analiz
            </button>
        </div>
    `;
}

// ============================================
// STATS ROW - With stagger animation
// ============================================
function renderStats(metadata) {
    const container = document.getElementById('stats-row');
    const fileInfo = metadata.file_info || {};
    const camera = metadata.camera || {};
    const settings = metadata.settings || {};
    const gps = metadata.gps || {};
    const datetime = metadata.datetime || {};

    const stats = [
        { icon: '📐', value: fileInfo.width && fileInfo.height ? `${fileInfo.width}×${fileInfo.height}` : '—', label: 'Çözünürlük' },
        { icon: '📷', value: truncate(camera.Make || camera.Model || '—', 14), label: 'Kamera' },
        { icon: '⚙️', value: settings.ISOSpeedRatings || settings.ISO || '—', label: 'ISO' },
        { icon: '🔍', value: settings.FocalLength || settings.FocalLengthIn35mmFilm || '—', label: 'Odak Uzaklığı' },
        { icon: '📅', value: extractDate(datetime), label: 'Çekim Tarihi' },
        { icon: '📍', value: gps.has_location ? '✅ Var' : '❌ Yok', label: 'GPS Verisi' },
    ];

    container.innerHTML = stats.map((s, i) => `
        <div class="stat-card stagger-${i + 1}">
            <div class="stat-card__icon">${s.icon}</div>
            <div class="stat-card__value">${s.value}</div>
            <div class="stat-card__label">${s.label}</div>
        </div>
    `).join('');
}

// ============================================
// PREVIEW
// ============================================
function renderPreview(thumbnailB64, imageUrl, thumbnailExt) {
    const container = document.getElementById('preview-container');
    const mimeType = thumbnailExt === 'png' ? 'image/png' : 'image/jpeg';

    if (thumbnailB64) {
        container.innerHTML = `
            <img src="data:${mimeType};base64,${thumbnailB64}"
                 alt="Fotoğraf önizleme"
                 class="preview-image" />
        `;
    } else if (imageUrl) {
        container.innerHTML = `
            <img src="${imageUrl}"
                 alt="Fotoğraf önizleme"
                 class="preview-image"
                 style="max-height: 350px;" />
        `;
    } else {
        container.innerHTML = `
            <div class="no-gps" style="padding: 24px;">
                <div class="no-gps__icon">🖼️</div>
                <div class="no-gps__title">Önizleme oluşturulamadı</div>
            </div>
        `;
    }
}

// ============================================
// METADATA TABS - With animated underline
// ============================================
function renderMetadataTabs(metadata) {
    const tabsContainer = document.getElementById('metadata-tabs');
    const panelsContainer = document.getElementById('metadata-panels');

    const categories = [
        { key: 'camera', label: 'Kamera', icon: '📷' },
        { key: 'settings', label: 'Ayarlar', icon: '⚙️' },
        { key: 'datetime', label: 'Tarih', icon: '📅' },
        { key: 'image_details', label: 'Görüntü', icon: '🖼️' },
        { key: 'gps_raw', label: 'GPS', icon: '🛰️' },
        { key: 'advanced', label: 'Gelişmiş', icon: '🔬' },
        { key: 'software', label: 'Yazılım', icon: '💻' },
        { key: 'other', label: 'Diğer', icon: '📋' },
    ];

    const activeCats = categories.filter(cat => {
        const data = metadata[cat.key];
        return data && typeof data === 'object' && Object.keys(data).length > 0;
    });

    if (activeCats.length === 0) {
        tabsContainer.innerHTML = '';
        panelsContainer.innerHTML = `
            <div class="no-gps" style="padding: 32px;">
                <div class="no-gps__icon">📭</div>
                <div class="no-gps__title">EXIF Verisi Bulunamadı</div>
                <div class="no-gps__text" style="max-width: 500px; line-height: 1.6; text-align: left; background: rgba(255,255,255,0.05); padding: 16px; border-radius: 8px; margin-top: 16px;">
                    Bu fotoğrafta metadata bilgisi bulunmuyor. Bunun başlıca sebepleri:<br><br>
                    • Fotoğraf <b>WhatsApp, Telegram, Instagram</b> gibi bir uygulama üzerinden gönderilmiş olabilir (bu uygulamalar gizlilik için EXIF verisini siler).<br>
                    • iPhone'dan bilgisayara USB kablo ile atılırken Windows tarafından dönüştürülüp verileri silinmiş olabilir.<br>
                    • Cihaz gizlilik ayarlarından "Konum/Veri Paylaşımı" kapatılmış olabilir.<br><br>
                    <i>Çözüm: Fotoğrafın orijinal halini (hiçbir uygulamadan göndermeden) kablo/bulut aracılığıyla aktarıp tekrar deneyin.</i>
                </div>
            </div>
        `;
        return;
    }

    // Render tabs with count badge
    tabsContainer.innerHTML = activeCats.map((cat, i) => {
        const count = Object.keys(metadata[cat.key]).length;
        return `
            <button class="category-tab ${i === 0 ? 'active' : ''}"
                    onclick="switchTab('${cat.key}', this)"
                    id="tab-${cat.key}">
                ${cat.icon} ${cat.label}
                <span style="
                    font-size: 0.6rem;
                    opacity: 0.6;
                    margin-left: 2px;
                    font-family: var(--font-mono);
                ">${count}</span>
            </button>
        `;
    }).join('');

    // Render panels
    panelsContainer.innerHTML = activeCats.map((cat, i) => {
        const fields = metadata[cat.key];
        const rows = Object.entries(fields).map(([key, val]) => `
            <tr>
                <th>${formatFieldName(key)}</th>
                <td>${escapeHtml(String(val))}</td>
            </tr>
        `).join('');

        return `
            <div class="category-panel ${i === 0 ? 'active' : ''}" id="panel-${cat.key}">
                <table class="metadata-table">
                    ${rows}
                </table>
            </div>
        `;
    }).join('');
}

function switchTab(key, btn) {
    document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');

    document.querySelectorAll('.category-panel').forEach(p => p.classList.remove('active'));
    const panel = document.getElementById(`panel-${key}`);
    if (panel) panel.classList.add('active');
}

// ============================================
// MAP - Dark themed Leaflet
// ============================================
function renderMap(metadata, address, thumbnailB64, fileName, imageUrl, thumbnailExt) {
    const mapSection = document.getElementById('map-section');
    const gps = metadata.gps || {};

    if (!gps.has_location) {
        mapSection.innerHTML = `
            <div class="card">
                <div class="card__header">
                    <span class="card__header-icon">🗺️</span>
                    <span class="card__header-title">Coğrafi Konum</span>
                </div>
                <div class="card__body">
                    <div class="no-gps">
                        <div class="no-gps__icon">📍</div>
                        <div class="no-gps__title">GPS Verisi Bulunamadı</div>
                        <div class="no-gps__text" style="max-width: 500px; text-align: left; background: rgba(255,255,255,0.05); padding: 16px; border-radius: 8px; margin-top: 16px;">
                            Bu fotoğrafta konum bilgisi bulunmuyor.<br><br>
                            Eğer bu fotoğrafı kendi telefonunuzla çektiyseniz:<br>
                            1. Telefonunuzun kamera ayarlarından "Konum Etiketleri"nin açık olduğundan emin olun.<br>
                            2. Fotoğrafı WhatsApp/Telegram gibi uygulamalar üzerinden <b>göndermediğinizden</b> (veya indirmediğinizden) emin olun. Orijinal dosyayı yükleyin.
                        </div>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    const lat = gps.latitude;
    const lon = gps.longitude;

    mapSection.innerHTML = `
        <div class="card">
            <div class="card__header">
                <span class="card__header-icon">🗺️</span>
                <span class="card__header-title">Coğrafi Konum</span>
                <span class="card__header-badge">GPS</span>
            </div>
            <div class="card__body" style="padding: 0;">
                <div class="map-container">
                    <div id="map"></div>
                </div>
            </div>
        </div>
        <div class="map-controls">
            <div class="coordinate-display">
                <div class="coord-chip">
                    <span class="coord-chip__label">Enlem</span>
                    ${lat.toFixed(6)}°
                </div>
                <div class="coord-chip">
                    <span class="coord-chip__label">Boylam</span>
                    ${lon.toFixed(6)}°
                </div>
                ${gps.altitude !== null && gps.altitude !== undefined ? `
                <div class="coord-chip">
                    <span class="coord-chip__label">Yükseklik</span>
                    ${gps.altitude} m
                </div>` : ''}
                ${gps.formatted_dms ? `
                <div class="coord-chip">
                    <span class="coord-chip__label">DMS</span>
                    ${gps.formatted_dms}
                </div>` : ''}
            </div>
        </div>
        ${address && address.success ? `
        <div class="address-card">
            <div class="address-card__title">📍 Adres Bilgisi</div>
            <div class="address-card__text">${escapeHtml(address.full_address)}</div>
        </div>` : ''}
    `;

    setTimeout(() => initMap(lat, lon, thumbnailB64, fileName, imageUrl, thumbnailExt), 100);
}

function initMap(lat, lon, thumbnailB64, fileName, imageUrl, thumbnailExt) {
    if (AppState.map) {
        AppState.map.remove();
        AppState.map = null;
    }

    const map = L.map('map', {
        zoomControl: true,
        attributionControl: true,
    }).setView([lat, lon], 14);

    // Map layers
    const darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© CartoDB',
        maxZoom: 19,
    });

    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
        maxZoom: 19,
    });

    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: '© Esri',
        maxZoom: 18,
    });

    darkLayer.addTo(map);

    const baseLayers = {
        '🌑 Koyu': darkLayer,
        '🗺️ Standart': osmLayer,
        '🛰️ Uydu': satelliteLayer,
    };
    L.control.layers(baseLayers).addTo(map);

    // Custom marker
    const markerIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
            width: 32px; height: 32px;
            background: linear-gradient(135deg, #7c6aff, #5b4dd4);
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px 20px rgba(124, 106, 255, 0.5);
            border: 2px solid rgba(255,255,255,0.9);
            animation: markerPulse 2s ease-in-out infinite;
        "><span style="transform: rotate(45deg); font-size: 14px;">📍</span></div>
        <style>
            @keyframes markerPulse {
                0%, 100% { box-shadow: 0 4px 20px rgba(124, 106, 255, 0.5); }
                50% { box-shadow: 0 4px 30px rgba(124, 106, 255, 0.8); }
            }
        </style>`,
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32],
    });

    // Popup
    const mimeType = thumbnailExt === 'png' ? 'image/png' : 'image/jpeg';
    let popupContent = `<div style="text-align: center;">`;
    if (thumbnailB64) {
        popupContent += `<img src="data:${mimeType};base64,${thumbnailB64}" class="popup-thumb" />`;
    } else if (imageUrl) {
        popupContent += `<img src="${imageUrl}" class="popup-thumb" style="max-width:150px;" />`;
    }
    popupContent += `
        <div class="popup-filename">${escapeHtml(fileName || 'Fotoğraf')}</div>
        <div class="popup-coords">${lat.toFixed(6)}, ${lon.toFixed(6)}</div>
    </div>`;

    const marker = L.marker([lat, lon], { icon: markerIcon })
        .addTo(map)
        .bindPopup(popupContent);

    // Animated glow circle
    L.circle([lat, lon], {
        radius: 120,
        color: '#7c6aff',
        fillColor: '#7c6aff',
        fillOpacity: 0.06,
        weight: 1,
        opacity: 0.3,
    }).addTo(map);

    AppState.map = map;
    AppState.markers = [marker];

    setTimeout(() => map.invalidateSize(), 200);
}

// ============================================
// EXPORT with Download Toast
// ============================================
function exportMetadata(format) {
    if (!AppState.resultId) {
        showToast('Dışa aktarılacak veri yok!', 'error');
        return;
    }

    const url = `/api/export/${AppState.resultId}/${format}`;
    window.open(url, '_blank');
    showToast(`${format.toUpperCase()} dosyası indiriliyor...`, 'info');
}

// ============================================
// RESET
// ============================================
function resetApp() {
    AppState.currentResult = null;
    AppState.resultId = null;

    if (AppState.map) {
        AppState.map.remove();
        AppState.map = null;
    }
    AppState.markers = [];

    DOM.resultsSection.classList.remove('active');
    DOM.uploadSection.style.display = 'block';
    DOM.fileInput.value = '';

    document.getElementById('file-info-bar').innerHTML = '';
    document.getElementById('stats-row').innerHTML = '';
    document.getElementById('preview-container').innerHTML = '';
    document.getElementById('metadata-tabs').innerHTML = '';
    document.getElementById('metadata-panels').innerHTML = '';
    document.getElementById('map-section').innerHTML = '';
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
function showLoading(show) {
    if (show) {
        DOM.loadingOverlay.classList.add('active');
    } else {
        DOM.loadingOverlay.classList.remove('active');
    }
}

function showToast(message, type = 'info') {
    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.style.position = 'relative';
    toast.innerHTML = `<span style="font-weight:700;">${icons[type] || 'ℹ'}</span> ${escapeHtml(message)}`;
    DOM.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(80px) scale(0.95)';
        toast.style.transition = '0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i];
}

function formatFieldName(name) {
    return name
        .replace(/([A-Z])/g, ' $1')
        .replace(/_/g, ' ')
        .replace(/EXIF\s?/gi, '')
        .replace(/Image\s?/gi, '')
        .trim();
}

function truncate(str, maxLen) {
    if (!str || str === '—') return '—';
    return str.length > maxLen ? str.substring(0, maxLen) + '…' : str;
}

function extractDate(datetime) {
    if (!datetime) return '—';
    const dateStr = datetime.DateTimeOriginal || datetime.DateTime || datetime.DateTimeDigitized || '';
    if (!dateStr) return '—';
    const match = dateStr.match(/(\d{4})[:\-/](\d{2})[:\-/](\d{2})/);
    if (match) return `${match[1]}-${match[2]}-${match[3]}`;
    return truncate(dateStr, 12);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
