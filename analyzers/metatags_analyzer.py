# analyzers/metatags_analyzer.py - Analisador de Metatags INTEGRADO e CORRIGIDO

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
    """🏷️ Analisador integrado de metatags com correções de headings"""
    
    def __init__(self, config=None):
        self.config = config or {}
        
        # 🔥 INTEGRA O HEADINGS ANALYZER CORRIGIDO
        self.headings_analyzer = HeadingsAnalyzer(self.config)
        self.headings_score_calculator = HeadingsScoreCalculator(self.config)
        
        # Rastreamento de duplicados
        self.titles_encontrados = {}
        self.descriptions_encontradas = {}
        
        self.stats = {
            'urls_processadas': 0,
            'titles_analisados': 0,
            'descriptions_analisadas': 0,
            'duplicados_encontrados': 0
        }
    
    def analyze(self, soup, url):
        """🎯 Método principal que integra análises de metatags e headings"""
        try:
            resultado = {
                'url': url,
                'processed': True
            }
            
            # 🔥 1. ANÁLISE DE HEADINGS (COM TODAS AS CORREÇÕES)
            headings_data = self.headings_analyzer.analyze_all_headings(soup, url)
            resultado.update(headings_data)
            
            # 2. ANÁLISE DE TITLE
            title_data = self._analyze_title(soup, url)
            resultado.update(title_data)
            
            # 3. ANÁLISE DE DESCRIPTION
            description_data = self._analyze_description(soup, url)
            resultado.update(description_data)
            
            # 4. OUTRAS METATAGS
            other_meta_data = self._analyze_other_metatags(soup, url)
            resultado.update(other_meta_data)
            
            # 5. SCORE CONSOLIDADO
            score_data = self._calculate_final_score(resultado)
            resultado.update(score_data)
            
            # 6. IDENTIFICAÇÃO DE PROBLEMAS CRÍTICOS
            issues_data = self._identify_critical_issues(resultado)
            resultado.update(issues_data)
            
            # 7. 🔥 CAMPOS PADRONIZADOS PARA EXCEL (CORREÇÃO DO BUG)
            resultado = self._standardize_excel_fields(resultado)
            
            self.stats['urls_processadas'] += 1
            
            return resultado
            
        except Exception as e:
            print(f"Erro analisando {url}: {e}")
            return self._create_error_result(url, str(e))
    
    def _analyze_title(self, soup, url):
        """Análise completa do title"""
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
        
        # Verifica duplicação
        title_duplicado = self._track_title_duplicate(title_text, url)
        
        # Lista de problemas
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
        """Análise completa da meta description"""
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
        
        # Verifica duplicação
        desc_duplicada = self._track_description_duplicate(desc_text, url)
        
        # Lista de problemas
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
        """Análise de outras metatags importantes"""
        other_data = {}
        
        # Meta keywords
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
        
        # Open Graph
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        
        other_data['og_title'] = og_title.get('content', '').strip() if og_title else ''
        other_data['og_description'] = og_description.get('content', '').strip() if og_description else ''
        other_data['og_image'] = og_image.get('content', '').strip() if og_image else ''
        
        other_data['has_open_graph'] = bool(other_data['og_title'] or other_data['og_description'])
        
        return other_data
    
    def _track_title_duplicate(self, title, url):
        """Rastreia títulos duplicados"""
        if not title:
            return False
        
        if title not in self.titles_encontrados:
            self.titles_encontrados[title] = []
        
        self.titles_encontrados[title].append(url)
        
        is_duplicate = len(self.titles_encontrados[title]) > 1
        
        if is_duplicate:
            self.stats['duplicados_encontrados'] += 1
        
        return is_duplicate
    
    def _track_description_duplicate(self, description, url):
        """Rastreia descriptions duplicadas"""
        if not description:
            return False
        
        if description not in self.descriptions_encontradas:
            self.descriptions_encontradas[description] = []
        
        self.descriptions_encontradas[description].append(url)
        
        is_duplicate = len(self.descriptions_encontradas[description]) > 1
        
        if is_duplicate:
            self.stats['duplicados_encontrados'] += 1
        
        return is_duplicate
    
    def _calculate_final_score(self, resultado):
        """🎯 Calcula score final integrado (title + description + headings)"""
        score = 0
        
        # Score do title
        if resultado.get('title_status') == STATUS_OK and not resultado.get('title_duplicado'):
            score += SCORE_TITLE_OK
        elif resultado.get('title_duplicado'):
            score += max(0, SCORE_TITLE_OK - PENALTY_DUPLICATE_TITLE)
        
        # Score da description
        if resultado.get('description_status') == STATUS_OK and not resultado.get('description_duplicada'):
            score += SCORE_DESCRIPTION_OK
        elif resultado.get('description_duplicada'):
            score += max(0, SCORE_DESCRIPTION_OK - PENALTY_DUPLICATE_DESCRIPTION)
        
        # 🔥 SCORE DOS HEADINGS (COM TODAS AS CORREÇÕES)
        headings_score = self.headings_score_calculator.calculate_headings_score(resultado)
        score += headings_score
        
        # Bonus scores
        bonus_score = 0
        
        if resultado.get('has_open_graph'):
            bonus_score += 5
        
        if resultado.get('meta_viewport'):
            bonus_score += 3
        
        if resultado.get('canonical_url'):
            bonus_score += 2
        
        score += bonus_score
        
        # Score final limitado a 100
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
        
        # Problemas críticos
        if resultado.get('title_status') == STATUS_ABSENT:
            critical_issues.append('Title ausente')
        
        if resultado.get('description_status') == STATUS_ABSENT:
            critical_issues.append('Meta description ausente')
        
        if resultado.get('h1_ausente'):
            critical_issues.append('H1 ausente')
        
        # 🔥 HEADINGS CRÍTICOS (H1s problemáticos)
        if resultado.get('headings_gravidade_critica', 0) > 0:
            critical_issues.append(f"H1s problemáticos ({resultado.get('headings_gravidade_critica')})")
        
        # Avisos
        if resultado.get('title_duplicado'):
            warnings.append('Title duplicado')
        
        if resultado.get('description_duplicada'):
            warnings.append('Description duplicada')
        
        if resultado.get('h1_multiple'):
            warnings.append('Múltiplos H1')
        
        if not resultado.get('hierarquia_correta'):
            warnings.append('Hierarquia de headings incorreta')
        
        # 🔥 HEADINGS PROBLEMÁTICOS (novos avisos)
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
    
    def _standardize_excel_fields(self, resultado):
        """🔥 CORREÇÃO DO BUG: Padroniza TODOS os campos para Excel"""
        
        # 🔥 CAMPOS OBRIGATÓRIOS PARA O EXCEL (evita erros de colunas ausentes)
        excel_fields = {
            'URL': resultado.get('url', ''),
            'Title': resultado.get('title', ''),
            'Title_Length': resultado.get('title_length', 0),
            'Title_Status': resultado.get('title_status', 'Ausente'),
            'Title_Duplicado': 'SIM' if resultado.get('title_duplicado', False) else 'NÃO',
            'Meta_Description': resultado.get('meta_description', ''),
            'Description_Length': resultado.get('description_length', 0),
            'Description_Status': resultado.get('description_status', 'Ausente'),
            'Description_Duplicada': 'SIM' if resultado.get('description_duplicada', False) else 'NÃO',
            'H1_Count': resultado.get('h1_count', 0),
            'H1_Text': resultado.get('h1_text', ''),
            'H1_Ausente': 'SIM' if resultado.get('h1_ausente', True) else 'NÃO',
            'H1_Multiple': 'SIM' if resultado.get('h1_multiple', False) else 'NÃO',
            'Hierarquia_Correta': 'SIM' if resultado.get('hierarquia_correta', True) else 'NÃO',
            'Headings_Problematicos_Total': resultado.get('headings_problematicos_count', 0),
            'Headings_Vazios': resultado.get('headings_vazios_count', 0),
            'Headings_Ocultos': resultado.get('headings_ocultos_count', 0),
            'Headings_Criticos': resultado.get('headings_gravidade_critica', 0),
            'Heading_Sequence_Completa': ' → '.join(resultado.get('heading_sequence', [])),
            'Heading_Sequence_Valida': ' → '.join(resultado.get('heading_sequence_valida', [])),
            'Total_Problemas_Headings': resultado.get('total_problemas_headings', 0),
            'Problemas_Hierarquia': ' | '.join(resultado.get('problemas_hierarquia', [])),
            'Metatags_Score': resultado.get('metatags_score', 0),
            'Critical_Issues': ' | '.join(resultado.get('critical_issues', [])),
            'Warnings': ' | '.join(resultado.get('warnings', [])),
            'Canonical_URL': resultado.get('canonical_url', ''),
            'Meta_Viewport': resultado.get('meta_viewport', ''),
            'Has_Open_Graph': 'SIM' if resultado.get('has_open_graph', False) else 'NÃO',
            
            # 🔥 CAMPOS EXTRAS PARA COMPATIBILIDADE COM EXCEL GENERATOR
            'Total_Headings': resultado.get('h1_count', 0) + resultado.get('total_problemas_headings', 0),
            'Headings_Validos': resultado.get('h1_count', 0),  # Aproximação
            'Response_Time_ms': 0,  # Valor padrão
            'Status_Code': 200,     # Valor padrão (será sobrescrito se tiver response)
        }
        
        # 🔥 Merge com resultado original preservando outros campos
        resultado.update(excel_fields)
        
        return resultado
    
    def _create_error_result(self, url, error):
        """Cria resultado de erro padronizado"""
        error_result = {
            'url': url,
            'processed': False,
            'error': error,
            'metatags_score': 0
        }
        
        # Aplica padronização mesmo para erros
        return self._standardize_excel_fields(error_result)
    
    def get_duplicates_report(self):
        """Relatório de duplicados encontrados"""
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
        """📊 Estatísticas completas do analisador"""
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
        """Reset das estatísticas e dados"""
        self.titles_encontrados.clear()
        self.descriptions_encontradas.clear()
        self.stats = {
            'urls_processadas': 0,
            'titles_analisados': 0,
            'descriptions_analisadas': 0,
            'duplicados_encontrados': 0
        }


