# config/settings.py - Configurações centralizadas

import os

# ========================
# 🚀 CONFIGURAÇÕES PRINCIPAIS
# ========================

# URLs e Crawling
DEFAULT_URL = "https://alastin.com.br/"
MAX_URLS_DEFAULT = 1000
MAX_DEPTH_DEFAULT = 5
MAX_THREADS_DEFAULT = 20

# Timeouts e Delays
REQUEST_TIMEOUT = 15
CONNECTION_TIMEOUT = 10
READ_TIMEOUT = 30

# Pastas
OUTPUT_FOLDER = "output"
LOGS_FOLDER = "logs"

# User Agent e Headers
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

DEFAULT_HEADERS = {
    'User-Agent': DEFAULT_USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# ========================
# 🔧 CONFIGURAÇÕES DE ANÁLISE
# ========================

# Metatags - Limites de Caracteres
TITLE_MIN_LENGTH = 30
TITLE_MAX_LENGTH = 60
DESCRIPTION_MIN_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 160

# Scores
SCORE_TITLE_OK = 30
SCORE_DESCRIPTION_OK = 25
SCORE_H1_OK = 20
SCORE_MOBILE_OPTIMIZED = 15
SCORE_OPEN_GRAPH = 10
SCORE_STRUCTURED_DATA = 5

# Penalizações
PENALTY_DUPLICATE_TITLE = 10
PENALTY_DUPLICATE_DESCRIPTION = 10
PENALTY_H1_CRITICAL = 10
PENALTY_H1_PROBLEMATIC = 3
PENALTY_INCORRECT_HIERARCHY = 15

# ========================
# 🚫 FILTROS DE URL
# ========================

# Padrões de e-commerce para bloquear
ECOMMERCE_PATTERNS = [
    '/checkout/cart/add/',
    '/checkout/cart/',
    '/customer/account/',
    '/customer/section/load/',
    '/wishlist/index/add/',
    '/review/product/post/',
    '/newsletter/subscriber/',
    '/sales/order/',
    '/downloadable/download/',
    '/paypal/',
    '/rest/V1/',
    '/graphql',
    '/admin/',
]

# Extensões de arquivos para excluir
EXCLUDED_EXTENSIONS = {
    '.js', '.css', '.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg',
    '.pdf', '.zip', '.mp3', '.mp4', '.woff', '.woff2', '.ttf',
    '.json', '.xml', '.txt', '.bmp', '.webp', '.avi', '.map'
}

# Padrões técnicos para bloquear
TECHNICAL_PATTERNS = [
    '/wp-content/uploads/', '/wp-content/themes/', '/wp-content/plugins/',
    '/wp-includes/', '/wp-admin/', '/wp-json/',
    '/assets/', '/static/', '/media/', '/images/',
    '/node_modules/', '/vendor/', '/_next/', '/dist/',
    '/api/', '/ajax/', '/cron/', '/cache/',
    'google-analytics', 'googleapis.com', 'facebook.com',
    'cloudflare', 'jquery', 'bootstrap', 'fontawesome'
]

# Parâmetros problemáticos
PROBLEMATIC_PARAMS = [
    'SID=', 'PHPSESSID=', 'utm_', 'gclid=', 'fbclid='
]

# ========================
# 🔍 DETECÇÃO DE HEADINGS OCULTOS
# ========================

# Classes CSS que indicam elementos ocultos
HIDDEN_CSS_CLASSES = [
    'hidden', 'hide', 'invisible', 'sr-only', 'screen-reader',
    'visually-hidden', 'off-screen', 'text-hide', 'visuallyhidden'
]

# Cores invisíveis
INVISIBLE_COLORS = [
    'color:white', 'color: white', 'color:#fff', 'color: #fff',
    'color:#ffffff', 'color: #ffffff', 'color:transparent',
    'color: transparent', 'color:rgba(0,0,0,0)', 'color: rgba(0,0,0,0)',
    'color:rgba(255,255,255,0)', 'color: rgba(255,255,255,0)'
]

# Estilos que indicam elementos ocultos
HIDDEN_STYLES = [
    'display:none', 'display: none',
    'visibility:hidden', 'visibility: hidden',
    'opacity:0', 'opacity: 0',
    'font-size:0', 'font-size: 0'
]

# Posicionamentos suspeitos
SUSPICIOUS_POSITIONING = [
    'text-indent:-', 'left:-', 'top:-',
    'position:absolute', 'clip:rect'
]

# ========================
# 📊 CONFIGURAÇÕES DE RELATÓRIOS
# ========================

# Formato de timestamp para arquivos
TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'

# Configurações do Excel
EXCEL_ENGINE = 'xlsxwriter'

# Cores para formatação
EXCEL_COLORS = {
    'header_bg': '#4472C4',
    'header_font': 'white',
    'success': '#00B050',
    'warning': '#FFC000',
    'error': '#FF0000'
}

# Larguras de colunas
COLUMN_WIDTHS = {
    'url': 70,
    'title': 50,
    'description': 60,
    'problems_detailed': 60,
    'sequence': 40,
    'standard': 15,
    'counter': 12
}

# ========================
# 🎯 CONFIGURAÇÕES AVANÇADAS
# ========================

# Limite de RGB para cores claras (próximas ao branco)
RGB_LIGHT_THRESHOLD = 250

# Configuração de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': ['console', 'file']
}

# Status HTTP críticos
CRITICAL_HTTP_STATUS = [404, 500, 502, 503, 504]
WARNING_HTTP_STATUS = [301, 302, 403]

# ========================
# 🔧 CONFIGURAÇÃO COMPLETA
# ========================

DEFAULT_CONFIG = {
    'crawler': {
        'max_urls': MAX_URLS_DEFAULT,
        'max_depth': MAX_DEPTH_DEFAULT,
        'max_threads': MAX_THREADS_DEFAULT,
        'timeout': REQUEST_TIMEOUT,
        'headers': DEFAULT_HEADERS
    },
    'analysis': {
        'title_limits': (TITLE_MIN_LENGTH, TITLE_MAX_LENGTH),
        'description_limits': (DESCRIPTION_MIN_LENGTH, DESCRIPTION_MAX_LENGTH),
        'detect_invisible_colors': True,
        'consolidate_headings': True,
        'differentiate_gravity': True
    },
    'filters': {
        'ecommerce_patterns': ECOMMERCE_PATTERNS,
        'excluded_extensions': EXCLUDED_EXTENSIONS,
        'technical_patterns': TECHNICAL_PATTERNS,
        'problematic_params': PROBLEMATIC_PARAMS
    },
    'output': {
        'folder': OUTPUT_FOLDER,
        'timestamp_format': TIMESTAMP_FORMAT,
        'excel_engine': EXCEL_ENGINE
    },
    'logging': LOGGING_CONFIG
}

# ========================
# 🚀 FUNÇÕES AUXILIARES
# ========================

def create_output_folders():
    """Cria pastas de saída necessárias"""
    import os
    folders = [OUTPUT_FOLDER, LOGS_FOLDER]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def get_config():
    """Retorna configuração padrão"""
    create_output_folders()
    return DEFAULT_CONFIG.copy()

def update_config(custom_config):
    """Atualiza configuração com valores customizados"""
    config = get_config()
    
    def deep_update(base_dict, update_dict):
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    deep_update(config, custom_config)
    return config