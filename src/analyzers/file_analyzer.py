"""
多语言文件分析器

对各种编程语言文件进行复杂度分析，计算代码行数、注释行数、
嵌套深度、import 耦合度等指标，并生成质量评分。
"""
import os

from src.config.constants import (
    LANG_DEFINITIONS, IMPORT_PATTERNS, CC_PATTERNS, LANG_FAMILY,
    SCRIPT_START, SCRIPT_END, STRING_LITERAL, EXEMPT_FILES
)
from src.analyzers.python_ast import analyze_python_ast


def sanitize_line(line, lang_name):
    """移除行内字符串字面量和注释，用于准确计算复杂度"""
    try:
        clean_line = STRING_LITERAL.sub('""', line)
    except:
        clean_line = line 
    
    # 各语言的行内注释符映射
    # 注意：PHP 同时支持 // 和 #，所以优先处理 //
    inline_comment_markers = {
        'Python': '#',
        'Ruby': '#',
        'Shell': '#',
        'PowerShell': '#',
        'Lua': '--',
        'PHP': '//',  # PHP 也支持 #，但 // 更常见，且处理 // 后 # 也会被 fallback 处理
    }
    
    marker = inline_comment_markers.get(lang_name)
    if marker and marker in clean_line:
        clean_line = clean_line.split(marker, 1)[0]
    
    # C 系语言的 // 注释 fallback
    if lang_name not in ['Python', 'Ruby', 'Shell', 'PowerShell', 'Lua']:
        if '//' in clean_line:
            clean_line = clean_line.split('//', 1)[0]
    
    # PHP 还需要处理 # 行内注释
    if lang_name == 'PHP' and '#' in clean_line:
        clean_line = clean_line.split('#', 1)[0]
        
    return clean_line


def estimate_cc_regex(line, lang_name):
    """使用正则表达式估算单行的圈复杂度贡献"""
    family = LANG_FAMILY.get(lang_name)
    if not family:
        return 0
    pattern = CC_PATTERNS.get(family)
    if not pattern:
        return 0
    clean_line = sanitize_line(line, lang_name)
    matches = pattern.findall(clean_line)
    score = 0
    for match in matches:
        # case/default/else 贡献较小
        if match in ['case', 'default', 'else']:
            score += 0.5 
        else:
            score += 1
    return score


def get_indentation_level(line):
    """计算缩进层级（每4空格为1级）"""
    expand = line.expandtabs(4)
    stripped = expand.lstrip()
    return (len(expand) - len(stripped)) // 4 if stripped else 0


def calculate_scores(stats, is_logic_lang):
    """计算 Shit Score 和 Coder Score"""
    effective_logic = stats.get('logic_lines', 0)
    base_lines = effective_logic if (not is_logic_lang and effective_logic > 0) else stats['total']
    
    shit_score = 0
    if is_logic_lang or effective_logic >= 5:
        size_penalty = effective_logic / 50.0 if not is_logic_lang else stats['total'] / 50.0
        cc = stats.get('complexity', 0)
        if cc == 0:
            complexity_penalty = (stats['max_nesting'] - 4) * 12 if stats['max_nesting'] > 4 else 0
        else:
            complexity_penalty = max(0, cc - 10) * 1.5
        coupling_penalty = stats['imports'] * 1.5
        comment_ratio = (stats['comments'] / base_lines) if base_lines > 0 else 0
        raw_shit = size_penalty + complexity_penalty + coupling_penalty
        shit_score = int(raw_shit * (1.0 - min(comment_ratio, 0.4)))

    coder_score = -1 
    if is_logic_lang or effective_logic >= 5:
        score = 100.0
        cc = stats.get('complexity', 0)
        score -= max(0, cc - 15) * 1.0
        limit = 500 if not is_logic_lang else 300
        if stats['total'] > limit:
            score -= (stats['total'] - limit) / 20.0
        comment_ratio = (stats['comments'] / stats['total']) if stats['total'] > 0 else 0
        if 0.1 <= comment_ratio <= 0.3:
            score += 5
        coder_score = max(0, min(100, int(score)))
        
    return shit_score, coder_score


