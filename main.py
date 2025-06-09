#!/usr/bin/env python3
# main.py - SEO Analyzer Integrado CORRIGIDO

"""
🏷️ SEO ANALYZER ULTRA COMPLETO - VERSÃO CORRIGIDA

Integra TODOS os analyzers:
✅ HeadingsAnalyzer (com correções)
✅ MetatagsAnalyzer (title, description, SEO)
✅ StatusAnalyzer (HTTP status, mixed content)

🚀 USO:
    python main.py                    # URL padrão
    python main.py --url https://exemplo.com
    python main.py --max-urls 500     # Análise rápida
"""

import argparse
import sys
from urllib.parse import urlparse

# Imports dos módulos modularizados
from config.settings import get_config, DEFAULT_URL, MAX_URLS_DEFAULT, MAX_THREADS_DEFAULT
from core.crawler import create_crawler
from analyzers.metatags_analyzer import MetatagsAnalyzer
from analyzers.headings_analyzer import HeadingsAnalyzer
from analyzers.status_analyzer import StatusAnalyzer
from reports.excel_generator import create_report_generator
from utils.constants import (
    MSG_CRAWLER_START, MSG_ANALYSIS_START, MSG_ANALYSIS_COMPLETE,
    MSG_CORRECTIONS_IMPLEMENTED, MSG_IMPROVEMENTS, MSG_NEW_CONSOLIDATED_TAB
)


class IntegratedAnalyzer:
    """🔥 Analyzer integrado que combina todos os analyzers"""
    
    def __init__(self, config=None):
        self.config = config or {}
        
        # Instancia todos os analyzers
        self.metatags_analyzer = MetatagsAnalyzer(self.config)
        self.headings_analyzer = HeadingsAnalyzer(self.config)
        self.status_analyzer = StatusAnalyzer(self.config)
        
        self.stats = {
            'urls_processadas': 0,
            'urls_com_erro': 0
        }
    
    def analyze(self, soup, url, response=None):
        """🎯 Análise integrada completa"""
        try:
            # Resultado base
            resultado = {
                'url': url,
                'processed': True
            }
            
            # 1. ANÁLISE DE METATAGS (inclui headings internamente)
            metatags_data = self.metatags_analyzer.analyze(soup, url)
            resultado.update(metatags_data)
            
            # 2. ANÁLISE DE STATUS E MIXED CONTENT
            status_data = self.status_analyzer.analyze(soup, url, response)
            resultado.update(status_data)
            
            # 3. CONSOLIDAÇÃO FINAL
            resultado = self._consolidate_results(resultado)
            
            self.stats['urls_processadas'] += 1
            
            return resultado
            
        except Exception as e:
            print(f"Erro na análise integrada de {url}: {e}")
            self.stats['urls_com_erro'] += 1
            
            return {
                'url': url,
                'processed': False,
                'error': str(e),
                'Status_Code': 'ERROR',
                'metatags_score': 0
            }
    
    def _consolidate_results(self, resultado):
        """🔧 Consolida resultados de todos os analyzers"""
        
        # Garante que campos obrigatórios existem
        if 'Warnings' not in resultado:
            resultado['Warnings'] = []
        
        if 'mixed_content_resources' not in resultado:
            resultado['mixed_content_resources'] = []
        
        # Consolida warnings de diferentes sources
        all_warnings = []
        
        # Warnings de status
        if resultado.get('Warnings'):
            all_warnings.extend(resultado['Warnings'])
        
        # Warnings de metatags
        if resultado.get('warnings'):
            all_warnings.extend(resultado['warnings'])
        
        # Warnings de headings críticos
        if resultado.get('critical_issues'):
            all_warnings.extend([f"CRÍTICO: {issue}" for issue in resultado['critical_issues']])
        
        resultado['Warnings'] = all_warnings
        
        # Padroniza campos para Excel
        resultado = self._standardize_excel_fields(resultado)
        
        return resultado
    
    def _standardize_excel_fields(self, resultado):
        """📊 Padroniza campos para o Excel"""
        
        # Campos obrigatórios com valores padrão
        excel_fields = {
            'URL': resultado.get('url', ''),
            'Status_Code': resultado.get('Status_Code', 'UNKNOWN'),
            'Response_Time_ms': resultado.get('Response_Time', 0),
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
            'Metatags_Score': resultado.get('metatags_score', 0),
            'Critical_Issues': ' | '.join(resultado.get('critical_issues', [])),
            'Warnings': ' | '.join(resultado.get('Warnings', [])),
            'Has_Mixed_Content': 'SIM' if resultado.get('has_mixed_content', False) else 'NÃO',
            'Mixed_Content_Count': resultado.get('mixed_content_count', 0),
            'Canonical_URL': resultado.get('canonical_url', ''),
            'Meta_Viewport': resultado.get('meta_viewport', ''),
            'Has_Open_Graph': 'SIM' if resultado.get('has_open_graph', False) else 'NÃO'
        }
        
        # Atualiza resultado com campos padronizados
        resultado.update(excel_fields)
        
        return resultado
    
    def get_stats(self):
        """📊 Estatísticas consolidadas"""
        metatags_stats = self.metatags_analyzer.get_stats()
        status_stats = self.status_analyzer.get_stats()
        
        return {
            'integrated': self.stats.copy(),
            'metatags': metatags_stats,
            'status': status_stats,
            'summary': {
                'total_urls_processadas': self.stats['urls_processadas'],
                'total_urls_com_erro': self.stats['urls_com_erro'],
                'success_rate': (self.stats['urls_processadas'] / max(self.stats['urls_processadas'] + self.stats['urls_com_erro'], 1)) * 100
            }
        }


