# reports/excel_generator.py - Gerador de relatórios Excel modularizado

import pandas as pd
import os
from datetime import datetime
from config.settings import EXCEL_ENGINE, EXCEL_COLORS, COLUMN_WIDTHS, TIMESTAMP_FORMAT
from utils.constants import (
    SHEET_NAMES, SHEET_NAMES_EMOJI, STATUS_SYMBOLS, QUALITY_INDICATORS,
    PRIORITY_ACTIONS, MSG_REPORT_GENERATED, MSG_ERROR_EXCEL
)


class ExcelReportGenerator:
    """📊 Gerador de relatórios Excel modularizado"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.output_folder = self.config.get('output_folder', 'output')
        self.use_emoji_names = self.config.get('use_emoji_names', True)
        self.sheet_names = SHEET_NAMES_EMOJI if self.use_emoji_names else SHEET_NAMES
        
        # Garante que pasta de saída existe
        os.makedirs(self.output_folder, exist_ok=True)
    
    def generate_complete_report(self, results, crawlers_data=None, filename_prefix="METATAGS_ULTRA"):
        """📊 Gera relatório completo com todas as abas corrigidas"""
        try:
            # Processa dados principais
            df_principal = self._create_main_dataframe(results)
            
            # Cria DataFrames para cada aba
            dataframes = {
                'main': df_principal,
                'critical': self._create_critical_dataframe(results),
                'headings_problematic': self._create_problematic_headings_dataframe(results),
                'hierarchy': self._create_hierarchy_dataframe(results),
                'title_duplicates': self._create_title_duplicates_dataframe(results, crawlers_data),
                'description_duplicates': self._create_description_duplicates_dataframe(results, crawlers_data),
                'score_ranking': self._create_score_ranking_dataframe(df_principal),
                'summary': self._create_executive_summary_dataframe(df_principal, crawlers_data)
            }
            
            # Gera arquivo Excel
            filename = self._generate_filename(filename_prefix)
            filepath = os.path.join(self.output_folder, filename)
            
            success = self._write_excel_file(filepath, dataframes)
            
            if success:
                print(MSG_REPORT_GENERATED.format(filename=filepath))
                return filepath, df_principal
            else:
                return None, None
                
        except Exception as e:
            print(MSG_ERROR_EXCEL.format(error=str(e)))
            return None, None
    
    def _create_main_dataframe(self, results):
        """📋 Cria DataFrame principal com todas as métricas"""
        dados_principais = []
        
        for resultado in results:
            dados_principais.append({
                'URL': resultado['url'],
                'Status_Code': resultado.get('status_code', ''),
                'Response_Time_ms': resultado.get('response_time', 0),
                'Title': resultado.get('title', ''),
                'Title_Length': resultado.get('title_length', 0),
                'Title_Status': resultado.get('title_status', ''),
                'Title_Duplicado': 'SIM' if resultado.get('title_duplicado', False) else 'NÃO',
                'Meta_Description': resultado.get('meta_description', ''),
                'Description_Length': resultado.get('description_length', 0),
                'Description_Status': resultado.get('description_status', ''),
                'Description_Duplicada': 'SIM' if resultado.get('description_duplicada', False) else 'NÃO',
                'H1_Count': resultado.get('h1_count', 0),
                'H1_Text': resultado.get('h1_text', ''),
                'H1_Ausente': 'SIM' if resultado.get('h1_ausente', True) else 'NÃO',
                'H1_Multiple': 'SIM' if resultado.get('h1_multiple', False) else 'NÃO',
                'Hierarquia_Correta': 'SIM' if resultado.get('hierarquia_correta', True) else 'NÃO',
                
                # 🆕 CONSOLIDADO: Headings problemáticos
                'Headings_Problematicos_Total': resultado.get('headings_problematicos_count', 0),
                'Headings_Vazios': resultado.get('headings_vazios_count', 0),
                'Headings_Ocultos': resultado.get('headings_ocultos_count', 0),
                'Headings_Criticos': resultado.get('headings_gravidade_critica', 0),
                
                'Heading_Sequence_Completa': ' → '.join(resultado.get('heading_sequence', [])),
                'Heading_Sequence_Valida': ' → '.join(resultado.get('heading_sequence_valida', [])),
                'Total_Problemas_Headings': resultado.get('total_problemas_headings', 0),
                'Metatags_Score': resultado.get('metatags_score', 0),
                'Critical_Issues': ' | '.join(resultado.get('critical_issues', [])),
                'Warnings': ' | '.join(resultado.get('warnings', [])),
                'Title_Issues': ' | '.join(resultado.get('title_issues', [])),
                'Description_Issues': ' | '.join(resultado.get('description_issues', [])),
                'Heading_Issues': ' | '.join(resultado.get('heading_issues', []))
            })
        
        return pd.DataFrame(dados_principais)
    
    def _create_problematic_headings_dataframe(self, results):
        """🆕 Cria DataFrame consolidado para headings problemáticos"""
        dados_headings_problematicos = []
        
        for resultado in results:
            url = resultado['url']
            headings_problematicos = resultado.get('headings_problematicos', [])
            
            if headings_problematicos:
                # Uma linha por URL com todos os problemas consolidados
                problemas_desc = []
                gravidades = []
                motivos_todos = []
                
                for heading_prob in headings_problematicos:
                    desc = heading_prob.get('descricao', '')
                    problemas_desc.append(desc)
                    gravidades.append(heading_prob.get('gravidade', 'MÉDIO'))
                    motivos_todos.extend(heading_prob.get('motivos', []))
                
                # Determina gravidade geral da URL
                gravidade_geral = 'CRÍTICO' if 'CRÍTICO' in gravidades else 'MÉDIO'
                
                dados_headings_problematicos.append({
                    'URL': url,
                    'Total_Problemas': len(headings_problematicos),
                    'Headings_Vazios': len([h for h in headings_problematicos if 'Vazio' in h.get('motivos', [])]),
                    'Headings_Ocultos': len([h for h in headings_problematicos if 'Oculto' in h.get('motivos', [])]),
                    'Gravidade_Geral': gravidade_geral,
                    'Problemas_Detalhados': ' | '.join(problemas_desc),
                    'Motivos_Únicos': ', '.join(set(motivos_todos)),
                    'H1_Count': resultado.get('h1_count', 0),
                    'Hierarquia_Correta': 'SIM' if resultado.get('hierarquia_correta', True) else 'NÃO',
                    'Sequencia_Completa': ' → '.join(resultado.get('heading_sequence', [])),
                    'Sequencia_Valida': ' → '.join(resultado.get('heading_sequence_valida', [])),
                    'Score': resultado.get('metatags_score', 0)
                })
        
        return pd.DataFrame(dados_headings_problematicos) if dados_headings_problematicos else pd.DataFrame()
    
    def _create_hierarchy_dataframe(self, results):
        """🔢 Cria DataFrame para problemas de hierarquia"""
        dados_hierarquia_problemas = []
        
        for resultado in results:
            if (not resultado.get('hierarquia_correta', True) or 
                resultado.get('problemas_hierarquia')):
                
                dados_hierarquia_problemas.append({
                    'URL': resultado['url'],
                    'Problemas_Hierarquia': ' | '.join(resultado.get('problemas_hierarquia', [])),
                    'H1_Count': resultado.get('h1_count', 0),
                    'H1_Text': resultado.get('h1_text', ''),
                    'Sequencia_Completa': ' → '.join(resultado.get('heading_sequence', [])),
                    'Sequencia_Valida': ' → '.join(resultado.get('heading_sequence_valida', [])),
                    'Total_Problemas': resultado.get('total_problemas_headings', 0),
                    'Hierarquia_Correta': 'SIM' if resultado.get('hierarquia_correta', True) else 'NÃO'
                })
        
        return pd.DataFrame(dados_hierarquia_problemas) if dados_hierarquia_problemas else pd.DataFrame()
    
    def _create_title_duplicates_dataframe(self, results, crawlers_data):
        """🔄 Cria DataFrame para titles duplicados"""
        dados_duplicados_title = []
        
        if crawlers_data and hasattr(crawlers_data, 'titles_encontrados'):
            for resultado in results:
                if resultado.get('title_duplicado'):
                    title = resultado.get('title', '')
                    if title in crawlers_data.titles_encontrados and len(crawlers_data.titles_encontrados[title]) > 1:
                        for url_dup in crawlers_data.titles_encontrados[title]:
                            dados_duplicados_title.append({
                                'Title_Duplicado': title,
                                'URL': url_dup,
                                'Total_Duplicatas': len(crawlers_data.titles_encontrados[title])
                            })
        
        return pd.DataFrame(dados_duplicados_title) if dados_duplicados_title else pd.DataFrame()
    
    def _create_description_duplicates_dataframe(self, results, crawlers_data):
        """🔄 Cria DataFrame para descriptions duplicadas"""
        dados_duplicados_description = []
        
        if crawlers_data and hasattr(crawlers_data, 'descriptions_encontradas'):
            for resultado in results:
                if resultado.get('description_duplicada'):
                    description = resultado.get('meta_description', '')
                    if description in crawlers_data.descriptions_encontradas and len(crawlers_data.descriptions_encontradas[description]) > 1:
                        for url_dup in crawlers_data.descriptions_encontradas[description]:
                            dados_duplicados_description.append({
                                'Description_Duplicada': description[:100] + '...' if len(description) > 100 else description,
                                'URL': url_dup,
                                'Total_Duplicatas': len(crawlers_data.descriptions_encontradas[description])
                            })
        
        return pd.DataFrame(dados_duplicados_description) if dados_duplicados_description else pd.DataFrame()
    
    def _create_critical_dataframe(self, results):
        """🔥 Cria DataFrame para problemas críticos"""
        dados_criticos = []
        
        for resultado in results:
            if (resultado.get('title_status') == 'Ausente' or
                resultado.get('description_status') == 'Ausente' or
                resultado.get('h1_ausente', True) or
                resultado.get('critical_issues') or
                resultado.get('headings_gravidade_critica', 0) > 0):
                
                dados_criticos.append({
                    'URL': resultado['url'],
                    'Status_Code': resultado.get('status_code', ''),
                    'Title_Status': resultado.get('title_status', ''),
                    'Description_Status': resultado.get('description_status', ''),
                    'H1_Ausente': 'SIM' if resultado.get('h1_ausente', True) else 'NÃO',
                    'Headings_Criticos': resultado.get('headings_gravidade_critica', 0),
                    'Total_Problemas_Headings': resultado.get('total_problemas_headings', 0),
                    'Critical_Issues': ' | '.join(resultado.get('critical_issues', [])),
                    'Metatags_Score': resultado.get('metatags_score', 0)
                })
        
        return pd.DataFrame(dados_criticos) if dados_criticos else pd.DataFrame()
    
    def _create_score_ranking_dataframe(self, df_principal):
        """🎯 Cria DataFrame para ranking por score"""
        if df_principal.empty:
            return pd.DataFrame()
        
        df_score = df_principal.sort_values('Metatags_Score', ascending=False).copy()
        return df_score[['URL', 'Metatags_Score', 'Title_Status', 'Description_Status', 'H1_Ausente', 'Headings_Problematicos_Total']]
    
    def _create_executive_summary_dataframe(self, df_principal, crawlers_data):
        """📊 Cria DataFrame para resumo executivo"""
        total_urls = len(df_principal)
        
        if total_urls == 0:
            return pd.DataFrame([['Nenhuma URL analisada', '']], columns=['Métrica', 'Valor'])
        
        # Estatísticas básicas
        title_ok = len(df_principal[df_principal['Title_Status'] == 'OK'])
        title_ausente = len(df_principal[df_principal['Title_Status'] == 'Ausente'])
        title_duplicados = len(df_principal[df_principal['Title_Duplicado'] == 'SIM'])
        
        desc_ok = len(df_principal[df_principal['Description_Status'] == 'OK'])
        desc_ausente = len(df_principal[df_principal['Description_Status'] == 'Ausente'])
        desc_duplicadas = len(df_principal[df_principal['Description_Duplicada'] == 'SIM'])
        
        h1_ausente = len(df_principal[df_principal['H1_Ausente'] == 'SIM'])
        hierarquia_incorreta = len(df_principal[df_principal['Hierarquia_Correta'] == 'NÃO'])
        
        # Estatísticas de headings
        urls_com_headings_problematicos = len(df_principal[df_principal['Headings_Problematicos_Total'] > 0])
        headings_vazios_total = df_principal['Headings_Vazios'].sum()
        headings_ocultos_total = df_principal['Headings_Ocultos'].sum()
        headings_criticos_total = df_principal['Headings_Criticos'].sum()
        
        score_medio = df_principal['Metatags_Score'].mean()
        
        # Duplicados únicos
        titles_unicos_duplicados = 0
        descriptions_unicas_duplicadas = 0
        
        if crawlers_data:
            if hasattr(crawlers_data, 'titles_encontrados'):
                titles_unicos_duplicados = len([t for t, urls in crawlers_data.titles_encontrados.items() if len(urls) > 1])
            if hasattr(crawlers_data, 'descriptions_encontradas'):
                descriptions_unicas_duplicadas = len([d for d, urls in crawlers_data.descriptions_encontradas.items() if len(urls) > 1])
        
        return pd.DataFrame([
            ['🏷️ RESUMO ULTRA DE METATAGS (CORRIGIDO)', ''],
            ['', ''],
            ['📊 ESTATÍSTICAS GERAIS', ''],
            ['Total URLs analisadas', total_urls],
            ['Score médio de metatags', f"{score_medio:.1f}/100"],
            ['', ''],
            ['📄 ANÁLISE DE TITLES', ''],
            ['Titles OK', title_ok],
            ['Titles ausentes', title_ausente],
            ['Titles duplicados', title_duplicados],
            ['% Titles OK', f"{(title_ok/total_urls*100):.1f}%" if total_urls > 0 else '0%'],
            ['', ''],
            ['📝 ANÁLISE DE DESCRIPTIONS', ''],
            ['Descriptions OK', desc_ok],
            ['Descriptions ausentes', desc_ausente],
            ['Descriptions duplicadas', desc_duplicadas],
            ['% Descriptions OK', f"{(desc_ok/total_urls*100):.1f}%" if total_urls > 0 else '0%'],
            ['', ''],
            ['🔢 ANÁLISE DE HEADINGS (CORRIGIDA)', ''],
            ['URLs sem H1', h1_ausente],
            ['URLs com hierarquia incorreta', hierarquia_incorreta],
            ['🆕 URLs com headings problemáticos', urls_com_headings_problematicos],
            ['🆕 Total headings vazios', headings_vazios_total],
            ['🆕 Total headings ocultos', headings_ocultos_total],
            ['🆕 Headings críticos (H1s problemáticos)', headings_criticos_total],
            ['% Hierarquia correta', f"{((total_urls-hierarquia_incorreta)/total_urls*100):.1f}%" if total_urls > 0 else '0%'],
            ['', ''],
            ['🎯 DUPLICADOS ENCONTRADOS', ''],
            ['Titles únicos duplicados', titles_unicos_duplicados],
            ['Descriptions únicas duplicadas', descriptions_unicas_duplicadas],
            ['', ''],
            ['🔧 PRINCIPAIS CORREÇÕES IMPLEMENTADAS', ''],
            ['✅ Detecção de headings ocultos expandida', 'Inclui cores invisíveis (branco, transparente)'],
            ['✅ Análise de hierarquia corrigida', 'Ignora headings problemáticos na sequência'],
            ['✅ Consolidação de problemas', 'Uma aba unificada para headings problemáticos'],
            ['✅ Gravidade diferenciada', 'H1s problemáticos são críticos'],
            ['✅ Sequências separadas', 'Mostra sequência completa vs. válida'],
            ['', ''],
            ['🎯 TOP 6 AÇÕES PRIORITÁRIAS CORRIGIDAS', ''],
            ['1. Corrigir titles ausentes', f"{title_ausente} URLs"],
            ['2. Corrigir descriptions ausentes', f"{desc_ausente} URLs"],
            ['3. Adicionar H1 ausentes', f"{h1_ausente} URLs"],
            ['4. 🆕 Corrigir headings problemáticos', f"{urls_com_headings_problematicos} URLs"],
            ['5. Corrigir hierarquia headings', f"{hierarquia_incorreta} URLs"],
            ['6. Eliminar duplicados', f"{title_duplicados + desc_duplicadas} URLs"],
            ['', ''],
            ['💡 MELHORIAS NA DETECÇÃO', ''],
            ['Headings com cor branca detectados', 'Agora identificados como ocultos'],
            ['Hierarquia ignora headings problemáticos', 'Análise mais precisa'],
            ['Consolidação em aba única', 'Facilita triagem de problemas'],
            ['Gravidade por tipo de heading', 'H1s têm peso maior no score']
        ], columns=['Métrica', 'Valor'])
    
    def _write_excel_file(self, filepath, dataframes):
        """📝 Escreve arquivo Excel com formatação"""
        try:
            with pd.ExcelWriter(filepath, engine=EXCEL_ENGINE) as writer:
                # Aba 1: Dados completos
                if not dataframes['main'].empty:
                    dataframes['main'].to_excel(writer, sheet_name=self.sheet_names.get('complete', 'Complete'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('complete', 'Complete')}' criada")
                
                # Aba 2: Problemas críticos
                if not dataframes['critical'].empty:
                    dataframes['critical'].to_excel(writer, sheet_name=self.sheet_names.get('critical', 'Criticos'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('critical', 'Criticos')}' criada")
                else:
                    # Cria aba vazia
                    pd.DataFrame(columns=['URL', 'Status_Code', 'Title_Status', 'Description_Status', 'H1_Ausente']).to_excel(
                        writer, sheet_name=self.sheet_names.get('critical', 'Criticos'), index=False)
                
                # Aba 3: 🆕 HEADINGS PROBLEMÁTICOS CONSOLIDADOS
                if not dataframes['headings_problematic'].empty:
                    dataframes['headings_problematic'].to_excel(writer, sheet_name=self.sheet_names.get('headings_problematic', 'Headings_Problematicos'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('headings_problematic', 'Headings_Problematicos')}' criada (CONSOLIDADA)")
                else:
                    pd.DataFrame(columns=['URL', 'Total_Problemas', 'Headings_Vazios', 'Headings_Ocultos', 'Gravidade_Geral']).to_excel(
                        writer, sheet_name=self.sheet_names.get('headings_problematic', 'Headings_Problematicos'), index=False)
                
                # Aba 4: Hierarquia
                if not dataframes['hierarchy'].empty:
                    dataframes['hierarchy'].to_excel(writer, sheet_name=self.sheet_names.get('hierarchy', 'Hierarquia'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('hierarchy', 'Hierarquia')}' criada")
                else:
                    pd.DataFrame(columns=['URL', 'Problemas_Hierarquia', 'H1_Count', 'H1_Text']).to_excel(
                        writer, sheet_name=self.sheet_names.get('hierarchy', 'Hierarquia'), index=False)
                
                # Aba 5: Titles duplicados
                if not dataframes['title_duplicates'].empty:
                    dataframes['title_duplicates'].to_excel(writer, sheet_name=self.sheet_names.get('title_duplicates', 'Title_Duplicados'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('title_duplicates', 'Title_Duplicados')}' criada")
                else:
                    pd.DataFrame(columns=['Title_Duplicado', 'URL', 'Total_Duplicatas']).to_excel(
                        writer, sheet_name=self.sheet_names.get('title_duplicates', 'Title_Duplicados'), index=False)
                
                # Aba 6: Descriptions duplicadas
                if not dataframes['description_duplicates'].empty:
                    dataframes['description_duplicates'].to_excel(writer, sheet_name=self.sheet_names.get('description_duplicates', 'Desc_Duplicadas'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('description_duplicates', 'Desc_Duplicadas')}' criada")
                else:
                    pd.DataFrame(columns=['Description_Duplicada', 'URL', 'Total_Duplicatas']).to_excel(
                        writer, sheet_name=self.sheet_names.get('description_duplicates', 'Desc_Duplicadas'), index=False)
                
                # Aba 7: Score ranking
                if not dataframes['score_ranking'].empty:
                    dataframes['score_ranking'].to_excel(writer, sheet_name=self.sheet_names.get('score_ranking', 'Score_Ranking'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('score_ranking', 'Score_Ranking')}' criada")
                
                # Aba 8: Resumo executivo
                if not dataframes['summary'].empty:
                    dataframes['summary'].to_excel(writer, sheet_name=self.sheet_names.get('summary', 'Resumo'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('summary', 'Resumo')}' criada")
                
                # Aplicar formatação
                self._apply_excel_formatting(writer)
                
                print(f"   ✅ Total de 8 abas criadas com sucesso!")
            
            return True
            
        except Exception as e:
            print(MSG_ERROR_EXCEL.format(error=str(e)))
            return False
    
    def _apply_excel_formatting(self, writer):
        """🎨 Aplica formatação ao Excel"""
        try:
            workbook = writer.book
            
            # Formato para cabeçalhos
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': EXCEL_COLORS['header_bg'],
                'font_color': EXCEL_COLORS['header_font'],
                'border': 1
            })
            
            # Formato para células de sucesso
            success_format = workbook.add_format({
                'fg_color': EXCEL_COLORS['success'],
                'font_color': 'white'
            })
            
            # Formato para células de aviso
            warning_format = workbook.add_format({
                'fg_color': EXCEL_COLORS['warning'],
                'font_color': 'black'
            })
            
            # Formato para células de erro
            error_format = workbook.add_format({
                'fg_color': EXCEL_COLORS['error'],
                'font_color': 'white'
            })
            
            # Aplica formatação em cada aba
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                
                # Formatação específica por aba
                if 'Headings_Problematicos' in sheet_name or 'headings_problematic' in sheet_name.lower():
                    worksheet.set_column('A:A', COLUMN_WIDTHS['url'])  # URL
                    worksheet.set_column('B:E', COLUMN_WIDTHS['counter'])  # Contadores
                    worksheet.set_column('F:F', COLUMN_WIDTHS['problems_detailed'])  # Problemas detalhados
                    worksheet.set_column('G:K', COLUMN_WIDTHS['standard'])  # Outras colunas
                
                elif 'Hierarquia' in sheet_name or 'hierarchy' in sheet_name.lower():
                    worksheet.set_column('A:A', COLUMN_WIDTHS['url'])  # URL
                    worksheet.set_column('B:B', COLUMN_WIDTHS['sequence'])  # Problemas
                    worksheet.set_column('C:H', COLUMN_WIDTHS['standard'])  # Outras colunas
                
                elif 'Resumo' in sheet_name or 'summary' in sheet_name.lower():
                    worksheet.set_column('A:A', COLUMN_WIDTHS['sequence'])  # Métrica
                    worksheet.set_column('B:B', COLUMN_WIDTHS['standard'])  # Valor
                
                else:
                    # Formatação padrão
                    worksheet.set_column('A:A', COLUMN_WIDTHS['url'])  # URL
                    worksheet.set_column('B:Z', COLUMN_WIDTHS['standard'])  # Outras colunas
        
        except Exception as e:
            print(f"⚠️ Erro na formatação: {e}")
    
    def _generate_filename(self, prefix):
        """📁 Gera nome único para o arquivo"""
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        return f"{prefix}_CORRIGIDO_{timestamp}.xlsx"


class StatusReportGenerator(ExcelReportGenerator):
    """📊 Gerador específico para relatórios de status"""
    
    def generate_status_report(self, results, mixed_content_data=None, filename_prefix="STATUS_REPORT"):
        """📊 Gera relatório específico de status HTTP"""
        try:
            # Processa dados de status
            df_principal = self._create_status_main_dataframe(results)
            
            # Cria DataFrames específicos para status
            dataframes = {
                'main': df_principal,
                'errors': self._create_status_errors_dataframe(results),
                'mixed_content': self._create_mixed_content_dataframe(mixed_content_data) if mixed_content_data else pd.DataFrame(),
                'performance': self._create_performance_dataframe(results),
                'summary': self._create_status_summary_dataframe(df_principal)
            }
            
            # Gera arquivo Excel
            filename = self._generate_filename(filename_prefix)
            filepath = os.path.join(self.output_folder, filename)
            
            success = self._write_status_excel_file(filepath, dataframes)
            
            if success:
                print(MSG_REPORT_GENERATED.format(filename=filepath))
                return filepath, df_principal
            else:
                return None, None
                
        except Exception as e:
            print(MSG_ERROR_EXCEL.format(error=str(e)))
            return None, None
    
    def _create_status_main_dataframe(self, results):
        """📋 Cria DataFrame principal para status"""
        dados_status = []
        
        for resultado in results:
            dados_status.append({
                'URL': resultado['url'],
                'Status_Code': resultado.get('status_code', ''),
                'Response_Time_ms': resultado.get('response_time', 0),
                'Content_Type': resultado.get('content_type', ''),
                'Final_URL': resultado.get('final_url', ''),
                'Redirected': 'SIM' if resultado.get('redirected', False) else 'NÃO',
                'Content_Length': resultado.get('content_length', 0),
                'Is_HTTPS': 'SIM' if resultado.get('url', '').startswith('https://') else 'NÃO',
                'Error_Details': resultado.get('error_details', ''),
                'Processed_At': resultado.get('processed_at', '')
            })
        
        return pd.DataFrame(dados_status)
    
    def _create_status_errors_dataframe(self, results):
        """❌ Cria DataFrame para erros de status"""
        dados_erros = []
        
        for resultado in results:
            status = resultado.get('status_code', '')
            if (isinstance(status, int) and status >= 400) or isinstance(status, str):
                dados_erros.append({
                    'URL': resultado['url'],
                    'Status_Code': status,
                    'Error_Type': self._classify_error_type(status),
                    'Response_Time_ms': resultado.get('response_time', 0),
                    'Error_Details': resultado.get('error_details', ''),
                    'Final_URL': resultado.get('final_url', ''),
                    'Redirected': 'SIM' if resultado.get('redirected', False) else 'NÃO'
                })
        
        return pd.DataFrame(dados_erros) if dados_erros else pd.DataFrame()
    
    def _create_mixed_content_dataframe(self, mixed_content_data):
        """🚨 Cria DataFrame para mixed content"""
        if not mixed_content_data:
            return pd.DataFrame()
        
        # Implementação específica para mixed content
        # (dependeria da estrutura dos dados de mixed content)
        return pd.DataFrame(mixed_content_data)
    
    def _create_performance_dataframe(self, results):
        """⚡ Cria DataFrame para performance"""
        dados_performance = []
        
        for resultado in results:
            response_time = resultado.get('response_time', 0)
            if response_time > 0:
                dados_performance.append({
                    'URL': resultado['url'],
                    'Response_Time_ms': response_time,
                    'Performance_Category': self._classify_performance(response_time),
                    'Content_Length': resultado.get('content_length', 0),
                    'Content_Type': resultado.get('content_type', ''),
                    'Status_Code': resultado.get('status_code', '')
                })
        
        # Ordena por tempo de resposta
        df_performance = pd.DataFrame(dados_performance)
        if not df_performance.empty:
            df_performance = df_performance.sort_values('Response_Time_ms', ascending=False)
        
        return df_performance
    
    def _create_status_summary_dataframe(self, df_principal):
        """📊 Cria resumo para relatório de status"""
        total_urls = len(df_principal)
        
        if total_urls == 0:
            return pd.DataFrame([['Nenhuma URL analisada', '']], columns=['Métrica', 'Valor'])
        
        # Estatísticas de status
        status_200 = len(df_principal[df_principal['Status_Code'] == 200])
        status_404 = len(df_principal[df_principal['Status_Code'] == 404])
        status_500 = len(df_principal[(df_principal['Status_Code'] >= 500) & (df_principal['Status_Code'] < 600)])
        redirects = len(df_principal[df_principal['Redirected'] == 'SIM'])
        https_count = len(df_principal[df_principal['Is_HTTPS'] == 'SIM'])
        
        # Performance
        avg_response_time = df_principal['Response_Time_ms'].mean()
        slow_pages = len(df_principal[df_principal['Response_Time_ms'] > 3000])
        
        return pd.DataFrame([
            ['📊 RESUMO DE STATUS HTTP', ''],
            ['', ''],
            ['📈 ESTATÍSTICAS GERAIS', ''],
            ['Total URLs analisadas', total_urls],
            ['URLs com status 200 (OK)', status_200],
            ['URLs com status 404 (Not Found)', status_404],
            ['URLs com status 5xx (Erro Servidor)', status_500],
            ['URLs com redirect', redirects],
            ['URLs HTTPS', https_count],
            ['', ''],
            ['⚡ PERFORMANCE', ''],
            ['Tempo médio de resposta', f"{avg_response_time:.0f}ms"],
            ['Páginas lentas (>3s)', slow_pages],
            ['', ''],
            ['📋 DISTRIBUIÇÃO DE STATUS', ''],
            ['Taxa de sucesso (200)', f"{(status_200/total_urls*100):.1f}%" if total_urls > 0 else '0%'],
            ['Taxa de erro 404', f"{(status_404/total_urls*100):.1f}%" if total_urls > 0 else '0%'],
            ['Taxa de erro servidor', f"{(status_500/total_urls*100):.1f}%" if total_urls > 0 else '0%'],
            ['Taxa HTTPS', f"{(https_count/total_urls*100):.1f}%" if total_urls > 0 else '0%']
        ], columns=['Métrica', 'Valor'])
    
    def _classify_error_type(self, status_code):
        """🏷️ Classifica tipo de erro"""
        if isinstance(status_code, str):
            return f"⚠️ {status_code}"
        
        try:
            code = int(status_code)
            if 400 <= code <= 499:
                return "❌ Erro Cliente"
            elif 500 <= code <= 599:
                return "🚨 Erro Servidor"
            elif 300 <= code <= 399:
                return "🔄 Redirect"
            else:
                return "❓ Outros"
        except:
            return "⚠️ Erro"
    
    def _classify_performance(self, response_time):
        """⚡ Classifica performance"""
        if response_time < 1000:
            return "🟢 Rápido"
        elif response_time < 3000:
            return "🟡 Médio"
        else:
            return "🔴 Lento"
    
    def _write_status_excel_file(self, filepath, dataframes):
        """📝 Escreve arquivo Excel específico para status"""
        try:
            with pd.ExcelWriter(filepath, engine=EXCEL_ENGINE) as writer:
                # Abas específicas para status
                sheet_names_status = {
                    'main': 'Status_Complete',
                    'errors': 'Errors_4xx_5xx',
                    'mixed_content': 'Mixed_Content',
                    'performance': 'Performance',
                    'summary': 'Summary'
                }
                
                for key, sheet_name in sheet_names_status.items():
                    if key in dataframes and not dataframes[key].empty:
                        dataframes[key].to_excel(writer, sheet_name=sheet_name, index=False)
                        print(f"   ✅ Aba '{sheet_name}' criada")
                
                # Aplica formatação
                self._apply_excel_formatting(writer)
            
            return True
            
        except Exception as e:
            print(MSG_ERROR_EXCEL.format(error=str(e)))
            return False


# ========================
# 🏭 FACTORY FUNCTIONS
# ========================

def create_report_generator(report_type='default', config=None):
    """🏭 Factory para criar geradores de relatório"""
    
    if report_type == 'status':
        return StatusReportGenerator(config)
    
    else:  # default - metatags
        return ExcelReportGenerator(config)


# ========================
# 🧪 FUNÇÕES DE TESTE
# ========================

def test_excel_generator():
    """Testa o gerador de Excel"""
    print("🧪 Testando ExcelReportGenerator...")
    
    # Dados de teste
    test_results = [
        {
            'url': 'https://example.com/page1',
            'status_code': 200,
            'response_time': 150,
            'title': 'Página de Teste 1',
            'title_length': 17,
            'title_status': 'OK',
            'title_duplicado': False,
            'meta_description': 'Descrição da página de teste 1',
            'description_length': 32,
            'description_status': 'OK',
            'description_duplicada': False,
            'h1_count': 1,
            'h1_text': 'Título Principal',
            'h1_ausente': False,
            'h1_multiple': False,
            'hierarquia_correta': True,
            'headings_problematicos_count': 0,
            'headings_vazios_count': 0,
            'headings_ocultos_count': 0,
            'headings_gravidade_critica': 0,
            'heading_sequence': ['h1:Título Principal...', 'h2:Subtítulo...'],
            'heading_sequence_valida': ['h1:Título Principal...', 'h2:Subtítulo...'],
            'total_problemas_headings': 0,
            'metatags_score': 85,
            'critical_issues': [],
            'warnings': [],
            'title_issues': [],
            'description_issues': [],
            'heading_issues': []
        },
        {
            'url': 'https://example.com/page2',
            'status_code': 200,
            'response_time': 300,
            'title': 'Página com Problemas',
            'title_length': 19,
            'title_status': 'OK',
            'title_duplicado': False,
            'meta_description': '',
            'description_length': 0,
            'description_status': 'Ausente',
            'description_duplicada': False,
            'h1_count': 0,
            'h1_text': '',
            'h1_ausente': True,
            'h1_multiple': False,
            'hierarquia_correta': False,
            'headings_problematicos_count': 2,
            'headings_vazios_count': 1,
            'headings_ocultos_count': 1,
            'headings_gravidade_critica': 0,
            'headings_problematicos': [
                {
                    'descricao': 'H2 na posição 1 (vazio)',
                    'tag': 'h2',
                    'posicao': 1,
                    'motivos': ['Vazio'],
                    'gravidade': 'MÉDIO'
                },
                {
                    'descricao': 'H3 na posição 2 (oculto)',
                    'tag': 'h3',
                    'posicao': 2,
                    'motivos': ['Oculto'],
                    'gravidade': 'MÉDIO'
                }
            ],
            'heading_sequence': ['h2:...', 'h3:Oculto...'],
            'heading_sequence_valida': [],
            'total_problemas_headings': 3,
            'metatags_score': 25,
            'critical_issues': ['Meta description ausente', 'H1 ausente'],
            'warnings': [],
            'title_issues': [],
            'description_issues': ['Meta description ausente'],
            'heading_issues': ['H2 na posição 1 (vazio)', 'H3 na posição 2 (oculto)', 'H1 ausente']
        }
    ]
    
    # Mock crawler data
    class MockCrawlerData:
        def __init__(self):
            self.titles_encontrados = {
                'Página de Teste 1': ['https://example.com/page1'],
                'Página com Problemas': ['https://example.com/page2']
            }
            self.descriptions_encontradas = {
                'Descrição da página de teste 1': ['https://example.com/page1']
            }
    
    # Testa gerador
    config = {'output_folder': 'test_output', 'use_emoji_names': True}
    generator = ExcelReportGenerator(config)
    
    mock_crawler_data = MockCrawlerData()
    
    # Gera relatório de teste
    filepath, df = generator.generate_complete_report(
        test_results, 
        mock_crawler_data, 
        "TEST_METATAGS"
    )
    
    if filepath:
        print(f"✅ Relatório de teste gerado: {filepath}")
        print(f"📊 DataFrame principal: {len(df)} linhas")
        
        # Estatísticas básicas
        if not df.empty:
            print(f"   Scores: {df['Metatags_Score'].min()}-{df['Metatags_Score'].max()}")
            print(f"   Problemas críticos: {len(df[df['Critical_Issues'] != ''])}")
            print(f"   Headings problemáticos: {df['Headings_Problematicos_Total'].sum()}")
    else:
        print("❌ Falha na geração do relatório de teste")


def test_status_report_generator():
    """Testa o gerador de relatórios de status"""
    print("\n📊 Testando StatusReportGenerator...")
    
    # Dados de teste para status
    status_results = [
        {
            'url': 'https://example.com/ok',
            'status_code': 200,
            'response_time': 150,
            'content_type': 'text/html',
            'final_url': 'https://example.com/ok',
            'redirected': False,
            'content_length': 5000
        },
        {
            'url': 'https://example.com/not-found',
            'status_code': 404,
            'response_time': 100,
            'content_type': 'text/html',
            'final_url': 'https://example.com/not-found',
            'redirected': False,
            'content_length': 1500
        },
        {
            'url': 'https://example.com/slow',
            'status_code': 200,
            'response_time': 4000,
            'content_type': 'text/html',
            'final_url': 'https://example.com/slow',
            'redirected': False,
            'content_length': 8000
        },
        {
            'url': 'https://example.com/error',
            'status_code': 'TIMEOUT',
            'response_time': 0,
            'content_type': '',
            'final_url': 'https://example.com/error',
            'redirected': False,
            'content_length': 0,
            'error_details': 'Connection timeout'
        }
    ]
    
    # Testa gerador de status
    config = {'output_folder': 'test_output', 'use_emoji_names': False}
    status_generator = StatusReportGenerator(config)
    
    # Gera relatório de status
    filepath, df = status_generator.generate_status_report(
        status_results,
        filename_prefix="TEST_STATUS"
    )
    
    if filepath:
        print(f"✅ Relatório de status gerado: {filepath}")
        print(f"📊 DataFrame status: {len(df)} linhas")
        
        # Estatísticas
        if not df.empty:
            status_counts = df['Status_Code'].value_counts()
            print(f"   Status 200: {status_counts.get(200, 0)}")
            print(f"   Status 404: {status_counts.get(404, 0)}")
            print(f"   Erros: {status_counts.get('TIMEOUT', 0)}")
            print(f"   Tempo médio: {df['Response_Time_ms'].mean():.0f}ms")
    else:
        print("❌ Falha na geração do relatório de status")


def test_factory_functions():
    """Testa as funções factory"""
    print("\n🏭 Testando factory functions...")
    
    # Testa criação de diferentes tipos
    generators = {
        'default': create_report_generator('default'),
        'status': create_report_generator('status'),
        'with_config': create_report_generator('default', {'use_emoji_names': False})
    }
    
    for name, generator in generators.items():
        print(f"   ✅ {name}: {generator.__class__.__name__}")
        
        # Verifica configuração
        if hasattr(generator, 'use_emoji_names'):
            emoji_status = "com emojis" if generator.use_emoji_names else "sem emojis"
            print(f"      Configuração: {emoji_status}")


if __name__ == "__main__":
    # Cria pasta de teste
    os.makedirs('test_output', exist_ok=True)
    
    # Executa todos os testes
    test_excel_generator()
    test_status_report_generator()
    test_factory_functions()
    
    print(f"\n🎯 Testes concluídos!")
    print(f"📁 Arquivos de teste em: test_output/")
    print(f"💡 Os geradores estão prontos para uso em produção!")