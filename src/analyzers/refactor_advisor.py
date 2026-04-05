"""
重构助手模块

分析文件的"Shit Score"成因，通过启发式扫描检测具体代码问题，
给出结合项目代码上下文的针对性重构建议。
"""
import os

from src.config.colors import Colors
from src.config.i18n import t
from src.config.constants import LANG_DEFINITIONS
from src.config.refactor_rules import THRESHOLDS, REFACTOR_SUGGESTIONS, LANG_EXTRACTORS

from src.analyzers.checkers.complexity_checker import ComplexityChecker
from src.analyzers.checkers.smell_scanner import SmellScanner


def analyze_function_complexity(file_path, lang_name):
    """
    分析文件中各函数/类的复杂度热点
    
    Args:
        file_path: 文件路径
        lang_name: 语言名称
        
    Returns:
        dict: 包含 functions 和 classes 的复杂度分析结果
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
    except:
        return {'functions': [], 'classes': []}
    
    extractor = LANG_EXTRACTORS.get(lang_name)
    if not extractor:
        # 尝试匹配相似语言
        for key in ['JavaScript', 'Python']:
            if key in lang_name or lang_name in ['React', 'React TS']:
                extractor = LANG_EXTRACTORS.get('JavaScript' if 'React' in lang_name else key)
                break
    
    if not extractor:
        return {'functions': [], 'classes': []}
    
    return ComplexityChecker().check(content, lines, extractor)


def scan_code_smells(file_path, lang_name='Python'):
    """
    启发式扫描代码异味
    
    Args:
        file_path: 文件路径
        lang_name: 语言名称
        
    Returns:
        list: 检测到的代码异味列表 [(smell_name, count, line_samples)]
    """
    extractor = LANG_EXTRACTORS.get(lang_name)
    if not extractor:
        for key in ['JavaScript', 'Python']:
            if key in lang_name or lang_name in ['React', 'React TS']:
                extractor = LANG_EXTRACTORS.get('JavaScript' if 'React' in lang_name else key)
                break
    return SmellScanner().scan(file_path, extractor)


def diagnose_file(stats):
    """诊断单个文件的统计问题"""
    problems = []
    
    cc = stats.get('complexity', 0)
    if cc > THRESHOLDS['high_complexity']:
        severity = min(100, int((cc - THRESHOLDS['high_complexity']) * 3))
        problems.append(('high_complexity', severity, cc))
    
    nesting = stats.get('max_nesting', 0)
    if nesting > THRESHOLDS['high_nesting']:
        severity = min(100, (nesting - THRESHOLDS['high_nesting']) * 15)
        problems.append(('high_nesting', severity, nesting))
    
    imports = stats.get('imports', 0)
    if imports > THRESHOLDS['high_coupling']:
        severity = min(100, (imports - THRESHOLDS['high_coupling']) * 5)
        problems.append(('high_coupling', severity, imports))
    
    total_lines = stats.get('total', 0)
    if total_lines > THRESHOLDS['long_file']:
        severity = min(100, int((total_lines - THRESHOLDS['long_file']) / 5))
        problems.append(('long_file', severity, total_lines))
    
    comment_ratio = (stats.get('comments', 0) / total_lines) if total_lines > 0 else 0
    if comment_ratio < THRESHOLDS['low_comment_ratio'] and total_lines > 50:
        severity = min(100, int((THRESHOLDS['low_comment_ratio'] - comment_ratio) * 500))
        problems.append(('low_comment', severity, f'{comment_ratio*100:.1f}%'))
    
    problems.sort(key=lambda x: x[1], reverse=True)
    return problems


def _format_hotspots(hotspots):
    """格式化热点函数报告"""
    lines = []
    if hotspots['functions']:
        lines.append(f"\n  {Colors.FAIL}▼ 复杂度热点函数:{Colors.ENDC}")
        for func in hotspots['functions'][:3]:  # 最多显示3个
            cc_color = Colors.FAIL if func['complexity'] > 15 else Colors.WARNING
            lines.append(
                f"    {cc_color}🔥 {func['name']}(){Colors.ENDC} "
                f"[L{func['line']}] CC={func['complexity']}, {func['length']}行, 嵌套{func['nesting']}层"
            )
            # 针对具体问题给建议
            if func['complexity'] > 20:
                lines.append(f"      {Colors.CYAN}└ 拆分为多个子函数，每个函数单一职责{Colors.ENDC}")
            elif func['length'] > 50:
                lines.append(f"      {Colors.CYAN}└ 提取重复逻辑为独立函数{Colors.ENDC}")
            elif func['nesting'] > 4:
                lines.append(f"      {Colors.CYAN}└ 使用 Guard Clauses 提前返回{Colors.ENDC}")
    return lines


def _format_smells(smells):
    """格式化代码异味报告"""
    lines = []
    if smells:
        lines.append(f"\n  {Colors.PURPLE}▼ 代码异味检测:{Colors.ENDC}")
        for smell in smells[:3]:  # 最多显示3种异味
            # 优先使用 formatted_lines（深度嵌套专用）
            if 'formatted_lines' in smell and smell['formatted_lines']:
                line_str = ', '.join(smell['formatted_lines'][:3])
                if len(smell['formatted_lines']) > 3:
                    line_str += '...'
            else:
                line_str = ', '.join(f'L{ln}' for ln in smell['lines'][:3])
                if len(smell['lines']) > 3:
                    line_str += '...'
            
            detail = ''
            if 'details' in smell:
                detail = ' → ' + ', '.join(f"{n}({l}行)" for n, l in smell['details'])
            
            lines.append(f"    {Colors.WARNING}⚠ {smell['name']}{Colors.ENDC} × {smell['count']} [{line_str}]{detail}")
            if smell['suggestion']:
                lines.append(f"      {Colors.CYAN}└ {smell['suggestion']}{Colors.ENDC}")
    return lines


def generate_report(stats, include_smells=True):
    """生成单个文件的重构建议报告"""
    problems = diagnose_file(stats)
    lines = []
    
    # 统计问题
    for problem_key, severity, value in problems:
        info = REFACTOR_SUGGESTIONS.get(problem_key, {})
        color = Colors.FAIL if severity > 60 else Colors.WARNING
        lines.append(f"  {color}■ {info.get('diagnosis', problem_key)}{Colors.ENDC} (值: {value})")
        for suggestion in info.get('suggestions', [])[:2]:
            lines.append(f"    {Colors.CYAN}{suggestion}{Colors.ENDC}")
    
    # 函数级复杂度热点
    lang_name = stats.get('lang', 'Python')
    hotspots = analyze_function_complexity(stats['path'], lang_name)
    
    lines.extend(_format_hotspots(hotspots))
    
    # 代码异味扫描
    if include_smells:
        smells = scan_code_smells(stats['path'], lang_name)
        lines.extend(_format_smells(smells))
    
    return '\n'.join(lines) if lines else None


def print_refactor_advice(top_files, root_dir):
    """打印 Top N 文件的重构建议"""
    print(f"\n{Colors.PURPLE}{Colors.BOLD}=== {t('refactor_advisor')} ==={Colors.ENDC}")
    
    has_advice = False
    for stats in top_files[:5]:
        report = generate_report(stats, include_smells=True)
        if report:
            has_advice = True
            rel_path = os.path.relpath(stats['path'], root_dir)
            score_color = Colors.FAIL if stats['shit_score'] > 80 else Colors.WARNING
            print(f"\n{score_color}📄 {rel_path}{Colors.ENDC} ({t('shit_score')}: {stats['shit_score']})")
            print(report)
    
    if not has_advice:
        print(f"  {Colors.GREEN}✨ 恭喜！Top 文件没有明显的重构需求{Colors.ENDC}")