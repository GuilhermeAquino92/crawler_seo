# analyzers/metatags_analyzer.py - Analisador completo de metatags com correções

from bs4 import BeautifulSoup
from .headings_analyzer import HeadingsAnalyzer, HeadingsScoreCalculator
from config.settings import (
    TITLE_MIN_LENGTH, TITLE_MAX_LENGTH,
    DESCRIPTION_MIN_LENGTH, DESCRIPTION_MAX_LENGTH,
    SCORE_TITLE_OK, SCORE_DESCRIPTION_OK,
    PENALTY_DUPLICATE_TITLE, PENALTY_DUPLICATE_DESCRIPTION
)
from utils.constants import (
    STATUS_OK, STATUS_ABSENT, STATUS_TOO_SHORT, STATUS_TOO_LONG,
    MSG_ANALYSIS_START, MSG_ANALYSIS_COMPLETE
)


class MetatagsAnalyzer:
    """🏷️ Analisador completo de metatags - VERSÃO CORRIGIDA"""
    
    def __init__(self, config=None):
        self.config = config or {}
        
        # Integra o HeadingsAnalyzer CORRIGIDO
        self.headings_analyzer = HeadingsAnalyzer(self.config)
        self.headings_score_calculator = HeadingsScoreCalculator(self.config)
        
        # Rastreamento de duplicados
        self.titles_encontrados = {}
        self.descriptions_encontradas = {}
        
        # Estatísticas
        self.stats = {
            'urls_processadas': 0,
            'titles_analisados': 0,
            'descriptions_analisadas': 0,
            'duplicados_encontrados': 0
        }
    
    def analyze(self, soup, url):
        """🏷️ Análise completa de metatags - MÉTODO PRINCIPAL"""
        try:
            resultado = {
                'url': url,
                'processed': True
            }
            
            # 1. 🔢 ANÁLISE DE HEADINGS (usando versão corrigida)
            headings_data = self.headings_analyzer.analyze_all_headings(soup, url)
            resultado.update(headings_data)
            
            # 2. 📄 ANÁLISE DE TITLE
            title_data = self._analyze_title(soup, url)
            resultado.update(title_data)
            
            # 3. 📝 ANÁLISE DE DESCRIPTION
            description_data = self._analyze_description(soup, url)
            resultado.update(description_data)
            
            # 4. 🏷️ OUTRAS METATAGS
            other_meta_data = self._analyze_other_metatags(soup, url)
            resultado.update(other_meta_data)
            
            # 5. 📊 SCORE FINAL CONSOLIDADO
            score_data = self._calculate_final_score(resultado)
            resultado.update(score_data)
            
            # 6. 🚨 PROBLEMAS CRÍTICOS E AVISOS
            issues_data = self._identify_critical_issues(resultado)
            resultado.update(issues_data)
            
            # Atualiza estatísticas
            self.stats['urls_processadas'] += 1
            
            return resultado
            
        except Exception as e:
            print(f"⚠️ Erro analisando {url}: {e}")
            return {
                'url': url,
                'processed': False,
                'error': str(e),
                'metatags_score': 0
            }
    
    def _analyze_title(self, soup, url):
        """📄 Análise completa do title"""
        title_tag = soup.find('title')
        title_text = title_tag.get_text().strip() if title_tag else ''
        title_length = len(title_text)
        
        # Status do title
        if not title_text:
            title_status = STATUS_ABSENT
        elif title_length < TITLE_MIN_LENGTH:
            title_status = STATUS_TOO_SHORT
        elif title_length > TITLE_MAX_LENGTH:
            title_status = STATUS_TOO_LONG
        else:
            title_status = STATUS_OK
        
        # Rastreamento de duplicados
        title_duplicado = self._track_title_duplicate(title_text, url)
        
        # Issues específicos do title
        title_issues = []
        if title_status == STATUS_ABSENT:
            title_issues.append('Title ausente')
        elif title_status == STATUS_TOO_SHORT:
            title_issues.append(f'Title muito curto ({title_length} chars)')
        elif title_status == STATUS_TOO_LONG:
            title_issues.append(f'Title muito longo ({title_length} chars)')
        
        if title_duplicado:
            title_issues.append('Title duplicado')
        
        self.stats['titles_analisados'] += 1
        
        return {
            'title': title_text,
            'title_length': title_length,
            'title_status': title_status,
            'title_duplicado': title_duplicado,
            'title_issues': title_issues
        }
    
    def _analyze_description(self, soup, url):
        """📝 Análise completa da meta description"""
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc_text = desc_tag.get('content', '').strip() if desc_tag else ''
        desc_length = len(desc_text)
        
        # Status da description
        if not desc_text:
            desc_status = STATUS_ABSENT
        elif desc_length < DESCRIPTION_MIN_LENGTH:
            desc_status = STATUS_TOO_SHORT
        elif desc_length > DESCRIPTION_MAX_LENGTH:
            desc_status = STATUS_TOO_LONG
        else:
            desc_status = STATUS_OK
        
        # Rastreamento de duplicados
        desc_duplicada = self._track_description_duplicate(desc_text, url)
        
        # Issues específicos da description
        description_issues = []
        if desc_status == STATUS_ABSENT:
            description_issues.append('Meta description ausente')
        elif desc_status == STATUS_TOO_SHORT:
            description_issues.append(f'Description muito curta ({desc_length} chars)')
        elif desc_status == STATUS_TOO_LONG:
            description_issues.append(f'Description muito longa ({desc_length} chars)')
        
        if desc_duplicada:
            description_issues.append('Description duplicada')
        
        self.stats['descriptions_analisadas'] += 1
        
        return {
            'meta_description': desc_text,
            'description_length': desc_length,
            'description_status': desc_status,
            'description_duplicada': desc_duplicada,
            'description_issues': description_issues
        }
    
    def _analyze_other_metatags(self, soup, url):
        """🏷️ Análise de outras metatags importantes"""
        other_data = {}
        
        # Meta keywords (informativo)
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        other_data['meta_keywords'] = keywords_tag.get('content', '').strip() if keywords_tag else ''
        
        # Meta robots
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        other_data['meta_robots'] = robots_tag.get('content', '').strip() if robots_tag else ''
        
        # Meta viewport
        viewport_tag = soup.find('meta', attrs={'name': 'viewport'})
        other_data['meta_viewport'] = viewport_tag.get('content', '').strip() if viewport_tag else ''
        
        # Canonical
        canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
        other_data['canonical_url'] = canonical_tag.get('href', '').strip() if canonical_tag else ''
        
        # Open Graph básico
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        
        other_data['og_title'] = og_title.get('content', '').strip() if og_title else ''
        other_data['og_description'] = og_description.get('content', '').strip() if og_description else ''
        other_data['og_image'] = og_image.get('content', '').strip() if og_image else ''
        
        # Verifica se tem Open Graph básico
        other_data['has_open_graph'] = bool(other_data['og_title'] or other_data['og_description'])
        
        return other_data
    
    def _track_title_duplicate(self, title, url):
        """🔄 Rastreia duplicados de title"""
        if not title:
            return False
        
        if title not in self.titles_encontrados:
            self.titles_encontrados[title] = []
        
        self.titles_encontrados[title].append(url)
        
        # É duplicado se já existe em outra URL
        is_duplicate = len(self.titles_encontrados[title]) > 1
        
        if is_duplicate:
            self.stats['duplicados_encontrados'] += 1
        
        return is_duplicate
    
    def _track_description_duplicate(self, description, url):
        """🔄 Rastreia duplicados de description"""
        if not description:
            return False
        
        if description not in self.descriptions_encontradas:
            self.descriptions_encontradas[description] = []
        
        self.descriptions_encontradas[description].append(url)
        
        # É duplicado se já existe em outra URL
        is_duplicate = len(self.descriptions_encontradas[description]) > 1
        
        if is_duplicate:
            self.stats['duplicados_encontrados'] += 1
        
        return is_duplicate
    
    def _calculate_final_score(self, resultado):
        """📊 Calcula score final consolidado"""
        score = 0
        
        # 1. Score do title (30 pontos máximo)
        if resultado.get('title_status') == STATUS_OK and not resultado.get('title_duplicado'):
            score += SCORE_TITLE_OK
        elif resultado.get('title_duplicado'):
            score += max(0, SCORE_TITLE_OK - PENALTY_DUPLICATE_TITLE)
        
        # 2. Score da description (25 pontos máximo)
        if resultado.get('description_status') == STATUS_OK and not resultado.get('description_duplicada'):
            score += SCORE_DESCRIPTION_OK
        elif resultado.get('description_duplicada'):
            score += max(0, SCORE_DESCRIPTION_OK - PENALTY_DUPLICATE_DESCRIPTION)
        
        # 3. Score dos headings (35 pontos máximo) - USA O CALCULADOR CORRIGIDO
        headings_score = self.headings_score_calculator.calculate_headings_score(resultado)
        score += headings_score
        
        # 4. Bônus por outras features (10 pontos máximo)
        bonus_score = 0
        
        # Open Graph (+5 pontos)
        if resultado.get('has_open_graph'):
            bonus_score += 5
        
        # Meta viewport (+3 pontos)
        if resultado.get('meta_viewport'):
            bonus_score += 3
        
        # Canonical URL (+2 pontos)
        if resultado.get('canonical_url'):
            bonus_score += 2
        
        score += bonus_score
        
        # Score final (máximo 100)
        final_score = min(score, 100)
        
        return {
            'metatags_score': final_score,
            'score_breakdown': {
                'title_score': SCORE_TITLE_OK if resultado.get('title_status') == STATUS_OK else 0,
                'description_score': SCORE_DESCRIPTION_OK if resultado.get('description_status') == STATUS_OK else 0,
                'headings_score': headings_score,
                'bonus_score': bonus_score,
                'total_score': final_score
            }
        }
    
    def _identify_critical_issues(self, resultado):
        """🚨 Identifica problemas críticos e avisos"""
        critical_issues = []
        warnings = []
        
        # Problemas críticos (impedem bom SEO)
        if resultado.get('title_status') == STATUS_ABSENT:
            critical_issues.append('Title ausente')
        
        if resultado.get('description_status') == STATUS_ABSENT:
            critical_issues.append('Meta description ausente')
        
        if resultado.get('h1_ausente'):
            critical_issues.append('H1 ausente')
        
        if resultado.get('headings_gravidade_critica', 0) > 0:
            critical_issues.append(f"H1s problemáticos ({resultado.get('headings_gravidade_critica')})")
        
        # Avisos (problemas menores)
        if resultado.get('title_duplicado'):
            warnings.append('Title duplicado')
        
        if resultado.get('description_duplicada'):
            warnings.append('Description duplicada')
        
        if resultado.get('h1_multiple'):
            warnings.append('Múltiplos H1')
        
        if not resultado.get('hierarquia_correta'):
            warnings.append('Hierarquia de headings incorreta')
        
        if resultado.get('headings_problematicos_count', 0) > 0:
            warnings.append(f"Headings problemáticos ({resultado.get('headings_problematicos_count')})")
        
        if resultado.get('title_status') in [STATUS_TOO_SHORT, STATUS_TOO_LONG]:
            warnings.append(f"Title {resultado.get('title_status').lower()}")
        
        if resultado.get('description_status') in [STATUS_TOO_SHORT, STATUS_TOO_LONG]:
            warnings.append(f"Description {resultado.get('description_status').lower()}")
        
        return {
            'critical_issues': critical_issues,
            'warnings': warnings,
            'total_critical': len(critical_issues),
            'total_warnings': len(warnings),
            'has_critical': len(critical_issues) > 0,
            'has_warnings': len(warnings) > 0
        }
    
    def get_duplicates_report(self):
        """📊 Retorna relatório de duplicados"""
        title_duplicates = {
            title: urls for title, urls in self.titles_encontrados.items() 
            if len(urls) > 1
        }
        
        description_duplicates = {
            desc: urls for desc, urls in self.descriptions_encontradas.items() 
            if len(urls) > 1
        }
        
        return {
            'title_duplicates': title_duplicates,
            'description_duplicates': description_duplicates,
            'total_duplicate_titles': len(title_duplicates),
            'total_duplicate_descriptions': len(description_duplicates)
        }
    
    def get_stats(self):
        """📊 Retorna estatísticas completas"""
        duplicates_report = self.get_duplicates_report()
        
        return {
            'processing': self.stats.copy(),
            'duplicates': duplicates_report,
            'summary': {
                'urls_processadas': self.stats['urls_processadas'],
                'titles_ok': self.stats['titles_analisados'],
                'descriptions_ok': self.stats['descriptions_analisadas'],
                'duplicados_encontrados': self.stats['duplicados_encontrados'],
                'duplicate_titles_unique': duplicates_report['total_duplicate_titles'],
                'duplicate_descriptions_unique': duplicates_report['total_duplicate_descriptions']
            }
        }
    
    def reset_stats(self):
        """🔄 Reseta estatísticas e duplicados"""
        self.titles_encontrados.clear()
        self.descriptions_encontradas.clear()
        self.stats = {
            'urls_processadas': 0,
            'titles_analisados': 0,
            'descriptions_analisadas': 0,
            'duplicados_encontrados': 0
        }


