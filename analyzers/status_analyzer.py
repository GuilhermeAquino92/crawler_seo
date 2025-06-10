# analyzers/status_analyzer.py - Análise de Status HTTP e Mixed Content

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re


class StatusAnalyzer:
    """🚨 Analisador de Status HTTP e Mixed Content"""
    
    def __init__(self, config=None):
        self.config = config or {}
        
        self.stats = {
            'urls_processadas': 0,
            'status_errors': 0,
            'mixed_content_found': 0,
            'redirects_found': 0
        }
    
    def analyze(self, soup, url, response=None):
        """🎯 Análise principal de status e mixed content"""
        try:
            result = {
                'url': url,
                'processed': True
            }
            
            # 1. ANÁLISE DE STATUS HTTP
            status_data = self._analyze_status(response, url)
            result.update(status_data)
            
            # 2. ANÁLISE DE MIXED CONTENT  
            mixed_content_data = self._analyze_mixed_content(soup, url)
            result.update(mixed_content_data)
            
            # 3. OUTRAS VERIFICAÇÕES DE STATUS
            other_status_data = self._analyze_other_status_issues(response, url)
            result.update(other_status_data)
            
            self.stats['urls_processadas'] += 1
            
            return result
            
        except Exception as e:
            print(f"Erro analisando status de {url}: {e}")
            return {
                'url': url,
                'processed': False,
                'error': str(e),
                'Status_Code': 'ERROR'
            }
    
    def _analyze_status(self, response, url):
        """🚨 Análise do código de status HTTP"""
        status_data = {
            'Status_Code': None,
            'Response_Time': 0,
            'Final_URL': url,
            'Redirected': False,
            'Content_Type': '',
            'Warnings': []
        }
        
        if response:
            # Status code obrigatório
            status_data['Status_Code'] = response.status_code
            
            # Response time
            status_data['Response_Time'] = getattr(response, 'response_time_ms', 0)
            
            # URL final (após redirects)
            status_data['Final_URL'] = response.url
            status_data['Redirected'] = response.url != url
            
            # Content type
            status_data['Content_Type'] = response.headers.get('content-type', '').split(';')[0]
            
            # Warnings para status diferentes de 200
            if response.status_code != 200:
                status_data['Warnings'].append(f"Página retornou código de status {response.status_code}")
                self.stats['status_errors'] += 1
                
                # Detalhes específicos por tipo de erro
                if response.status_code in [301, 302, 303, 307, 308]:
                    status_data['Warnings'].append(f"Redirect {response.status_code}: {url} → {response.url}")
                    self.stats['redirects_found'] += 1
                elif response.status_code == 404:
                    status_data['Warnings'].append("Página não encontrada (404)")
                elif response.status_code >= 500:
                    status_data['Warnings'].append(f"Erro do servidor ({response.status_code})")
                elif response.status_code == 403:
                    status_data['Warnings'].append("Acesso negado (403)")
        else:
            status_data['Status_Code'] = 'NO_RESPONSE'
            status_data['Warnings'].append("Sem resposta HTTP")
        
        return status_data

    def _is_insecure_url(self, value):
        """Check if a URL uses the insecure HTTP protocol"""
        try:
            return isinstance(value, str) and value.strip().lower().startswith('http://')
        except Exception:
            return False
    
    def _analyze_mixed_content(self, soup, url):
        """🔒 Análise de Mixed Content (recursos HTTP em páginas HTTPS)"""
        mixed_content_data = {
            'mixed_content_resources': [],
            'has_mixed_content': False,
            'mixed_content_count': 0
        }
        
        # Só analisa se a página é HTTPS
        if not url.startswith('https://'):
            return mixed_content_data
        
        if not soup:
            return mixed_content_data
        
        try:
            mixed_resources = []
            
            # 1. IMAGENS com src HTTP
            for img in soup.find_all('img', src=True):
                src = img.get('src', '').strip()
                if self._is_insecure_url(src):
                    full_url = urljoin(url, src)
                    mixed_resources.append({
                        'type': 'image',
                        'tag': 'img',
                        'attribute': 'src',
                        'url': full_url,
                        'element': str(img)[:100] + '...' if len(str(img)) > 100 else str(img)
                    })
            
            # 2. SCRIPTS com src HTTP
            for script in soup.find_all('script', src=True):
                src = script.get('src', '').strip()
                if self._is_insecure_url(src):
                    full_url = urljoin(url, src)
                    mixed_resources.append({
                        'type': 'script',
                        'tag': 'script',
                        'attribute': 'src', 
                        'url': full_url,
                        'element': str(script)[:100] + '...' if len(str(script)) > 100 else str(script)
                    })
            
            # 3. LINKS (CSS) com href HTTP
            for link in soup.find_all('link', href=True):
                href = link.get('href', '').strip()
                if self._is_insecure_url(href):
                    full_url = urljoin(url, href)
                    mixed_resources.append({
                        'type': 'stylesheet',
                        'tag': 'link',
                        'attribute': 'href',
                        'url': full_url,
                        'element': str(link)[:100] + '...' if len(str(link)) > 100 else str(link)
                    })
            
            # 4. IFRAMES com src HTTP
            for iframe in soup.find_all('iframe', src=True):
                src = iframe.get('src', '').strip()
                if self._is_insecure_url(src):
                    full_url = urljoin(url, src)
                    mixed_resources.append({
                        'type': 'iframe',
                        'tag': 'iframe',
                        'attribute': 'src',
                        'url': full_url,
                        'element': str(iframe)[:100] + '...' if len(str(iframe)) > 100 else str(iframe)
                    })
            
            # 5. OUTROS recursos com URLs HTTP
            for tag in soup.find_all(['video', 'audio', 'source']):
                for attr in ['src', 'poster']:
                    if tag.has_attr(attr):
                        url_attr = tag.get(attr, '').strip()
                        if self._is_insecure_url(url_attr):
                            full_url = urljoin(url, url_attr)
                            mixed_resources.append({
                                'type': 'media',
                                'tag': tag.name,
                                'attribute': attr,
                                'url': full_url,
                                'element': str(tag)[:100] + '...' if len(str(tag)) > 100 else str(tag)
                            })

            # 6. <style> contendo url(http://...)
            for style_tag in soup.find_all('style'):
                content = style_tag.string or ''
                for match in re.findall(r'url\(\s*["\']?(http://[^)"\']+)', content, re.IGNORECASE):
                    if self._is_insecure_url(match):
                        full_url = urljoin(url, match)
                        mixed_resources.append({
                            'type': 'inline-style',
                            'tag': 'style',
                            'attribute': 'content',
                            'url': full_url,
                            'element': str(style_tag)[:100] + '...' if len(str(style_tag)) > 100 else str(style_tag)
                        })

            # 7. Atributo style com url(http://...)
            for element in soup.find_all(style=True):
                style_attr = element.get('style', '')
                for match in re.findall(r'url\(\s*["\']?(http://[^)"\']+)', style_attr, re.IGNORECASE):
                    if self._is_insecure_url(match):
                        full_url = urljoin(url, match)
                        mixed_resources.append({
                            'type': 'inline-style',
                            'tag': element.name,
                            'attribute': 'style',
                            'url': full_url,
                            'element': str(element)[:100] + '...' if len(str(element)) > 100 else str(element)
                        })

            # 8. Formulários com action HTTP
            for form in soup.find_all('form', action=True):
                action = form.get('action', '').strip()
                if self._is_insecure_url(action):
                    full_url = urljoin(url, action)
                    mixed_resources.append({
                        'type': 'form',
                        'tag': 'form',
                        'attribute': 'action',
                        'url': full_url,
                        'element': str(form)[:100] + '...' if len(str(form)) > 100 else str(form)
                    })
            
            mixed_content_data['mixed_content_resources'] = mixed_resources
            mixed_content_data['has_mixed_content'] = len(mixed_resources) > 0
            mixed_content_data['mixed_content_count'] = len(mixed_resources)
            
            if mixed_resources:
                self.stats['mixed_content_found'] += 1
            
        except Exception as e:
            print(f"Erro analisando mixed content em {url}: {e}")
        
        return mixed_content_data
    
    def _analyze_other_status_issues(self, response, url):
        """🔍 Outras verificações de status e headers"""
        other_data = {
            'Security_Headers': {},
            'Performance_Issues': [],
            'SEO_Status_Issues': []
        }
        
        if not response:
            return other_data
        
        try:
            headers = response.headers
            
            # Verifica headers de segurança importantes
            security_headers = {
                'X-Frame-Options': headers.get('X-Frame-Options'),
                'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
                'X-XSS-Protection': headers.get('X-XSS-Protection'),
                'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
                'Content-Security-Policy': headers.get('Content-Security-Policy')
            }
            
            other_data['Security_Headers'] = {k: v for k, v in security_headers.items() if v}
            
            # Verifica performance issues
            content_length = headers.get('Content-Length')
            if content_length and int(content_length) > 1024 * 1024:  # > 1MB
                other_data['Performance_Issues'].append(f"Página muito grande ({content_length} bytes)")
            
            # Verifica issues de SEO relacionados a status
            if response.status_code in [301, 302]:
                other_data['SEO_Status_Issues'].append("Redirect pode afetar SEO")
            
            if 'text/html' not in headers.get('content-type', '').lower():
                other_data['SEO_Status_Issues'].append("Content-Type não é HTML")
            
        except Exception as e:
            print(f"Erro analisando outros status em {url}: {e}")
        
        return other_data
    
    def get_stats(self):
        """📊 Estatísticas do analisador de status"""
        return {
            'processing': self.stats.copy(),
            'summary': {
                'urls_processadas': self.stats['urls_processadas'],
                'status_errors': self.stats['status_errors'],
                'mixed_content_found': self.stats['mixed_content_found'], 
                'redirects_found': self.stats['redirects_found'],
                'error_rate': (self.stats['status_errors'] / max(self.stats['urls_processadas'], 1)) * 100,
                'mixed_content_rate': (self.stats['mixed_content_found'] / max(self.stats['urls_processadas'], 1)) * 100
            }
        }
    
    def get_mixed_content_report(self):
        """📋 Relatório detalhado de mixed content"""
        # Esta função poderia ser expandida para gerar relatórios mais detalhados
        return {
            'total_pages_with_mixed_content': self.stats['mixed_content_found'],
            'analysis_details': 'Mixed content encontrado em recursos HTTP em páginas HTTPS'
        }
    
    def reset_stats(self):
        """🔄 Reset das estatísticas"""
        self.stats = {
            'urls_processadas': 0,
            'status_errors': 0,
            'mixed_content_found': 0,
            'redirects_found': 0
        }


