import requests
import time
from urllib.parse import urlparse


class SessionManager:
    
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
        session = requests.Session()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        config_headers = self.config.get('headers', {})
        headers.update(config_headers)
        session.headers.update(headers)
        
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=3
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def get(self, url, **kwargs):
        start_time = time.time()
        self.stats['requests_made'] += 1
        
        try:
            default_kwargs = {
                'timeout': self.config.get('timeout', 15),
                'allow_redirects': True,
                'verify': False
            }
            default_kwargs.update(kwargs)
            
            response = self.session.get(url, **default_kwargs)
            
            response_time = (time.time() - start_time) * 1000
            self.stats['total_response_time'] += response_time
            self.stats['successful_requests'] += 1
            
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
        if self.session:
            self.session.close()
    
    def get_stats(self):
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
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0
        }
    
    def update_headers(self, new_headers):
        self.session.headers.update(new_headers)
    
    def set_proxy(self, proxy_config):
        if proxy_config:
            self.session.proxies.update(proxy_config)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class RateLimitedSessionManager(SessionManager):
    
    def __init__(self, config=None, rate_limit=None):
        super().__init__(config)
        self.rate_limit = rate_limit or {'requests_per_second': 10}
        self.last_request_time = 0
        self.min_interval = 1.0 / self.rate_limit['requests_per_second']
    
    def get(self, url, **kwargs):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        
        return super().get(url, **kwargs)


class MultiDomainSessionManager:
    
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
        domain = urlparse(url).netloc
        
        if domain not in self.domain_sessions:
            self.domain_sessions[domain] = SessionManager(self.config)
            self.global_stats['domains_accessed'] += 1
        
        return self.domain_sessions[domain]
    
    def get(self, url, **kwargs):
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
        for session in self.domain_sessions.values():
            session.close()
        self.domain_sessions.clear()
    
    def get_global_stats(self):
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
    
    if session_type == 'rate_limited':
        rate_config = config.get('rate_limit', {}) if config else {}
        return RateLimitedSessionManager(config, rate_config)
    
    elif session_type == 'multi_domain':
        return MultiDomainSessionManager(config)
    
    else:
        return SessionManager(config)


def test_session_manager(url="https://httpbin.org/get"):
    print("Testando SessionManager...")
    
    with SessionManager() as session_manager:
        try:
            response = session_manager.get(url)
            print(f"Status: {response.status_code}")
            print(f"Tempo: {response.response_time_ms}ms")
            
            stats = session_manager.get_stats()
            print(f"Stats: {stats}")
            
        except Exception as e:
            print(f"Erro: {e}")


def test_rate_limited_session(url="https://httpbin.org/get", requests_count=5):
    print("Testando RateLimitedSessionManager...")
    
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
    test_session_manager()
    print("\n" + "="*50 + "\n")
    test_rate_limited_session()