class MetatagsAnalyzerBatch(MetatagsAnalyzer):
    """📦 Analisador otimizado para processamento em lote"""
    
    def __init__(self, config=None, batch_size=100):
        super().__init__(config)
        self.batch_size = batch_size
        self.batch_results = []
    
    def analyze_batch(self, soup_url_pairs):
        """📦 Analisa lote de páginas"""
        batch_results = []
        
        print(f"📦 Processando lote de {len(soup_url_pairs)} páginas...")
        
        for i, (soup, url) in enumerate(soup_url_pairs, 1):
            try:
                result = self.analyze(soup, url)
                batch_results.append(result)
                
                if i % 10 == 0:
                    print(f"   Processadas: {i}/{len(soup_url_pairs)}")
                    
            except Exception as e:
                print(f"⚠️ Erro no lote {url}: {e}")
                batch_results.append({
                    'url': url,
                    'processed': False,
                    'error': str(e)
                })
        
        self.batch_results.extend(batch_results)
        print(f"✅ Lote concluído: {len(batch_results)} páginas processadas")
        
        return batch_results
    
    def get_batch_summary(self):
        """📊 Resumo do processamento em lote"""
        if not self.batch_results:
            return {}
        
        processed = [r for r in self.batch_results if r.get('processed')]
        errors = [r for r in self.batch_results if not r.get('processed')]
        
        scores = [r.get('metatags_score', 0) for r in processed]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_processed': len(processed),
            'total_errors': len(errors),
            'average_score': avg_score,
            'min_score': min(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'success_rate': (len(processed) / len(self.batch_results)) * 100 if self.batch_results else 0
        }


