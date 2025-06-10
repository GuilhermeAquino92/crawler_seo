from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode
from collections import deque
import re
import hashlib


class URLManager:
    
    def __init__(self, base_domain=None, config=None):
        self.base_domain = base_domain
        self.config = config or {}
        
        # 🔥 CORREÇÃO: Conjuntos para deduplicação
        self.processed_urls = set()           # URLs já processadas
        self.normalized_urls = set()          # URLs normalizadas para deduplicação
        self.url_hashes = set()               # Hashes de URLs para detecção extra
        
        self.urls_to_process = deque()
        self.filtered_urls = []
        
        self.stats = {
            'total_found': 0,
            'total_processed': 0,
            'total_filtered': 0,
            'total_duplicates': 0,               # 🆕 Estatística de duplicados
            'filtered_by_reason': {}
        }
    
    def set_base_domain(self, url):
        """Define o domínio base a partir de uma URL"""
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        self.base_domain = domain
    
    def normalize_url(self, url, base_url=None):
        """🔥 CORREÇÃO: Normalização robusta anti-duplicação"""
        if not url:
            return None
        
        try:
            url = url.strip()
            
            # Resolve URL relativa
            if base_url:
                url = urljoin(base_url, url)
            
            parsed = urlparse(url)

            # Validações básicas
            if parsed.scheme not in ['http', 'https']:
                return None

            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            if self.base_domain and domain != self.base_domain:
                return None
            
            # 🔥 NORMALIZAÇÃO ANTI-DUPLICAÇÃO
            normalized_url = self._deep_normalize_url(parsed)
            
            return normalized_url
            
        except Exception as e:
            self._log_filter('INVALID_URL', url, f'Erro na normalização: {str(e)}')
            return None
    
    def _deep_normalize_url(self, parsed):
        """🔥 Normalização profunda para evitar duplicados"""
        
        # 1. Remove fragment (anchor)
        parsed = parsed._replace(fragment='')
        
        # 2. Normaliza path
        path = parsed.path
        
        # Remove trailing slash duplo
        path = re.sub(r'/+', '/', path)
        
        # Remove trailing slash se não for root
        if path.endswith('/') and len(path) > 1:
            path = path.rstrip('/')
        
        # Se path vazio, garante que seja /
        if not path:
            path = '/'
        
        # 3. Normaliza query parameters
        query = self._normalize_query_params(parsed.query)
        
        # 4. Reconstrói URL limpa
        clean_parsed = parsed._replace(
            path=path,
            query=query
        )
        
        # 5. Constrói URL final
        normalized_url = urlunparse(clean_parsed)
        
        return normalized_url
    
    def _normalize_query_params(self, query_string):
        """Normaliza parâmetros de query para evitar duplicados"""
        if not query_string:
            return ''
        
        try:
            # Parse query parameters
            params = parse_qs(query_string, keep_blank_values=False)
            
            # Remove parâmetros problemáticos que causam duplicação
            problematic_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
                'gclid', 'fbclid', 'ref', '_ga', 'sessionid', 'sid', 'jsessionid',
                'phpsessid', 'timestamp', '_t', 'v', 'cache', 'nocache'
            ]
            
            for param in problematic_params:
                params.pop(param, None)
            
            # Se não sobrou nenhum parâmetro, retorna vazio
            if not params:
                return ''
            
            # Reconstrói query string ordenada
            sorted_params = []
            for key in sorted(params.keys()):
                values = params[key]
                for value in sorted(values):
                    sorted_params.append((key, value))
            
            return urlencode(sorted_params)
            
        except Exception:
            # Se falhar, retorna string original
            return query_string
    
    def is_url_relevant(self, url):
        """Verifica se URL é relevante para crawling"""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # 🔥 PADRÕES E-COMMERCE BLOQUEADOS
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
        
        # Extensões excluídas
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
        
        # Padrões técnicos bloqueados
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
        
        return True
    
    def add_url(self, url, depth=0, base_url=None):
        """🔥 CORREÇÃO: Adiciona URL com deduplicação robusta"""
        normalized_url = self.normalize_url(url, base_url)
        
        if not normalized_url:
            return False
        
        # 🔥 VERIFICAÇÃO ANTI-DUPLICAÇÃO
        if self._is_duplicate(normalized_url):
            self.stats['total_duplicates'] += 1
            return False
        
        if not self.is_url_relevant(normalized_url):
            return False
        
        # Adiciona às estruturas de controle
        self._register_url(normalized_url)
        
        self.urls_to_process.append((normalized_url, depth))
        self.stats['total_found'] += 1
        return True
    
    def _is_duplicate(self, normalized_url):
        """🔥 Verifica se URL é duplicada usando múltiplas estratégias"""
        
        # 1. Verificação direta na URL normalizada
        if normalized_url in self.normalized_urls:
            return True
        
        # 2. Verificação na lista de processadas
        if normalized_url in self.processed_urls:
            return True
        
        # 3. Verificação por hash (para casos edge)
        url_hash = hashlib.md5(normalized_url.encode()).hexdigest()
        if url_hash in self.url_hashes:
            return True
        
        return False
    
    def _register_url(self, normalized_url):
        """Registra URL nas estruturas de controle"""
        self.normalized_urls.add(normalized_url)
        
        # Adiciona hash para detecção extra
        url_hash = hashlib.md5(normalized_url.encode()).hexdigest()
        self.url_hashes.add(url_hash)
    
    def get_next_url(self):
        """🔥 CORREÇÃO: Pega próxima URL com verificação final"""
        if self.urls_to_process:
            url, depth = self.urls_to_process.popleft()
            
            # Verificação final antes de processar
            if url in self.processed_urls:
                return self.get_next_url()  # Recursiva para pegar próxima
            
            self.processed_urls.add(url)
            self.stats['total_processed'] += 1
            return url, depth
        return None, None
    
    def has_urls_to_process(self):
        """Verifica se há URLs para processar"""
        return len(self.urls_to_process) > 0
    
    def mark_as_processed(self, url):
        """Marca URL como processada"""
        normalized_url = self.normalize_url(url)
        if normalized_url:
            self.processed_urls.add(normalized_url)
    
    def is_processed(self, url):
        """Verifica se URL já foi processada"""
        normalized_url = self.normalize_url(url)
        if normalized_url:
            return normalized_url in self.processed_urls
        return False
    
    def get_queue_size(self):
        """Retorna tamanho da fila"""
        return len(self.urls_to_process)
    
    def get_processed_count(self):
        """Retorna número de URLs processadas"""
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
        """🆕 Estatísticas incluindo duplicados"""
        return {
            'urls_found': self.stats['total_found'],
            'urls_processed': self.stats['total_processed'],
            'urls_filtered': self.stats['total_filtered'],
            'urls_duplicates': self.stats['total_duplicates'],  # 🆕
            'urls_in_queue': len(self.urls_to_process),
            'filter_breakdown': self.stats['filtered_by_reason'].copy(),
            'processing_rate': (
                self.stats['total_processed'] / max(self.stats['total_found'], 1) * 100
            ),
            'deduplication_info': {  # 🆕 Info de deduplicação
                'normalized_urls': len(self.normalized_urls),
                'processed_urls': len(self.processed_urls),
                'url_hashes': len(self.url_hashes)
            }
        }
    
    def get_filtered_urls(self, reason=None):
        """Retorna URLs filtradas"""
        if reason:
            return [f for f in self.filtered_urls if f['reason'] == reason]
        return self.filtered_urls.copy()
    
    def clear_queue(self):
        """Limpa fila de URLs"""
        self.urls_to_process.clear()
    
    def reset(self):
        """🔥 Reset completo incluindo estruturas de deduplicação"""
        self.processed_urls.clear()
        self.normalized_urls.clear()
        self.url_hashes.clear()
        self.urls_to_process.clear()
        self.filtered_urls.clear()
        self.stats = {
            'total_found': 0,
            'total_processed': 0,
            'total_filtered': 0,
            'total_duplicates': 0,
            'filtered_by_reason': {}
        }


