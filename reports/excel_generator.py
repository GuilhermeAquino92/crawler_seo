# reports/excel_generator.py - Gerador Excel COMPLETO RESTAURADO

import pandas as pd
import xlsxwriter
from datetime import datetime
import os
from utils.constants import (
    MSG_REPORT_GENERATED, MSG_NO_RESULTS, SHEET_NAMES_EMOJI
)


class ExcelReportGenerator:
    def __init__(self, config=None):
        self.config = config or {}
        self.output_folder = self.config.get('folder', 'output')
        os.makedirs(self.output_folder, exist_ok=True)

    def generate_complete_report(self, results, filename_prefix="SEO_ANALYSIS"):
        if not results:
            print(MSG_NO_RESULTS)
            return None, None

        df_main = pd.DataFrame(results)
        filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(self.output_folder, filename)

        try:
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                df_main.to_excel(writer, sheet_name=SHEET_NAMES_EMOJI.get('complete', 'Complete'), index=False)

                aba_configs = {
                    'headings_problematic': self._generate_headings_problematicos(df_main),
                    'title_duplicates': self._generate_title_duplicates(df_main),
                    'description_duplicates': self._generate_description_duplicates(df_main),
                    'score_ranking': self._generate_score_ranking(df_main),
                    'summary': self._generate_summary(df_main),
                    'headings_empty': self._generate_headings_vazios(df_main),
                    'heading_sequences': self._generate_sequencia_headings(df_main),
                    'hierarchy_problems': self._generate_hierarquia_problemas(df_main),
                    'executive_summary': self._generate_resumo_executivo(df_main),
                }

                for aba_nome, df_data in aba_configs.items():
                    try:
                        if isinstance(df_data, pd.DataFrame) and not df_data.empty:
                            sheet_name = SHEET_NAMES_EMOJI.get(aba_nome, aba_nome)
                            df_data.to_excel(writer, sheet_name=sheet_name, index=False)
                            worksheet = writer.sheets[sheet_name]
                            self._set_column_widths(worksheet, df_data)
                    except Exception as e:
                        print(f"⚠️ Erro na aba {aba_nome}: {e}")

            print(MSG_REPORT_GENERATED.format(filename=filepath))
            return filepath, df_main

        except Exception as e:
            print(f"❌ ERRO ao gerar Excel: {e}")
            return None, None

    def _generate_headings_problematicos(self, df_main):
        rows = []
        for _, row in df_main.iterrows():
            url = row.get('URL', row.get('url', ''))
            headings_problematicos = row.get('headings_problematicos', [])
            total_problematicos = row.get('Headings_Problematicos_Total', 0)

            if total_problematicos > 0 or (isinstance(headings_problematicos, list) and len(headings_problematicos) > 0):
                row_data = {
                    'URL': url,
                    'Total_Problemas': total_problematicos,
                    'Headings_Vazios': row.get('Headings_Vazios', 0),
                    'Headings_Ocultos': row.get('Headings_Ocultos', 0),
                    'Headings_Criticos': row.get('Headings_Criticos', 0),
                    'H1_Count': row.get('H1_Count', 0),
                    'Hierarquia_Correta': row.get('Hierarquia_Correta', 'SIM'),
                    'Sequencia_Completa': row.get('Heading_Sequence_Completa', ''),
                    'Sequencia_Valida': row.get('Heading_Sequence_Valida', ''),
                    'Score': row.get('Metatags_Score', 0)
                }

                if isinstance(headings_problematicos, list):
                    problemas_desc = []
                    motivos_set = set()
                    for problema in headings_problematicos:
                        if isinstance(problema, dict):
                            desc = problema.get('descricao', '')
                            if desc:
                                problemas_desc.append(desc)
                            motivos = problema.get('motivos', [])
                            if isinstance(motivos, list):
                                motivos_set.update(motivos)

                    row_data['Problemas_Detalhados'] = ' | '.join(problemas_desc)
                    row_data['Motivos_Únicos'] = ', '.join(motivos_set)

                rows.append(row_data)

        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def _generate_title_duplicates(self, df_main):
        return df_main[df_main['Title_Duplicado'] == 'SIM'][['URL', 'Title', 'Title_Length', 'Metatags_Score']].copy()

    def _generate_description_duplicates(self, df_main):
        return df_main[df_main['Description_Duplicada'] == 'SIM'][['URL', 'Meta_Description', 'Description_Length', 'Metatags_Score']].copy()

    def _generate_score_ranking(self, df_main):
        cols = ['URL', 'Metatags_Score', 'Title', 'Meta_Description', 'H1_Count', 'Hierarquia_Correta']
        return df_main[cols].sort_values(by='Metatags_Score', ascending=False).copy()

    def _generate_summary(self, df_main):
        summary_data = []
        total_urls = len(df_main)
        summary_data.append({'Métrica': 'Total de URLs analisadas', 'Valor': total_urls})
        if 'Metatags_Score' in df_main.columns:
            summary_data.append({'Métrica': 'Score médio', 'Valor': f"{df_main['Metatags_Score'].mean():.1f}/100"})
        summary_data.append({'Métrica': 'H1 ausentes', 'Valor': (df_main['H1_Ausente'] == 'SIM').sum()})
        summary_data.append({'Métrica': 'Titles duplicados', 'Valor': (df_main['Title_Duplicado'] == 'SIM').sum()})
        summary_data.append({'Métrica': 'Descriptions duplicadas', 'Valor': (df_main['Description_Duplicada'] == 'SIM').sum()})
        summary_data.append({'Métrica': 'Hierarquias incorretas', 'Valor': (df_main['Hierarquia_Correta'] == 'NÃO').sum()})
        return pd.DataFrame(summary_data)

    def _generate_headings_vazios(self, df_main):
        return df_main[df_main['Headings_Vazios'] > 0][['URL', 'Headings_Vazios', 'Headings_Problematicos_Total']].copy()

    def _generate_sequencia_headings(self, df_main):
        return df_main[['URL', 'Heading_Sequence_Completa', 'Heading_Sequence_Valida', 'Hierarquia_Correta']].copy()

    def _generate_hierarquia_problemas(self, df_main):
        return df_main[df_main['Hierarquia_Correta'] == 'NÃO'][['URL', 'H1_Count', 'H1_Text', 'Heading_Sequence_Completa', 'Heading_Sequence_Valida']].copy()

    def _generate_resumo_executivo(self, df_main):
        resumo = {
            'Total de URLs': len(df_main),
            'Media de Score': f"{df_main['Metatags_Score'].mean():.1f}",
            'Sem H1': (df_main['H1_Ausente'] == 'SIM').sum(),
            'Hierarquia Incorreta': (df_main['Hierarquia_Correta'] == 'NÃO').sum(),
            'Headings Ocultos': (df_main['Headings_Ocultos'] > 0).sum(),
            'Headings Vazios': (df_main['Headings_Vazios'] > 0).sum(),
        }
        return pd.DataFrame(list(resumo.items()), columns=['Métrica', 'Valor'])

    def _set_column_widths(self, worksheet, df):
        for i, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(str(col)))
            worksheet.set_column(i, i, min(max_length + 2, 70))


def create_report_generator(generator_type='default', config=None):
    return ExcelReportGenerator(config)