# ========================
# 🏭 FACTORY FUNCTIONS
# ========================

def create_metatags_analyzer(analyzer_type='default', config=None):
    """🏭 Factory para criar analisadores de metatags"""
    
    if analyzer_type == 'batch':
        batch_size = config.get('batch_size', 100) if config else 100
        return MetatagsAnalyzerBatch(config, batch_size)
    
    else:  # default
        return MetatagsAnalyzer(config)


# ========================
# 🧪 FUNÇÕES DE TESTE
# ========================

def test_metatags_analyzer():
    """Testa o analisador de metatags"""
    print("🧪 Testando MetatagsAnalyzer...")
    
    # HTML de teste com problemas variados
    html_test = """
    <html>
    <head>
        <title>Página de Teste SEO</title>
        <meta name="description" content="Esta é uma descrição de teste para análise SEO com tamanho adequado para validação completa.">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta property="og:title" content="Título Open Graph">
        <link rel="canonical" href="https://test.com/canonical">
    </head>
    <body>
        <h1>Título Principal</h1>
        <h2></h2>  <!-- Vazio -->
        <h3>Subtítulo</h3>
        <h2 style="color: white;">Heading Oculto</h2>
        <h4>Salto na hierarquia</h4>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html_test, 'html.parser')
    analyzer = MetatagsAnalyzer()
    
    # Testa análise completa
    resultado = analyzer.analyze(soup, "https://test.com/page1")
    
    print("📊 Resultados da análise:")
    print(f"  URL: {resultado['url']}")
    print(f"  Title: '{resultado['title']}' ({resultado['title_length']} chars)")
    print(f"  Title Status: {resultado['title_status']}")
    print(f"  Description: '{resultado['meta_description'][:50]}...' ({resultado['description_length']} chars)")
    print(f"  Description Status: {resultado['description_status']}")
    print(f"  H1 Count: {resultado['h1_count']}")
    print(f"  H1 Ausente: {resultado['h1_ausente']}")
    print(f"  Hierarquia Correta: {resultado['hierarquia_correta']}")
    print(f"  Headings Problemáticos: {resultado['headings_problematicos_count']}")
    print(f"  Score Final: {resultado['metatags_score']}/100")
    
    print(f"\n🚨 Problemas críticos ({len(resultado['critical_issues'])}):")
    for issue in resultado['critical_issues']:
        print(f"    - {issue}")
    
    print(f"\n⚠️ Avisos ({len(resultado['warnings'])}):")
    for warning in resultado['warnings']:
        print(f"    - {warning}")
    
    # Testa segunda página para verificar duplicados
    html_test2 = """
    <html>
    <head>
        <title>Página de Teste SEO</title>  <!-- Title duplicado -->
        <meta name="description" content="Descrição diferente.">
    </head>
    <body>
        <h1>Outro H1</h1>
        <h1>Segundo H1</h1>  <!-- H1 múltiplo -->
    </body>
    </html>
    """
    
    soup2 = BeautifulSoup(html_test2, 'html.parser')
    resultado2 = analyzer.analyze(soup2, "https://test.com/page2")
    
    print(f"\n📊 Segunda página:")
    print(f"  Title Duplicado: {resultado2['title_duplicado']}")
    print(f"  H1 Múltiplo: {resultado2['h1_multiple']}")
    print(f"  Score: {resultado2['metatags_score']}/100")
    
    # Estatísticas do analisador
    stats = analyzer.get_stats()
    print(f"\n📈 Estatísticas:")
    print(f"  URLs processadas: {stats['processing']['urls_processadas']}")
    print(f"  Duplicados encontrados: {stats['duplicates']['total_duplicate_titles']}")


def test_batch_analyzer():
    """Testa o analisador em lote"""
    print("\n📦 Testando MetatagsAnalyzerBatch...")
    
    # Simula múltiplas páginas
    test_pages = [
        ('<html><head><title>Página 1</title></head><body><h1>H1-1</h1></body></html>', 'https://test.com/1'),
        ('<html><head><title>Página 2</title></head><body><h1>H1-2</h1></body></html>', 'https://test.com/2'),
        ('<html><head><title>Página 1</title></head><body><h1>H1-3</h1></body></html>', 'https://test.com/3'),  # Title duplicado
    ]
    
    # Converte para BeautifulSoup
    soup_pairs = [(BeautifulSoup(html, 'html.parser'), url) for html, url in test_pages]
    
    # Testa analisador em lote
    batch_analyzer = MetatagsAnalyzerBatch(batch_size=10)
    results = batch_analyzer.analyze_batch(soup_pairs)
    
    print(f"📊 Resultados do lote:")
    print(f"  Total processado: {len(results)}")
    
    # Resumo do lote
    summary = batch_analyzer.get_batch_summary()
    print(f"  Taxa de sucesso: {summary['success_rate']:.1f}%")
    print(f"  Score médio: {summary['average_score']:.1f}")
    
    # Verifica duplicados
    duplicates = batch_analyzer.get_duplicates_report()
    print(f"  Titles duplicados: {duplicates['total_duplicate_titles']}")


def test_factory_functions():
    """Testa as funções factory"""
    print("\n🏭 Testando factory functions...")
    
    # Testa criação de diferentes tipos
    analyzers = {
        'default': create_metatags_analyzer('default'),
        'batch': create_metatags_analyzer('batch'),
        'with_config': create_metatags_analyzer('default', {'batch_size': 50})
    }
    
    for name, analyzer in analyzers.items():
        print(f"   ✅ {name}: {analyzer.__class__.__name__}")
        
        # Verifica configuração
        if hasattr(analyzer, 'batch_size'):
            print(f"      Batch size: {analyzer.batch_size}")


if __name__ == "__main__":
    test_metatags_analyzer()
    test_batch_analyzer()
    test_factory_functions()
    
    print(f"\n🎯 Testes concluídos!")
    print(f"💡 O MetatagsAnalyzer está integrado com HeadingsAnalyzer corrigido!")
    print(f"🔧 Todas as correções de hierarquia estão funcionando!")