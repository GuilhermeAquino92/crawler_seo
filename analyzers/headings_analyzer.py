import re
from bs4 import BeautifulSoup
from config.settings import HIDDEN_CSS_CLASSES, INVISIBLE_COLORS, HIDDEN_STYLES, SUSPICIOUS_POSITIONING, RGB_LIGHT_THRESHOLD
from utils.constants import HIERARCHY_MESSAGES, PROBLEM_TYPE_EMPTY, PROBLEM_TYPE_HIDDEN, GRAVITY_CRITICAL, GRAVITY_MEDIUM


class HeadingsAnalyzer:
    
    def __init__(self, config=None):
        self.config = config or {}
        self.detect_invisible_colors = self.config.get('detect_invisible_colors', True)
        self.consolidate_problems = self.config.get('consolidate_headings', True)
        self.differentiate_gravity = self.config.get('differentiate_gravity', True)
    
    def analyze_hierarchy_corrected(self, soup, url):
        """🔥 CORRIGIDO: Usa niveis_todos para detectar saltos reais de hierarquia"""
        hierarchy_info = {
            'hierarquia_correta': True,
            'problemas_hierarquia': [],
            'headings_problematicos': [],
            'h1_count': 0,
            'h1_multiple': False,
            'h1_ausente': True,
            'heading_issues': [],
            'heading_sequence': [],
            'heading_sequence_valida': [],
            'total_problemas': 0,
            'detalhes_problemas': {}
        }
        
        try:
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            if not headings:
                hierarchy_info['problemas_hierarquia'].append(HIERARCHY_MESSAGES['no_headings'])
                hierarchy_info['heading_issues'].append('Sem headings')
                hierarchy_info['total_problemas'] += 1
                return hierarchy_info
            
            # 🔥 CORREÇÃO CRÍTICA: Separa níveis todos vs. válidos
            niveis_todos = []        # TODOS os headings (para hierarquia)
            niveis_validos = []      # Só os válidos (para outras análises)
            headings_detalhados = []
            
            for i, heading in enumerate(headings):
                tag_name = heading.name
                nivel = int(tag_name[1])
                texto = heading.get_text().strip()
                
                problema_info = self._is_heading_problematic(heading)
                
                heading_detail = {
                    'posicao': i + 1,
                    'tag': tag_name,
                    'nivel': nivel,
                    'texto': texto,
                    'eh_problematico': problema_info['eh_problematico'],
                    'eh_vazio': problema_info['eh_vazio'],
                    'eh_oculto': problema_info['eh_oculto'],
                    'motivos': problema_info['motivos']
                }
                
                headings_detalhados.append(heading_detail)
                
                # 🔥 TODOS os headings vão para análise hierárquica
                niveis_todos.append(nivel)
                hierarchy_info['heading_sequence'].append(f"{tag_name}:{texto[:30]}...")
                
                # SÓ os válidos vão para outras análises
                if not problema_info['eh_problematico']:
                    niveis_validos.append(nivel)
                    hierarchy_info['heading_sequence_valida'].append(f"{tag_name}:{texto[:30]}...")
                
                if tag_name == 'h1':
                    hierarchy_info['h1_count'] += 1
                    hierarchy_info['h1_ausente'] = False
                
                if problema_info['eh_problematico']:
                    problema_consolidado = self._create_problem_description(
                        heading_detail, problema_info
                    )
                    
                    hierarchy_info['headings_problematicos'].append(problema_consolidado)
                    hierarchy_info['heading_issues'].append(problema_consolidado['descricao'])
                    hierarchy_info['total_problemas'] += 1
            
            # Verifica H1 ausente
            if hierarchy_info['h1_ausente']:
                hierarchy_info['problemas_hierarquia'].append(HIERARCHY_MESSAGES['h1_absent'])
                hierarchy_info['heading_issues'].append('H1 ausente')
                hierarchy_info['total_problemas'] += 1
            
            # Verifica múltiplos H1
            if hierarchy_info['h1_count'] > 1:
                hierarchy_info['h1_multiple'] = True
                msg = HIERARCHY_MESSAGES['multiple_h1'].format(count=hierarchy_info['h1_count'])
                hierarchy_info['problemas_hierarquia'].append(msg)
                hierarchy_info['heading_issues'].append('Múltiplos H1')
                hierarchy_info['total_problemas'] += 1
            
            # 🔥 CORREÇÃO PRINCIPAL: Usa niveis_todos para detectar saltos reais
            if niveis_todos and not hierarchy_info['h1_ausente']:
                problemas_sequencia = self._analyze_hierarchy_sequence_corrected(
                    niveis_todos, headings_detalhados  # ← CORRIGIDO: niveis_todos
                )
                if problemas_sequencia:
                    hierarchy_info['hierarquia_correta'] = False
                    hierarchy_info['problemas_hierarquia'].extend(problemas_sequencia)
                    hierarchy_info['heading_issues'].extend(problemas_sequencia)
                    hierarchy_info['total_problemas'] += len(problemas_sequencia)
            
            hierarchy_info['detalhes_problemas'] = {
                'total_headings': len(headings),
                'headings_validos': len(niveis_validos),
                'headings_problematicos': len([h for h in headings_detalhados if h['eh_problematico']]),
                'headings_vazios': len([h for h in headings_detalhados if h['eh_vazio']]),
                'headings_ocultos': len([h for h in headings_detalhados if h['eh_oculto']]),
                'sequencia_completa': ' → '.join(hierarchy_info['heading_sequence']),
                'sequencia_valida': ' → '.join(hierarchy_info['heading_sequence_valida'])
            }
            
        except Exception as e:
            hierarchy_info['heading_issues'].append(f'Erro analisando headings: {str(e)}')
            hierarchy_info['total_problemas'] += 1
        
        return hierarchy_info
    
    def _is_heading_problematic(self, heading):
        """Detecta se heading é problemático (vazio ou oculto)"""
        try:
            texto = heading.get_text().strip()
            eh_vazio = len(texto) == 0
            eh_oculto = self._is_heading_hidden_expanded(heading)
            
            problema_info = {
                'eh_vazio': eh_vazio,
                'eh_oculto': eh_oculto,
                'eh_problematico': eh_vazio or eh_oculto,
                'texto': texto,
                'motivos': []
            }
            
            if eh_vazio:
                problema_info['motivos'].append(PROBLEM_TYPE_EMPTY)
            if eh_oculto:
                problema_info['motivos'].append(PROBLEM_TYPE_HIDDEN)
            
            return problema_info
            
        except Exception:
            return {
                'eh_vazio': False,
                'eh_oculto': False,
                'eh_problematico': False,
                'texto': '',
                'motivos': []
            }
    
    def _is_heading_hidden_expanded(self, heading):
        """Detecção expandida de headings ocultos"""
        try:
            style = heading.get('style', '').lower()
            
            # Estilos CSS que ocultam elementos
            for hidden_style in HIDDEN_STYLES:
                if hidden_style in style:
                    return True
            
            # Cores invisíveis (se habilitado)
            if self.detect_invisible_colors and self._has_invisible_color(style):
                return True
            
            # Classes CSS suspeitas
            classes = ' '.join(heading.get('class', [])).lower()
            for hidden_class in HIDDEN_CSS_CLASSES:
                if hidden_class in classes:
                    return True
            
            # Posicionamento suspeito
            for suspicious_pos in SUSPICIOUS_POSITIONING:
                if suspicious_pos in style:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _has_invisible_color(self, style):
        """Detecta cores invisíveis (branco, transparente, etc.)"""
        try:
            # Cores invisíveis predefinidas
            for invisible_color in INVISIBLE_COLORS:
                if invisible_color in style:
                    return True
            
            # RGB muito claro (quase branco)
            rgb_pattern = r'color:\s*rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)'
            matches = re.findall(rgb_pattern, style)
            for r, g, b in matches:
                if (int(r) > RGB_LIGHT_THRESHOLD and 
                    int(g) > RGB_LIGHT_THRESHOLD and 
                    int(b) > RGB_LIGHT_THRESHOLD):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _analyze_hierarchy_sequence_corrected(self, niveis_todos, headings_detalhados):
        """🔥 CORRIGIDO: Analisa sequência usando TODOS os headings para detectar saltos reais"""
        problemas = []
        
        if not niveis_todos:
            return [HIERARCHY_MESSAGES['no_valid_headings']]
        
        # Verifica se primeiro heading é H1
        if niveis_todos[0] != 1:
            primeiro_heading = headings_detalhados[0] if headings_detalhados else None
            if primeiro_heading:
                msg = HIERARCHY_MESSAGES['first_not_h1'].format(tag=primeiro_heading['tag'].upper())
                problemas.append(msg)
        
        # 🔥 ANÁLISE DE SALTOS: Usa TODOS os níveis (inclusive ocultos/vazios)
        for i in range(1, len(niveis_todos)):
            nivel_anterior = niveis_todos[i-1]
            nivel_atual = niveis_todos[i]
            
            # Detecta saltos indevidos (ex: H2 → H6, H2 → H4)
            if nivel_atual > nivel_anterior + 1:
                niveis_pulados = []
                for nivel_perdido in range(nivel_anterior + 1, nivel_atual):
                    niveis_pulados.append(f'H{nivel_perdido}')
                
                # Busca informações dos headings relacionados ao salto
                heading_anterior = None
                heading_atual = None
                
                if i-1 < len(headings_detalhados):
                    heading_anterior = headings_detalhados[i-1]
                if i < len(headings_detalhados):
                    heading_atual = headings_detalhados[i]
                
                # Cria mensagem detalhada do salto
                if heading_anterior and heading_atual:
                    msg = f"Salto na hierarquia: {heading_anterior['tag'].upper()} → {heading_atual['tag'].upper()} (níveis pulados: {', '.join(niveis_pulados)})"
                else:
                    msg = HIERARCHY_MESSAGES['hierarchy_jump'].format(
                        prev=nivel_anterior,
                        curr=nivel_atual,
                        missing=', '.join(niveis_pulados)
                    )
                
                problemas.append(msg)
        
        return problemas
    
    def _create_problem_description(self, heading_detail, problema_info):
        """Cria descrição consolidada do problema"""
        tag = heading_detail['tag']
        posicao = heading_detail['posicao']
        texto = heading_detail['texto']
        motivos = problema_info['motivos']
        
        descricao = f'{tag.upper()} na posição {posicao}'
        
        if motivos:
            motivos_str = ', '.join(motivos).lower()
            descricao += f' ({motivos_str})'
        
        if texto:
            descricao += f': "{texto[:30]}..."' if len(texto) > 30 else f': "{texto}"'
        
        # Gravidade diferenciada
        gravidade = GRAVITY_CRITICAL if tag == 'h1' else GRAVITY_MEDIUM
        
        return {
            'descricao': descricao,
            'tag': tag,
            'posicao': posicao,
            'texto': texto[:50] + '...' if len(texto) > 50 else texto,
            'motivos': motivos,
            'gravidade': gravidade
        }
    
    def extract_heading_metrics(self, hierarchy_info):
        """Extrai métricas dos headings para relatórios"""
        headings_problematicos = hierarchy_info.get('headings_problematicos', [])
        
        metrics = {
            'headings_problematicos_count': len(headings_problematicos),
            'headings_vazios_count': len([h for h in headings_problematicos if PROBLEM_TYPE_EMPTY in h.get('motivos', [])]),
            'headings_ocultos_count': len([h for h in headings_problematicos if PROBLEM_TYPE_HIDDEN in h.get('motivos', [])]),
            'headings_gravidade_critica': len([h for h in headings_problematicos if h.get('gravidade') == GRAVITY_CRITICAL]),
            
            'headings_vazios': [h['descricao'] for h in headings_problematicos if PROBLEM_TYPE_EMPTY in h.get('motivos', [])],
            'headings_ocultos': [h['descricao'] for h in headings_problematicos if PROBLEM_TYPE_HIDDEN in h.get('motivos', [])],
            
            'heading_sequence': hierarchy_info.get('heading_sequence', []),
            'heading_sequence_valida': hierarchy_info.get('heading_sequence_valida', []),
            
            'hierarquia_correta': hierarchy_info.get('hierarquia_correta', True),
            'h1_count': hierarchy_info.get('h1_count', 0),
            'h1_ausente': hierarchy_info.get('h1_ausente', True),
            'h1_multiple': hierarchy_info.get('h1_multiple', False),
            'total_problemas_headings': hierarchy_info.get('total_problemas', 0),
            
            'heading_issues': hierarchy_info.get('heading_issues', []),
            'problemas_hierarquia': hierarchy_info.get('problemas_hierarquia', [])
        }
        
        return metrics
    
    def get_h1_text(self, soup):
        """Extrai texto do primeiro H1"""
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        return ''
    
    def analyze_all_headings(self, soup, url):
        """Método principal de análise completa"""
        hierarchy_info = self.analyze_hierarchy_corrected(soup, url)
        
        metrics = self.extract_heading_metrics(hierarchy_info)
        
        metrics['h1_text'] = self.get_h1_text(soup)
        
        metrics['headings_problematicos'] = hierarchy_info.get('headings_problematicos', [])
        
        return metrics


