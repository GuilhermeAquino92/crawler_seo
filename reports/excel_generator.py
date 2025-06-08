# reports/excel_generator.py

import pandas as pd
import xlsxwriter
from datetime import datetime
import os

class ExcelReportGenerator:
    def __init__(self, config=None):
        self.config = config or {}
        self.output_folder = self.config.get('folder', 'output')
        os.makedirs(self.output_folder, exist_ok=True)

    def generate_complete_report(self, results, crawlers_data=None, filename_prefix="SEO_ANALYSIS"):
        if not results:
            print("Nenhum resultado para gerar o relatório.")
            return None, None

        df_main = pd.DataFrame(results)

        dataframes = {
            'Metatags_Ultra_Complete': df_main.copy(),
            'Headings_Problematicos': self._generate_headings_problematicos(df_main),
            'Problemas_Estrutura_Headings': self._generate_heading_structure_issues_df(df_main),
            'Title_Duplicados': self._generate_duplicates_df(crawlers_data.metatags_analyzer.titles_encontrados),
            'Desc_Duplicadas': self._generate_duplicates_df(crawlers_data.metatags_analyzer.descriptions_encontradas),
            'Mixed_Content': self._generate_mixed_content_df(df_main),
            'Score_Ranking': self._generate_score_ranking_df(df_main),
            'Erros_HTTP': self._generate_http_errors_df(df_main),
            'Resumo': self._generate_summary_df(crawlers_data),
            'Todos_os_Resultados': df_main.copy()
        }

        filepath = self._generate_excel_file(dataframes, filename_prefix)
        return filepath, df_main

    def _generate_headings_problematicos(self, df):
        rows = []
        for _, row in df.iterrows():
            for problema in row.get('headings_problematicos', []):
                rows.append({
                    'URL': row['URL'],
                    'Tag': problema.get('tag'),
                    'Texto': problema.get('texto'),
                    'Posição': problema.get('posicao'),
                    'Gravidade': problema.get('gravidade'),
                    'Vazio': 'SIM' if 'VAZIO' in problema.get('motivos', []) else 'NÃO',
                    'Oculto': 'SIM' if 'OCULTO' in problema.get('motivos', []) else 'NÃO',
                    'Descrição': problema.get('descricao')
                })
        return pd.DataFrame(rows)

    def _generate_heading_structure_issues_df(self, df):
        rows = []
        for _, row in df.iterrows():
            tags_seq = [h.split(':')[0] for h in row.get('heading_sequence', [])]
            rows.append({
                'URL': row['URL'],
                'H1 Count': row.get('h1_count'),
                'H1 Ausente': 'SIM' if row.get('h1_ausente') else 'NÃO',
                'H1 Múltiplo': 'SIM' if row.get('h1_multiple') else 'NÃO',
                'Hierarquia Correta': 'SIM' if row.get('hierarquia_correta') else 'NÃO',
                'Problemas Hierarquia': ' | '.join(row.get('problemas_hierarquia', [])),
                'Sequência Heading Tags': ' → '.join(tags_seq)
            })
        return pd.DataFrame(rows)

    def _generate_duplicates_df(self, duplicates_dict):
        rows = []
        for value, urls in duplicates_dict.items():
            if len(urls) > 1:
                for url in urls:
                    rows.append({
                        'Valor Duplicado': value,
                        'Ocorrência': len(urls),
                        'URL': url
                    })
        return pd.DataFrame(rows)

    def _generate_mixed_content_df(self, df):
        rows = []
        for _, row in df.iterrows():
            for recurso in row.get('mixed_content_resources', []):
                rows.append({
                    'URL da Página': row['URL'],
                    'Tipo': recurso.get('type'),
                    'Tag': recurso.get('tag'),
                    'Atributo': recurso.get('attribute'),
                    'Recurso Inseguro': recurso.get('url')
                })
        return pd.DataFrame(rows)

    def _generate_score_ranking_df(self, df):
        cols = [
            'URL',
            'metatags_score',
            'title_status',
            'description_status',
            'h1_ausente',
            'title_duplicado',
            'description_duplicada',
            'Warnings',
            'Critical_Issues'
        ]
        df_filtered = df[cols].copy()
        df_filtered = df_filtered.sort_values(by='metatags_score', ascending=False)
        df_filtered['h1_ausente'] = df_filtered['h1_ausente'].apply(lambda x: 'SIM' if x else 'NÃO')
        df_filtered['title_duplicado'] = df_filtered['title_duplicado'].apply(lambda x: 'SIM' if x else 'NÃO')
        df_filtered['description_duplicada'] = df_filtered['description_duplicada'].apply(lambda x: 'SIM' if x else 'NÃO')
        return df_filtered

    def _generate_http_errors_df(self, df):
        df_errors = df[
            (df['Status_Code'].astype(str).str.startswith(('3', '4', '5'))) |
            (df['processed'] == False)
        ].copy()

        df_errors = df_errors[[
            'URL',
            'Status_Code',
            'Warnings'
        ]]

        df_errors['Tipo'] = df_errors['Status_Code'].astype(str).apply(self._classificar_status)

        return df_errors[['URL', 'Status_Code', 'Tipo', 'Warnings']]

    def _classificar_status(self, code):
        try:
            code = int(code)
            if 300 <= code < 400:
                return 'Redirecionamento'
            elif 400 <= code < 500:
                return 'Erro do cliente'
            elif 500 <= code < 600:
                return 'Erro do servidor'
        except:
            return 'Desconhecido'

    def _generate_summary_df(self, crawlers_data):
        stats = crawlers_data.get_stats()
        resumo = {
            'Total URLs Processadas': stats['summary']['total_urls_processadas'],
            'URLs com Erro': stats['summary']['total_urls_com_erro'],
            'Success Rate (%)': round(stats['summary']['success_rate'], 2),
            'Titles Duplicados': stats['metatags']['duplicates']['total_duplicate_titles'],
            'Descriptions Duplicadas': stats['metatags']['duplicates']['total_duplicate_descriptions'],
            'Páginas com Mixed Content': stats['status']['summary']['mixed_content_found']
        }
        return pd.DataFrame([resumo])

    def _generate_excel_file(self, dataframes, filename_prefix):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.xlsx"
        filepath = os.path.join(self.output_folder, filename)
        workbook = xlsxwriter.Workbook(filepath, {'remove_timezone': True})

        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'middle',
            'align': 'center',
            'bg_color': '#e0e0e0',
            'border': 1
        })

        normal_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'border': 1
        })

        for name, df in dataframes.items():
            sheet = workbook.add_worksheet(name[:31])
            if df.empty:
                sheet.write(0, 0, 'Sem dados.')
                continue

            for col_num, column in enumerate(df.columns):
                sheet.write(0, col_num, column, header_format)

            for row_num, row in df.iterrows():
                for col_num, value in enumerate(row):
                    val = self._convert_value_for_excel(value)
                    sheet.write(row_num + 1, col_num, val, normal_format)

            for i, col in enumerate(df.columns):
                max_width = max([len(str(v)) for v in df[col].astype(str).values] + [len(col)])
                sheet.set_column(i, i, min(max_width + 2, 60))

            sheet.freeze_panes(1, 0)
            sheet.autofilter(0, 0, len(df), len(df.columns) - 1)

        workbook.close()
        return filepath

    def _convert_value_for_excel(self, value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ''
        if isinstance(value, list):
            return ' | '.join(str(v) for v in value)
        if isinstance(value, dict):
            return str(value)
        if isinstance(value, bool):
            return 'SIM' if value else 'NÃO'
        if isinstance(value, str) and len(value) > 32767:
            return value[:32760] + '...'
        return value

def create_report_generator(generator_type='default', config=None):
    return ExcelReportGenerator(config)
