"""
管道处理阶段
"""
import re
from src.config.constants import (
    LANG_DEFINITIONS, IMPORT_PATTERNS, CC_PATTERNS, LANG_FAMILY,
    SCRIPT_START, SCRIPT_END, STRING_LITERAL
)
from src.analyzers.python_ast import analyze_python_ast
from .base_pipe import BasePipe

class ReaderStage(BasePipe):
    """读取文件内容"""
    def process(self, context):
        try:
            with open(context.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                context.content = content
                context.lines = content.split('\n') # splitlines creates a list
                context.stats['total'] = len(context.lines)
        except Exception:
            context.stats['total'] = 0
            context.lines = []


class LanguageStage(BasePipe):
    """确定语言类型和配置"""
    def process(self, context):
        ext = context.file_path.split('.')[-1].lower() if '.' in context.file_path else ''
        if ext in LANG_DEFINITIONS:
            lang_info = LANG_DEFINITIONS[ext]
            context.lang_name = lang_info[0]
            context.single_comments = lang_info[1]
            context.multi_start = lang_info[2]
            context.multi_end = lang_info[3]
            context.is_logic = lang_info[4]
            
            context.stats['lang'] = context.lang_name
            context.stats['is_logic'] = context.is_logic


class ASTStage(BasePipe):
    """AST 分析 (仅 Python)"""
    def process(self, context):
        if context.lang_name == 'Python':
            ast_result = analyze_python_ast(context.file_path)
            if ast_result['success']:
                context.stats['ast_success'] = True
                context.stats['complexity'] = ast_result['complexity']
                context.stats['imports'] = ast_result['imports']


class ScannerStage(BasePipe):
    """正则扫描分析"""
    
    def process(self, context):
        if context.stats['ast_success']:
            # AST 成功，只需统计非AST指标 (comments, etc)
            # 但我们需要扫描所有行来统计 comments, boilerplate
            # 逻辑稍微有点绕，不如统一扫描一次，AST只覆盖 complexity 和 imports
            pass

        self._scan_lines(context)

    def _scan_lines(self, context):
        in_script = False
        js_single, js_ms, js_me = ['//'], ['/*'], ['*/']
        js_import_regex = IMPORT_PATTERNS.get('JavaScript')
        import_regex = IMPORT_PATTERNS.get(context.lang_name)
        unique_imports = set()
        regex_cc = 1
        
        in_multiline = False
        lang_name = context.lang_name
        
        for line in context.lines:
            stripped = line.strip()
            
            # HTML 中的 script 标签处理
            if lang_name == 'HTML':
                if SCRIPT_START.search(line):
                    in_script = True
                    context.stats['boilerplate'] += 1
                    continue
                if SCRIPT_END.search(line):
                    in_script = False
                    context.stats['boilerplate'] += 1
                    continue

            if lang_name == 'HTML' and in_script:
                curr_s, curr_ms, curr_me = js_single, js_ms, js_me
                is_logic_line, calc_lang = True, 'JavaScript'
            else:
                curr_s, curr_ms, curr_me = context.single_comments, context.multi_start, context.multi_end
                is_logic_line, calc_lang = context.is_logic, lang_name

            if not stripped:
                context.stats['boilerplate'] += 1
                continue
            
            # 多行注释处理
            if in_multiline:
                context.stats['comments'] += 1
                if any(t in line for t in curr_me):
                    in_multiline = False
                continue
            
            is_m_start = False
            for start_t in curr_ms:
                if start_t in stripped:
                    context.stats['comments'] += 1
                    in_multiline = True
                    is_m_start = True
                    if any(end_t in stripped[stripped.find(start_t)+len(start_t):] for end_t in curr_me):
                        in_multiline = False
                    break
            if is_m_start:
                continue
            
            # 单行注释
            if any(stripped.startswith(t) for t in curr_s):
                context.stats['comments'] += 1
                continue
            
            # 逻辑代码行处理
            if is_logic_line:
                context.stats['logic_lines'] += 1
                if not context.stats['ast_success']:
                    regex_cc += self._estimate_cc_regex(stripped, calc_lang)
                    indent = self._get_indentation_level(line)
                    if indent > context.stats['max_nesting']:
                        context.stats['max_nesting'] = indent
                    regex = js_import_regex if (lang_name == 'HTML' and in_script) else import_regex
                    if regex and regex.match(stripped):
                        unique_imports.add(stripped)
            
            if len(stripped) < 2 and stripped in '{}[]();,':
                context.stats['boilerplate'] += 1
            else:
                context.stats['code'] += 1
        
        # 应用结果
        if not context.stats['ast_success']:
            context.stats['complexity'] = int(regex_cc)
            context.stats['imports'] = len(unique_imports)
        
        if lang_name == 'HTML' and context.stats['logic_lines'] >= 5:
            context.stats['lang'] = 'HTML+JS'

    def _estimate_cc_regex(self, line, lang_name):
        family = LANG_FAMILY.get(lang_name)
        if not family: return 0
        pattern = CC_PATTERNS.get(family)
        if not pattern: return 0
        clean_line = self._sanitize_line(line, lang_name)
        matches = pattern.findall(clean_line)
        score = 0
        for match in matches:
            if match in ['case', 'default', 'else']: score += 0.5
            else: score += 1
        return score

    def _sanitize_line(self, line, lang_name):
        try: clean_line = STRING_LITERAL.sub('""', line)
        except: clean_line = line 
        
        inline_comment_markers = {
            'Python': '#', 'Ruby': '#', 'Shell': '#', 'PowerShell': '#', 
            'Lua': '--', 'PHP': '//'
        }
        marker = inline_comment_markers.get(lang_name)
        if marker and marker in clean_line:
            clean_line = clean_line.split(marker, 1)[0]
        
        if lang_name not in ['Python', 'Ruby', 'Shell', 'PowerShell', 'Lua']:
            if '//' in clean_line:
                clean_line = clean_line.split('//', 1)[0]
        
        if lang_name == 'PHP' and '#' in clean_line:
            clean_line = clean_line.split('#', 1)[0]
        return clean_line

    def _get_indentation_level(self, line):
        expand = line.expandtabs(4)
        stripped = expand.lstrip()
        return (len(expand) - len(stripped)) // 4 if stripped else 0


class ScoringStage(BasePipe):
    """评分计算"""
    
    def process(self, context):
        shit, coder = self._calculate_scores(context.stats, context.is_logic)
        context.stats['shit_score'] = shit
        context.stats['coder_score'] = coder

    def _calculate_scores(self, stats, is_logic_lang):
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
