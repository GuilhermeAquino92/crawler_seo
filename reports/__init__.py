# reports/__init__.py - Módulo de relatórios (CORRIGIDO)

from .excel_generator import ExcelReportGenerator, create_report_generator

__all__ = [
    'ExcelReportGenerator',
    'create_report_generator'
]
