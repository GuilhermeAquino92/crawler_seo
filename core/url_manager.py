# core/url_manager.py - Gerenciamento e normalização de URLs

from urllib.parse import urlparse, urljoin, urlunparse
from collections import deque
import re
from config.settings import (
    ECOMMERCE_PATTERNS, EXCLUDED_EXTENSIONS, TECHNICAL_PATTERNS, 
    PROBLEMATIC_PARAMS
)


class URLManager:
    """🔗 Gerenciador de URLs com filtros inteligentes"""
    
    def __init__(self, base_domain=None, config=None):
        self.base_domain = base_domain
        self.config = config or {}
        
        # Controle de URLs
        self.processed_urls = set()
        self.urls_to_process = deque()
        self.filtered_urls = []
        
        # Estatísticas
        self.stats = {
            'total_found': 0,
            'total_processed': 0,
            'total_filtered': 0,
            'filtered_by_reason': {}
        }
    
    def set_base_domain(self, url):
        """Define domínio base a partir de uma URL"""
        self.base_domain = urlparse(url).netloc
    
    def normalize_url(self, url, base_url=None):
        """🔧 Normaliza URL - VERSÃO MELHORADA"""
        if not url:
            return None
        
        try:
            url = url.strip()
            
            # Se não for absoluta, torna absoluta
            if base_url:
                url = urljoin(base_url, url)
            
            parsed = urlparse(url)
            
            # Verifica esquema
            if parsed.scheme not in ['http', 'https']:
                return None
            
            # Verifica domínio (se definido)
            if self.base_domain and parsed.netloc != self.base_domain:
                return None
            
            # Remove fragmento
            clean_parsed = parsed._replace(fragment='')
            
            # Normaliza path (remove barras duplas, etc.)
            path = re.sub(r'/+', '/', clean_parsed.path)
            if path != '/' and path.endswith('/'):
                path = path.rstrip('/')
            
            clean_parsed = clean_parsed._replace(path=path)
            
            # Reconstrói URL
            clean_url = urlunparse(clean_parsed)
            
            return clean_url
            
        except Exception as e:
            self._log_filter('INVALID_URL', url, f'Erro na normalização: {str(e)}')
            return None
    
    def is_url_relevant(self, url):
        """🔧 Verifica se URL é relevante para SEO - VERSÃO MELHORADA"""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # 🚫 FILTROS DE E-COMMERCE
        for pattern in ECOMMERCE_PATTERNS:
            if pattern in url_lower:
                self._log_filter('ECOMMERCE', url, f'Padrão e-commerce: {pattern}')
                return False
        
        # 🚫 EXTENSÕES DE ARQUIVOS
        for ext in EXCLUDED_EXTENSIONS:
            if url_lower.endswith(ext):
                self._log_filter('FILE_EXTENSION', url, f'Extensão: {ext}')
                return False
        
        # 🚫 PADRÕES TÉCNICOS
        for pattern in TECHNICAL_PATTERNS:
            if pattern in url_lower:
                self._log_filter('TECHNICAL', url, f'Padrão técnico: {pattern}')
                return False
        
        # 🚫 PARÂMETROS PROBLEMÁTICOS
        for param in PROBLEMATIC_PARAMS:
            if param in url_lower:
                self._log_filter('PROBLEMATIC_PARAM', url, f'Parâmetro: {param}')
                return False
        
        # ✅ URL aprovada
        return True
    
    def add_url(self, url, depth=0, base_url=None):
        """Adiciona URL à fila de processamento"""
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
        """Retorna próxima URL da fila"""
        if self.urls_to_process:
            url, depth = self.urls_to_process.popleft()
            self.processed_urls.add(url)
            self.stats['total_processed'] += 1
            return url, depth
        return None, None
    
    def has_urls_to_process(self):
        """Verifica se há URLs para processar"""
        return len(self.urls_to_process) > 0
    
    def mark_as_processed(self, url):
        """Marca URL como processada"""
        self.processed_urls.add(url)
    
    def is_processed(self, url):
        """Verifica se URL já foi processada"""
        return url in self.processed_urls
    
    def get_queue_size(self):
        """Retorna tamanho da fila"""
        return len(self.urls_to_process)
    
    def get_processed_count(self):
        """Retorna quantidade de URLs processadas"""
        return len(self.processed_urls)
    
    def _log_filter(self, reason, url, details):
        """Registra URL filtrada"""
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
        """Retorna estatísticas completas"""
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
        """Retorna URLs filtradas, opcionalmente por motivo"""
        if reason:
            return [f for f in self.filtered_urls if f['reason'] == reason]
        return self.filtered_urls.copy()
    
    def clear_queue(self):
        """Limpa fila de URLs"""
        self.urls_to_process.clear()
    
    def reset(self):
        """Reseta completamente o gerenciador"""
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
    """🧠 Gerenciador inteligente com priorização"""
    
    def __init__(self, base_domain=None, config=None):
        super().__init__(base_domain, config)
        self.priority_patterns = config.get('priority_patterns', []) if config else []
        self.priority_queue = deque()
        self.normal_queue = deque()
    
    def add_url(self, url, depth=0, base_url=None, priority=False):
        """Adiciona URL com priorização"""
        normalized_url = self.normalize_url(url, base_url)
        
        if not normalized_url:
            return False
        
        if normalized_url in self.processed_urls:
            return False
        
        if not self.is_url_relevant(normalized_url):
            return False
        
        # Determina prioridade automaticamente se não especificada
        if not priority and self.priority_patterns:
            priority = any(pattern in normalized_url.lower() 
                          for pattern in self.priority_patterns)
        
        # Adiciona à fila apropriada
        if priority:
            self.priority_queue.append((normalized_url, depth))
        else:
            self.normal_queue.append((normalized_url, depth))
        
        self.stats['total_found'] += 1
        return True
    
    def get_next_url(self):
        """Retorna próxima URL priorizando fila de alta prioridade"""
        # Primeiro verifica fila de prioridade
        if self.priority_queue:
            url, depth = self.priority_queue.popleft()
            self.processed_urls.add(url)
            self.stats['total_processed'] += 1
            return url, depth
        
        # Depois fila normal
        if self.normal_queue:
            url, depth = self.normal_queue.popleft()
            self.processed_urls.add(url)
            self.stats['total_processed'] += 1
            return url, depth
        
        return None, None
    
    def has_urls_to_process(self):
        """Verifica se há URLs para processar"""
        return len(self.priority_queue) > 0 or len(self.normal_queue) > 0
    
    def get_queue_size(self):
        """Retorna tamanho total das filas"""
        return len(self.priority_queue) + len(self.normal_queue)
    
    def get_queue_breakdown(self):
        """Retorna breakdown das filas"""
        return {
            'priority_queue': len(self.priority_queue),
            'normal_queue': len(self.normal_queue),
            'total_queue': len(self.priority_queue) + len(self.normal_queue)
        }
    
    def clear_queue(self):
        """Limpa todas as filas"""
        self.priority_queue.clear()
        self.normal_queue.clear()
    
    def reset(self):
        """Reseta completamente incluindo filas prioritárias"""
        super().reset()
        self.priority_queue.clear()
        self.normal_queue.clear()


