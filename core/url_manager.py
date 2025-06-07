from urllib.parse import urlparse, urljoin, urlunparse
from collections import deque
import re


class URLManager:
    
    def __init__(self, base_domain=None, config=None):
        self.base_domain = base_domain
        self.config = config or {}
        
        self.processed_urls = set()
        self.urls_to_process = deque()
        self.filtered_urls = []
        
        self.stats = {
            'total_found': 0,
            'total_processed': 0,
            'total_filtered': 0,
            'filtered_by_reason': {}
        }
    
    def set_base_domain(self, url):
        self.base_domain = urlparse(url).netloc
    
    def normalize_url(self, url, base_url=None):
        if not url:
            return None
        
        try:
            url = url.strip()
            
            if base_url:
                url = urljoin(base_url, url)
            
            parsed = urlparse(url)
            
            if parsed.scheme not in ['http', 'https']:
                return None
            
            if self.base_domain and parsed.netloc != self.base_domain:
                return None
            
            clean_parsed = parsed._replace(fragment='')
            
            url_limpa = f"{clean_parsed.scheme}://{clean_parsed.netloc}{clean_parsed.path}"
            if clean_parsed.query:
                url_limpa += f"?{clean_parsed.query}"
            
            if url_limpa.endswith('/') and url_limpa.count('/') > 3:
                url_limpa = url_limpa.rstrip('/')
            
            return url_limpa
            
        except Exception as e:
            self._log_filter('INVALID_URL', url, f'Erro na normalização: {str(e)}')
            return None
    
    def is_url_relevant(self, url):
        if not url:
            return False
        
        url_lower = url.lower()
        
        padroes_ecommerce_bloquear = [
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
        
        for padrao in padroes_ecommerce_bloquear:
            if padrao in url_lower:
                self._log_filter('ECOMMERCE_ENDPOINT', url, f'E-commerce endpoint: {padrao}')
                return False
        
        extensoes_excluir = {
            '.js', '.css', '.json', '.xml', '.txt', '.ico',
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.zip', '.rar', '.7z', '.mp3', '.mp4', '.avi',
            '.woff', '.woff2', '.ttf', '.eot', '.map'
        }
        
        for ext in extensoes_excluir:
            if url_lower.endswith(ext):
                self._log_filter('FILE_EXTENSION', url, f'Extensão de arquivo: {ext}')
                return False
        
        padroes_tecnicos_bloquear = [
            '/wp-content/uploads/', '/wp-content/themes/', '/wp-content/plugins/',
            '/wp-includes/', '/wp-admin/', '/wp-json/',
            '/assets/', '/static/', '/media/', '/images/',
            '/node_modules/', '/vendor/', '/_next/', '/dist/',
            '/api/', '/ajax/', '/cron/', '/cache/',
            'google-analytics', 'googleapis.com', 'facebook.com',
            'cloudflare', 'jquery', 'bootstrap', 'fontawesome'
        ]
        
        for padrao in padroes_tecnicos_bloquear:
            if padrao in url_lower:
                self._log_filter('TECHNICAL_PATTERN', url, f'Padrão técnico: {padrao}')
                return False
        
        parametros_bloquear = [
            'SID=',
            'PHPSESSID=',
            'utm_',
            'gclid=',
            'fbclid=',
        ]
        
        for param in parametros_bloquear:
            if param in url_lower:
                self._log_filter('PROBLEMATIC_PARAM', url, f'Parâmetro problemático: {param}')
                return False
        
        return True
    
    def add_url(self, url, depth=0, base_url=None):
        normalized_url = self.normalize_url(url, base_url)
        
        if not normalized_url:
            return False
        
        if normalized_url in self.processed_urls:
            return False
        
        if not self.is_url_relevant(normalized_url):
            return False
        
        self.urls_to_process.append((normalized_url, depth))
        self.stats['total_found'] += 1
        return True
    
    def get_next_url(self):
        if self.urls_to_process:
            url, depth = self.urls_to_process.popleft()
            self.processed_urls.add(url)
            self.stats['total_processed'] += 1
            return url, depth
        return None, None
    
    def has_urls_to_process(self):
        return len(self.urls_to_process) > 0
    
    def mark_as_processed(self, url):
        self.processed_urls.add(url)
    
    def is_processed(self, url):
        return url in self.processed_urls
    
    def get_queue_size(self):
        return len(self.urls_to_process)
    
    def get_processed_count(self):
        return len(self.processed_urls)
    
    def _log_filter(self, reason, url, details):
        self.stats['total_filtered'] += 1
        
        if reason not in self.stats['filtered_by_reason']:
            self.stats['filtered_by_reason'][reason] = 0
        self.stats['filtered_by_reason'][reason] += 1
        
        self.filtered_urls.append({
            'url': url,
            'reason': reason,
            'details': details
        })
    
    def get_stats(self):
        return {
            'urls_found': self.stats['total_found'],
            'urls_processed': self.stats['total_processed'],
            'urls_filtered': self.stats['total_filtered'],
            'urls_in_queue': len(self.urls_to_process),
            'filter_breakdown': self.stats['filtered_by_reason'].copy(),
            'processing_rate': (
                self.stats['total_processed'] / max(self.stats['total_found'], 1) * 100
            )
        }
    
    def get_filtered_urls(self, reason=None):
        if reason:
            return [f for f in self.filtered_urls if f['reason'] == reason]
        return self.filtered_urls.copy()
    
    def clear_queue(self):
        self.urls_to_process.clear()
    
    def reset(self):
        self.processed_urls.clear()
        self.urls_to_process.clear()
        self.filtered_urls.clear()
        self.stats = {
            'total_found': 0,
            'total_processed': 0,
            'total_filtered': 0,
            'filtered_by_reason': {}
        }


class SmartURLManager(URLManager):
    
    def __init__(self, base_domain=None, config=None):
        super().__init__(base_domain, config)
        self.priority_patterns = config.get('priority_patterns', []) if config else []
        self.priority_queue = deque()
        self.normal_queue = deque()
    
    def add_url(self, url, depth=0, base_url=None, priority=False):
        normalized_url = self.normalize_url(url, base_url)
        
        if not normalized_url:
            return False
        
        if normalized_url in self.processed_urls:
            return False
        
        if not self.is_url_relevant(normalized_url):
            return False
        
        if not priority and self.priority_patterns:
            priority = any(pattern in normalized_url.lower() 
                          for pattern in self.priority_patterns)
        
        if priority:
            self.priority_queue.append((normalized_url, depth))
        else:
            self.normal_queue.append((normalized_url, depth))
        
        self.stats['total_found'] += 1
        return True
    
    def get_next_url(self):
        if self.priority_queue:
            url, depth = self.priority_queue.popleft()
            self.processed_urls.add(url)
            self.stats['total_processed'] += 1
            return url, depth
        
        if self.normal_queue:
            url, depth = self.normal_queue.popleft()
            self.processed_urls.add(url)
            self.stats['total_processed'] += 1
            return url, depth
        
        return None, None
    
    def has_urls_to_process(self):
        return len(self.priority_queue) > 0 or len(self.normal_queue) > 0
    
    def get_queue_size(self):
        return len(self.priority_queue) + len(self.normal_queue)
    
    def get_queue_breakdown(self):
        return {
            'priority_queue': len(self.priority_queue),
            'normal_queue': len(self.normal_queue),
            'total_queue': len(self.priority_queue) + len(self.normal_queue)
        }
    
    def clear_queue(self):
        self.priority_queue.clear()
        self.normal_queue.clear()
    
    def reset(self):
        super().reset()
        self.priority_queue.clear()
        self.normal_queue.clear()


class BatchURLManager(URLManager):
    
    def __init__(self, base_domain=None, config=None, batch_size=20):
        super().__init__(base_domain, config)
        self.batch_size = batch_size
        self.current_batch = []
    
    def get_next_batch(self):
        batch = []
        
        while len(batch) < self.batch_size and self.has_urls_to_process():
            url, depth = self.get_next_url()
            if url:
                batch.append((url, depth))
        
        return batch
    
    def has_full_batch(self):
        return len(self.urls_to_process) >= self.batch_size


def create_url_manager(manager_type='default', base_domain=None, config=None):
    
    if manager_type == 'smart':
        return SmartURLManager(base_domain, config)
    
    elif manager_type == 'batch':
        batch_size = config.get('batch_size', 20) if config else 20
        return BatchURLManager(base_domain, config, batch_size)
    
    else:
        return URLManager(base_domain, config)


def test_url_manager():
    print("Testando URLManager...")
    
    manager = URLManager()
    manager.set_base_domain("https://example.com/")
    
    test_urls = [
        "https://example.com/page1",
        "https://example.com/page2/",
        "https://example.com/page1",
        "https://example.com/checkout/cart/add/123",
        "https://example.com/style.css",
        "https://other-domain.com/page",
        "javascript:void(0)",
        "https://example.com/normal-page"
    ]
    
    print(f"Testando {len(test_urls)} URLs...")
    
    for url in test_urls:
        result = manager.add_url(url)
        print(f"  {url} -> {'OK' if result else 'FILTRADA'}")
    
    print(f"\nEstatísticas:")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nURLs filtradas:")
    filtered = manager.get_filtered_urls()
    for f in filtered[:3]:
        print(f"  {f['url']} - {f['reason']}: {f['details']}")


def test_smart_url_manager():
    print("\nTestando SmartURLManager...")
    
    config = {
        'priority_patterns': ['/important/', '/product/', '/category/']
    }
    
    manager = SmartURLManager("example.com", config)
    
    urls = [
        "https://example.com/page1",
        "https://example.com/important/page",
        "https://example.com/product/123",
        "https://example.com/normal-page"
    ]
    
    for url in urls:
        manager.add_url(url)
    
    print("Breakdown das filas:")
    breakdown = manager.get_queue_breakdown()
    for key, value in breakdown.items():
        print(f"  {key}: {value}")
    
    print("\nProcessando URLs (ordem de prioridade):")
    while manager.has_urls_to_process():
        url, depth = manager.get_next_url()
        if url:
            print(f"  Processando: {url}")


if __name__ == "__main__":
    test_url_manager()
    test_smart_url_manager()