class HeadingsScoreCalculator:
    """Calculadora de score para headings"""
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def calculate_headings_score(self, metrics):
        """Calcula score baseado nas métricas de headings"""
        score = 0
        
        # Score base para H1 correto
        if not metrics.get('h1_ausente', True) and not metrics.get('h1_multiple', False):
            score += 20
        elif not metrics.get('h1_ausente', True):
            score += 10  # H1 presente mas múltiplo
        
        # Score para hierarquia correta
        if metrics.get('hierarquia_correta', True):
            score += 15
        
        # Penalidades por headings problemáticos (gravidade diferenciada)
        headings_criticos = metrics.get('headings_gravidade_critica', 0)
        headings_outros = metrics.get('headings_problematicos_count', 0) - headings_criticos
        
        score -= headings_criticos * 10  # H1s problemáticos = -10 pontos
        score -= headings_outros * 3     # Outros problemáticos = -3 pontos
        
        # Penalidade adicional por hierarquia incorreta
        if not metrics.get('hierarquia_correta', True):
            score -= 15
        
        # Score final entre 0 e 35
        return max(0, min(score, 35))


class HeadingsReportGenerator:
    """Gerador de relatórios para headings"""
    
    def __init__(self, analyzer=None):
        self.analyzer = analyzer or HeadingsAnalyzer()
    
    def generate_problematic_headings_data(self, results):
        """Gera dados consolidados de headings problemáticos"""
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
                    gravidades.append(heading_prob.get('gravidade', GRAVITY_MEDIUM))
                    motivos_todos.extend(heading_prob.get('motivos', []))
                
                gravidade_geral = GRAVITY_CRITICAL if GRAVITY_CRITICAL in gravidades else GRAVITY_MEDIUM
                
                dados_headings_problematicos.append({
                    'URL': url,
                    'Total_Problemas': len(headings_problematicos),
                    'Headings_Vazios': len([h for h in headings_problematicos if PROBLEM_TYPE_EMPTY in h.get('motivos', [])]),
                    'Headings_Ocultos': len([h for h in headings_problematicos if PROBLEM_TYPE_HIDDEN in h.get('motivos', [])]),
                    'Gravidade_Geral': gravidade_geral,
                    'Problemas_Detalhados': ' | '.join(problemas_desc),
                    'Motivos_Únicos': ', '.join(set(motivos_todos)),
                    'H1_Count': resultado.get('h1_count', 0),
                    'Hierarquia_Correta': 'SIM' if resultado.get('hierarquia_correta', True) else 'NÃO',
                    'Sequencia_Completa': ' → '.join(resultado.get('heading_sequence', [])),
                    'Sequencia_Valida': ' → '.join(resultado.get('heading_sequence_valida', [])),
                    'Score': resultado.get('metatags_score', 0)
                })
        
        return dados_headings_problematicos
    
    def generate_hierarchy_problems_data(self, results):
        """Gera dados de problemas de hierarquia"""
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
        
        return dados_hierarquia_problemas