def parse_arguments():
    """📋 Parse argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description='🏷️ SEO Analyzer Ultra Completo - Análise integrada',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 ANÁLISE COMPLETA INTEGRADA:
  • HeadingsAnalyzer: hierarquia, h1s, sequências (COM CORREÇÕES)
  • MetatagsAnalyzer: title, description, duplicados, scores
  • StatusAnalyzer: códigos HTTP, mixed content, redirects

✅ GERA PLANILHA EXCEL COMPLETA COM TODAS AS ABAS:
  • Metatags_Ultra_Complete: dados principais
  • Headings_Problematicos: headings vazios/ocultos consolidados
  • Title_Duplicados: títulos duplicados
  • Desc_Duplicadas: descriptions duplicadas  
  • Mixed_Content: recursos HTTP em páginas HTTPS
  • Score_Ranking: páginas ordenadas por score
  • Resumo: estatísticas gerais

🎯 URL PADRÃO: {default_url}
        """.format(default_url=DEFAULT_URL)
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default=DEFAULT_URL,
        help=f'URL inicial para análise (padrão: {DEFAULT_URL})'
    )
    
    parser.add_argument(
        '--max-urls',
        type=int,
        default=MAX_URLS_DEFAULT,
        help=f'Número máximo de URLs para analisar (padrão: {MAX_URLS_DEFAULT})'
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        default=10,
        help='Profundidade máxima de crawling (padrão: 10)'
    )
    
    parser.add_argument(
        '--threads',
        type=int,
        default=MAX_THREADS_DEFAULT,
        help=f'Número de threads para crawling (padrão: {MAX_THREADS_DEFAULT})'
    )
    
    parser.add_argument(
        '--crawler',
        choices=['default', 'smart', 'batch'],
        default='smart',
        help='Tipo de crawler a usar (padrão: smart)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Pasta de saída para relatórios (padrão: output)'
    )
    
    parser.add_argument(
        '--filename',
        type=str,
        default='SEO_ANALYSIS_COMPLETE',
        help='Prefixo do nome do arquivo de relatório'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Análise rápida (100 URLs, 5 threads)'
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """✅ Valida argumentos fornecidos"""
    errors = []
    
    # Valida URL
    try:
        parsed_url = urlparse(args.url)
        if not parsed_url.scheme or not parsed_url.netloc:
            errors.append(f"❌ URL inválida: {args.url}")
    except Exception:
        errors.append(f"❌ Erro parsing URL: {args.url}")
    
    # Valida números
    if args.max_urls <= 0:
        errors.append("❌ max-urls deve ser maior que 0")
    
    if args.threads <= 0 or args.threads > 50:
        errors.append("❌ threads deve estar entre 1 e 50")
    
    return errors


def apply_quick_mode(args):
    """⚡ Aplica configurações de modo rápido"""
    if args.quick:
        args.max_urls = min(args.max_urls, 100)
        args.threads = min(args.threads, 5)
        args.max_depth = min(args.max_depth, 3)
        print("⚡ MODO RÁPIDO ativado: 100 URLs máx, 5 threads, profundidade 3")


def create_config_from_args(args):
    """🔧 Cria configuração baseada nos argumentos"""
    config = get_config()
    
    # Atualiza configurações do crawler
    config['crawler'].update({
        'max_urls': args.max_urls,
        'max_depth': args.max_depth,
        'max_threads': args.threads,
        'timeout': 15
    })
    
    # Configurações de saída
    config['output'].update({
        'folder': args.output,
        'use_emoji_names': True,
        'filename_prefix': args.filename
    })
    
    return config


def print_startup_info(args):
    """📢 Exibe informações de inicialização"""
    domain = urlparse(args.url).netloc
    
    print("=" * 80)
    print("🏷️  SEO ANALYZER ULTRA COMPLETO - ANÁLISE INTEGRADA")
    print("=" * 80)
    
    print("🔥 ANALYZERS INTEGRADOS:")
    print("   ✅ HeadingsAnalyzer: hierarquia, H1s, sequências (COM CORREÇÕES)")
    print("   ✅ MetatagsAnalyzer: title, description, duplicados, scores")
    print("   ✅ StatusAnalyzer: códigos HTTP, mixed content, redirects")
    
    print(MSG_CORRECTIONS_IMPLEMENTED)
    print(MSG_IMPROVEMENTS)
    print(MSG_NEW_CONSOLIDATED_TAB)
    
    print(f"\n📊 CONFIGURAÇÕES DE ANÁLISE:")
    print(f"   🎯 URL inicial: {args.url}")
    print(f"   📈 Max URLs: {args.max_urls:,}")
    print(f"   📏 Max profundidade: {args.max_depth}")
    print(f"   ⚡ Threads: {args.threads}")
    print(f"   🕷️ Tipo de crawler: {args.crawler}")
    print(f"   📁 Pasta de saída: {args.output}")
    
    print(f"\n🚀 Iniciando análise COMPLETA do domínio: {domain}")
    print("=" * 80)


class ModifiedCrawler:
    """🔧 Wrapper do crawler para passar response para analyzers"""
    
    def __init__(self, crawler, integrated_analyzer):
        self.crawler = crawler
        self.integrated_analyzer = integrated_analyzer
    
    def crawl(self, start_url, max_urls=None, analyzers=None):
        """🔥 Crawl modificado que passa response para analyzers"""
        
        # Substitui o método _process_single_url do crawler
        original_process = self.crawler._process_single_url
        
        def modified_process_single_url(url, depth, analyzers_ignored):
            # Chama o processo original para obter response
            result = original_process(url, depth, [])  # Sem analyzers no original
            
            # Se foi bem-sucedido, faz nossa análise integrada
            if result.get('status_code') == 200 and 'text/html' in result.get('content_type', '').lower():
                try:
                    # Faz nova requisição para obter soup
                    response = self.crawler.session_manager.get(url)
                    
                    if response.status_code == 200:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Análise integrada com soup, url E response
                        analysis_result = self.integrated_analyzer.analyze(soup, url, response)
                        
                        # Merge com resultado original
                        result.update(analysis_result)
                
                except Exception as e:
                    print(f"Erro na análise integrada de {url}: {e}")
                    result['analysis_error'] = str(e)
            
            return result
        
        # Substitui método temporariamente
        self.crawler._process_single_url = modified_process_single_url
        
        # Executa crawl
        try:
            return self.crawler.crawl(start_url, max_urls, [])  # Sem analyzers externos
        finally:
            # Restaura método original
            self.crawler._process_single_url = original_process


def main():
    """🚀 Função principal CORRIGIDA"""
    try:
        # 1. Parse e validação de argumentos
        args = parse_arguments()
        
        # 2. Aplica modo rápido se solicitado
        apply_quick_mode(args)
        
        # 3. Validação
        validation_errors = validate_arguments(args)
        if validation_errors:
            print("❌ ERROS DE VALIDAÇÃO:")
            for error in validation_errors:
                print(f"   {error}")
            sys.exit(1)
        
        # 4. Cria configuração
        config = create_config_from_args(args)
        
        # 5. Exibe informações de inicialização
        print_startup_info(args)
        
        # 6. Cria componentes integrados
        print("🔧 Inicializando componentes integrados...")
        
        # Crawler base
        base_crawler = create_crawler(args.crawler, config)
        print(f"   ✅ Crawler '{args.crawler}' criado")
        
        # Analyzer integrado
        integrated_analyzer = IntegratedAnalyzer(config)
        print(f"   ✅ Analyzer integrado criado (Metatags + Headings + Status)")
        
        # Crawler modificado
        crawler = ModifiedCrawler(base_crawler, integrated_analyzer)
        print(f"   ✅ Crawler integrado configurado")
        
        # Gerador de relatórios
        report_generator = create_report_generator('default', config['output'])
        print(f"   ✅ Gerador de relatórios criado")
        
        # 7. Executa crawling e análise integrada
        print("\n🕷️ FASE 1: CRAWLING E ANÁLISE INTEGRADA")
        print(MSG_CRAWLER_START.format(domain=urlparse(args.url).netloc))
        
        results = crawler.crawl(
            start_url=args.url,
            max_urls=args.max_urls
        )
        
        if not results:
            print("❌ Nenhum resultado obtido do crawling!")
            sys.exit(1)
        
        print(MSG_ANALYSIS_COMPLETE.format(total_urls=len(results)))
        
        # 8. Gera relatório completo - CORREÇÃO APLICADA
        print("\n📊 FASE 2: GERAÇÃO DE RELATÓRIOS INTEGRADOS")
        
        # 🔥 CORREÇÃO: Usar apenas os parâmetros corretos
        filepath, df_principal = report_generator.generate_complete_report(
            results=results,
            filename_prefix=args.filename
        )
        
        if not filepath:
            print("❌ Erro na geração do relatório!")
            sys.exit(1)
        
        # 9. Exibe estatísticas finais
        print("\n📈 FASE 3: ESTATÍSTICAS FINAIS INTEGRADAS")
        print("=" * 80)
        
        # Estatísticas do crawler
        crawler_stats = base_crawler.get_stats()
        print("🕷️ ESTATÍSTICAS DO CRAWLER:")
        print(f"   URLs encontradas: {crawler_stats['crawling']['urls_found']}")
        print(f"   URLs processadas: {crawler_stats['crawling']['urls_processed']}")
        print(f"   Taxa de sucesso: {crawler_stats['summary']['success_rate']:.1f}%")
        print(f"   Tempo total: {crawler_stats['summary']['total_crawling_time']:.2f}s")
        
        # Estatísticas integradas
        integrated_stats = integrated_analyzer.get_stats()
        print(f"\n🔥 ESTATÍSTICAS INTEGRADAS:")
        print(f"   URLs analisadas: {integrated_stats['integrated']['urls_processadas']}")
        print(f"   URLs com erro: {integrated_stats['integrated']['urls_com_erro']}")
        print(f"   Taxa de sucesso análise: {integrated_stats['summary']['success_rate']:.1f}%")
        
        # Estatísticas específicas
        metatags_stats = integrated_stats['metatags']
        status_stats = integrated_stats['status']
        
        print(f"\n🏷️ METATAGS & HEADINGS:")
        print(f"   Titles duplicados únicos: {metatags_stats['duplicates']['total_duplicate_titles']}")
        print(f"   Descriptions duplicadas únicas: {metatags_stats['duplicates']['total_duplicate_descriptions']}")
        
        print(f"\n🚨 STATUS & MIXED CONTENT:")
        print(f"   Páginas com status errors: {status_stats['processing']['status_errors']}")
        print(f"   Páginas com mixed content: {status_stats['processing']['mixed_content_found']}")
        print(f"   Redirects encontrados: {status_stats['processing']['redirects_found']}")
        
        # Estatísticas do relatório
        if not df_principal.empty:
            print(f"\n📊 ESTATÍSTICAS DO RELATÓRIO:")
            print(f"   Páginas no relatório: {len(df_principal)}")
            
            # Score médio
            score_medio = df_principal['Metatags_Score'].mean()
            print(f"   Score médio: {score_medio:.1f}/100")
            
            # Problemas críticos
            criticos = len(df_principal[df_principal['Critical_Issues'] != ''])
            print(f"   URLs com problemas críticos: {criticos}")
            
            # Headings problemáticos
            headings_problematicos = len(df_principal[df_principal['Headings_Problematicos_Total'] > 0])
            print(f"   URLs com headings problemáticos: {headings_problematicos}")
            
            # Mixed content
            mixed_content = len(df_principal[df_principal['Has_Mixed_Content'] == 'SIM'])
            print(f"   URLs com mixed content: {mixed_content}")
        
        # 10. Informações finais
        print("\n🎯 ANÁLISE INTEGRADA CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print(f"📁 Relatório completo gerado: {filepath}")
        print("\n💡 ANÁLISES REALIZADAS:")
        print("   ✅ Headings: hierarquia, H1s, vazios/ocultos (COM CORREÇÕES)")
        print("   ✅ Metatags: title, description, duplicados, scores")
        print("   ✅ Status: códigos HTTP, redirects, mixed content")
        print("   ✅ Consolidação: uma planilha com todas as abas")
        
        print(f"\n🔥 Abra o arquivo Excel para ver TODAS as análises integradas!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n⚠️ Análise interrompida pelo usuário")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def quick_analysis(url, max_urls=100, output_folder="output"):
    """🚀 Função de conveniência para análise rápida"""
    try:
        config = get_config()
        config['crawler'].update({
            'max_urls': max_urls,
            'max_depth': 3,
            'max_threads': 5
        })
        config['output']['folder'] = output_folder
        
        # Componentes
        crawler = create_crawler('smart', config)
        analyzer = IntegratedAnalyzer(config)
        reporter = create_report_generator('default', config['output'])
        
        # Wrapper
        modified_crawler = ModifiedCrawler(crawler, analyzer)
        
        # Execução
        results = modified_crawler.crawl(url, max_urls)
        
        if results:
            filepath, df = reporter.generate_complete_report(
                results, 
                filename_prefix="QUICK_ANALYSIS"
            )
            
            stats = analyzer.get_stats()
            
            return filepath, df, stats
        
        return None, None, None
        
    except Exception as e:
        print(f"Erro na análise rápida: {e}")
        return None, None, None


if __name__ == "__main__":
    main()