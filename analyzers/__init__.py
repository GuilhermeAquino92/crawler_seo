# analyzers/__init__.py - Módulo de analisadores SEO

from .headings_analyzer import HeadingsAnalyzer, HeadingsScoreCalculator, HeadingsReportGenerator
from .metatags_analyzer import MetatagsAnalyzer, MetatagsAnalyzerBatch, create_metatags_analyzer

__all__ = [
    'HeadingsAnalyzer',
    'HeadingsScoreCalculator', 
    'HeadingsReportGenerator',
    'MetatagsAnalyzer',
    'MetatagsAnalyzerBatch',
    'create_metatags_analyzer'
]

__version__ = '1.0.0'
__author__ = 'SEO Analyzer Team'