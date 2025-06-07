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
            
            niveis_todos = []
            niveis_validos = []
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
                niveis_todos.append(nivel)
                hierarchy_info['heading_sequence'].append(f"{tag_name}:{texto[:30]}...")
                
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
            
            if hierarchy_info['h1_ausente']:
                hierarchy_info['problemas_hierarquia'].append(HIERARCHY_MESSAGES['h1_absent'])
                hierarchy_info['heading_issues'].append('H1 ausente')
                hierarchy_info['total_problemas'] += 1
            
            if hierarchy_info['h1_count'] > 1:
                hierarchy_info['h1_multiple'] = True
                msg = HIERARCHY_MESSAGES['multiple_h1'].format(count=hierarchy_info['h1_count'])
                hierarchy_info['problemas_hierarquia'].append(msg)
                hierarchy_info['heading_issues'].append('Múltiplos H1')
                hierarchy_info['total_problemas'] += 1
            
            if niveis_validos and not hierarchy_info['h1_ausente']:
                problemas_sequencia = self._analyze_hierarchy_sequence_corrected(
                    niveis_validos, headings_detalhados
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
        try:
            style = heading.get('style', '').lower()
            
            for hidden_style in HIDDEN_STYLES:
                if hidden_style in style:
                    return True
            
            if self.detect_invisible_colors and self._has_invisible_color(style):
                return True
            
            classes = ' '.join(heading.get('class', [])).lower()
            for hidden_class in HIDDEN_CSS_CLASSES:
                if hidden_class in classes:
                    return True
            
            for suspicious_pos in SUSPICIOUS_POSITIONING:
                if suspicious_pos in style:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _has_invisible_color(self, style):
        try:
            for invisible_color in INVISIBLE_COLORS:
                if invisible_color in style:
                    return True
            
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
    
    def _analyze_hierarchy_sequence_corrected(self, niveis_validos, headings_detalhados):
        problemas = []
        
        if not niveis_validos:
            return [HIERARCHY_MESSAGES['no_valid_headings']]
        
        if niveis_validos[0] != 1:
            primeiro_valido = None
            for h in headings_detalhados:
                if not h.get('eh_problematico', False):
                    primeiro_valido = h
                    break
            
            if primeiro_valido:
                msg = HIERARCHY_MESSAGES['first_not_h1'].format(tag=primeiro_valido['tag'].upper())
                problemas.append(msg)
        
        for i in range(1, len(niveis_validos)):
            nivel_anterior = niveis_validos[i-1]
            nivel_atual = niveis_validos[i]
            
            if nivel_atual > nivel_anterior + 1:
                niveis_pulados = []
                for nivel_perdido in range(nivel_anterior + 1, nivel_atual):
                    niveis_pulados.append(f'H{nivel_perdido}')
                
                msg = HIERARCHY_MESSAGES['hierarchy_jump'].format(
                    prev=nivel_anterior,
                    curr=nivel_atual,
                    missing=', '.join(niveis_pulados)
                )
                problemas.append(msg)
        
        return problemas
    
    def _create_problem_description(self, heading_detail, problema_info):
        tag = heading_detail['tag']
        posicao = heading_detail['posicao']
        texto = heading_detail['texto']
        motivos = problema_info['motivos']
        
        descricao = f'{tag.upper()} na posição {posicao}'
        
        if motivos:
            motivos_str = ', '.join(motivos).lower()
            descricao += f' ({motivos_str})'
        
        detalhes_motivos = ' - Motivos: ' + ', '.join(motivos) if motivos else ''
        if detalhes_motivos:
            descricao += detalhes_motivos
        
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
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        return ''
    
    def analyze_all_headings(self, soup, url):
        hierarchy_info = self.analyze_hierarchy_corrected(soup, url)
        
        metrics = self.extract_heading_metrics(hierarchy_info)
        
        metrics['h1_text'] = self.get_h1_text(soup)
        
        metrics['headings_problematicos'] = hierarchy_info.get('headings_problematicos', [])
        
        return metrics


class HeadingsScoreCalculator:
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def calculate_headings_score(self, metrics):
        score = 0
        
        if not metrics.get('h1_ausente', True) and not metrics.get('h1_multiple', False):
            score += 20
        elif not metrics.get('h1_ausente', True):
            score += 10
        
        if metrics.get('hierarquia_correta', True):
            score += 15
        
        headings_criticos = metrics.get('headings_gravidade_critica', 0)
        headings_outros = metrics.get('headings_problematicos_count', 0) - headings_criticos
        
        score -= headings_criticos * 10
        score -= headings_outros * 3
        
        if not metrics.get('hierarquia_correta', True):
            score -= 15
        
        return max(0, min(score, 35))


class HeadingsReportGenerator:
    
    def __init__(self, analyzer=None):
        self.analyzer = analyzer or HeadingsAnalyzer()
    
    def generate_problematic_headings_data(self, results):
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


def test_headings_analyzer():
    print("Testando HeadingsAnalyzer...")
    
    html_test = """
    <html>
    <head><title>Teste</title></head>
    <body>
        <h1>Título Principal</h1>
        <h2></h2>
        <h3>Subtítulo</h3>
        <h6>Salto na hierarquia</h6>
        <h2 style="color: white;">Heading Oculto</h2>
        <h1>Segundo H1</h1>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html_test, 'html.parser')
    analyzer = HeadingsAnalyzer({'detect_invisible_colors': True})
    
    metrics = analyzer.analyze_all_headings(soup, "https://test.com")
    
    print("Resultados da análise:")
    print(f"  URL: {metrics.get('url', 'N/A')}")
    print(f"  H1 Count: {metrics['h1_count']}")
    print(f"  H1 Ausente: {metrics['h1_ausente']}")
    print(f"  H1 Múltiplo: {metrics['h1_multiple']}")
    print(f"  Hierarquia Correta: {metrics['hierarquia_correta']}")
    print(f"  Headings Problemáticos: {metrics['headings_problematicos_count']}")
    print(f"  Headings Vazios: {metrics['headings_vazios_count']}")
    print(f"  Headings Ocultos: {metrics['headings_ocultos_count']}")
    print(f"  Headings Críticos: {metrics['headings_gravidade_critica']}")
    
    print(f"\nSequências:")
    print(f"  Completa: {' → '.join(metrics['heading_sequence'])}")
    print(f"  Válida: {' → '.join(metrics['heading_sequence_valida'])}")
    
    print(f"\nProblemas encontrados:")
    for issue in metrics['heading_issues'][:5]:
        print(f"  - {issue}")
    
    calculator = HeadingsScoreCalculator()
    score = calculator.calculate_headings_score(metrics)
    print(f"\nScore dos headings: {score}/35")


def test_invisible_color_detection():
    print("\nTestando detecção de cores invisíveis...")
    
    analyzer = HeadingsAnalyzer({'detect_invisible_colors': True})
    
    test_cases = [
        '<h2 style="color: white;">Texto branco</h2>',
        '<h2 style="color: rgb(255, 255, 255);">RGB branco</h2>',
        '<h2 style="color: transparent;">Transparente</h2>',
        '<h2 style="color: black;">Texto preto (visível)</h2>',
        '<h2 style="color: rgb(100, 100, 100);">RGB escuro (visível)</h2>',
    ]
    
    for i, html in enumerate(test_cases, 1):
        soup = BeautifulSoup(html, 'html.parser')
        heading = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        is_hidden = analyzer._is_heading_hidden_expanded(heading)
        print(f"  Teste {i}: {'OCULTO' if is_hidden else 'VISÍVEL'} - {html}")


if __name__ == "__main__":
    test_headings_analyzer()
    test_invisible_color_detection()