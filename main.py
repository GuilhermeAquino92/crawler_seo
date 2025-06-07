#!/usr/bin/env python3
# main.py - SEO Analyzer Modularizado - VERSÃO CORRIGIDA

"""
🏷️ SEO ANALYZER ULTRA CORRIGIDO

Analisador de SEO modularizado com todas as correções implementadas:
✅ Hierarquia de headings corrigida (ignora headings problemáticos)
✅ Detecção expandida de headings ocultos (cores invisíveis)
✅ Consolidação em aba única para headings problemáticos  
✅ Gravidade diferenciada (H1s = CRÍTICO, outros = MÉDIO)
✅ Sequências separadas (completa vs. válida)

Uso:
    python main.py --url https://example.com --max-urls 100 --threads 10
"""

import argparse
import sys
from urllib.parse import urlparse

# Imports dos módulos modularizados
from config.settings import get_config, DEFAULT_URL, MAX_URLS_DEFAULT, MAX_THREADS_DEFAULT
from core.crawler import create_crawler
from analyzers.metatags_analyzer import create_metatags_analyzer
from reports.excel_generator import create_report_generator
from utils.constants import (
    MSG_CRAWLER_START, MSG_ANALYSIS_START, MSG_ANALYSIS_COMPLETE,
    MSG_CORRECTIONS_IMPLEMENTED, MSG_IMPROVEMENTS, MSG_NEW_CONSOLIDATED_TAB
)


