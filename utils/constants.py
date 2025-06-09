# utils/constants.py - Constantes do projeto (CORRIGIDO)

# ========================
# 📋 MENSAGENS DO SISTEMA
# ========================

# Mensagens de início
MSG_CRAWLER_START = "🎯 Crawler ULTRA CORRIGIDO iniciado para: {domain}"
MSG_ANALYSIS_START = "🏷️ Analisador ULTRA de metatags CORRIGIDO iniciado para: {domain}"
MSG_PROCESSING_BATCH = "🔄 Processando {batch_size} URLs... (total: {current}/{max_urls})"

# Mensagens de conclusão
MSG_CRAWL_COMPLETE = "✅ Crawl ULTRA concluído: {total_urls} URLs encontradas"
MSG_ANALYSIS_COMPLETE = "✅ Análise ultra completa CORRIGIDA concluída: {total_urls} URLs"
MSG_REPORT_GENERATED = "✅ RELATÓRIO METATAGS ULTRA CORRIGIDO gerado: {filepath}"

# Mensagens de erro
MSG_NO_RESULTS = "❌ Nenhum resultado para gerar relatório!"
MSG_NO_URLS = "❌ Nenhuma URL encontrada!"
MSG_ERROR_PROCESSING = "⚠️ Erro processando {url}: {error}"
MSG_ERROR_EXCEL = "❌ ERRO ao gerar Excel: {error}"

# ========================
# 🎯 MENSAGENS DE CORREÇÕES
# ========================

MSG_CORRECTIONS_IMPLEMENTED = """🔧 CORREÇÕES IMPLEMENTADAS:
   ✅ Headings vazios IGNORADOS na análise hierárquica
   ✅ Detecção EXPANDIDA de headings ocultos (cores invisíveis)
   ✅ Consolidação em ABA ÚNICA para headings problemáticos
   ✅ Gravidade DIFERENCIADA (H1s = crítico, outros = médio)
   ✅ Sequências SEPARADAS (completa vs. válida)"""

MSG_IMPROVEMENTS = """💡 PRINCIPAIS MELHORIAS:
   🎯 Headings vazios/ocultos NÃO afetam análise hierárquica
   🔍 Detecção expandida: cores invisíveis identificadas
   📊 Consolidação: uma aba para todos os problemas
   ⚖️ Gravidade: H1s problemáticos = crítico"""

MSG_NEW_CONSOLIDATED_TAB = """🆕 NOVA ABA CONSOLIDADA:
   📋 'Headings_Problematicos' - Todos os problemas em uma aba
   🎯 Gravidade diferenciada (Crítico/Médio)
   🔍 Motivos consolidados (Vazio/Oculto)
   📊 Sequências separadas (Completa vs. Válida)"""

# ========================
# 🏷️ LABELS E TEXTOS
# ========================

# Status de metatags
STATUS_OK = "OK"
STATUS_ABSENT = "Ausente"
STATUS_TOO_SHORT = "Muito curto"
STATUS_TOO_LONG = "Muito longo"

# Gravidade de problemas
GRAVITY_CRITICAL = "CRÍTICO"
GRAVITY_MEDIUM = "MÉDIO"
GRAVITY_LOW = "BAIXO"

# Tipos de problemas
PROBLEM_TYPE_EMPTY = "Vazio"
PROBLEM_TYPE_HIDDEN = "Oculto"
PROBLEM_TYPE_DUPLICATE = "Duplicado"
PROBLEM_TYPE_HIERARCHY = "Hierarquia"

# ========================
# 📊 NOMES DE ABAS DO EXCEL
# ========================

SHEET_NAMES = {
    'complete': 'Complete',
    'critical': 'Criticos',
    'headings_problematic': 'Headings_Problematicos',
    'hierarchy': 'Hierarquia',
    'title_duplicates': 'Title_Duplicados',
    'description_duplicates': 'Desc_Duplicadas',
    'score_ranking': 'Score_Ranking',
    'summary': 'Resumo'
}

# Nomes com emojis para relatórios avançados
SHEET_NAMES_EMOJI = {
    'complete': 'Metatags_Ultra_Complete',
    'headings_problematic': '🔍_Headings_Problematicos',
    'title_duplicates': '🔄_Titles_Duplicados',
    'description_duplicates': '🔄_Descriptions_Duplicadas',
    'hierarchy_problems': '🔢_Hierarquia_Problemas',
    'empty_headings': '🕳️_Headings_Vazios',
    'hidden_headings': '👻_Headings_Ocultos',
    'critical': '🔥_CRITICOS',
    'score_ranking': '🎯_Score_Ranking',
    'summary': '📊_RESUMO_ULTRA_CORRIGIDO',
    'principal': '📊_Dados_Principais'
}

# ========================
# 🔍 PROBLEMAS DE HIERARQUIA
# ========================

