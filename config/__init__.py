# config/__init__.py - Módulo de configurações

from .settings import (
    get_config, update_config, create_output_folders,
    DEFAULT_CONFIG, DEFAULT_URL, MAX_URLS_DEFAULT, MAX_THREADS_DEFAULT,  # 🆕 ADICIONADO DEFAULT_URL
    TITLE_MIN_LENGTH, TITLE_MAX_LENGTH, DESCRIPTION_MIN_LENGTH, DESCRIPTION_MAX_LENGTH
)

__all__ = [
    'get_config',
    'update_config', 
    'create_output_folders',
    'DEFAULT_CONFIG',
    'DEFAULT_URL',  
    'MAX_URLS_DEFAULT',
    'MAX_THREADS_DEFAULT',
    'TITLE_MIN_LENGTH',
    'TITLE_MAX_LENGTH',
    'DESCRIPTION_MIN_LENGTH', 
    'DESCRIPTION_MAX_LENGTH'
]