def analyze_file(file_path, lang_info):
    """分析单个文件的各项指标"""
    lang_name, single_comments, multi_start, multi_end, is_logic = lang_info
    stats = {
        'path': file_path, 'lang': lang_name, 'is_logic': is_logic,
        'total': 0, 'code': 0, 'comments': 0, 'boilerplate': 0,
        'imports': 0, 'max_nesting': 0, 'shit_score': 0, 'coder_score': -1,
        'logic_lines': 0, 'complexity': 0, 'ast_success': False,
        'is_exempt': False
    }
    
    if os.path.basename(file_path) in EXEMPT_FILES:
        stats['is_exempt'] = True

    # Python 文件使用 AST 精确分析
    if lang_name == 'Python':
        ast_result = analyze_python_ast(file_path)
        if ast_result['success']:
            stats['ast_success'] = True
            stats['complexity'] = ast_result['complexity']
            stats['imports'] = ast_result['imports']

    in_script = False
    js_single, js_ms, js_me = ['//'], ['/*'], ['*/']
    js_import_regex = IMPORT_PATTERNS.get('JavaScript')
    import_regex = IMPORT_PATTERNS.get(lang_name)
    unique_imports = set()
    regex_cc = 1

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        stats['total'] = len(lines)
        in_multiline = False
        
        for line in lines:
            stripped = line.strip()
            
            # HTML 中的 script 标签处理
            if lang_name == 'HTML':
                if SCRIPT_START.search(line):
                    in_script = True
                    stats['boilerplate'] += 1
                    continue
                if SCRIPT_END.search(line):
                    in_script = False
                    stats['boilerplate'] += 1
                    continue

            if lang_name == 'HTML' and in_script:
                curr_s, curr_ms, curr_me = js_single, js_ms, js_me
                is_logic_line, calc_lang = True, 'JavaScript'
            else:
                curr_s, curr_ms, curr_me = single_comments, multi_start, multi_end
                is_logic_line, calc_lang = is_logic, lang_name

            if not stripped:
                stats['boilerplate'] += 1
                continue
            
            # 多行注释处理
            if in_multiline:
                stats['comments'] += 1
                if any(t in line for t in curr_me):
                    in_multiline = False
                continue
            
            is_m_start = False
            for start_t in curr_ms:
                if start_t in stripped:
                    stats['comments'] += 1
                    in_multiline = True
                    is_m_start = True
                    if any(end_t in stripped[stripped.find(start_t)+len(start_t):] for end_t in curr_me):
                        in_multiline = False
                    break
            if is_m_start:
                continue
            
            # 单行注释
            if any(stripped.startswith(t) for t in curr_s):
                stats['comments'] += 1
                continue
            
            # 逻辑代码行处理
            if is_logic_line:
                stats['logic_lines'] += 1
                if not stats['ast_success']:
                    regex_cc += estimate_cc_regex(stripped, calc_lang)
                    indent = get_indentation_level(line)
                    if indent > stats['max_nesting']:
                        stats['max_nesting'] = indent
                    regex = js_import_regex if (lang_name == 'HTML' and in_script) else import_regex
                    if regex and regex.match(stripped):
                        unique_imports.add(stripped)
            
            if len(stripped) < 2 and stripped in '{}[]();,':
                stats['boilerplate'] += 1
            else:
                stats['code'] += 1
        
        if not stats['ast_success']:
            stats['complexity'] = int(regex_cc)
            stats['imports'] = len(unique_imports)
        
        if lang_name == 'HTML' and stats['logic_lines'] >= 5:
            stats['lang'] = 'HTML+JS'
            
        stats['shit_score'], stats['coder_score'] = calculate_scores(stats, is_logic)
    except:
        pass
    
    return stats
