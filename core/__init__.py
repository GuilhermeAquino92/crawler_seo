# core/__init__.py - Módulo principal do sistema

from .session_manager import SessionManager, RateLimitedSessionManager, MultiDomainSessionManager, create_session_manager
from .url_manager import URLManager, SmartURLManager, BatchURLManager, create_url_manager  
from .crawler import SEOCrawler, SmartSEOCrawler, BatchSEOCrawler, create_crawler

__all__ = [
    'SessionManager',
    'RateLimitedSessionManager',
    'MultiDomainSessionManager', 
    'create_session_manager',
    'URLManager',
    'SmartURLManager',
    'BatchURLManager',
    'create_url_manager',
    'SEOCrawler',
    'SmartSEOCrawler', 
    'BatchSEOCrawler',
    'create_crawler'
]

__version__ = '1.0.0'