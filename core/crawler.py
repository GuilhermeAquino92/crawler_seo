# core/crawler.py - Motor de crawling modularizado

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime

from core.session_manager import SessionManager, create_session_manager
from core.url_manager import URLManager, create_url_manager
from config.settings import DEFAULT_CONFIG, MAX_THREADS_DEFAULT
from utils.constants import (
    MSG_CRAWLER_START, MSG_PROCESSING_BATCH, MSG_CRAWL_COMPLETE,
    MSG_ERROR_PROCESSING, MSG_NO_URLS
)


class SEOCrawler:
    """🕷️ Motor de crawling SEO modularizado"""
    
    def __init__(self, config=None):
        self.config = config or DEFAULT_CONFIG.copy()
        
        # Configurações do crawler
        self.max_urls = self.config['crawler']['max_urls']
        self.max_depth = self.config['crawler']['max_depth']
        self.max_threads = self.config['crawler']['max_threads']
        
        # Gerenciadores
        self.session_manager = None
        self.url_manager = None
        
        # Resultados
        self.results = []
        self.start_time = None
        self.end_time = None
        
        # Estatísticas
        self.stats = {
            'urls_found': 0,
            'urls_processed': 0,
            'urls_successful': 0,
            'urls_failed': 0,
            'total_time': 0,
            'average_response_time': 0
        }
    
    def initialize(self, start_url):
        """🚀 Inicializa o crawler com URL inicial"""
        parsed_url = urlparse(start_url)
        domain = parsed_url.netloc
        
        print(MSG_CRAWLER_START.format(domain=domain))
        
        # Cria gerenciadores
        session_config = self.config.get('crawler', {})
        self.session_manager = create_session_manager(session_config, 'default')
        
        url_config = self.config.get('filters', {})
        self.url_manager = create_url_manager('default', domain, url_config)
        
        # Adiciona URL inicial
        self.url_manager.add_url(start_url, depth=0)
        
        # Estatísticas
        self.start_time = time.time()
        
        return True
    
    def crawl(self, start_url, max_urls=None, analyzers=None):
        """🕷️ Executa crawling completo"""
        # Configuração
        if max_urls:
            self.max_urls = max_urls
        
        analyzers = analyzers or []
        
        # Inicializa
        if not self.initialize(start_url):
            print(MSG_NO_URLS)
            return []
        
        # Loop principal de crawling
        while (self.url_manager.has_urls_to_process() and 
               len(self.results) < self.max_urls):
            
            # Monta lote de URLs
            batch = self._create_batch()
            
            if not batch:
                break
            
            print(MSG_PROCESSING_BATCH.format(
                batch_size=len(batch),
                current=len(self.results),
                max_urls=self.max_urls
            ))
            
            # Processa lote em paralelo
            batch_results = self._process_batch(batch, analyzers)
            
            # Adiciona resultados
            self.results.extend(batch_results)
            
            # Extrai novos links dos resultados
            self._extract_new_links(batch_results)
        
        # Finaliza
        self._finalize_crawling()
        
        return self.results
    
    def _create_batch(self):
        """📦 Cria lote de URLs para processamento"""
        batch = []
        
        while (len(batch) < self.max_threads and 
               self.url_manager.has_urls_to_process() and
               len(self.results) + len(batch) < self.max_urls):
            
            url, depth = self.url_manager.get_next_url()
            if url:
                batch.append((url, depth))
        
        return batch
    
    def _process_batch(self, batch, analyzers):
        """⚡ Processa lote de URLs em paralelo"""
        batch_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # Submete tarefas
            futures = {
                executor.submit(self._process_single_url, url, depth, analyzers): (url, depth)
                for url, depth in batch
            }
            
            # Coleta resultados
            for future in as_completed(futures):
                url, depth = futures[future]
                try:
                    result = future.result(timeout=30)
                    batch_results.append(result)
                    self.stats['urls_processed'] += 1
                    
                    if result.get('status_code') == 200:
                        self.stats['urls_successful'] += 1
                    else:
                        self.stats['urls_failed'] += 1
                        
                except Exception as e:
                    print(MSG_ERROR_PROCESSING.format(url=url, error=str(e)))
                    self.stats['urls_failed'] += 1
                    
                    # Cria resultado de erro
                    error_result = self._create_error_result(url, depth, str(e))
                    batch_results.append(error_result)
        
        return batch_results
    
    def _process_single_url(self, url, depth, analyzers):
        """🔍 Processa uma única URL"""
        result = {
            'url': url,
            'depth': depth,
            'status_code': None,
            'response_time': None,
            'content_type': '',
            'final_url': url,
            'redirected': False,
            'links_encontrados': [],
            'processed_at': datetime.now().isoformat()
        }
        
        try:
            # Faz requisição
            response = self.session_manager.get(url)
            
            # Dados básicos da resposta
            result.update({
                'status_code': response.status_code,
                'response_time': getattr(response, 'response_time_ms', 0),
                'content_type': response.headers.get('content-type', '').split(';')[0],
                'final_url': response.url,
                'redirected': response.url != url,
                'content_length': len(response.content)
            })
            
            # Se é HTML e status 200, processa conteúdo
            if (response.status_code == 200 and 
                'text/html' in result['content_type'].lower()):
                
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Executa analisadores
                for analyzer in analyzers:
                    try:
                        analyzer_result = analyzer.analyze(soup, url)
                        result.update(analyzer_result)
                    except Exception as e:
                        print(f"⚠️ Erro no analisador {analyzer.__class__.__name__}: {e}")
                
                # Extrai links se não atingiu profundidade máxima
                if depth < self.max_depth:
                    result['links_encontrados'] = self._extract_links(soup, url)
            
        except Exception as e:
            result['status_code'] = 'ERROR'
            result['error_details'] = str(e)
        
        return result
    
    def _extract_links(self, soup, base_url):
        """🔗 Extrai links da página"""
        links = []
        
        try:
            for tag_a in soup.find_all('a', href=True):
                href = tag_a.get('href', '').strip()
                if href:
                    normalized_url = self.url_manager.normalize_url(href, base_url)
                    if normalized_url and self.url_manager.is_url_relevant(normalized_url):
                        links.append(normalized_url)
        
        except Exception as e:
            print(f"⚠️ Erro extraindo links de {base_url}: {e}")
        
        return links
    
    def _extract_new_links(self, batch_results):
        """🆕 Extrai novos links dos resultados do lote"""
        for result in batch_results:
            current_depth = result.get('depth', 0)
            new_links = result.get('links_encontrados', [])
            
            for link in new_links:
                if not self.url_manager.is_processed(link):
                    self.url_manager.add_url(
                        link, 
                        depth=current_depth + 1, 
                        base_url=result['url']
                    )
                    self.stats['urls_found'] += 1
    
    def _create_error_result(self, url, depth, error):
        """❌ Cria resultado para URLs com erro"""
        return {
            'url': url,
            'depth': depth,
            'status_code': 'ERROR',
            'error_details': error,
            'response_time': 0,
            'content_type': '',
            'final_url': url,
            'redirected': False,
            'links_encontrados': [],
            'processed_at': datetime.now().isoformat()
        }
    
    def _finalize_crawling(self):
        """🏁 Finaliza o processo de crawling"""
        self.end_time = time.time()
        self.stats['total_time'] = self.end_time - self.start_time
        
        # Calcula estatísticas finais
        if self.stats['urls_successful'] > 0:
            total_response_time = sum(
                r.get('response_time', 0) for r in self.results 
                if r.get('response_time') and r.get('status_code') == 200
            )
            self.stats['average_response_time'] = total_response_time / self.stats['urls_successful']
        
        # Estatísticas do gerenciador de URLs
        url_stats = self.url_manager.get_stats()
        self.stats.update(url_stats)
        
        # Estatísticas do gerenciador de sessão
        session_stats = self.session_manager.get_stats()
        self.stats['session_stats'] = session_stats
        
        print(MSG_CRAWL_COMPLETE.format(total_urls=len(self.results)))
        
        # Fecha gerenciadores
        self.session_manager.close()
    
    def get_stats(self):
        """📊 Retorna estatísticas completas"""
        return {
            'crawling': self.stats.copy(),
            'urls_manager': self.url_manager.get_stats() if self.url_manager else {},
            'session_manager': self.session_manager.get_stats() if self.session_manager else {},
            'summary': {
                'total_urls_found': self.stats.get('urls_found', 0),
                'total_urls_processed': len(self.results),
                'success_rate': (self.stats.get('urls_successful', 0) / max(len(self.results), 1)) * 100,
                'average_response_time': self.stats.get('average_response_time', 0),
                'total_crawling_time': self.stats.get('total_time', 0),
                'urls_per_second': len(self.results) / max(self.stats.get('total_time', 1), 1)
            }
        }
    
    def get_filtered_urls(self):
        """🚫 Retorna URLs que foram filtradas"""
        if self.url_manager:
            return self.url_manager.get_filtered_urls()
        return []


