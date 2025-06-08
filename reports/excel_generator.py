# reports/excel_generator.py - Gerador Excel SIMPLIFICADO (4 abas apenas)

import pandas as pd
import xlsxwriter
from datetime import datetime
import os
from urllib.parse import urlparse

from utils.constants import MSG_REPORT_GENERATED, MSG_NO_RESULTS
from config.settings import COLUMN_WIDTHS


class ExcelReportGenerator:
    """📊 Gerador Excel SIMPLIFICADO - APENAS 4 ABAS"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.output_folder = self.config.get('folder', 'output')
        
        # Garante que pasta existe
        os.makedirs(self.output_folder, exist_ok=True)
        
    def generate_complete_report(self, results, crawlers_data=None, filename_prefix="SEO_ANALYSIS"):
        """🎯 Gera relatório Excel com APENAS 4 abas específicas"""
        
        if not results:
            print(MSG_NO_RESULTS)
            return None, None
        
        try:
            print(f"📊 Processando {len(results)} resultados...")
            
            # Processa e padroniza dados
            processed_results = self._process_results(results)
            
            # Cria as 4 abas obrigatórias
            dataframes = self._create_four_tabs_only(processed_results)
            
            # Gera arquivo Excel
            filepath = self._generate_excel_file(dataframes, filename_prefix)
            
            # Retorna dados principais
            main_df = dataframes.get('todas_urls', pd.DataFrame())
            
            print(MSG_REPORT_GENERATED.format(filename=filepath))
            return filepath, main_df
            
        except Exception as e:
            print(f"❌ Erro gerando relatório Excel: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def _process_results(self, results):
        """🔧 Processa resultados combinando status + metatags"""
        processed = []
        
        for result in results:
            if not isinstance(result, dict):
                continue
            
            # Combina dados de status e metatags em um resultado único
            combined_result = self._combine_status_and_metatags(result)
            processed.append(combined_result)
        
        return processed
    
    def _combine_status_and_metatags(self, result):
        """🔗 Combina dados de StatusAnalyzer e MetatagsAnalyzer"""
        
        combined = {
            # URL e Status (StatusAnalyzer)
            'URL': result.get('url', result.get('URL', '')),
            'Status_Code': result.get('Status_Code', result.get('status_code', 'UNKNOWN')),
            'Response_Time_ms': result.get('Response_Time_ms', result.get('response_time', result.get('Response_Time', 0))),
            'Final_URL': result.get('Final_URL', result.get('final_url', result.get('url', ''))),
            'Redirected': self._convert_to_sim_nao(result.get('Redirected', result.get('redirected', False))),
            
            # Title (MetatagsAnalyzer)
            'Title': result.get('Title', result.get('title', '')),
            'Title_Length': result.get('Title_Length', result.get('title_length', 0)),
            'Title_Status': result.get('Title_Status', result.get('title_status', 'Ausente')),
            'Title_Duplicado': self._convert_to_sim_nao(result.get('Title_Duplicado', result.get('title_duplicado', False))),
            
            # Description (MetatagsAnalyzer)
            'Meta_Description': result.get('Meta_Description', result.get('meta_description', '')),
            'Description_Length': result.get('Description_Length', result.get('description_length', 0)),
            'Description_Status': result.get('Description_Status', result.get('description_status', 'Ausente')),
            'Description_Duplicada': self._convert_to_sim_nao(result.get('Description_Duplicada', result.get('description_duplicada', False))),
            
            # H1 e Headings (HeadingsAnalyzer integrado)
            'H1_Count': result.get('H1_Count', result.get('h1_count', 0)),
            'H1_Text': result.get('H1_Text', result.get('h1_text', '')),
            'H1_Ausente': self._convert_to_sim_nao(result.get('H1_Ausente', result.get('h1_ausente', True))),
            'H1_Multiple': self._convert_to_sim_nao(result.get('H1_Multiple', result.get('h1_multiple', False))),
            'Hierarquia_Correta': self._convert_to_sim_nao(result.get('Hierarquia_Correta', result.get('hierarquia_correta', True))),
            
            # Headings Problemáticos (correções implementadas)
            'Headings_Problematicos_Total': result.get('Headings_Problematicos_Total', result.get('headings_problematicos_count', 0)),
            'Headings_Vazios': result.get('Headings_Vazios', result.get('headings_vazios_count', 0)),
            'Headings_Ocultos': result.get('Headings_Ocultos', result.get('headings_ocultos_count', 0)),
            
            # Score
            'Metatags_Score': result.get('Metatags_Score', result.get('metatags_score', 0)),
            
            # Issues
            'Critical_Issues': self._format_list_field(result.get('Critical_Issues', result.get('critical_issues', []))),
            'Warnings': self._format_list_field(result.get('Warnings', result.get('warnings', []))),
            
            # Mixed Content (StatusAnalyzer)
            'Has_Mixed_Content': self._convert_to_sim_nao(result.get('Has_Mixed_Content', result.get('has_mixed_content', False))),
            'Mixed_Content_Count': result.get('Mixed_Content_Count', result.get('mixed_content_count', 0)),
            'Mixed_Content_Resources': result.get('mixed_content_resources', []),
            
            # Outras metatags
            'Canonical_URL': result.get('Canonical_URL', result.get('canonical_url', '')),
            'Meta_Viewport': result.get('Meta_Viewport', result.get('meta_viewport', '')),
            'Has_Open_Graph': self._convert_to_sim_nao(result.get('Has_Open_Graph', result.get('has_open_graph', False))),
        }
        
        return combined
    
    def _convert_to_sim_nao(self, value):
        """🔄 Converte boolean para SIM/NÃO"""
        if isinstance(value, bool):
            return 'SIM' if value else 'NÃO'
        elif isinstance(value, str):
            return value.upper() if value.upper() in ['SIM', 'NÃO'] else ('SIM' if value.lower() in ['true', 'yes', 'sim'] else 'NÃO')
        else:
            return 'NÃO'
    
    def _format_list_field(self, field):
        """📋 Formata campos de lista para string"""
        if isinstance(field, list):
            if not field:
                return ''
            str_items = []
            for item in field:
                if isinstance(item, dict):
                    if 'descricao' in item:
                        str_items.append(item['descricao'])
                    elif 'url' in item:
                        str_items.append(item['url'])
                    else:
                        str_items.append(str(item))
                else:
                    str_items.append(str(item))
            return ' | '.join(str_items)
        elif isinstance(field, str):
            return field
        elif field is None:
            return ''
        else:
            return str(field)
    
    def _create_four_tabs_only(self, processed_results):
        """📊 Cria APENAS as 4 abas obrigatórias"""
        
        dataframes = {}
        
        # ABA 1: TODAS AS URLs (combinando status + metatags)
        dataframes['todas_urls'] = self._create_all_urls_dataframe(processed_results)
        
        # ABA 2: MIXED CONTENT (mesmo que vazia)
        dataframes['mixed_content'] = self._create_mixed_content_dataframe(processed_results)
        
        # ABA 3: TITLES (duplicados + ausentes)
        dataframes['titles_issues'] = self._create_titles_issues_dataframe(processed_results)
        
        # ABA 4: DESCRIPTIONS (duplicadas + ausentes)
        dataframes['descriptions_issues'] = self._create_descriptions_issues_dataframe(processed_results)
        
        return dataframes
    
    def _create_all_urls_dataframe(self, results):
        """📋 ABA 1: Todas as URLs com dados combinados (status + metatags)"""
        
        if not results:
            return pd.DataFrame()
        
        # Colunas na ordem desejada
        columns_order = [
            'URL', 'Status_Code', 'Response_Time_ms', 'Final_URL', 'Redirected',
            'Title', 'Title_Length', 'Title_Status', 'Title_Duplicado',
            'Meta_Description', 'Description_Length', 'Description_Status', 'Description_Duplicada',
            'H1_Count', 'H1_Text', 'H1_Ausente', 'H1_Multiple', 'Hierarquia_Correta',
            'Headings_Problematicos_Total', 'Headings_Vazios', 'Headings_Ocultos',
            'Metatags_Score', 'Critical_Issues', 'Warnings',
            'Has_Mixed_Content', 'Mixed_Content_Count',
            'Canonical_URL', 'Meta_Viewport', 'Has_Open_Graph'
        ]
        
        df = pd.DataFrame(results)
        
        # Reordena colunas se existirem
        available_columns = [col for col in columns_order if col in df.columns]
        other_columns = [col for col in df.columns if col not in columns_order]
        
        final_columns = available_columns + other_columns
        df = df[final_columns] if final_columns else df
        
        return df
    
    def _create_mixed_content_dataframe(self, results):
        """🔒 ABA 2: Mixed Content (pode ficar vazia)"""
        
        mixed_content_data = []
        
        for result in results:
            if result.get('Has_Mixed_Content') == 'SIM':
                mixed_resources = result.get('Mixed_Content_Resources', [])
                
                if isinstance(mixed_resources, list) and mixed_resources:
                    for resource in mixed_resources:
                        if isinstance(resource, dict):
                            mixed_content_data.append({
                                'URL_Pagina': result['URL'],
                                'Recurso_Inseguro': resource.get('url', ''),
                                'Tipo_Recurso': resource.get('type', ''),
                                'Tag_HTML': resource.get('tag', ''),
                                'Atributo': resource.get('attribute', ''),
                                'Elemento_HTML': resource.get('element', '')[:100] + '...' if len(resource.get('element', '')) > 100 else resource.get('element', ''),
                                'Dominio_Inseguro': urlparse(resource.get('url', '')).netloc if resource.get('url') else '',
                                'Risco_Seguranca': self._assess_mixed_content_risk(resource.get('type', ''))
                            })
                        elif isinstance(resource, str):
                            mixed_content_data.append({
                                'URL_Pagina': result['URL'],
                                'Recurso_Inseguro': resource,
                                'Tipo_Recurso': 'unknown',
                                'Tag_HTML': '',
                                'Atributo': '',
                                'Elemento_HTML': '',
                                'Dominio_Inseguro': urlparse(resource).netloc if resource else '',
                                'Risco_Seguranca': 'MÉDIO'
                            })
                else:
                    # Se tem mixed content mas sem detalhes, cria entrada genérica
                    mixed_content_data.append({
                        'URL_Pagina': result['URL'],
                        'Recurso_Inseguro': 'Mixed content detectado (sem detalhes)',
                        'Tipo_Recurso': 'unknown',
                        'Tag_HTML': '',
                        'Atributo': '',
                        'Elemento_HTML': '',
                        'Dominio_Inseguro': '',
                        'Risco_Seguranca': 'MÉDIO'
                    })
        
        # Retorna DataFrame mesmo que vazio
        return pd.DataFrame(mixed_content_data)
    
    def _assess_mixed_content_risk(self, resource_type):
        """🔒 Avalia risco de segurança do mixed content"""
        high_risk = ['script', 'iframe', 'object', 'embed']
        medium_risk = ['stylesheet', 'font']
        
        if resource_type in high_risk:
            return 'ALTO'
        elif resource_type in medium_risk:
            return 'MÉDIO'
        else:
            return 'BAIXO'
    
    def _create_titles_issues_dataframe(self, results):
        """🔄 ABA 3: Titles Duplicados + Ausentes"""
        
        titles_issues_data = []
        
        # Agrupa por título para duplicados
        title_groups = {}
        titles_ausentes = []
        
        for result in results:
            title = result.get('Title', '').strip()
            url = result.get('URL', '')
            
            # Verifica se title está ausente
            if not title or result.get('Title_Status') == 'Ausente':
                titles_ausentes.append({
                    'URL': url,
                    'Problema': 'Title Ausente',
                    'Title': title,
                    'Title_Length': result.get('Title_Length', 0),
                    'Status_Code': result.get('Status_Code', ''),
                    'Score': result.get('Metatags_Score', 0)
                })
            
            # Agrupa duplicados
            if title and result.get('Title_Duplicado') == 'SIM':
                if title not in title_groups:
                    title_groups[title] = []
                title_groups[title].append({
                    'url': url,
                    'score': result.get('Metatags_Score', 0),
                    'status': result.get('Status_Code', '')
                })
        
        # Adiciona títulos ausentes
        titles_issues_data.extend(titles_ausentes)
        
        # Adiciona títulos duplicados
        for title, urls_data in title_groups.items():
            if len(urls_data) > 1:
                for url_data in urls_data:
                    titles_issues_data.append({
                        'URL': url_data['url'],
                        'Problema': 'Title Duplicado',
                        'Title': title,
                        'Title_Length': len(title),
                        'Status_Code': url_data['status'],
                        'Score': url_data['score'],
                        'Total_URLs_Com_Mesmo_Title': len(urls_data),
                        'Outras_URLs': ' | '.join([u['url'] for u in urls_data if u['url'] != url_data['url']])
                    })
        
        # Retorna DataFrame mesmo que vazio
        return pd.DataFrame(titles_issues_data)
    
    def _create_descriptions_issues_dataframe(self, results):
        """🔄 ABA 4: Descriptions Duplicadas + Ausentes"""
        
        descriptions_issues_data = []
        
        # Agrupa por description para duplicados
        desc_groups = {}
        descriptions_ausentes = []
        
        for result in results:
            description = result.get('Meta_Description', '').strip()
            url = result.get('URL', '')
            
            # Verifica se description está ausente
            if not description or result.get('Description_Status') == 'Ausente':
                descriptions_ausentes.append({
                    'URL': url,
                    'Problema': 'Description Ausente',
                    'Meta_Description': description,
                    'Description_Length': result.get('Description_Length', 0),
                    'Status_Code': result.get('Status_Code', ''),
                    'Score': result.get('Metatags_Score', 0)
                })
            
            # Agrupa duplicados
            if description and result.get('Description_Duplicada') == 'SIM':
                if description not in desc_groups:
                    desc_groups[description] = []
                desc_groups[description].append({
                    'url': url,
                    'score': result.get('Metatags_Score', 0),
                    'status': result.get('Status_Code', '')
                })
        
        # Adiciona descriptions ausentes
        descriptions_issues_data.extend(descriptions_ausentes)
        
        # Adiciona descriptions duplicadas
        for description, urls_data in desc_groups.items():
            if len(urls_data) > 1:
                for url_data in urls_data:
                    descriptions_issues_data.append({
                        'URL': url_data['url'],
                        'Problema': 'Description Duplicada',
                        'Meta_Description': description[:100] + '...' if len(description) > 100 else description,
                        'Description_Completa': description,
                        'Description_Length': len(description),
                        'Status_Code': url_data['status'],
                        'Score': url_data['score'],
                        'Total_URLs_Com_Mesma_Description': len(urls_data),
                        'Outras_URLs': ' | '.join([u['url'] for u in urls_data if u['url'] != url_data['url']])
                    })
        
        # Retorna DataFrame mesmo que vazio
        return pd.DataFrame(descriptions_issues_data)
    
    def _generate_excel_file(self, dataframes, filename_prefix):
        """📊 Gera arquivo Excel com as 4 abas"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.xlsx"
        filepath = os.path.join(self.output_folder, filename)
        
        # Configuração do writer
        workbook = xlsxwriter.Workbook(filepath, {'remove_timezone': True})
        
        # Formato para headers
        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })
        
        # Formato para dados
        normal_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'top',
            'text_wrap': True
        })
        
        # Formato para números
        number_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'num_format': '0'
        })
        
        # CRIA AS 4 ABAS OBRIGATÓRIAS
        sheet_configs = [
            ('todas_urls', 'Todas_URLs'),
            ('mixed_content', 'Mixed_Content'),
            ('titles_issues', 'Titles_Issues'),
            ('descriptions_issues', 'Descriptions_Issues')
        ]
        
        for key, sheet_name in sheet_configs:
            worksheet = workbook.add_worksheet(sheet_name)
            df = dataframes.get(key, pd.DataFrame())
            
            if df.empty:
                # Cria aba vazia com header informativo
                worksheet.write(0, 0, f"Nenhum dado encontrado para {sheet_name}", header_format)
                worksheet.set_column(0, 0, 50)
            else:
                # Escreve headers
                for col_num, column in enumerate(df.columns):
                    worksheet.write(0, col_num, column, header_format)
                
                # Escreve dados
                for row_num, row in df.iterrows():
                    for col_num, value in enumerate(row):
                        # Converte valores para tipos suportados
                        safe_value = self._convert_value_for_excel(value)
                        
                        # Escolhe formato
                        if isinstance(safe_value, (int, float)) and not isinstance(safe_value, bool):
                            cell_format = number_format
                        else:
                            cell_format = normal_format
                        
                        worksheet.write(row_num + 1, col_num, safe_value, cell_format)
                
                # Configura larguras de coluna
                self._set_column_widths(worksheet, df)
                
                # Aplica filtros
                if len(df) > 0:
                    worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
                
                # Congela primeira linha
                worksheet.freeze_panes(1, 0)
        
        workbook.close()
        return filepath
    
    def _convert_value_for_excel(self, value):
        """🔧 Converte valores para formatos suportados pelo xlsxwriter"""
        
        if value is None or (isinstance(value, float) and str(value) == 'nan'):
            return ''
        
        if isinstance(value, list):
            if not value:
                return ''
            str_items = []
            for item in value:
                if isinstance(item, dict):
                    if 'url' in item:
                        str_items.append(item['url'])
                    else:
                        str_items.append(str(item))
                else:
                    str_items.append(str(item))
            return ' | '.join(str_items)
        
        if isinstance(value, dict):
            if 'url' in value:
                return value['url']
            else:
                return str(value)
        
        if isinstance(value, bool):
            return 'SIM' if value else 'NÃO'
        
        if isinstance(value, str) and len(value) > 32767:
            return value[:32760] + '...'
        
        return value
    
    def _set_column_widths(self, worksheet, df):
        """📏 Define larguras das colunas"""
        
        for col_num, column in enumerate(df.columns):
            if 'URL' in column:
                worksheet.set_column(col_num, col_num, 60)
            elif column in ['Title', 'Meta_Description', 'Description_Completa']:
                worksheet.set_column(col_num, col_num, 50)
            elif column in ['Critical_Issues', 'Warnings', 'Outras_URLs']:
                worksheet.set_column(col_num, col_num, 40)
            elif 'Length' in column or 'Count' in column or 'Score' in column:
                worksheet.set_column(col_num, col_num, 12)
            else:
                worksheet.set_column(col_num, col_num, 20)


