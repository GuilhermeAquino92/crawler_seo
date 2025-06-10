# reports/excel_generator.py - Gerador Excel COMPLETO e ESTILIZADO com abas clássicas

import pandas as pd
import xlsxwriter
from datetime import datetime
import os
from utils.constants import MSG_REPORT_GENERATED, MSG_NO_RESULTS


class ExcelReportGenerator:
    def __init__(self, config=None):
        self.config = config or {}
        self.output_folder = self.config.get("folder", "output")
        os.makedirs(self.output_folder, exist_ok=True)

    def generate_complete_report(self, results, filename_prefix="SEO_ANALYSIS"):
        if not results:
            print(MSG_NO_RESULTS)
            return None, None

        df_main = pd.DataFrame(results)
        filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(self.output_folder, filename)

        try:
            with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
                df_main.to_excel(writer, sheet_name="📊_ANALISE_COMPLETA", index=False)
                self._ajustar_colunas(writer, df_main, "📊_ANALISE_COMPLETA")

                abas = {
                    "🔍_Headings_Problematicos": self._aba_headings_problematicos(df_main),
                    "🕳️_Headings_Vazios": self._aba_headings_vazios(df_main),
                    "📏_Sequencia_Headings": self._aba_sequencia_headings(df_main),
                    "⚖️_Gravidade_Headings": self._aba_gravidade_headings(df_main),
                    "🔢_Hierarquia_Problemas": self._aba_hierarquia(df_main),
                    "🎯_Score_Ranking": self._aba_score(df_main),
                    "📈_RESUMO_EXECUTIVO": self._aba_resumo(df_main),
                    "🔄_Titles_Duplicados": df_main[df_main.get('Title_Duplicado') == 'SIM'][['URL', 'Title']],
                    "🔄_Descriptions_Duplicadas": df_main[df_main.get('Description_Duplicada') == 'SIM'][['URL', 'Meta_Description']],
                    "❌_Mixed_Content": self._aba_mixed(df_main)
                }

                for nome, aba in abas.items():
                    if isinstance(aba, pd.DataFrame) and not aba.empty:
                        aba.to_excel(writer, sheet_name=nome, index=False)
                        self._ajustar_colunas(writer, aba, nome)
                        self._formatar_score(writer, aba, nome)

            print(MSG_REPORT_GENERATED.format(filepath=filepath))
            return filepath, df_main
        except Exception as e:
            print(f"❌ ERRO ao gerar Excel: {e}")
            return None, None

    def _ajustar_colunas(self, writer, df, aba):
        worksheet = writer.sheets[aba]
        for i, col in enumerate(df.columns):
            largura = min(max(df[col].astype(str).map(len).max(), len(col)) + 2, 80)
            worksheet.set_column(i, i, largura)

    def _formatar_score(self, writer, df, aba):
        worksheet = writer.sheets[aba]
        for col in ["Score", "🎯 Score", "Metatags_Score"]:
            if col in df.columns:
                idx = df.columns.get_loc(col)
                formato = writer.book.add_format({'num_format': '0.0', 'align': 'center'})
                worksheet.set_column(idx, idx, None, formato)
                worksheet.conditional_format(1, idx, len(df), idx, {
                    'type': '3_color_scale',
                    'min_color': "#F8696B",
                    'mid_color': "#FFEB84",
                    'max_color': "#63BE7B"
                })

    def _aba_headings_problematicos(self, df):
        rows = []
        for _, row in df.iterrows():
            problemas = row.get('headings_problematicos', [])
            if isinstance(problemas, float) or not problemas:
                continue
            rows.append({
                '🔗 URL': row.get('URL'),
                'Total_Problemas': row.get('Headings_Problematicos_Total'),
                'Vazios': row.get('Headings_Vazios'),
                'Ocultos': row.get('Headings_Ocultos'),
                'CRITICOS': row.get('Headings_Criticos'),
                'MEDIOS': len(problemas) - row.get('Headings_Criticos', 0),
                'Gravidade_Geral': 'CRÍTICO' if row.get('Headings_Criticos', 0) > 0 else 'MÉDIO',
                'Detalhes': ' | '.join([p.get('descricao', '') for p in problemas if isinstance(p, dict)])
            })
        return pd.DataFrame(rows)

    def _aba_headings_vazios(self, df):
        rows = []
        for _, row in df.iterrows():
            problemas = row.get('headings_problematicos', [])
            if isinstance(problemas, float):
                continue
            vazios = [p for p in problemas if 'vazio' in p.get('motivos', [])]
            for p in vazios:
                rows.append({
                    '🔗 URL': row.get('URL'),
                    'Tag': p.get('tag'),
                    'Posição': p.get('position'),
                    '⚖️ Gravidade': 'CRÍTICO' if p.get('tag') == 'H1' else 'MÉDIO',
                    'Descrição': p.get('descricao'),
                    'Score_Página': row.get('Metatags_Score')
                })
        return pd.DataFrame(rows)

    def _aba_sequencia_headings(self, df):
        return df.rename(columns={
            'URL': '🔗 URL',
            'Metatags_Score': '🎯 Score',
            'Hierarquia_Correta': 'Hierarquia_OK',
            'Headings_Problematicos_Total': '🔍 Problemáticos'
        })[[
            '🔗 URL', 'Heading_Sequence_Completa', 'Heading_Sequence_Valida',
            'Total_Headings', 'Headings_Validos', '🔍 Problemáticos',
            'Hierarquia_OK', 'Problemas_Hierarquia', '🎯 Score'
        ]]

    def _aba_gravidade_headings(self, df):
        return df[['URL', 'Headings_Criticos', 'Metatags_Score']].rename(columns={'URL': '🔗 URL'})

    def _aba_hierarquia(self, df):
        return df.rename(columns={
            'URL': '🔗 URL',
            'H1_Count': 'H1s',
            'Metatags_Score': 'Score'
        })[[
            '🔗 URL', 'Problemas_Hierarquia', 'H1s', 'H1_Text',
            'Heading_Sequence_Completa', 'Heading_Sequence_Valida',
            'Headings_Problematicos_Total', 'Score'
        ]]

    def _aba_score(self, df):
        return df[['URL', 'Metatags_Score']].sort_values(by='Metatags_Score', ascending=False)

    def _aba_resumo(self, df):
        return pd.DataFrame([
            {'Métrica': 'Total URLs', 'Valor': len(df)},
            {'Métrica': 'H1 ausentes', 'Valor': len(df[df.get('H1_Ausente') == 'SIM'])},
            {'Métrica': 'Títulos duplicados', 'Valor': len(df[df.get('Title_Duplicado') == 'SIM'])},
            {'Métrica': 'Descrições duplicadas', 'Valor': len(df[df.get('Description_Duplicada') == 'SIM'])},
            {'Métrica': 'Com problemas de heading', 'Valor': len(df[df.get('Headings_Problematicos_Total', 0) > 0])}
        ])

    def _aba_mixed(self, df):
        if 'mixed_content' not in df.columns:
            return pd.DataFrame()
        rows = []
        for _, row in df.iterrows():
            entries = row.get('mixed_content', [])
            if not isinstance(entries, list):
                continue
            for entry in entries:
                rows.append({
                    '🔗 URL': row.get('URL'),
                    'Tipo': entry.get('tipo'),
                    'Tag': entry.get('tag'),
                    'Conteúdo': entry.get('conteudo'),
                    'Exemplo': entry.get('exemplo')
                })
        return pd.DataFrame(rows)


def create_report_generator(generator_type='default', config=None):
    return ExcelReportGenerator(config)