class SmartURLManager(URLManager):
    """URL Manager inteligente com priorização"""
    
    def __init__(self, base_domain=None, config=None):
        super().__init__(base_domain, config)
        self.priority_patterns = config.get('priority_patterns', []) if config else []
        self.priority_queue = deque()
        self.normal_queue = deque()
    
    def add_url(self, url, depth=0, base_url=None, priority=False):
        """Adiciona URL com sistema de prioridade"""
        normalized_url = self.normalize_url(url, base_url)
        
        if not normalized_url:
            return False
        
        if self._is_duplicate(normalized_url):
            self.stats['total_duplicates'] += 1
            return False
        
        if not self.is_url_relevant(normalized_url):
            return False
        
        # Determina prioridade
        if not priority and self.priority_patterns:
            priority = any(pattern in normalized_url.lower() 
                          for pattern in self.priority_patterns)
        
        # Registra URL
        self._register_url(normalized_url)
        
        # Adiciona na fila apropriada
        if priority:
            self.priority_queue.append((normalized_url, depth))
        else:
            self.normal_queue.append((normalized_url, depth))
        
        self.stats['total_found'] += 1
        return True
    
    def get_next_url(self):
        """Pega próxima URL priorizando fila de prioridade"""
        # Primeiro, verifica fila de prioridade
        if self.priority_queue:
            url, depth = self.priority_queue.popleft()
            if url not in self.processed_urls:
                self.processed_urls.add(url)
                self.stats['total_processed'] += 1
                return url, depth
        
        # Depois, fila normal
        if self.normal_queue:
            url, depth = self.normal_queue.popleft()
            if url not in self.processed_urls:
                self.processed_urls.add(url)
                self.stats['total_processed'] += 1
                return url, depth
        
        return None, None
    
    def has_urls_to_process(self):
        """Verifica se há URLs em qualquer fila"""
        return len(self.priority_queue) > 0 or len(self.normal_queue) > 0
    
    def get_queue_size(self):
        """Tamanho total das filas"""
        return len(self.priority_queue) + len(self.normal_queue)
    
    def get_queue_breakdown(self):
        """Breakdown das filas"""
        return {
            'priority_queue': len(self.priority_queue),
            'normal_queue': len(self.normal_queue),
            'total_queue': len(self.priority_queue) + len(self.normal_queue)
        }
    
    def clear_queue(self):
        """Limpa ambas as filas"""
        self.priority_queue.clear()
        self.normal_queue.clear()
    
    def reset(self):
        """Reset completo incluindo filas de prioridade"""
        super().reset()
        self.priority_queue.clear()
        self.normal_queue.clear()


