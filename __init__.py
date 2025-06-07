# __init__.py - SEO Analyzer Ultra Corrigido

"""
🏷️ SEO ANALYZER ULTRA CORRIGIDO

Analisador de SEO modularizado com todas as correções implementadas:
✅ Hierarquia de headings corrigida (ignora headings problemáticos)
✅ Detecção expandida de headings ocultos (cores invisíveis) 
✅ Consolidação em aba única para headings problemáticos
✅ Gravidade diferenciada (H1s = CRÍTICO, outros = MÉDIO)
✅ Sequências separadas (completa vs. válida)

Uso rápido:
    from seo_analyzer import quick_analysis
    filepath, df, stats = quick_analysis("https://example.com", max_urls=50)
"""

# Imports principais para uso direto
from .main import main, quick_analysis
from .analyzers import MetatagsAnalyzer, create_metatags_analyzer
from .core import create_crawler
from .reports import create_report_generator
from .config import get_config

__version__ = '1.0.0'
__author__ = 'SEO Analyzer Team'
__license__ = 'MIT'

__all__ = [
    'main',
    'quick_analysis',
    'MetatagsAnalyzer',
    'create_metatags_analyzer',
    'create_crawler',
    'create_report_generator',
    'get_config'
]


def get_version():
    """Retorna versão do projeto"""
    return __version__


def get_corrections_info():
    """Retorna informações sobre as correções implementadas"""
    return {
        'version': __version__,
        'corrections': [
            'Headings vazios/ocultos ignorados na análise hierárquica',
            'Detecção expandida de headings ocultos (cores invisíveis)',
            'Consolidação em aba única "Headings_Problematicos"', 
            'Gravidade diferenciada (H1s = CRÍTICO, outros = MÉDIO)',
            'Sequências separadas (Completa vs. Válida)'
        ],
        'modules': [
            'config - Configurações centralizadas',
            'utils - Constantes e utilitários',
            'core - Motor de crawling e gerenciamento',
            'analyzers - Análise de metatags e headings (CORRIGIDO)',
            'reports - Geração de relatórios Excel'
        ]
    }