class SmartSEOCrawler(SEOCrawler):
    """🧠 Crawler inteligente com priorização"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.priority_patterns = self.config.get('priority_patterns', [
            '/produto/', '/product/', '/categoria/', '/category/',
            '/servico/', '/service/', '/sobre/', '/about/'
        ])
    
    def initialize(self, start_url):
        """🚀 Inicializa com gerenciador inteligente"""
        parsed_url = urlparse(start_url)
        domain = parsed_url.netloc
        
        print(MSG_CRAWLER_START.format(domain=domain))
        
        # Cria gerenciadores
        session_config = self.config.get('crawler', {})
        self.session_manager = create_session_manager(session_config, 'default')
        
        url_config = self.config.get('filters', {})
        url_config['priority_patterns'] = self.priority_patterns
        self.url_manager = create_url_manager('smart', domain, url_config)
        
        # Adiciona URL inicial com prioridade
        self.url_manager.add_url(start_url, depth=0, priority=True)
        
        self.start_time = time.time()
        return True


class BatchSEOCrawler(SEOCrawler):
    """📦 Crawler otimizado para lotes grandes"""
    
    def __init__(self, config=None, batch_size=50):
        super().__init__(config)
        self.batch_size = batch_size
    
    def initialize(self, start_url):
        """🚀 Inicializa com gerenciador de lotes"""
        parsed_url = urlparse(start_url)
        domain = parsed_url.netloc
        
        print(MSG_CRAWLER_START.format(domain=domain))
        
        # Cria gerenciadores
        session_config = self.config.get('crawler', {})
        self.session_manager = create_session_manager(session_config, 'default')
        
        url_config = self.config.get('filters', {})
        url_config['batch_size'] = self.batch_size
        self.url_manager = create_url_manager('batch', domain, url_config)
        
        self.url_manager.add_url(start_url, depth=0)
        
        self.start_time = time.time()
        return True
    
    def _create_batch(self):
        """📦 Cria lotes otimizados"""
        if hasattr(self.url_manager, 'get_next_batch'):
            return self.url_manager.get_next_batch()
        else:
            return super()._create_batch()


# ========================
# 🏭 FACTORY FUNCTIONS
# ========================

def create_crawler(crawler_type='default', config=None):
    """🏭 Factory para criar crawlers"""
    
    if crawler_type == 'smart':
        return SmartSEOCrawler(config)
    
    elif crawler_type == 'batch':
        batch_size = config.get('batch_size', 50) if config else 50
        return BatchSEOCrawler(config, batch_size)
    
    else:  # default
        return SEOCrawler(config)


# ========================
# 🧪 FUNÇÕES DE TESTE
# ========================

def test_crawler():
    """Testa o crawler básico"""
    print("🧪 Testando SEOCrawler...")
    
    # Configuração de teste
    test_config = {
        'crawler': {
            'max_urls': 5,
            'max_depth': 2,
            'max_threads': 2,
            'timeout': 10
        }
    }
    
    crawler = SEOCrawler(test_config)
    
    # Mock analyzer para teste
    class MockAnalyzer:
        def analyze(self, soup, url):
            title_tag = soup.find('title')
            return {
                'title': title_tag.get_text().strip() if title_tag else '',
                'title_length': len(title_tag.get_text().strip()) if title_tag else 0
            }
    
    # Executa crawl de teste
    results = crawler.crawl(
        start_url="https://httpbin.org/html",
        analyzers=[MockAnalyzer()]
    )
    
    print(f"📊 Resultados do teste:")
    print(f"  URLs processadas: {len(results)}")
    
    # Mostra estatísticas
    stats = crawler.get_stats()
    print(f"  Taxa de sucesso: {stats['summary']['success_rate']:.1f}%")
    print(f"  Tempo médio de resposta: {stats['summary']['average_response_time']:.2f}ms")
    print(f"  Tempo total: {stats['summary']['total_crawling_time']:.2f}s")
    
    # Mostra primeiro resultado
    if results:
        first_result = results[0]
        print(f"  Primeiro resultado:")
        print(f"    URL: {first_result['url']}")
        print(f"    Status: {first_result['status_code']}")
        print(f"    Title: {first_result.get('title', 'N/A')[:50]}...")


def test_smart_crawler():
    """Testa o crawler inteligente"""
    print("\n🧠 Testando SmartSEOCrawler...")
    
    test_config = {
        'crawler': {'max_urls': 3, 'max_depth': 1, 'max_threads': 1},
        'priority_patterns': ['/important/', '/priority/']
    }
    
    crawler = SmartSEOCrawler(test_config)
    
    # Simula teste (sem executar)
    print("  ✅ SmartSEOCrawler inicializado com padrões de prioridade")
    print("  📋 Padrões de prioridade configurados:", crawler.priority_patterns)


if __name__ == "__main__":
    test_crawler()
    test_smart_crawler()