class BatchURLManager(URLManager):
    """URL Manager para processamento em lotes"""
    
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


def create_url_manager(manager_type='default', base_domain=None, config=None):
    """Factory function para criar URL managers"""
    
    if manager_type == 'smart':
        return SmartURLManager(base_domain, config)
    
    elif manager_type == 'batch':
        batch_size = config.get('batch_size', 20) if config else 20
        return BatchURLManager(base_domain, config, batch_size)
    
    else:
        return URLManager(base_domain, config)


def test_url_manager():
    """🧪 Teste robusto incluindo deduplicação"""
    print("🧪 Testando URLManager com anti-duplicação...")
    
    manager = URLManager()
    manager.set_base_domain("https://example.com/")
    
    test_urls = [
        "https://example.com/page1",           # Original
        "https://example.com/page1/",          # Com trailing slash
        "https://example.com/page1?utm_source=test",  # Com parâmetro problemático
        "https://example.com/page1#section",   # Com fragment
        "https://example.com/page2",           # Diferente
        "https://example.com/page1",           # Duplicado exato
        "https://example.com/checkout/cart/add/123",  # E-commerce (filtrado)
        "https://example.com/style.css",       # Arquivo (filtrado)
        "https://other-domain.com/page",       # Outro domínio (filtrado)
        "https://example.com/page1/?ref=123",  # Outra variação
    ]
    
    print(f"📋 Testando {len(test_urls)} URLs...")
    
    for i, url in enumerate(test_urls, 1):
        result = manager.add_url(url)
        status = '✅ ADICIONADA' if result else '❌ FILTRADA/DUPLICADA'
        print(f"  {i:2d}. {status} - {url}")
    
    print(f"\n📊 Estatísticas finais:")
    stats = manager.get_stats()
    for key, value in stats.items():
        if key == 'deduplication_info':
            print(f"  🔄 Informações de deduplicação:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\n🎯 URLs para processar:")
    count = 0
    while manager.has_urls_to_process():
        url, depth = manager.get_next_url()
        if url:
            count += 1
            print(f"  {count}. {url}")
    
    print(f"\n✅ Teste concluído! URLs únicas processadas: {count}")


def test_smart_url_manager():
    """🧪 Teste do Smart URL Manager"""
    print("\n🧪 Testando SmartURLManager...")
    
    config = {
        'priority_patterns': ['/important/', '/product/', '/category/']
    }
    
    manager = SmartURLManager("example.com", config)
    
    urls = [
        "https://example.com/page1",
        "https://example.com/important/page",
        "https://example.com/product/123",
        "https://example.com/normal-page",
        "https://example.com/product/123/",  # Duplicado com trailing slash
    ]
    
    for url in urls:
        result = manager.add_url(url)
        print(f"  {'✅' if result else '❌'} {url}")
    
    print("\n📊 Breakdown das filas:")
    breakdown = manager.get_queue_breakdown()
    for key, value in breakdown.items():
        print(f"  {key}: {value}")
    
    print("\n🎯 Processando URLs (ordem de prioridade):")
    while manager.has_urls_to_process():
        url, depth = manager.get_next_url()
        if url:
            print(f"  Processando: {url}")


if __name__ == "__main__":
    test_url_manager()
    test_smart_url_manager()
    print("\n🎯 Todos os testes concluídos!")