# reports/excel_generator.py - Gerador Excel CORRIGIDO (resolve bug do Excel vazio)

import pandas as pd
import xlsxwriter
from datetime import datetime
import os
from utils.constants import MSG_REPORT_GENERATED, MSG_NO_RESULTS, MSG_ERROR_EXCEL


class ExcelReportGenerator:
    """🔥 Gerador Excel CORRIGIDO - resolve bug do Excel vazio"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.output_folder = self.config.get("folder", "output")
        os.makedirs(self.output_folder, exist_ok=True)

    def generate_complete_report(self, results, filename_prefix="SEO_ANALYSIS"):
        """🔥 MÉTODO PRINCIPAL CORRIGIDO - resolve bug do Excel vazio"""
        if not results:
            print(MSG_NO_RESULTS)
            return None, None

        print(f"🔧 Iniciando geração de relatório com {len(results)} resultados...")

        # 🔥 CORREÇÃO 1: Converte resultados para DataFrame ANTES do ExcelWriter
        try:
            df_main = pd.DataFrame(results)
            print(f"✅ DataFrame criado com {len(df_main)} linhas e {len(df_main.columns)} colunas")
            
            # Debug: mostra primeiras colunas
            print(f"📊 Primeiras colunas: {list(df_main.columns[:5])}")
            
            if df_main.empty:
                print("❌ DataFrame está vazio após conversão!")
                return None, None
                
        except Exception as e:
            print(f"❌ Erro criando DataFrame: {e}")
            return None, None

        # 🔥 CORREÇÃO 2: Nome de arquivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.xlsx"
        filepath = os.path.join(self.output_folder, filename)
        
        print(f"📁 Gerando arquivo: {filepath}")

        # 🔥 CORREÇÃO 3: Usa try/except robusto + close explícito
        writer = None
        try:
            # Cria writer com configurações explícitas
            writer = pd.ExcelWriter(
                filepath, 
                engine="xlsxwriter",
            )
            
            print(f"✅ ExcelWriter criado com sucesso")

            # 🔥 CORREÇÃO 4: Escreve aba principal PRIMEIRO
            df_main.to_excel(writer, sheet_name="📊_ANALISE_COMPLETA", index=False)
            print(f"✅ Aba principal escrita: {len(df_main)} linhas")
            
            # Ajusta largura das colunas da aba principal
            self._ajustar_colunas(writer, df_main, "📊_ANALISE_COMPLETA")
            
            # 🔥 CORREÇÃO 5: Gera abas adicionais somente se tiver dados
            abas_criadas = 1  # Conta aba principal
            
            try:
                # Aba de headings problemáticos (PRINCIPAL - DETALHADA)
                aba_headings = self._aba_headings_problematicos(df_main)
                if not aba_headings.empty:
                    aba_headings.to_excel(writer, sheet_name="🔍_Headings_Problematicos", index=False)
                    self._ajustar_colunas(writer, aba_headings, "🔍_Headings_Problematicos")
                    abas_criadas += 1
                    print(f"✅ Aba headings problemáticos: {len(aba_headings)} linhas")
                
                # Aba de headings vazios (DETALHADA POR TAG)
                aba_vazios = self._aba_headings_vazios(df_main)
                if not aba_vazios.empty:
                    aba_vazios.to_excel(writer, sheet_name="🕳️_Headings_Vazios", index=False)
                    self._ajustar_colunas(writer, aba_vazios, "🕳️_Headings_Vazios")
                    abas_criadas += 1
                    print(f"✅ Aba headings vazios: {len(aba_vazios)} linhas")
                
                # Aba de sequência de headings (COMPLETA vs VÁLIDA)
                aba_sequencia = self._aba_sequencia_headings(df_main)
                if not aba_sequencia.empty:
                    aba_sequencia.to_excel(writer, sheet_name="📏_Sequencia_Headings", index=False)
                    self._ajustar_colunas(writer, aba_sequencia, "📏_Sequencia_Headings")
                    abas_criadas += 1
                    print(f"✅ Aba sequência headings: {len(aba_sequencia)} linhas")
                
                # Aba de gravidade de headings (CRÍTICO vs MÉDIO)
                aba_gravidade = self._aba_gravidade_headings(df_main)
                if not aba_gravidade.empty:
                    aba_gravidade.to_excel(writer, sheet_name="⚖️_Gravidade_Headings", index=False)
                    self._ajustar_colunas(writer, aba_gravidade, "⚖️_Gravidade_Headings")
                    self._formatar_score(writer, aba_gravidade, "⚖️_Gravidade_Headings")  # Aplica formatação especial
                    abas_criadas += 1
                    print(f"✅ Aba gravidade headings: {len(aba_gravidade)} linhas")
                
                # Aplica formatação especial às abas principais
                self._formatar_score(writer, aba_headings, "🔍_Headings_Problematicos")
                if not aba_vazios.empty:
                    self._formatar_score(writer, aba_vazios, "🕳️_Headings_Vazios")
                if not aba_sequencia.empty:
                    self._formatar_score(writer, aba_sequencia, "📏_Sequencia_Headings")
                
                # Aba de títulos duplicados  
                aba_titles = self._aba_titles_duplicados(df_main)
                if not aba_titles.empty:
                    aba_titles.to_excel(writer, sheet_name="🔄_Titles_Duplicados", index=False)
                    self._ajustar_colunas(writer, aba_titles, "🔄_Titles_Duplicados")
                    abas_criadas += 1
                    print(f"✅ Aba títulos duplicados: {len(aba_titles)} linhas")
                
                # Aba de descriptions duplicadas
                aba_desc = self._aba_descriptions_duplicadas(df_main)
                if not aba_desc.empty:
                    aba_desc.to_excel(writer, sheet_name="🔄_Descriptions_Duplicadas", index=False)
                    self._ajustar_colunas(writer, aba_desc, "🔄_Descriptions_Duplicadas")
                    abas_criadas += 1
                    print(f"✅ Aba descriptions duplicadas: {len(aba_desc)} linhas")
                
                # Aba de hierarquia
                aba_hierarquia = self._aba_hierarquia(df_main)
                if not aba_hierarquia.empty:
                    aba_hierarquia.to_excel(writer, sheet_name="🔢_Hierarquia_Problemas", index=False)
                    self._ajustar_colunas(writer, aba_hierarquia, "🔢_Hierarquia_Problemas")
                    abas_criadas += 1
                    print(f"✅ Aba hierarquia: {len(aba_hierarquia)} linhas")
                
                # Aba de score ranking
                aba_score = self._aba_score(df_main)
                if not aba_score.empty:
                    aba_score.to_excel(writer, sheet_name="🎯_Score_Ranking", index=False)
                    self._ajustar_colunas(writer, aba_score, "🎯_Score_Ranking")
                    self._formatar_score(writer, aba_score, "🎯_Score_Ranking")
                    abas_criadas += 1
                    print(f"✅ Aba score ranking: {len(aba_score)} linhas")
                
                # Aba resumo executivo
                aba_resumo = self._aba_resumo(df_main)
                if not aba_resumo.empty:
                    aba_resumo.to_excel(writer, sheet_name="📈_RESUMO_EXECUTIVO", index=False)
                    self._ajustar_colunas(writer, aba_resumo, "📈_RESUMO_EXECUTIVO")
                    abas_criadas += 1
                    print(f"✅ Aba resumo: {len(aba_resumo)} linhas")
                
                # Aba mixed content (se disponível)
                if 'mixed_content_resources' in df_main.columns or 'Has_Mixed_Content' in df_main.columns:
                    aba_mixed = self._aba_mixed(df_main)
                    aba_mixed.to_excel(writer, sheet_name="🔒_Mixed_Content", index=False)
                    self._ajustar_colunas(writer, aba_mixed, "🔒_Mixed_Content")
                    abas_criadas += 1
                    print(f"✅ Aba mixed content: {len(aba_mixed)} linhas")
                
            except Exception as e:
                print(f"⚠️ Erro gerando abas adicionais: {e}")
                print(f"📊 Continuando com {abas_criadas} aba(s) criada(s)")

            # 🔥 CORREÇÃO 6: Close explícito e controle de erro
            print(f"💾 Salvando arquivo com {abas_criadas} abas...")
            writer.close()
            writer = None  # Evita close duplo
            
            print(f"✅ Arquivo Excel salvo com sucesso: {filepath}")
            print(MSG_REPORT_GENERATED.format(filepath=filepath))
            
            return filepath, df_main

        except Exception as e:
            print(f"❌ {MSG_ERROR_EXCEL.format(error=str(e))}")
            
            # Cleanup em caso de erro
            if writer:
                try:
                    writer.close()
                except:
                    pass
            
            # Remove arquivo corrompido se existir
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"🗑️ Arquivo corrompido removido: {filepath}")
                except:
                    pass
            
            return None, None

    def _ajustar_colunas(self, writer, df, aba_nome):
        """🔧 Ajusta largura das colunas automaticamente"""
        try:
            worksheet = writer.sheets[aba_nome]
            
            for i, col in enumerate(df.columns):
                # Calcula largura baseada no conteúdo
                max_len = max(
                    df[col].astype(str).map(len).max() if not df[col].empty else 0,
                    len(str(col))
                )
                
                # Aplica largura entre 10 e 80 caracteres
                largura = min(max(max_len + 2, 10), 80)
                worksheet.set_column(i, i, largura)
                
        except Exception as e:
            print(f"⚠️ Erro ajustando colunas da aba {aba_nome}: {e}")

    def _formatar_score(self, writer, df, aba_nome):
        """🎨 Aplica formatação condicional ao score COM EMOJIS E ESTILO VISUAL"""
        try:
            worksheet = writer.sheets[aba_nome]
            workbook = writer.book
            
            # Encontra colunas de score (incluindo com emoji)
            score_columns = []
            for i, col in enumerate(df.columns):
                col_lower = str(col).lower()
                if any(score_word in col_lower for score_word in ['score', 'pontuação', 'nota', '🎯']):
                    score_columns.append(i)
            
            if score_columns and len(df) > 0:
                # 🎨 FORMATO ESPECIAL com emoji visual
                score_format = workbook.add_format({
                    'num_format': '🎯 0.0',  # Emoji + número
                    'align': 'center',
                    'bold': True,
                    'font_size': 11
                })
                
                # 🎨 FORMATOS CONDICIONAIS por faixas
                high_score_format = workbook.add_format({
                    'bg_color': '#C6EFCE',  # Verde claro
                    'font_color': '#006100', # Verde escuro
                    'num_format': '🎯 0.0',
                    'align': 'center',
                    'bold': True
                })
                
                medium_score_format = workbook.add_format({
                    'bg_color': '#FFEB9C',  # Amarelo claro
                    'font_color': '#9C6500', # Amarelo escuro
                    'num_format': '🎯 0.0',
                    'align': 'center',
                    'bold': True
                })
                
                low_score_format = workbook.add_format({
                    'bg_color': '#FFC7CE',  # Vermelho claro
                    'font_color': '#9C0006', # Vermelho escuro
                    'num_format': '🎯 0.0',
                    'align': 'center',
                    'bold': True
                })
                
                # Aplica formato às colunas de score
                for col_idx in score_columns:
                    worksheet.set_column(col_idx, col_idx, 15, score_format)  # Largura fixa para scores
                    
                    # 🎨 FORMATAÇÃO CONDICIONAL AVANÇADA
                    # Scores altos (80+) = Verde
                    worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                        'type': 'cell',
                        'criteria': '>=',
                        'value': 80,
                        'format': high_score_format
                    })
                    
                    # Scores médios (50-79) = Amarelo
                    worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                        'type': 'cell',
                        'criteria': 'between',
                        'minimum': 50,
                        'maximum': 79,
                        'format': medium_score_format
                    })
                    
                    # Scores baixos (<50) = Vermelho
                    worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                        'type': 'cell',
                        'criteria': '<',
                        'value': 50,
                        'format': low_score_format
                    })
                    
                    # 🌈 GRADIENTE ADICIONAL (semáforo)
                    worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                        'type': '3_color_scale',
                        'min_color': "#F8696B",    # Vermelho (score baixo)
                        'mid_color': "#FFEB84",    # Amarelo (score médio)  
                        'max_color': "#63BE7B"     # Verde (score alto)
                    })
            
            # 🎨 FORMATAÇÃO ESPECIAL para colunas de gravidade
            gravidade_columns = []
            for i, col in enumerate(df.columns):
                col_lower = str(col).lower()
                if any(grav_word in col_lower for grav_word in ['gravidade', 'crítico', 'médio', '⚖️', '🔥']):
                    gravidade_columns.append(i)
            
            if gravidade_columns:
                # Formatos para gravidade
                critico_format = workbook.add_format({
                    'bg_color': '#FF0000',  # Vermelho
                    'font_color': '#FFFFFF', # Branco
                    'align': 'center',
                    'bold': True
                })
                
                medio_format = workbook.add_format({
                    'bg_color': '#FFA500',  # Laranja
                    'font_color': '#FFFFFF', # Branco
                    'align': 'center',
                    'bold': True
                })
                
                for col_idx in gravidade_columns:
                    # Formatação condicional para CRÍTICO
                    worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                        'type': 'text',
                        'criteria': 'containing',
                        'value': 'CRÍTICO',
                        'format': critico_format
                    })
                    
                    # Formatação condicional para MÉDIO
                    worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                        'type': 'text',
                        'criteria': 'containing',
                        'value': 'MÉDIO',
                        'format': medio_format
                    })
                    
        except Exception as e:
            print(f"⚠️ Erro formatando scores da aba {aba_nome}: {e}")

    def _aba_headings_problematicos(self, df):
        """🔍 Gera aba de headings problemáticos consolidada COM DETALHES COMPLETOS"""
        try:
            rows = []
            
            for _, row in df.iterrows():
                # Verifica se tem problemas de headings
                problemas_total = row.get('Headings_Problematicos_Total', 0)
                if problemas_total > 0:
                    
                    # 🔥 DETALHES COMPLETOS dos problemas
                    problemas_list = row.get('headings_problematicos', [])
                    detalhes_problemas = []
                    
                    if isinstance(problemas_list, list):
                        for problema in problemas_list:
                            if isinstance(problema, dict):
                                desc = problema.get('descricao', '')
                                detalhes_problemas.append(desc)
                    
                    # Se não tem lista detalhada, cria descrição básica
                    if not detalhes_problemas:
                        if row.get('Headings_Vazios', 0) > 0:
                            detalhes_problemas.append(f"{row.get('Headings_Vazios')} headings vazios")
                        if row.get('Headings_Ocultos', 0) > 0:
                            detalhes_problemas.append(f"{row.get('Headings_Ocultos')} headings ocultos")
                    
                    rows.append({
                        '🔗 URL': row.get('URL', ''),
                        'Total_Problemas': problemas_total,
                        'Vazios': row.get('Headings_Vazios', 0),
                        'Ocultos': row.get('Headings_Ocultos', 0),
                        'CRITICOS': row.get('Headings_Criticos', 0),
                        'MEDIOS': max(0, problemas_total - row.get('Headings_Criticos', 0)),
                        'Gravidade_Geral': 'CRÍTICO' if row.get('Headings_Criticos', 0) > 0 else 'MÉDIO',
                        'Detalhes': ' | '.join(detalhes_problemas) if detalhes_problemas else 'Problemas não especificados',
                        'Motivos_Únicos': self._extract_unique_motivos(problemas_list),
                        'H1_Count': row.get('H1_Count', 0),
                        'Hierarquia_OK': row.get('Hierarquia_Correta', 'SIM'),
                        'Sequencia_Completa': row.get('Heading_Sequence_Completa', ''),
                        'Sequencia_Valida': row.get('Heading_Sequence_Valida', ''),
                        '🎯 Score': row.get('Metatags_Score', 0)
                    })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            print(f"⚠️ Erro gerando aba headings problemáticos: {e}")
            return pd.DataFrame()

    def _aba_headings_vazios(self, df):
        """🕳️ Gera aba DETALHADA de headings vazios por tag e posição"""
        try:
            rows = []
            
            for _, row in df.iterrows():
                url = row.get('URL', '')
                problemas_list = row.get('headings_problematicos', [])
                
                if isinstance(problemas_list, list):
                    for problema in problemas_list:
                        if isinstance(problema, dict):
                            motivos = problema.get('motivos', [])
                            if 'Vazio' in motivos or 'vazio' in motivos:
                                rows.append({
                                    '🔗 URL': url,
                                    'Tag': problema.get('tag', '').upper(),
                                    'Posição': problema.get('posicao', problema.get('position', 0)),
                                    '⚖️ Gravidade': 'CRÍTICO' if problema.get('tag', '').upper() == 'H1' else 'MÉDIO',
                                    'Descrição': problema.get('descricao', ''),
                                    'Texto': problema.get('texto', ''),
                                    '🎯 Score_Página': row.get('Metatags_Score', 0)
                                })
                
                # Se não tem dados detalhados, usa dados básicos
                elif row.get('Headings_Vazios', 0) > 0:
                    rows.append({
                        '🔗 URL': url,
                        'Tag': 'MÚLTIPLOS',
                        'Posição': 0,
                        '⚖️ Gravidade': 'MÉDIO',
                        'Descrição': f"{row.get('Headings_Vazios')} headings vazios detectados",
                        'Texto': '',
                        '🎯 Score_Página': row.get('Metatags_Score', 0)
                    })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            print(f"⚠️ Erro gerando aba headings vazios: {e}")
            return pd.DataFrame()

    def _aba_sequencia_headings(self, df):
        """📏 Gera aba de sequência completa vs válida de headings"""
        try:
            colunas_sequencia = [
                'URL', 'Heading_Sequence_Completa', 'Heading_Sequence_Valida',
                'H1_Count', 'Headings_Problematicos_Total', 'Hierarquia_Correta',
                'Total_Problemas_Headings', 'Problemas_Hierarquia', 'Metatags_Score'
            ]
            
            # Filtra apenas colunas que existem
            colunas_existentes = [col for col in colunas_sequencia if col in df.columns]
            
            # Adiciona colunas calculadas
            df_sequencia = df[colunas_existentes].copy()
            
            # Calcula total de headings e headings válidos
            df_sequencia['Total_Headings'] = df_sequencia.get('H1_Count', 0) + df_sequencia.get('Total_Problemas_Headings', 0)
            df_sequencia['Headings_Validos'] = df_sequencia['Total_Headings'] - df_sequencia.get('Headings_Problematicos_Total', 0)
            
            return df_sequencia.rename(columns={
                'URL': '🔗 URL',
                'Heading_Sequence_Completa': 'Sequência_Completa',
                'Heading_Sequence_Valida': 'Sequência_Válida',
                'H1_Count': 'H1s',
                'Headings_Problematicos_Total': '🔍 Problemáticos',
                'Hierarquia_Correta': 'Hierarquia_OK',
                'Total_Problemas_Headings': 'Total_Problemas',
                'Problemas_Hierarquia': 'Problemas_Hierarquia',
                'Metatags_Score': '🎯 Score'
            })
            
        except Exception as e:
            print(f"⚠️ Erro gerando aba sequência headings: {e}")
            return pd.DataFrame()

    def _aba_gravidade_headings(self, df):
        """⚖️ Gera aba de gravidade diferenciada dos headings"""
        try:
            # Filtra apenas URLs que tem headings críticos ou problemáticos
            problematicos = df[
                (df.get('Headings_Criticos', 0) > 0) | 
                (df.get('Headings_Problematicos_Total', 0) > 0)
            ]
            
            if problematicos.empty:
                return pd.DataFrame()
            
            return problematicos[['URL', 'Headings_Criticos', 'Headings_Problematicos_Total', 
                               'H1_Count', 'H1_Multiple', 'Metatags_Score']].rename(columns={
                'URL': '🔗 URL',
                'Headings_Criticos': '🔥 CRÍTICOS',
                'Headings_Problematicos_Total': '⚠️ Total_Problemáticos',
                'H1_Count': 'H1s',
                'H1_Multiple': 'H1_Múltiplo',
                'Metatags_Score': '🎯 Score'
            })
            
        except Exception as e:
            print(f"⚠️ Erro gerando aba gravidade headings: {e}")
            return pd.DataFrame()

    def _extract_unique_motivos(self, problemas_list):
        """🔍 Extrai motivos únicos dos problemas"""
        try:
            motivos_set = set()
            
            if isinstance(problemas_list, list):
                for problema in problemas_list:
                    if isinstance(problema, dict):
                        motivos = problema.get('motivos', [])
                        if isinstance(motivos, list):
                            motivos_set.update(motivos)
            
            return ', '.join(sorted(motivos_set)) if motivos_set else 'Não especificado'
            
        except Exception:
            return 'Erro ao extrair motivos'

    def _aba_titles_duplicados(self, df):
        """🔄 Gera aba de títulos duplicados"""
        try:
            # Filtra URLs com títulos duplicados
            duplicados = df[df.get('Title_Duplicado', 'NÃO') == 'SIM']
            
            if duplicados.empty:
                return pd.DataFrame()
            
            return duplicados[['URL', 'Title', 'Title_Length', 'Metatags_Score']].rename(columns={
                'URL': '🔗 URL',
                'Title': '📝 Título',
                'Title_Length': 'Tamanho',
                'Metatags_Score': '🎯 Score'
            })
            
        except Exception as e:
            print(f"⚠️ Erro gerando aba títulos duplicados: {e}")
            return pd.DataFrame()

    def _aba_descriptions_duplicadas(self, df):
        """🔄 Gera aba de descriptions duplicadas"""
        try:
            # Filtra URLs com descriptions duplicadas
            duplicadas = df[df.get('Description_Duplicada', 'NÃO') == 'SIM']
            
            if duplicadas.empty:
                return pd.DataFrame()
            
            return duplicadas[['URL', 'Meta_Description', 'Description_Length', 'Metatags_Score']].rename(columns={
                'URL': '🔗 URL',
                'Meta_Description': '📄 Description',
                'Description_Length': 'Tamanho',
                'Metatags_Score': '🎯 Score'
            })
            
        except Exception as e:
            print(f"⚠️ Erro gerando aba descriptions duplicadas: {e}")
            return pd.DataFrame()

    def _aba_hierarquia(self, df):
        """🔢 Gera aba de problemas de hierarquia"""
        try:
            # Filtra URLs com problemas de hierarquia
            problemas_hierarquia = df[df.get('Hierarquia_Correta', 'SIM') == 'NÃO']
            
            if problemas_hierarquia.empty:
                return pd.DataFrame()
            
            colunas_relevantes = ['URL', 'H1_Count', 'H1_Text', 'Hierarquia_Correta', 
                                'Heading_Sequence_Completa', 'Heading_Sequence_Valida', 
                                'Total_Problemas_Headings', 'Metatags_Score']
            
            # Filtra apenas colunas que existem
            colunas_existentes = [col for col in colunas_relevantes if col in df.columns]
            
            return problemas_hierarquia[colunas_existentes].rename(columns={
                'URL': '🔗 URL',
                'H1_Count': 'H1s',
                'H1_Text': 'Texto H1',
                'Hierarquia_Correta': 'Hierarquia_OK',
                'Heading_Sequence_Completa': 'Sequência Completa',
                'Heading_Sequence_Valida': 'Sequência Válida',
                'Total_Problemas_Headings': 'Total Problemas',
                'Metatags_Score': '🎯 Score'
            })
            
        except Exception as e:
            print(f"⚠️ Erro gerando aba hierarquia: {e}")
            return pd.DataFrame()

    def _aba_score(self, df):
        """🎯 Gera aba de ranking por score"""
        try:
            if 'Metatags_Score' not in df.columns:
                return pd.DataFrame()
            
            # Ordena por score (maior primeiro)
            score_ranking = df.nlargest(100, 'Metatags_Score')  # Top 100
            
            colunas_score = ['URL', 'Metatags_Score', 'Title', 'H1_Count', 
                           'Title_Status', 'Description_Status', 'Hierarquia_Correta']
            
            # Filtra apenas colunas que existem
            colunas_existentes = [col for col in colunas_score if col in df.columns]
            
            return score_ranking[colunas_existentes].rename(columns={
                'URL': '🔗 URL',
                'Metatags_Score': '🎯 Score',
                'Title': '📝 Título',
                'H1_Count': 'H1s',
                'Title_Status': 'Status Título',
                'Description_Status': 'Status Description',
                'Hierarquia_Correta': 'Hierarquia OK'
            })
            
        except Exception as e:
            print(f"⚠️ Erro gerando aba score: {e}")
            return pd.DataFrame()

    def _aba_resumo(self, df):
        """📈 Gera aba de resumo executivo"""
        try:
            resumo_data = []
            
            # Estatísticas básicas
            resumo_data.append({'📊 Métrica': 'Total de URLs analisadas', 'Valor': len(df)})
            
            # URLs com problemas críticos
            if 'Critical_Issues' in df.columns:
                criticos = len(df[df['Critical_Issues'] != ''])
                resumo_data.append({'📊 Métrica': 'URLs com problemas críticos', 'Valor': criticos})
            
            # H1s
            if 'H1_Ausente' in df.columns:
                h1_ausentes = len(df[df['H1_Ausente'] == 'SIM'])
                resumo_data.append({'📊 Métrica': 'URLs sem H1', 'Valor': h1_ausentes})
            
            # Títulos duplicados
            if 'Title_Duplicado' in df.columns:
                titles_dup = len(df[df['Title_Duplicado'] == 'SIM'])
                resumo_data.append({'📊 Métrica': 'Títulos duplicados', 'Valor': titles_dup})
            
            # Descriptions duplicadas
            if 'Description_Duplicada' in df.columns:
                desc_dup = len(df[df['Description_Duplicada'] == 'SIM'])
                resumo_data.append({'📊 Métrica': 'Descriptions duplicadas', 'Valor': desc_dup})
            
            # Headings problemáticos
            if 'Headings_Problematicos_Total' in df.columns:
                headings_prob = len(df[df['Headings_Problematicos_Total'] > 0])
                resumo_data.append({'📊 Métrica': 'URLs com headings problemáticos', 'Valor': headings_prob})
            
            # Mixed content
            if 'Has_Mixed_Content' in df.columns:
                mixed = len(df[df['Has_Mixed_Content'] == 'SIM'])
                resumo_data.append({'📊 Métrica': 'URLs com mixed content', 'Valor': mixed})

            # Quantidade total de recursos mixed content críticos/passivos
            if 'critical_mixed_count' in df.columns:
                crit_total = int(df['critical_mixed_count'].sum())
                resumo_data.append({'📊 Métrica': 'Recursos críticos em mixed content', 'Valor': crit_total})

            if 'passive_mixed_count' in df.columns:
                pass_total = int(df['passive_mixed_count'].sum())
                resumo_data.append({'📊 Métrica': 'Recursos passivos em mixed content', 'Valor': pass_total})

            # Distribuição de níveis de risco, se disponível
            if 'risk_level' in df.columns:
                for level, count in df['risk_level'].value_counts().items():
                    resumo_data.append({'📊 Métrica': f'URLs risco {level}', 'Valor': int(count)})
            
            # Score médio
            if 'Metatags_Score' in df.columns:
                score_medio = df['Metatags_Score'].mean()
                resumo_data.append({'📊 Métrica': 'Score médio geral', 'Valor': f'{score_medio:.1f}/100'})
            
            return pd.DataFrame(resumo_data)
            
        except Exception as e:
            print(f"⚠️ Erro gerando aba resumo: {e}")
            return pd.DataFrame()

    def _aba_mixed(self, df):
        """🔒 Gera aba de mixed content"""
        try:
            # Filtra URLs com mixed content
            if 'Has_Mixed_Content' in df.columns:
                mixed_urls = df[df['Has_Mixed_Content'] == 'SIM']
            else:
                mixed_urls = pd.DataFrame()
            
            if mixed_urls.empty:
                return pd.DataFrame(columns=[
                    '🔗 URL',
                    'Tem Mixed Content',
                    'Quantidade',
                    'Críticos',
                    'Passivos',
                    'Nível de Risco',
                    '🎯 Score'
                ])
            
            colunas_mixed = [
                'URL',
                'Has_Mixed_Content',
                'Mixed_Content_Count',
                'critical_mixed_count',
                'passive_mixed_count',
                'risk_level',
                'Metatags_Score'
            ]
            colunas_existentes = [col for col in colunas_mixed if col in df.columns]
            
            return mixed_urls[colunas_existentes].rename(columns={
                'URL': '🔗 URL',
                'Has_Mixed_Content': 'Tem Mixed Content',
                'Mixed_Content_Count': 'Quantidade',
                'critical_mixed_count': 'Críticos',
                'passive_mixed_count': 'Passivos',
                'risk_level': 'Nível de Risco',
                'Metatags_Score': '🎯 Score'
            })
            
        except Exception as e:
            print(f"⚠️ Erro gerando aba mixed content: {e}")
            return pd.DataFrame()


def create_report_generator(generator_type='default', config=None):
    """🏭 Factory function para criar gerador de relatórios"""
    return ExcelReportGenerator(config)


def test_excel_generator():
    """🧪 Teste do gerador Excel corrigido"""
    print("🧪 Testando ExcelReportGenerator CORRIGIDO...")
    
    # Dados de teste que simula o resultado real
    test_results = []
    
    for i in range(5):
        test_results.append({
            'URL': f'https://test.com/page-{i+1}',
            'Title': f'Título da Página {i+1}',
            'Title_Length': 25 + i,
            'Title_Status': 'OK' if i % 2 == 0 else 'Muito curto',
            'Title_Duplicado': 'SIM' if i == 1 else 'NÃO',
            'Meta_Description': f'Description da página {i+1} com conteúdo relevante',
            'Description_Length': 120 + i*10,
            'Description_Status': 'OK',
            'Description_Duplicada': 'NÃO',
            'H1_Count': 1,
            'H1_Text': f'H1 Principal {i+1}',
            'H1_Ausente': 'NÃO',
            'H1_Multiple': 'NÃO',
            'Hierarquia_Correta': 'SIM' if i % 3 != 0 else 'NÃO',
            'Headings_Problematicos_Total': i,
            'Headings_Vazios': i // 2,
            'Headings_Ocultos': i // 3,
            'Headings_Criticos': 1 if i == 2 else 0,
            'Heading_Sequence_Completa': f'H1:Title → H2:Subtitle → H3:Section',
            'Heading_Sequence_Valida': f'H1:Title → H2:Subtitle',
            'Total_Problemas_Headings': i,
            'Metatags_Score': 75.5 + i*5,
            'Critical_Issues': 'H1 problemático' if i == 2 else '',
            'Warnings': f'Warning {i}' if i > 0 else '',
            'Has_Mixed_Content': 'SIM' if i == 3 else 'NÃO',
            'Mixed_Content_Count': 2 if i == 3 else 0,
            'Status_Code': 200,
            'Response_Time_ms': 150 + i*50
        })
    
    # Testa geração
    generator = ExcelReportGenerator({'folder': 'output'})
    
    filepath, df = generator.generate_complete_report(
        results=test_results,
        filename_prefix="TESTE_EXCEL_CORRIGIDO"
    )
    
    if filepath:
        print(f"✅ Teste SUCESSO!")
        print(f"📁 Arquivo gerado: {filepath}")
        print(f"📊 DataFrame: {len(df)} linhas")
        print(f"🔥 CORREÇÃO APLICADA: Excel não ficará mais vazio!")
    else:
        print(f"❌ Teste FALHOU!")
    
    return filepath, df


if __name__ == "__main__":
    test_excel_generator()