def create_status_analyzer(config=None):
    """🏭 Factory function para criar StatusAnalyzer"""
    return StatusAnalyzer(config)


def test_status_analyzer():
    """🧪 Teste do StatusAnalyzer"""
    print("🧪 Testando StatusAnalyzer...")
    
    # HTML de teste com mixed content
    html_test_mixed = """
    <html>
    <head>
        <title>Teste Mixed Content</title>
        <link rel="stylesheet" href="http://insecure.com/style.css">
        <script src="http://insecure.com/script.js"></script>
    </head>
    <body>
        <img src="http://insecure.com/image.jpg" alt="Imagem insegura">
        <iframe src="http://insecure.com/iframe.html"></iframe>
        <img src="https://secure.com/safe.jpg" alt="Imagem segura">
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html_test_mixed, 'html.parser')
    analyzer = StatusAnalyzer()
    
    # Mock response object
    class MockResponse:
        def __init__(self, status_code=200, url="https://test.com"):
            self.status_code = status_code
            self.url = url
            self.response_time_ms = 150
            self.headers = {
                'content-type': 'text/html; charset=utf-8',
                'Content-Length': '1024',
                'X-Frame-Options': 'DENY'
            }
    
    # Teste com página HTTPS e mixed content
    response_https = MockResponse(200, "https://test.com")
    resultado = analyzer.analyze(soup, "https://test.com", response_https)
    
    print("🔒 ANÁLISE DE MIXED CONTENT:")
    print(f"  URL: {resultado['url']}")
    print(f"  Status Code: {resultado['Status_Code']}")
    print(f"  Mixed Content encontrado: {resultado['has_mixed_content']}")
    print(f"  Número de recursos inseguros: {resultado['mixed_content_count']}")
    
    if resultado['mixed_content_resources']:
        print(f"  Recursos inseguros encontrados:")
        for resource in resultado['mixed_content_resources']:
            print(f"    - {resource['type']}: {resource['url']}")
    
    # Teste com status de erro
    response_error = MockResponse(404, "https://test.com/404")
    resultado_error = analyzer.analyze(soup, "https://test.com/404", response_error)
    
    print(f"\n🚨 ANÁLISE DE STATUS DE ERRO:")
    print(f"  URL: {resultado_error['url']}")
    print(f"  Status Code: {resultado_error['Status_Code']}")
    print(f"  Warnings: {resultado_error['Warnings']}")
    
    # Teste com redirect
    response_redirect = MockResponse(301, "https://test.com/new-url")
    resultado_redirect = analyzer.analyze(soup, "https://test.com/old-url", response_redirect)
    
    print(f"\n🔄 ANÁLISE DE REDIRECT:")
    print(f"  URL original: https://test.com/old-url")
    print(f"  URL final: {resultado_redirect['Final_URL']}")
    print(f"  Redirected: {resultado_redirect['Redirected']}")
    print(f"  Warnings: {resultado_redirect['Warnings']}")
    
    # Estatísticas
    stats = analyzer.get_stats()
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"  URLs processadas: {stats['processing']['urls_processadas']}")
    print(f"  Status errors: {stats['processing']['status_errors']}")
    print(f"  Mixed content found: {stats['processing']['mixed_content_found']}")
    print(f"  Redirects found: {stats['processing']['redirects_found']}")
    print(f"  Error rate: {stats['summary']['error_rate']:.1f}%")
    print(f"  Mixed content rate: {stats['summary']['mixed_content_rate']:.1f}%")
    
    print(f"\n✅ StatusAnalyzer testado com sucesso!")
    print(f"   🔒 Mixed content: detecta recursos HTTP em páginas HTTPS")
    print(f"   🚨 Status codes: analisa e reporta erros HTTP")
    print(f"   🔄 Redirects: detecta e reporta redirects")
    print(f"   📊 Headers: analisa headers de segurança")


if __name__ == "__main__":
    test_status_analyzer()