def create_report_generator(generator_type='default', config=None):
    """🏭 Factory function para criar gerador de relatório"""
    return ExcelReportGenerator(config)


def test_excel_generator():
    """🧪 Teste do gerador Excel simplificado"""
    print("🧪 Testando ExcelReportGenerator SIMPLIFICADO...")
    
    # Dados de teste
    test_results = [
        {
            'url': 'https://test.com/page1',
            'Status_Code': 200,
            'Response_Time_ms': 150,
            'title': 'Página de Teste',
            'title_length': 15,
            'title_status': 'OK',
            'title_duplicado': False,
            'meta_description': 'Esta é uma descrição de teste.',
            'description_length': 30,
            'description_status': 'Muito curta',
            'description_duplicada': False,
            'h1_count': 1,
            'h1_text': 'Título H1',
            'h1_ausente': False,
            'metatags_score': 85,
            'has_mixed_content': False,
            'mixed_content_resources': []
        },
        {
            'url': 'https://test.com/page2',
            'Status_Code': 404,
            'title': '',  # Title ausente
            'title_status': 'Ausente',
            'meta_description': '',  # Description ausente
            'description_status': 'Ausente',
            'h1_ausente': True,
            'metatags_score': 25,
            'has_mixed_content': True,
            'mixed_content_resources': [
                {'type': 'script', 'url': 'http://insecure.com/script.js'}
            ]
        },
        {
            'url': 'https://test.com/page3',
            'Status_Code': 200,
            'title': 'Página de Teste',  # Title duplicado
            'title_duplicado': True,
            'meta_description': 'Esta é uma descrição de teste.',  # Description duplicada
            'description_duplicada': True,
            'metatags_score': 70
        }
    ]
    
    # Cria gerador
    generator = ExcelReportGenerator({'folder': 'test_output'})
    
    # Gera relatório
    filepath, main_df = generator.generate_complete_report(
        results=test_results,
        filename_prefix="TEST_SIMPLIFIED"
    )
    
    if filepath:
        print(f"✅ Relatório simplificado gerado: {filepath}")
        print(f"📊 4 abas criadas:")
        print(f"   1. Todas_URLs: {len(main_df)} URLs")
        print(f"   2. Mixed_Content: criada (pode estar vazia)")
        print(f"   3. Titles_Issues: criada")
        print(f"   4. Descriptions_Issues: criada")
        
        print(f"\n✅ Teste concluído!")
        print(f"   ✅ Status + Metatags combinados na primeira aba")
        print(f"   ✅ Mixed content separado")
        print(f"   ✅ Titles duplicados/ausentes separados")
        print(f"   ✅ Descriptions duplicadas/ausentes separadas")
    else:
        print("❌ Erro na geração do relatório de teste")


if __name__ == "__main__":
    test_excel_generator()