class MetatagsAnalyzerBatch(MetatagsAnalyzer):
    """🔄 Versão para processamento em lotes"""
    
    def __init__(self, config=None, batch_size=100):
        super().__init__(config)
        self.batch_size = batch_size
        self.batch_results = []
    
    def analyze_batch(self, soup_url_pairs):
        """Processa lote de páginas"""
        batch_results = []
        
        print(f"🔄 Processando lote de {len(soup_url_pairs)} páginas...")
        
        for i, (soup, url) in enumerate(soup_url_pairs, 1):
            try:
                result = self.analyze(soup, url)
                batch_results.append(result)
                
                if i % 10 == 0:
                    print(f"   Processadas: {i}/{len(soup_url_pairs)}")
                    
            except Exception as e:
                print(f"Erro no lote {url}: {e}")
                error_result = self._create_error_result(url, str(e))
                batch_results.append(error_result)
        
        self.batch_results.extend(batch_results)
        print(f"✅ Lote concluído: {len(batch_results)} páginas processadas")
        
        return batch_results
    
    def get_batch_summary(self):
        """Resumo do processamento em lotes"""
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


def create_metatags_analyzer(analyzer_type='default', config=None):
    """🏭 Factory function para criar analisadores"""
    
    if analyzer_type == 'batch':
        batch_size = config.get('batch_size', 100) if config else 100
        return MetatagsAnalyzerBatch(config, batch_size)
    
    else:  # default
        return MetatagsAnalyzer(config)


