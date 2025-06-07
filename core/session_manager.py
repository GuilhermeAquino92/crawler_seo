# core/session_manager.py - Gerenciamento de sessões HTTP

import requests
import time
from urllib.parse import urlparse
from config.settings import DEFAULT_HEADERS, REQUEST_TIMEOUT


class SessionManager:
    """🔧 Gerenciador de sessões HTTP otimizado"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.session = self._create_optimized_session()
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0
        }
    
    def _create_optimized_session(self):
        """Cria sessão HTTP otimizada"""
        session = requests.Session()
        
        # Headers padrão
        headers = self.config.get('headers', DEFAULT_HEADERS)
        session.headers.update(headers)
        
        # Configurações de conexão
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=3
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def get(self, url, **kwargs):
        """Faz requisição GET com tratamento de erros"""
        start_time = time.time()
        self.stats['requests_made'] += 1
        
        try:
            # Configurações padrão
            default_kwargs = {
                'timeout': self.config.get('timeout', REQUEST_TIMEOUT),
                'allow_redirects': True,
                'verify': True
            }
            default_kwargs.update(kwargs)
            
            response = self.session.get(url, **default_kwargs)
            
            # Atualiza estatísticas
            response_time = (time.time() - start_time) * 1000
            self.stats['total_response_time'] += response_time
            self.stats['successful_requests'] += 1
            
            # Adiciona tempo de resposta ao objeto response
            response.response_time_ms = round(response_time, 2)
            
            return response
            
        except requests.exceptions.Timeout:
            self.stats['failed_requests'] += 1
            raise requests.exceptions.Timeout(f"Timeout ao acessar {url}")
            
        except requests.exceptions.ConnectionError:
            self.stats['failed_requests'] += 1
            raise requests.exceptions.ConnectionError(f"Erro de conexão ao acessar {url}")
            
        except requests.exceptions.SSLError:
            self.stats['failed_requests'] += 1
            raise requests.exceptions.SSLError(f"Erro SSL ao acessar {url}")
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            raise Exception(f"Erro inesperado ao acessar {url}: {str(e)}")
    
    def close(self):
        """Fecha a sessão"""
        if self.session:
            self.session.close()
    
    def get_stats(self):
        """Retorna estatísticas da sessão"""
        avg_response_time = 0
        if self.stats['successful_requests'] > 0:
            avg_response_time = self.stats['total_response_time'] / self.stats['successful_requests']
        
        return {
            'requests_made': self.stats['requests_made'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': (self.stats['successful_requests'] / max(self.stats['requests_made'], 1)) * 100,
            'average_response_time_ms': round(avg_response_time, 2)
        }
    
    def reset_stats(self):
        """Reseta estatísticas"""
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0
        }
    
    def update_headers(self, new_headers):
        """Atualiza headers da sessão"""
        self.session.headers.update(new_headers)
    
    def set_proxy(self, proxy_config):
        """Configura proxy"""
        if proxy_config:
            self.session.proxies.update(proxy_config)
    
    def __enter__(self):
        """Context manager - entrada"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - saída"""
        self.close()


class RateLimitedSessionManager(SessionManager):
    """🚦 Gerenciador de sessão com rate limiting"""
    
    def __init__(self, config=None, rate_limit=None):
        super().__init__(config)
        self.rate_limit = rate_limit or {'requests_per_second': 10}
        self.last_request_time = 0
        self.min_interval = 1.0 / self.rate_limit['requests_per_second']
    
    def get(self, url, **kwargs):
        """GET com rate limiting"""
        # Aplica rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        
        return super().get(url, **kwargs)


class MultiDomainSessionManager:
    """🌐 Gerenciador para múltiplos domínios"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.domain_sessions = {}
        self.global_stats = {
            'domains_accessed': 0,
            'total_requests': 0,
            'total_successful': 0,
            'total_failed': 0
        }
    
    def get_session_for_domain(self, url):
        """Retorna sessão específica para o domínio"""
        domain = urlparse(url).netloc
        
        if domain not in self.domain_sessions:
            self.domain_sessions[domain] = SessionManager(self.config)
            self.global_stats['domains_accessed'] += 1
        
        return self.domain_sessions[domain]
    
    def get(self, url, **kwargs):
        """GET usando sessão específica do domínio"""
        session = self.get_session_for_domain(url)
        
        try:
            response = session.get(url, **kwargs)
            self.global_stats['total_requests'] += 1
            self.global_stats['total_successful'] += 1
            return response
            
        except Exception as e:
            self.global_stats['total_requests'] += 1
            self.global_stats['total_failed'] += 1
            raise e
    
    def close_all(self):
        """Fecha todas as sessões"""
        for session in self.domain_sessions.values():
            session.close()
        self.domain_sessions.clear()
    
    def get_global_stats(self):
        """Retorna estatísticas globais"""
        domain_stats = {}
        for domain, session in self.domain_sessions.items():
            domain_stats[domain] = session.get_stats()
        
        return {
            'global': self.global_stats,
            'by_domain': domain_stats
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()


def create_session_manager(config=None, session_type='default'):
    """🏭 Factory para criar gerenciadores de sessão"""
    
    if session_type == 'rate_limited':
        rate_config = config.get('rate_limit', {}) if config else {}
        return RateLimitedSessionManager(config, rate_config)
    
    elif session_type == 'multi_domain':
        return MultiDomainSessionManager(config)
    
    else:  # default
        return SessionManager(config)


# ========================
# 🧪 FUNÇÕES DE TESTE
# ========================

def test_session_manager(url="https://httpbin.org/get"):
    """Testa o gerenciador de sessão"""
    print("🧪 Testando SessionManager...")
    
    with SessionManager() as session_manager:
        try:
            response = session_manager.get(url)
            print(f"✅ Status: {response.status_code}")
            print(f"⏱️ Tempo: {response.response_time_ms}ms")
            
            stats = session_manager.get_stats()
            print(f"📊 Stats: {stats}")
            
        except Exception as e:
            print(f"❌ Erro: {e}")


def test_rate_limited_session(url="https://httpbin.org/get", requests_count=5):
    """Testa sessão com rate limiting"""
    print("🚦 Testando RateLimitedSessionManager...")
    
    config = {'rate_limit': {'requests_per_second': 2}}
    
    with RateLimitedSessionManager(rate_limit=config['rate_limit']) as session_manager:
        start_time = time.time()
        
        for i in range(requests_count):
            try:
                response = session_manager.get(url)
                print(f"Request {i+1}: {response.status_code} - {response.response_time_ms}ms")
            except Exception as e:
                print(f"Request {i+1}: Erro - {e}")
        
        total_time = time.time() - start_time
        print(f"Tempo total: {total_time:.2f}s")
        print(f"Rate efetivo: {requests_count/total_time:.2f} req/s")


if __name__ == "__main__":
    # Testes básicos
    test_session_manager()
    print("\n" + "="*50 + "\n")
    test_rate_limited_session()