def parse_arguments():
    """📋 Parse argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description='🏷️ SEO Analyzer Ultra Corrigido - Análise completa de metatags',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 CRAWLING MÁXIMO - ANÁLISE COMPLETA DE DOMÍNIO:
  python main.py --url https://seusite.com.br
  python main.py --url https://exemplo.com --threads 30
  python main.py --url https://loja.com.br --max-urls 5000

📋 CONFIGURAÇÃO OTIMIZADA PARA MÁXIMO CRAWLING:
  ✅ Padrão: 10.000 URLs máximas (ajustável)
  ✅ Padrão: Profundidade 10 níveis (completa)
  ✅ Padrão: 25 threads (alta velocidade)
  ✅ Padrão: Crawler inteligente com priorização

🎯 USO RECOMENDADO:
  Apenas informe a URL do domínio - o sistema vai buscar TODAS as páginas possíveis!

Tipos de crawler:
  smart   - Crawler inteligente com priorização (PADRÃO)
  default - Crawler padrão
  batch   - Crawler otimizado para lotes grandes

Correções implementadas:
  ✅ Headings vazios/ocultos ignorados na análise hierárquica
  ✅ Detecção expandida de headings ocultos (cores invisíveis)
  ✅ Consolidação em aba única "Headings_Problematicos"
  ✅ Gravidade diferenciada (H1s = CRÍTICO, outros = MÉDIO)
        """
    )
    
    parser.add_argument(
        '--url',
        type=str,
        required=True,  # 🔥 OBRIGATÓRIO: Usuário DEVE informar URL
        help='URL inicial para análise completa do domínio (OBRIGATÓRIO)'
    )
    
    parser.add_argument(
        '--max-urls',
        type=int,
        default=MAX_URLS_DEFAULT,
        help=f'Número máximo de URLs para analisar (padrão: {MAX_URLS_DEFAULT} - CRAWLING MÁXIMO)'
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        default=10,  # 🔥 PADRÃO MAIOR: Profundidade máxima para pegar todas as páginas
        help='Profundidade máxima de crawling (padrão: 10 - BUSCA COMPLETA)'
    )
    
    parser.add_argument(
        '--threads',
        type=int,
        default=MAX_THREADS_DEFAULT,
        help=f'Número de threads para crawling (padrão: {MAX_THREADS_DEFAULT} - ALTA VELOCIDADE)'
    )
    
    parser.add_argument(
        '--crawler',
        choices=['default', 'smart', 'batch'],
        default='smart',  # 🔥 PADRÃO INTELIGENTE: Crawler com priorização
        help='Tipo de crawler a usar (padrão: smart - CRAWLER INTELIGENTE)'
    )
    
    parser.add_argument(
        '--analyzer',
        choices=['default', 'batch'],
        default='default',
        help='Tipo de analisador a usar (padrão: default)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Tamanho do lote para processamento (padrão: 100)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Pasta de saída para relatórios (padrão: output)'
    )
    
    parser.add_argument(
        '--emoji-names',
        action='store_true',
        help='Usar nomes com emoji nas abas do Excel'
    )
    
    parser.add_argument(
        '--filename',
        type=str,
        default='METATAGS_ULTRA',
        help='Prefixo do nome do arquivo de relatório (padrão: METATAGS_ULTRA)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=15,
        help='Timeout para requisições em segundos (padrão: 15)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verboso com mais detalhes'
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
    
    if args.max_depth <= 0:
        errors.append("❌ max-depth deve ser maior que 0")
    
    if args.threads <= 0 or args.threads > 50:
        errors.append("❌ threads deve estar entre 1 e 50")
    
    if args.batch_size <= 0:
        errors.append("❌ batch-size deve ser maior que 0")
    
    if args.timeout <= 0:
        errors.append("❌ timeout deve ser maior que 0")
    
    return errors


def create_config_from_args(args):
    """🔧 Cria configuração baseada nos argumentos"""
    config = get_config()
    
    # Atualiza configurações do crawler
    config['crawler'].update({
        'max_urls': args.max_urls,
        'max_depth': args.max_depth,
        'max_threads': args.threads,
        'timeout': args.timeout
    })
    
    # Configurações do analisador
    config['analyzer'] = {
        'type': args.analyzer,
        'batch_size': args.batch_size
    }
    
    # Configurações de saída
    config['output'].update({
        'folder': args.output,
        'use_emoji_names': args.emoji_names,
        'filename_prefix': args.filename
    })
    
    # Configurações de crawler específicas
    if args.crawler == 'smart':
        config['priority_patterns'] = [
            '/produto/', '/product/', '/categoria/', '/category/',
            '/servico/', '/service/', '/sobre/', '/about/'
        ]
    elif args.crawler == 'batch':
        config['batch_size'] = args.batch_size
    
    return config


def print_startup_info(args, config):
    """📢 Exibe informações de inicialização"""
    domain = urlparse(args.url).netloc
    
    print("=" * 80)
    print("🏷️  SEO ANALYZER ULTRA - CRAWLING MÁXIMO DE DOMÍNIO")
    print("=" * 80)
    
    print("🔥 CONFIGURAÇÃO PARA MÁXIMO CRAWLING:")
    print("   ✅ Busca TODAS as páginas possíveis do domínio")
    print("   ✅ Crawler inteligente com priorização automática")
    print("   ✅ Multi-threading para alta velocidade")
    print("   ✅ Filtros automáticos para URLs relevantes")
    
    print(MSG_CORRECTIONS_IMPLEMENTED)
    print(MSG_IMPROVEMENTS)
    print(MSG_NEW_CONSOLIDATED_TAB)
    
    print("\n📊 CONFIGURAÇÕES DE CRAWLING MÁXIMO:")
    print(f"   🎯 URL inicial: {args.url}")
    print(f"   📈 Max URLs: {args.max_urls:,} (MÁXIMO POSSÍVEL)")
    print(f"   📏 Max profundidade: {args.max_depth} (BUSCA COMPLETA)")
    print(f"   ⚡ Threads: {args.threads} (ALTA VELOCIDADE)")
    print(f"   🕷️ Tipo de crawler: {args.crawler} (INTELIGENTE)")
    print(f"   🏷️ Tipo de analisador: {args.analyzer}")
    print(f"   📦 Batch size: {args.batch_size}")
    print(f"   📁 Pasta de saída: {args.output}")
    print(f"   ⏱️ Timeout: {args.timeout}s")
    
    print(f"\n🚀 Iniciando CRAWLING MÁXIMO do domínio: {domain}")
    print(f"⚡ O sistema vai buscar TODAS as páginas possíveis!")
    print("=" * 80)


def main():
    """🚀 Função principal"""
    try:
        # 1. Parse e validação de argumentos
        args = parse_arguments()
        
        validation_errors = validate_arguments(args)
        if validation_errors:
            print("❌ ERROS DE VALIDAÇÃO:")
            for error in validation_errors:
                print(f"   {error}")
            sys.exit(1)
        
        # 2. Cria configuração
        config = create_config_from_args(args)
        
        # 3. Exibe informações de inicialização
        print_startup_info(args, config)
        
        # 4. Cria componentes modulares
        print("🔧 Inicializando componentes...")
        
        crawler = create_crawler(args.crawler, config)
        print(f"   ✅ Crawler '{args.crawler}' criado")
        
        analyzer = create_metatags_analyzer(args.analyzer, config)
        print(f"   ✅ Analisador '{args.analyzer}' criado")
        
        report_generator = create_report_generator('default', config['output'])
        print(f"   ✅ Gerador de relatórios criado")
        
        # 5. Executa crawling e análise
        print("\n🕷️ FASE 1: CRAWLING E ANÁLISE")
        print(MSG_CRAWLER_START.format(domain=urlparse(args.url).netloc))
        
        results = crawler.crawl(
            start_url=args.url,
            max_urls=args.max_urls,
            analyzers=[analyzer]
        )
        
        if not results:
            print("❌ Nenhum resultado obtido do crawling!")
            sys.exit(1)
        
        print(MSG_ANALYSIS_COMPLETE.format(total_urls=len(results)))
        
        # 6. Gera relatório
        print("\n📊 FASE 2: GERAÇÃO DE RELATÓRIOS")
        
        filepath, df_principal = report_generator.generate_complete_report(
            results=results,
            crawlers_data=analyzer,
            filename_prefix=args.filename
        )
        
        if not filepath:
            print("❌ Erro na geração do relatório!")
            sys.exit(1)
        
        # 7. Exibe estatísticas finais
        print("\n📈 FASE 3: ESTATÍSTICAS FINAIS")
        print("=" * 80)
        
        # Estatísticas do crawler
        crawler_stats = crawler.get_stats()
        print("🕷️ ESTATÍSTICAS DO CRAWLER:")
        print(f"   URLs encontradas: {crawler_stats['crawling']['urls_found']}")
        print(f"   URLs processadas: {crawler_stats['crawling']['urls_processed']}")
        print(f"   Taxa de sucesso: {crawler_stats['summary']['success_rate']:.1f}%")
        print(f"   Tempo total: {crawler_stats['summary']['total_crawling_time']:.2f}s")
        print(f"   URLs/segundo: {crawler_stats['summary']['urls_per_second']:.2f}")
        
        # Estatísticas do analisador
        analyzer_stats = analyzer.get_stats()
        print(f"\n🏷️ ESTATÍSTICAS DO ANALISADOR:")
        print(f"   URLs analisadas: {analyzer_stats['processing']['urls_processadas']}")
        print(f"   Titles duplicados únicos: {analyzer_stats['duplicates']['total_duplicate_titles']}")
        print(f"   Descriptions duplicadas únicas: {analyzer_stats['duplicates']['total_duplicate_descriptions']}")
        
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
            
            # Headings problemáticos (NOVA MÉTRICA)
            headings_problematicos = len(df_principal[df_principal['Headings_Problematicos_Total'] > 0])
            print(f"   🆕 URLs com headings problemáticos: {headings_problematicos}")
            
            # Top 3 problemas
            if criticos > 0:
                top_issues = []
                
                # Title ausente
                title_ausente = len(df_principal[df_principal['Title_Status'] == 'Ausente'])
                if title_ausente > 0:
                    top_issues.append(f"Titles ausentes ({title_ausente})")
                
                # Description ausente
                desc_ausente = len(df_principal[df_principal['Description_Status'] == 'Ausente'])
                if desc_ausente > 0:
                    top_issues.append(f"Descriptions ausentes ({desc_ausente})")
                
                # H1 ausente
                h1_ausente = len(df_principal[df_principal['H1_Ausente'] == 'SIM'])
                if h1_ausente > 0:
                    top_issues.append(f"H1s ausentes ({h1_ausente})")
                
                if top_issues:
                    print(f"   Top problemas: {', '.join(top_issues[:3])}")
        
        # 8. Informações finais
        print("\n🎯 ANÁLISE CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print(f"📁 Relatório gerado: {filepath}")
        print("\n💡 PRINCIPAIS CORREÇÕES IMPLEMENTADAS:")
        print("   ✅ Headings vazios/ocultos IGNORADOS na análise hierárquica")
        print("   ✅ Detecção EXPANDIDA de headings ocultos (cores invisíveis)")
        print("   ✅ Consolidação em aba única 'Headings_Problematicos'")
        print("   ✅ Gravidade diferenciada (H1s = CRÍTICO, outros = MÉDIO)")
        print("   ✅ Sequências separadas (Completa vs. Válida)")
        
        print(f"\n🔥 Abra o arquivo Excel para ver todas as 8 abas com as correções!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n⚠️ Análise interrompida pelo usuário")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {str(e)}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def quick_analysis(url, max_urls=10000):  # 🔥 PADRÃO MAIOR
    """⚡ Função para análise rápida com configuração máxima (uso programático)"""
    config = get_config()
    config['crawler']['max_urls'] = max_urls
    config['crawler']['max_depth'] = 10      # 🔥 PROFUNDIDADE MÁXIMA
    config['crawler']['max_threads'] = 25    # 🔥 ALTA VELOCIDADE
    
    # Componentes com configuração otimizada
    crawler = create_crawler('smart', config)  # 🔥 CRAWLER INTELIGENTE
    analyzer = create_metatags_analyzer('default', config)
    report_generator = create_report_generator('default', config['output'])
    
    # Execução
    results = crawler.crawl(url, max_urls, [analyzer])
    
    if results:
        filepath, df = report_generator.generate_complete_report(
            results, analyzer, "QUICK_ANALYSIS_MAXIMO"
        )
        return filepath, df, analyzer.get_stats()
    
    return None, None, None


if __name__ == "__main__":
    main()