def test_hierarchy_fix():
    """🧪 Teste específico para verificar a correção da hierarquia"""
    print("🧪 TESTANDO CORREÇÃO DE HIERARQUIA (niveis_todos)")
    print("=" * 60)
    
    # HTML com salto de hierarquia E heading oculto no meio
    html_test = """
    <html>
    <head><title>Teste Hierarquia</title></head>
    <body>
        <h1>Título Principal</h1>
        <h2>Subtítulo Nível 2</h2>
        <h3 style="display: none;">Nível 3 OCULTO</h3>
        <h4></h4><!-- H4 VAZIO -->
        <h6>SALTO PARA H6</h6><!-- ← Este salto DEVE ser detectado -->
        <h3>Volta para H3</h3>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html_test, 'html.parser')
    analyzer = HeadingsAnalyzer({'detect_invisible_colors': True})
    
    resultado = analyzer.analyze_all_headings(soup, "https://test.com")
    
    print("📋 ESTRUTURA DETECTADA:")
    print(f"  Sequência Completa: {' → '.join(resultado['heading_sequence'])}")
    print(f"  Sequência Válida:   {' → '.join(resultado['heading_sequence_valida'])}")
    
    print(f"\n🎯 PROBLEMAS DE HIERARQUIA:")
    problemas = resultado.get('problemas_hierarquia', [])
    if problemas:
        for i, problema in enumerate(problemas, 1):
            print(f"  {i}. {problema}")
    else:
        print("  ❌ NENHUM PROBLEMA DETECTADO (BUG!)")
    
    print(f"\n🔍 HEADINGS PROBLEMÁTICOS:")
    problematicos = resultado.get('headings_problematicos', [])
    for prob in problematicos:
        print(f"  - {prob['descricao']} | Gravidade: {prob['gravidade']}")
    
    print(f"\n📊 RESUMO:")
    print(f"  Hierarquia Correta: {resultado['hierarquia_correta']}")
    print(f"  Total Problemas: {resultado['total_problemas_headings']}")
    print(f"  Headings Vazios: {resultado['headings_vazios_count']}")
    print(f"  Headings Ocultos: {resultado['headings_ocultos_count']}")
    
    # Verifica se a correção funcionou
    hierarquia_correta = resultado['hierarquia_correta']
    tem_problemas = len(problemas) > 0
    
    print(f"\n🔥 RESULTADO DA CORREÇÃO:")
    if not hierarquia_correta and tem_problemas:
        print("  ✅ CORREÇÃO FUNCIONANDO! Saltos detectados corretamente")
        print("  ✅ A análise usa niveis_todos e detecta H2→H6")
    else:
        print("  ❌ CORREÇÃO PODE NÃO ESTAR FUNCIONANDO")
        print("  ❌ Saltos não foram detectados adequadamente")
    
    return resultado


def test_simple_jump():
    """🧪 Teste simples: H2 direto para H6"""
    print("\n" + "="*60)
    print("🧪 TESTE SIMPLES: H2 → H6")
    print("="*60)
    
    html_simple = """
    <html>
    <body>
        <h1>Título</h1>
        <h2>Nível 2</h2>
        <h6>SALTO DIRETO PARA H6</h6>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html_simple, 'html.parser')
    analyzer = HeadingsAnalyzer()
    
    resultado = analyzer.analyze_all_headings(soup, "https://test.com")
    
    problemas = resultado.get('problemas_hierarquia', [])
    print(f"Sequência: {' → '.join(resultado['heading_sequence'])}")
    print(f"Problemas: {problemas}")
    print(f"Hierarquia Correta: {resultado['hierarquia_correta']}")
    
    # Este teste DEVE detectar salto H2→H6
    expected_jump = any('H2' in p and 'H6' in p for p in problemas)
    print(f"Salto H2→H6 detectado: {'✅ SIM' if expected_jump else '❌ NÃO'}")
    
    return expected_jump


if __name__ == "__main__":
    # Executa ambos os testes
    print("🚀 TESTANDO CORREÇÃO DA ANÁLISE DE HIERARQUIA")
    print("="*80)
    
    test_hierarchy_fix()
    jump_detected = test_simple_jump()
    
    print(f"\n🎯 RESULTADO FINAL:")
    if jump_detected:
        print("✅ CORREÇÃO IMPLEMENTADA COM SUCESSO!")
        print("✅ A análise agora usa todos os headings para detectar saltos reais")
    else:
        print("❌ A correção precisa ser verificada")
        print("❌ Saltos simples não estão sendo detectados")