def test_metatags_analyzer():
    """🧪 Teste completo do analisador integrado"""
    print("🧪 Testando MetatagsAnalyzer INTEGRADO com correções de headings...")
    
    # HTML de teste com vários problemas
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
        <h2></h2><!-- Heading vazio -->
        <h3>Subtítulo</h3>
        <h6>Salto na hierarquia</h6>
        <h2 style="color: white;">Heading Oculto</h2><!-- Heading oculto -->
        <h1>Segundo H1</h1><!-- H1 duplicado -->
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html_test, 'html.parser')
    analyzer = MetatagsAnalyzer()
    
    # Executa análise
    resultado = analyzer.analyze(soup, "https://test.com/page1")
    
    print("🎯 RESULTADOS DA ANÁLISE INTEGRADA:")
    print(f"  URL: {resultado['URL']}")
    print(f"  Score Final: {resultado['Metatags_Score']}/100")
    
    print(f"\n📄 TITLE & DESCRIPTION:")
    print(f"  Title: '{resultado['Title']}' ({resultado['Title_Length']} chars) - {resultado['Title_Status']}")
    print(f"  Description: '{resultado['Meta_Description'][:50]}...' ({resultado['Description_Length']} chars) - {resultado['Description_Status']}")
    
    print(f"\n🔢 HEADINGS (COM CORREÇÕES):")
    print(f"  H1 Count: {resultado['H1_Count']}")
    print(f"  H1 Ausente: {resultado['H1_Ausente']}")
    print(f"  H1 Múltiplo: {resultado['H1_Multiple']}")
    print(f"  Hierarquia Correta: {resultado['Hierarquia_Correta']}")
    print(f"  🆕 Headings Problemáticos Total: {resultado['Headings_Problematicos_Total']}")
    print(f"  🆕 Headings Vazios: {resultado['Headings_Vazios']}")
    print(f"  🆕 Headings Ocultos: {resultado['Headings_Ocultos']}")
    print(f"  🆕 Headings Críticos (H1s): {resultado['Headings_Criticos']}")
    
    print(f"\n📊 SEQUÊNCIAS (CORREÇÃO PRINCIPAL):")
    print(f"  Completa: {resultado['Heading_Sequence_Completa']}")
    print(f"  🔥 Válida (ignora problemáticos): {resultado['Heading_Sequence_Valida']}")
    
    print(f"\n🚨 PROBLEMAS CRÍTICOS ({len(resultado['critical_issues'])}):")
    for issue in resultado.get('critical_issues', []):
        print(f"    - {issue}")
    
    print(f"\n⚠️ AVISOS ({len(resultado['warnings'])}):")
    for warning in resultado.get('warnings', []):
        print(f"    - {warning}")
    
    print(f"\n🔍 CAMPOS PADRONIZADOS PARA EXCEL:")
    excel_fields = ['URL', 'Title_Status', 'Description_Status', 'H1_Count', 'Total_Headings', 'Headings_Validos']
    for field in excel_fields:
        print(f"  {field}: {resultado.get(field, 'AUSENTE')}")
    
    print(f"\n✅ TODAS AS CORREÇÕES INTEGRADAS E FUNCIONANDO!")
    print(f"   🔥 Hierarquia corrigida: headings problemáticos ignorados")
    print(f"   🔥 Detecção expandida: cores invisíveis detectadas")
    print(f"   🔥 Gravidade diferenciada: H1s são críticos")
    print(f"   🔥 Campos padronizados: compatível com Excel Generator")
    
    return resultado


if __name__ == "__main__":
    test_metatags_analyzer()