import pandas as pd
import os
from datetime import datetime
from config.settings import EXCEL_ENGINE, EXCEL_COLORS, COLUMN_WIDTHS, TIMESTAMP_FORMAT
from utils.constants import (
    SHEET_NAMES, SHEET_NAMES_EMOJI, STATUS_SYMBOLS, QUALITY_INDICATORS,
    PRIORITY_ACTIONS, MSG_REPORT_GENERATED, MSG_ERROR_EXCEL
)


class ExcelReportGenerator:
    
    def __init__(self, config=None):
        self.config = config or {}
        self.output_folder = self.config.get('output_folder', 'output')
        self.use_emoji_names = self.config.get('use_emoji_names', True)
        self.sheet_names = SHEET_NAMES_EMOJI if self.use_emoji_names else SHEET_NAMES
        
        os.makedirs(self.output_folder, exist_ok=True)
    
    def generate_complete_report(self, results, crawlers_data=None, filename_prefix="METATAGS_ULTRA"):
        """Gera relatório completo com 8 abas principais"""
        try:
            df_principal = self._create_main_dataframe(results)
            
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
    
    def generate_complete_report_with_filters(self, results, crawlers_data=None, crawler_instance=None, filename_prefix="METATAGS_ULTRA"):
        """Gera relatório completo incluindo dados de URLs filtradas"""
        try:
            df_principal = self._create_main_dataframe(results)
            
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
            
            # Adiciona aba de URLs filtradas se disponível
            if crawler_instance and hasattr(crawler_instance, 'url_manager'):
                filtered_urls = crawler_instance.url_manager.get_filtered_urls()
                if filtered_urls:
                    dataframes['filtered_urls'] = self._create_filtered_urls_dataframe(filtered_urls)
            
            filename = self._generate_filename(filename_prefix)
            filepath = os.path.join(self.output_folder, filename)
            
            success = self._write_excel_file_with_filters(filepath, dataframes)
            
            if success:
                print(MSG_REPORT_GENERATED.format(filename=filepath))
                return filepath, df_principal
            else:
                return None, None
                
        except Exception as e:
            print(MSG_ERROR_EXCEL.format(error=str(e)))
            return None, None
    
    def _create_main_dataframe(self, results):
        """Cria DataFrame principal com todas as métricas"""
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
                # 🆕 MÉTRICAS CORRIGIDAS DE HEADINGS
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
        """🆕 Cria DataFrame consolidado de headings problemáticos (CORREÇÃO PRINCIPAL)"""
        dados_headings_problematicos = []
        
        for resultado in results:
            url = resultado['url']
            headings_problematicos = resultado.get('headings_problematicos', [])
            
            if headings_problematicos:
                problemas_desc = []
                gravidades = []
                motivos_todos = []
                
                for heading_prob in headings_problematicos:
                    desc = heading_prob.get('descricao', '')
                    problemas_desc.append(desc)
                    gravidades.append(heading_prob.get('gravidade', 'MÉDIO'))
                    motivos_todos.extend(heading_prob.get('motivos', []))
                
                # 🔥 GRAVIDADE DIFERENCIADA: CRÍTICO se tem H1s problemáticos
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
        """Cria DataFrame específico para problemas de hierarquia"""
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
        """Cria DataFrame de títulos duplicados"""
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
        """Cria DataFrame de descriptions duplicadas"""
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
        """Cria DataFrame só com problemas críticos"""
        dados_criticos = []
        
        for resultado in results:
            if (resultado.get('title_status') == 'Ausente' or
                resultado.get('description_status') == 'Ausente' or
                resultado.get('h1_ausente', True) or
                resultado.get('critical_issues') or
                resultado.get('headings_gravidade_critica', 0) > 0):  # 🆕 HEADINGS CRÍTICOS
                
                dados_criticos.append({
                    'URL': resultado['url'],
                    'Status_Code': resultado.get('status_code', ''),
                    'Title_Status': resultado.get('title_status', ''),
                    'Description_Status': resultado.get('description_status', ''),
                    'H1_Ausente': 'SIM' if resultado.get('h1_ausente', True) else 'NÃO',
                    'Headings_Criticos': resultado.get('headings_gravidade_critica', 0),  # 🆕
                    'Total_Problemas_Headings': resultado.get('total_problemas_headings', 0),  # 🆕
                    'Critical_Issues': ' | '.join(resultado.get('critical_issues', [])),
                    'Metatags_Score': resultado.get('metatags_score', 0)
                })
        
        return pd.DataFrame(dados_criticos) if dados_criticos else pd.DataFrame()
    
    def _create_score_ranking_dataframe(self, df_principal):
        """Cria DataFrame ranking por score"""
        if df_principal.empty:
            return pd.DataFrame()
        
        df_score = df_principal.sort_values('Metatags_Score', ascending=False).copy()
        return df_score[['URL', 'Metatags_Score', 'Title_Status', 'Description_Status', 'H1_Ausente', 'Headings_Problematicos_Total']]
    
    def _create_executive_summary_dataframe(self, df_principal, crawlers_data):
        """🆕 Cria resumo executivo com todas as correções"""
        total_urls = len(df_principal)
        
        if total_urls == 0:
            return pd.DataFrame([['Nenhuma URL analisada', '']], columns=['Métrica', 'Valor'])
        
        # Métricas básicas
        title_ok = len(df_principal[df_principal['Title_Status'] == 'OK'])
        title_ausente = len(df_principal[df_principal['Title_Status'] == 'Ausente'])
        title_duplicados = len(df_principal[df_principal['Title_Duplicado'] == 'SIM'])
        
        desc_ok = len(df_principal[df_principal['Description_Status'] == 'OK'])
        desc_ausente = len(df_principal[df_principal['Description_Status'] == 'Ausente'])
        desc_duplicadas = len(df_principal[df_principal['Description_Duplicada'] == 'SIM'])
        
        h1_ausente = len(df_principal[df_principal['H1_Ausente'] == 'SIM'])
        hierarquia_incorreta = len(df_principal[df_principal['Hierarquia_Correta'] == 'NÃO'])
        
        # 🆕 MÉTRICAS CORRIGIDAS DE HEADINGS
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
        ], columns=['Métrica', 'Valor'])
    
    def _create_filtered_urls_dataframe(self, filtered_urls):
        """Cria DataFrame de URLs filtradas durante o crawling"""
        if not filtered_urls:
            return pd.DataFrame()
        
        dados_filtrados = []
        
        # Análise dos tipos de filtro
        tipos_filtro = {}
        for url_data in filtered_urls:
            tipo = url_data.get('reason', 'Desconhecido')
            if tipo not in tipos_filtro:
                tipos_filtro[tipo] = []
            tipos_filtro[tipo].append(url_data)
        
        # Cria dados detalhados
        for url_data in filtered_urls:
            dados_filtrados.append({
                'URL_Filtrada': url_data.get('url', ''),
                'Motivo_Filtro': url_data.get('reason', 'Desconhecido'),
                'Detalhes': url_data.get('details', ''),
                'Categoria': self._classify_filter_type(url_data.get('reason', '')),
                'Impacto_SEO': self._get_filter_seo_impact(url_data.get('reason', ''))
            })
        
        df_filtered = pd.DataFrame(dados_filtrados)
        
        # Adiciona resumo no topo
        if not df_filtered.empty:
            resumo_data = []
            for categoria in df_filtered['Categoria'].unique():
                count = len(df_filtered[df_filtered['Categoria'] == categoria])
                resumo_data.append({
                    'URL_Filtrada': f'📊 RESUMO: {categoria}',
                    'Motivo_Filtro': f'{count} URLs filtradas',
                    'Detalhes': 'Estatística automática',
                    'Categoria': 'RESUMO',
                    'Impacto_SEO': 'URLs filtradas não afetam SEO'
                })
            
            df_resumo = pd.DataFrame(resumo_data)
            df_filtered = pd.concat([df_resumo, df_filtered], ignore_index=True)
        
        return df_filtered
    
    def _classify_filter_type(self, reason):
        """Classifica tipo de filtro para melhor organização"""
        if 'ECOMMERCE' in reason.upper():
            return '🛒 E-commerce'
        elif 'FILE_EXTENSION' in reason.upper():
            return '📁 Arquivo'
        elif 'TECHNICAL' in reason.upper():
            return '⚙️ Técnico'
        elif 'PARAM' in reason.upper():
            return '🔗 Parâmetro'
        elif 'INVALID' in reason.upper():
            return '❌ Inválida'
        else:
            return '❓ Outros'
    
    def _get_filter_seo_impact(self, reason):
        """Avalia impacto SEO do filtro aplicado"""
        if 'ECOMMERCE' in reason.upper():
            return 'Positivo: Evita 404s de endpoints'
        elif 'FILE_EXTENSION' in reason.upper():
            return 'Positivo: Foca apenas em páginas'
        elif 'TECHNICAL' in reason.upper():
            return 'Positivo: Evita URLs técnicas'
        elif 'PARAM' in reason.upper():
            return 'Positivo: Evita URLs com parâmetros'
        elif 'INVALID' in reason.upper():
            return 'Neutral: URL inválida'
        else:
            return 'Verificar caso específico'
    
    def _write_excel_file(self, filepath, dataframes):
        """Escreve arquivo Excel com 8 abas principais"""
        try:
            with pd.ExcelWriter(filepath, engine=EXCEL_ENGINE) as writer:
                # 1. ABA PRINCIPAL - Dados completos
                if not dataframes['main'].empty:
                    dataframes['main'].to_excel(writer, sheet_name=self.sheet_names.get('complete', 'Complete'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('complete', 'Complete')}' criada")
                
                # 2. ABA CRÍTICOS - Problemas críticos
                if not dataframes['critical'].empty:
                    dataframes['critical'].to_excel(writer, sheet_name=self.sheet_names.get('critical', 'Criticos'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('critical', 'Criticos')}' criada")
                else:
                    pd.DataFrame(columns=['URL', 'Status_Code', 'Title_Status', 'Description_Status', 'H1_Ausente']).to_excel(
                        writer, sheet_name=self.sheet_names.get('critical', 'Criticos'), index=False)
                
                # 3. 🆕 ABA HEADINGS PROBLEMÁTICOS - Consolidada (CORREÇÃO PRINCIPAL)
                if not dataframes['headings_problematic'].empty:
                    dataframes['headings_problematic'].to_excel(writer, sheet_name=self.sheet_names.get('headings_problematic', 'Headings_Problematicos'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('headings_problematic', 'Headings_Problematicos')}' criada (CONSOLIDADA)")
                else:
                    pd.DataFrame(columns=['URL', 'Total_Problemas', 'Headings_Vazios', 'Headings_Ocultos', 'Gravidade_Geral']).to_excel(
                        writer, sheet_name=self.sheet_names.get('headings_problematic', 'Headings_Problematicos'), index=False)
                
                # 4. ABA HIERARQUIA - Problemas de hierarquia
                if not dataframes['hierarchy'].empty:
                    dataframes['hierarchy'].to_excel(writer, sheet_name=self.sheet_names.get('hierarchy', 'Hierarquia'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('hierarchy', 'Hierarquia')}' criada")
                else:
                    pd.DataFrame(columns=['URL', 'Problemas_Hierarquia', 'H1_Count', 'H1_Text']).to_excel(
                        writer, sheet_name=self.sheet_names.get('hierarchy', 'Hierarquia'), index=False)
                
                # 5. ABA TÍTULOS DUPLICADOS
                if not dataframes['title_duplicates'].empty:
                    dataframes['title_duplicates'].to_excel(writer, sheet_name=self.sheet_names.get('title_duplicates', 'Title_Duplicados'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('title_duplicates', 'Title_Duplicados')}' criada")
                else:
                    pd.DataFrame(columns=['Title_Duplicado', 'URL', 'Total_Duplicatas']).to_excel(
                        writer, sheet_name=self.sheet_names.get('title_duplicates', 'Title_Duplicados'), index=False)
                
                # 6. ABA DESCRIPTIONS DUPLICADAS
                if not dataframes['description_duplicates'].empty:
                    dataframes['description_duplicates'].to_excel(writer, sheet_name=self.sheet_names.get('description_duplicates', 'Desc_Duplicadas'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('description_duplicates', 'Desc_Duplicadas')}' criada")
                else:
                    pd.DataFrame(columns=['Description_Duplicada', 'URL', 'Total_Duplicatas']).to_excel(
                        writer, sheet_name=self.sheet_names.get('description_duplicates', 'Desc_Duplicadas'), index=False)
                
                # 7. ABA RANKING POR SCORE
                if not dataframes['score_ranking'].empty:
                    dataframes['score_ranking'].to_excel(writer, sheet_name=self.sheet_names.get('score_ranking', 'Score_Ranking'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('score_ranking', 'Score_Ranking')}' criada")
                else:
                    pd.DataFrame(columns=['URL', 'Metatags_Score', 'Title_Status']).to_excel(
                        writer, sheet_name=self.sheet_names.get('score_ranking', 'Score_Ranking'), index=False)
                
                # 8. ABA RESUMO EXECUTIVO
                if not dataframes['summary'].empty:
                    dataframes['summary'].to_excel(writer, sheet_name=self.sheet_names.get('summary', 'Resumo'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('summary', 'Resumo')}' criada")
                else:
                    pd.DataFrame(columns=['Métrica', 'Valor']).to_excel(
                        writer, sheet_name=self.sheet_names.get('summary', 'Resumo'), index=False)
                
                # Aplica formatação
                self._apply_excel_formatting(writer)
                
                print(f"   ✅ Total de 8 abas criadas com sucesso!")
            
            return True
            
        except Exception as e:
            print(MSG_ERROR_EXCEL.format(error=str(e)))
            return False
    
    def _write_excel_file_with_filters(self, filepath, dataframes):
        """Escreve arquivo Excel incluindo aba de URLs filtradas"""
        try:
            with pd.ExcelWriter(filepath, engine=EXCEL_ENGINE) as writer:
                # 1-8. ABAS PRINCIPAIS (mesmo código do método anterior)
                if not dataframes['main'].empty:
                    dataframes['main'].to_excel(writer, sheet_name=self.sheet_names.get('complete', 'Complete'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('complete', 'Complete')}' criada")
                
                if not dataframes['critical'].empty:
                    dataframes['critical'].to_excel(writer, sheet_name=self.sheet_names.get('critical', 'Criticos'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('critical', 'Criticos')}' criada")
                else:
                    pd.DataFrame(columns=['URL', 'Status_Code', 'Title_Status']).to_excel(
                        writer, sheet_name=self.sheet_names.get('critical', 'Criticos'), index=False)
                
                if not dataframes['headings_problematic'].empty:
                    dataframes['headings_problematic'].to_excel(writer, sheet_name=self.sheet_names.get('headings_problematic', 'Headings_Problematicos'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('headings_problematic', 'Headings_Problematicos')}' criada (CONSOLIDADA)")
                else:
                    pd.DataFrame(columns=['URL', 'Total_Problemas']).to_excel(
                        writer, sheet_name=self.sheet_names.get('headings_problematic', 'Headings_Problematicos'), index=False)
                
                if not dataframes['hierarchy'].empty:
                    dataframes['hierarchy'].to_excel(writer, sheet_name=self.sheet_names.get('hierarchy', 'Hierarquia'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('hierarchy', 'Hierarquia')}' criada")
                
                if not dataframes['title_duplicates'].empty:
                    dataframes['title_duplicates'].to_excel(writer, sheet_name=self.sheet_names.get('title_duplicates', 'Title_Duplicados'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('title_duplicates', 'Title_Duplicados')}' criada")
                
                if not dataframes['description_duplicates'].empty:
                    dataframes['description_duplicates'].to_excel(writer, sheet_name=self.sheet_names.get('description_duplicates', 'Desc_Duplicadas'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('description_duplicates', 'Desc_Duplicadas')}' criada")
                
                if not dataframes['score_ranking'].empty:
                    dataframes['score_ranking'].to_excel(writer, sheet_name=self.sheet_names.get('score_ranking', 'Score_Ranking'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('score_ranking', 'Score_Ranking')}' criada")
                
                if not dataframes['summary'].empty:
                    dataframes['summary'].to_excel(writer, sheet_name=self.sheet_names.get('summary', 'Resumo'), index=False)
                    print(f"   ✅ Aba '{self.sheet_names.get('summary', 'Resumo')}' criada")
                
                # 9. ABA ADICIONAL - URLs FILTRADAS (se disponível)
                if 'filtered_urls' in dataframes and not dataframes['filtered_urls'].empty:
                    dataframes['filtered_urls'].to_excel(writer, sheet_name='URLs_Filtradas', index=False)
                    print(f"   ✅ Aba 'URLs_Filtradas' criada")
                
                # Aplica formatação
                self._apply_excel_formatting(writer)
                
                total_abas = 8 + (1 if 'filtered_urls' in dataframes and not dataframes['filtered_urls'].empty else 0)
                print(f"   ✅ Total de {total_abas} abas criadas com sucesso!")
            
            return True
            
        except Exception as e:
            print(MSG_ERROR_EXCEL.format(error=str(e)))
            return False
    
    def _apply_excel_formatting(self, writer):
        """Aplica formatação condicional nas abas do Excel"""
        try:
            workbook = writer.book
            
            # Formatos
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': EXCEL_COLORS['header_bg'],
                'font_color': EXCEL_COLORS['header_font'],
                'border': 1
            })
            
            success_format = workbook.add_format({
                'fg_color': EXCEL_COLORS['success'],
                'font_color': 'white'
            })
            
            warning_format = workbook.add_format({
                'fg_color': EXCEL_COLORS['warning'],
                'font_color': 'black'
            })
            
            error_format = workbook.add_format({
                'fg_color': EXCEL_COLORS['error'],
                'font_color': 'white'
            })
            
            # Aplica formatação específica por aba
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                
                # Formatação específica para aba de Headings Problemáticos
                if 'Headings_Problematicos' in sheet_name or 'headings_problematic' in sheet_name.lower():
                    worksheet.set_column('A:A', COLUMN_WIDTHS['url'])      # URL
                    worksheet.set_column('B:E', COLUMN_WIDTHS['counter'])   # Contadores
                    worksheet.set_column('F:F', COLUMN_WIDTHS['problems_detailed'])  # Problemas detalhados
                    worksheet.set_column('G:K', COLUMN_WIDTHS['standard'])  # Outras colunas
                
                # Formatação para aba de Hierarquia
                elif 'Hierarquia' in sheet_name or 'hierarchy' in sheet_name.lower():
                    worksheet.set_column('A:A', COLUMN_WIDTHS['url'])
                    worksheet.set_column('B:B', COLUMN_WIDTHS['sequence'])  # Problemas hierarquia
                    worksheet.set_column('C:H', COLUMN_WIDTHS['standard'])
                
                # Formatação para aba de Resumo
                elif 'Resumo' in sheet_name or 'summary' in sheet_name.lower():
                    worksheet.set_column('A:A', COLUMN_WIDTHS['sequence'])  # Métrica
                    worksheet.set_column('B:B', COLUMN_WIDTHS['standard'])  # Valor
                
                # Formatação para aba de URLs Filtradas
                elif 'URLs_Filtradas' in sheet_name:
                    worksheet.set_column('A:A', COLUMN_WIDTHS['url'])
                    worksheet.set_column('B:E', COLUMN_WIDTHS['standard'])
                
                # Formatação padrão para outras abas
                else:
                    worksheet.set_column('A:A', COLUMN_WIDTHS['url'])
                    worksheet.set_column('B:Z', COLUMN_WIDTHS['standard'])
        
        except Exception as e:
            print(f"⚠️ Erro na formatação: {e}")
    
    def _generate_filename(self, prefix):
        """Gera nome do arquivo com timestamp"""
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        return f"{prefix}_CORRIGIDO_{timestamp}.xlsx"


class StatusReportGenerator(ExcelReportGenerator):
    """Gerador especializado para relatórios de status HTTP"""
    
    def generate_status_report(self, results, mixed_content_data=None, filename_prefix="STATUS_REPORT"):
        """Gera relatório específico para análise de status HTTP"""
        try:
            df_principal = self._create_status_main_dataframe(results)
            
            dataframes = {
                'main': df_principal,
                'errors': self._create_status_errors_dataframe(results),
                'mixed_content': self._create_mixed_content_dataframe(mixed_content_data) if mixed_content_data else pd.DataFrame(),
                'performance': self._create_performance_dataframe(results),
                'summary': self._create_status_summary_dataframe(df_principal)
            }
            
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
        """Cria DataFrame principal para análise de status"""
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
        """Cria DataFrame específico para erros HTTP"""
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
        """Cria DataFrame para problemas de mixed content"""
        if not mixed_content_data:
            return pd.DataFrame()
        
        return pd.DataFrame(mixed_content_data)
    
    def _create_performance_dataframe(self, results):
        """Cria DataFrame focado em performance"""
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
        
        df_performance = pd.DataFrame(dados_performance)
        if not df_performance.empty:
            df_performance = df_performance.sort_values('Response_Time_ms', ascending=False)
        
        return df_performance
    
    def _create_status_summary_dataframe(self, df_principal):
        """Cria resumo executivo para status HTTP"""
        total_urls = len(df_principal)
        
        if total_urls == 0:
            return pd.DataFrame([['Nenhuma URL analisada', '']], columns=['Métrica', 'Valor'])
        
        status_200 = len(df_principal[df_principal['Status_Code'] == 200])
        status_404 = len(df_principal[df_principal['Status_Code'] == 404])
        status_500 = len(df_principal[(df_principal['Status_Code'] >= 500) & (df_principal['Status_Code'] < 600)])
        redirects = len(df_principal[df_principal['Redirected'] == 'SIM'])
        https_count = len(df_principal[df_principal['Is_HTTPS'] == 'SIM'])
        
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
        """Classifica tipo de erro HTTP"""
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
        """Classifica performance da página"""
        if response_time < 1000:
            return "🟢 Rápido"
        elif response_time < 3000:
            return "🟡 Médio"
        else:
            return "🔴 Lento"
    
    def _write_status_excel_file(self, filepath, dataframes):
        """Escreve arquivo Excel específico para status"""
        try:
            with pd.ExcelWriter(filepath, engine=EXCEL_ENGINE) as writer:
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
                
                self._apply_excel_formatting(writer)
            
            return True
            
        except Exception as e:
            print(MSG_ERROR_EXCEL.format(error=str(e)))
            return False


def create_report_generator(report_type='default', config=None):
    """Factory function para criar geradores de relatório"""
    
    if report_type == 'status':
        return StatusReportGenerator(config)
    
    else:  # default
        return ExcelReportGenerator(config)


def test_excel_generator():
    """Função de teste para o ExcelReportGenerator"""
    print("Testando ExcelReportGenerator...")
    
    # Dados de teste simulando resultados do análise
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
            # 🆕 MÉTRICAS CORRIGIDAS
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
            'heading_issues': [],
            'headings_problematicos': []
        },
        {
            'url': 'https://example.com/page2',
            'status_code': 200,
            'response_time': 200,
            'title': '',  # Title ausente
            'title_length': 0,
            'title_status': 'Ausente',
            'title_duplicado': False,
            'meta_description': '',  # Description ausente
            'description_length': 0,
            'description_status': 'Ausente',
            'description_duplicada': False,
            'h1_count': 0,  # H1 ausente
            'h1_text': '',
            'h1_ausente': True,
            'h1_multiple': False,
            'hierarquia_correta': False,
            # 🆕 MÉTRICAS CORRIGIDAS - COM PROBLEMAS
            'headings_problematicos_count': 2,
            'headings_vazios_count': 1,
            'headings_ocultos_count': 1,
            'headings_gravidade_critica': 1,  # H1 problemático
            'heading_sequence': ['h2:(vazio)', 'h3:Texto oculto'],
            'heading_sequence_valida': [],  # Sequência válida vazia
            'total_problemas_headings': 3,
            'metatags_score': 25,
            'critical_issues': ['Title ausente', 'Meta description ausente', 'H1 ausente'],
            'warnings': ['Headings problemáticos (2)'],
            'title_issues': ['Title ausente'],
            'description_issues': ['Meta description ausente'],
            'heading_issues': ['H1 ausente', 'H2 vazio na posição 1', 'H3 oculto na posição 2'],
            'headings_problematicos': [
                {
                    'descricao': 'H2 na posição 1 (vazio)',
                    'tag': 'h2',
                    'posicao': 1,
                    'texto': '',
                    'motivos': ['Vazio'],
                    'gravidade': 'MÉDIO'
                },
                {
                    'descricao': 'H3 na posição 2 (oculto)',
                    'tag': 'h3',
                    'posicao': 2,
                    'texto': 'Texto oculto',
                    'motivos': ['Oculto'],
                    'gravidade': 'MÉDIO'
                }
            ]
        }
    ]
    
    # Mock para dados do crawler
    class MockCrawlerData:
        def __init__(self):
            self.titles_encontrados = {
                'Página de Teste 1': ['https://example.com/page1']
            }
            self.descriptions_encontradas = {
                'Descrição da página de teste 1': ['https://example.com/page1']
            }
    
    # Configuração de teste
    config = {'output_folder': 'test_output', 'use_emoji_names': True}
    generator = ExcelReportGenerator(config)
    
    mock_crawler_data = MockCrawlerData()
    
    # Gera relatório de teste
    filepath, df = generator.generate_complete_report(
        test_results, 
        mock_crawler_data, 
        "TEST_METATAGS_CORRIGIDO"
    )
    
    if filepath:
        print(f"✅ Relatório de teste gerado: {filepath}")
        print(f"📊 DataFrame principal: {len(df)} linhas")
        print(f"🔥 Teste das correções de headings incluído!")
    else:
        print("❌ Falha na geração do relatório de teste")


if __name__ == "__main__":
    import os
    os.makedirs('test_output', exist_ok=True)
    test_excel_generator()
    print("🎯 Testes concluídos!")