# Mensagens de problemas hierárquicos
HIERARCHY_MESSAGES = {
    'no_headings': 'Nenhum heading encontrado',
    'no_valid_headings': 'Nenhum heading válido encontrado para análise hierárquica',
    'h1_absent': 'H1 ausente',
    'multiple_h1': 'Múltiplos H1 ({count})',
    'first_not_h1': 'Primeiro heading válido é {tag}, deveria ser H1',
    'hierarchy_jump': 'Salto na hierarquia válida: H{prev} → H{curr} (níveis ignorados: {missing})',
    'hierarchy_jump_simple': 'Salto de {prev_tag} para {curr_tag} (faltam: {missing_levels})'
}

# ========================
# 📋 COLUNAS DOS RELATÓRIOS
# ========================

# Colunas principais
MAIN_COLUMNS = [
    'URL', 'Status_Code', 'Response_Time_ms',
    'Title', 'Title_Length', 'Title_Status', 'Title_Duplicado',
    'Meta_Description', 'Description_Length', 'Description_Status', 'Description_Duplicada',
    'H1_Count', 'H1_Text', 'H1_Ausente', 'H1_Multiple', 'Hierarquia_Correta',
    'Headings_Problematicos_Total', 'Headings_Vazios', 'Headings_Ocultos', 'Headings_Criticos',
    'Heading_Sequence_Completa', 'Heading_Sequence_Valida',
    'Total_Problemas_Headings', 'Metatags_Score'
]

# Colunas de headings problemáticos
PROBLEMATIC_HEADINGS_COLUMNS = [
    'URL', 'Total_Problemas', 'Headings_Vazios', 'Headings_Ocultos',
    'Gravidade_Geral', 'Problemas_Detalhados', 'Motivos_Únicos',
    'H1_Count', 'Hierarquia_Correta', 'Sequencia_Completa', 'Sequencia_Valida', 'Score'
]

# Colunas de hierarquia
HIERARCHY_COLUMNS = [
    'URL', 'Problemas_Hierarquia', 'H1_Count', 'H1_Text',
    'Sequencia_Completa', 'Sequencia_Valida', 'Total_Problemas', 'Hierarquia_Correta'
]

# ========================
# 🎨 FORMATAÇÃO
# ========================

# Símbolos de status
STATUS_SYMBOLS = {
    'success': '✅',
    'warning': '⚠️',
    'error': '❌',
    'info': 'ℹ️',
    'new': '🆕',
    'fire': '🔥',
    'target': '🎯',
    'magnifier': '🔍',
    'repeat': '🔄',
    'numbers': '🔢',
    'hole': '🕳️',
    'ghost': '👻'
}

# Indicadores de qualidade
QUALITY_INDICATORS = {
    'excellent': '🟢 EXCELENTE',
    'good': '🟡 BOM',
    'critical': '🔴 CRÍTICO'
}

# ========================
# 📊 REGEX PATTERNS
# ========================

# Padrões para análise
REGEX_PATTERNS = {
    'rgb_color': r'color:\s*rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',
    'description_meta': r'^description$',
    'keywords_meta': r'^keywords$',
    'robots_meta': r'^robots$',
    'viewport_meta': r'^viewport$',
    'canonical_rel': r'^canonical$'
}

# ========================
# 🔧 CONFIGURAÇÕES DE VALIDAÇÃO
# ========================

# Limites para análise de cores RGB
RGB_LIMITS = {
    'light_threshold': 250,  # Valores acima deste são considerados claros
    'min_value': 0,
    'max_value': 255
}

# Limites de palavras
WORD_LIMITS = {
    'title_min_words': 3,
    'description_min_words': 10
}

# ========================
# 🎯 AÇÕES PRIORITÁRIAS
# ========================

PRIORITY_ACTIONS = [
    "Corrigir titles ausentes",
    "Corrigir descriptions ausentes", 
    "Adicionar H1 ausentes",
    "🆕 Corrigir headings problemáticos",
    "Corrigir hierarquia headings",
    "Eliminar duplicados",
    "Revisar headings críticos",
    "Otimizar scores baixos"
]

# ========================
# 🏥 HEALTH INDICATORS
# ========================

HEALTH_THRESHOLDS = {
    'excellent': {
        'duplicates_percentage': 0,
        'absent_percentage': 0,
        'score_min': 80
    },
    'good': {
        'duplicates_percentage': 0.1,  # 10%
        'absent_percentage': 0.1,      # 10%
        'score_min': 60
    }
    # Acima disso é considerado CRÍTICO
}

# ========================
# 📝 TEMPLATES DE TEXTO
# ========================

TEMPLATES = {
    'heading_problem_description': '{tag} na posição {position}',
    'heading_problem_with_reasons': '{tag} na posição {position} ({reasons})',
    'heading_empty_at_position': '{tag} vazio na posição {position}',
    'heading_hidden_description': '{tag} oculto: "{text}"',
    'duplicate_found': '{type} duplicado',
    'score_with_percentage': "{score:.1f}/100",
    'percentage': "{value:.1f}%"
}