class BatchURLManager(URLManager):
    """📦 Gerenciador com processamento em lotes"""
    
    def __init__(self, base_domain=None, config=None, batch_size=20):
        super().__init__(base_domain, config)
        self.batch_size = batch_size
        self.current_batch = []
    
    def get_next_batch(self):
        """Retorna próximo lote de URLs"""
        batch = []
        
        while len(batch) < self.batch_size and self.has_urls_to_process():
            url, depth = self.get_next_url()
            if url:
                batch.append((url, depth))
        
        return batch
    
    def has_full_batch(self):
        """Verifica se há URLs suficientes para um lote completo"""
        return len(self.urls_to_process) >= self.batch_size


# ========================
# 🏭 FACTORY FUNCTIONS
# ========================

def create_url_manager(manager_type='default', base_domain=None, config=None):
    """🏭 Factory para criar gerenciadores de URL"""
    
    if manager_type == 'smart':
        return SmartURLManager(base_domain, config)
    
    elif manager_type == 'batch':
        batch_size = config.get('batch_size', 20) if config else 20
        return BatchURLManager(base_domain, config, batch_size)
    
    else:  # default
        return URLManager(base_domain, config)


# ========================
# 🧪 FUNÇÕES DE TESTE
# ========================

def test_url_manager():
    """Testa o gerenciador de URLs"""
    print("🧪 Testando URLManager...")
    
    manager = URLManager()
    manager.set_base_domain("https://example.com/")
    
    # URLs de teste
    test_urls = [
        "https://example.com/page1",
        "https://example.com/page2/",
        "https://example.com/page1",  # Duplicada
        "https://example.com/checkout/cart/add/123",  # E-commerce
        "https://example.com/style.css",  # CSS
        "https://other-domain.com/page",  # Outro domínio
        "javascript:void(0)",  # JavaScript
        "https://example.com/normal-page"
    ]
    
    print(f"📝 Testando {len(test_urls)} URLs...")
    
    for url in test_urls:
        result = manager.add_url(url)
        print(f"  {url} -> {'✅' if result else '❌'}")
    
    print(f"\n📊 Estatísticas:")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n🚫 URLs filtradas:")
    filtered = manager.get_filtered_urls()
    for f in filtered[:3]:  # Mostra apenas as primeiras 3
        print(f"  {f['url']} - {f['reason']}: {f['details']}")


def test_smart_url_manager():
    """Testa o gerenciador inteligente"""
    print("\n🧠 Testando SmartURLManager...")
    
    config = {
        'priority_patterns': ['/important/', '/product/', '/category/']
    }
    
    manager = SmartURLManager("example.com", config)
    
    urls = [
        "https://example.com/page1",
        "https://example.com/important/page",  # Prioridade
        "https://example.com/product/123",     # Prioridade
        "https://example.com/normal-page"
    ]
    
    for url in urls:
        manager.add_url(url)
    
    print("📦 Breakdown das filas:")
    breakdown = manager.get_queue_breakdown()
    for key, value in breakdown.items():
        print(f"  {key}: {value}")
    
    print("\n🔄 Processando URLs (ordem de prioridade):")
    while manager.has_urls_to_process():
        url, depth = manager.get_next_url()
        if url:
            print(f"  Processando: {url}")


if __name__ == "__main__":
    test_url_manager()
    test_smart_url_manager()