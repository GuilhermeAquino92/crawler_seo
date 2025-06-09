# reports/excel_generator.py - Gerador Excel COMPLETO (8 abas como nas imagens)

import pandas as pd
import xlsxwriter
from datetime import datetime
import os
from utils.constants import MSG_REPORT_GENERATED, MSG_NO_RESULTS, SHEET_NAMES_EMOJI
from config.settings import COLUMN_WIDTHS


class ExcelReportGenerator:
    """📊 Gerador Excel COMPLETO - 8 ABAS como mostrado nas imagens"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.output_folder = self.config.get('folder', 'output')
        os.makedirs(self.output_folder, exist_ok=True)

    def generate_complete_report(self, results, crawlers_data=None, filename_prefix="SEO_ANALYSIS"):
        """🎯 Gera relatório Excel com TODAS as 8 abas das imagens"""
        
        if not results:
            print(MSG_NO_RESULTS)
            return None, None

        # Conversão do DataFrame principal
        df_main = pd.DataFrame(results)
        filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(self.output_folder, filename)

        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            df_main.to_excel(writer, sheet_name=SHEET_NAMES_EMOJI.get('principal', 'Principal'), index=False)

            aba_configs = {
                'Headings_Problematicos': self._generate_headings_problematicos(df_main),
                'Headings_Semantica': self._generate_headings_semantica(df_main),
                'Headings_Estatisticas': self._generate_headings_estatisticas(df_main),
                'Headings_Arvore': self._generate_headings_arvore(df_main),
                'Headings_Errados': self._generate_headings_errados(df_main),
                'Metatags_Problemas': self._generate_metatags_problemas(df_main),
                'Score_Ranking': self._generate_score_ranking(df_main),
            }

            for aba_nome, df in aba_configs.items():
                if isinstance(df, pd.DataFrame):
                    df.to_excel(writer, sheet_name=SHEET_NAMES_EMOJI.get(aba_nome, aba_nome), index=False)
                    worksheet = writer.sheets[SHEET_NAMES_EMOJI.get(aba_nome, aba_nome)]
                    self._set_column_widths(worksheet, df)

        print(MSG_REPORT_GENERATED.format(path=filepath))
        return filepath, df_main

    def _generate_headings_problematicos(self, df_main):
        rows = []
        for _, row in df_main.iterrows():
            url = row.get('url')
            problematicos = row.get('headings_problematicos', [])
            if isinstance(problematicos, float):  # Quando for NaN
                continue
            for item in problematicos:
                rows.append({'url': url, **item})
        return pd.DataFrame(rows)

    def _generate_headings_semantica(self, df_main):
        rows = []
        for _, row in df_main.iterrows():
            url = row.get('url')
            estrutura = row.get('headings_semantica', {})
            if not estrutura:
                continue
            for key, items in estrutura.items():
                if isinstance(items, list):
                    for item in items:
                        rows.append({'url': url, 'tipo_problema': key, 'descricao': item.get('description')})
        return pd.DataFrame(rows)

    def _generate_headings_estatisticas(self, df_main):
        rows = []
        for _, row in df_main.iterrows():
            url = row.get('url')
            metricas = row.get('headings_estatisticas', {})
            if not metricas:
                continue
            metricas_formatadas = {'url': url, **metricas}
            rows.append(metricas_formatadas)
        return pd.DataFrame(rows)

    def _generate_headings_arvore(self, df_main):
        rows = []
        for _, row in df_main.iterrows():
            url = row.get('url')
            arvore = row.get('headings_arvore', [])
            if not arvore:
                continue
            for linha in arvore:
                rows.append({'url': url, 'estrutura': linha})
        return pd.DataFrame(rows)

    def _generate_headings_errados(self, df_main):
        rows = []
        for _, row in df_main.iterrows():
            url = row.get('url')
            headings = row.get('headings', [])
            if isinstance(headings, float):  # Quando for NaN
                continue
            for h in headings:
                if h.get('eh_problematico'):
                    rows.append({'url': url, **h})
        return pd.DataFrame(rows)

    def _generate_metatags_problemas(self, df_main):
        rows = []
        for _, row in df_main.iterrows():
            url = row.get('url')
            problemas = row.get('metatags_problemas', [])
            if isinstance(problemas, float):  # Quando for NaN
                continue
            for item in problemas:
                rows.append({'url': url, **item})
        return pd.DataFrame(rows)

    def _generate_score_ranking(self, df_main):
        colunas_score = [c for c in df_main.columns if 'score' in c.lower()]
        colunas_usar = ['url'] + colunas_score
        return df_main[colunas_usar].copy()

    def _set_column_widths(self, worksheet, df):
        for i, col in enumerate(df.columns):
            col_width = COLUMN_WIDTHS.get(col, max(15, df[col].astype(str).map(len).max()))
            worksheet.set_column(i, i, col_width)


def create_report_generator(generator_type='default', config=None):
    return ExcelReportGenerator(config)
