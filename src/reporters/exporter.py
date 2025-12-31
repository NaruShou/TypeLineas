"""
报告导出器

将分析结果导出为 CSV 或 Markdown 格式的报告文件。
支持中英文本地化。
"""
import os
import csv
import unicodedata

from src.config.colors import Colors
from src.config.i18n import t
from src.analyzers.refactor_advisor import (
    diagnose_file, analyze_function_complexity, scan_code_smells,
    REFACTOR_SUGGESTIONS
)


def str_width(s):
    """计算字符串显示宽度（考虑中文字符占2格）"""
    width = 0
    for char in s:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width


def pad_to_width(s, width, align='left'):
    """将字符串填充到指定显示宽度"""
    current = str_width(s)
    padding = width - current
    if padding <= 0:
        return s
    if align == 'right':
        return ' ' * padding + s
    return s + ' ' * padding


def export_report(all_stats, filename, root_dir, include_advice=False):
    """导出分析报告到 CSV 或 Markdown 格式"""
    try:
        if filename.endswith('.csv'):
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = [t('file_path'), t('language'), t('shit_score'), t('coder_score'), 
                              t('complexity'), 'Type', t('lines'), t('code'), t('comments'), t('imports')]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for s in sorted(all_stats, key=lambda x: x['shit_score'], reverse=True):
                    comp_str = f"{s['complexity']}" if s['complexity'] > 0 else f"{s['max_nesting']}"
                    comp_type = "AST" if s['ast_success'] else ("Regex" if s['complexity'] > 0 else "Depth")
                    c_score = str(s['coder_score']) if s['coder_score'] >= 0 else '--'
                    writer.writerow({
                        t('file_path'): os.path.relpath(s['path'], root_dir),
                        t('language'): s['lang'],
                        t('shit_score'): s['shit_score'],
                        t('coder_score'): c_score,
                        t('complexity'): comp_str,
                        'Type': comp_type,
                        t('lines'): s['total'],
                        t('code'): s['code'],
                        t('comments'): s['comments'],
                        t('imports'): s['imports']
                    })
        else:
            # Markdown 格式
            headers = [t('file_path'), t('language'), t('shit_score'), t('coder_score'), t('complexity'), t('lines'), t('imports')]
            rows = []
            sorted_stats = sorted(all_stats, key=lambda x: x['shit_score'], reverse=True)
            
            for s in sorted_stats:
                rel_p = os.path.relpath(s['path'], root_dir)
                comp_str = f"{s['complexity']}" if s['complexity'] > 0 else f"Dp:{s['max_nesting']}"
                c_score = str(s['coder_score']) if s['coder_score'] >= 0 else '--'
                rows.append([
                    f"`{rel_p}`",
                    s['lang'],
                    str(s['shit_score']),
                    c_score,
                    comp_str,
                    str(s['total']),
                    str(s['imports'])
                ])

            # 计算每列宽度
            widths = [str_width(h) for h in headers]
            for row in rows:
                for i, val in enumerate(row):
                    widths[i] = max(widths[i], str_width(val))

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {t('code_quality_report')}\n\n{t('generated_by')}\n\n")
                
                # 统计表格
                f.write(f"## {t('file_analysis')}\n\n")
                header_line = "| " + " | ".join(pad_to_width(h, w) for h, w in zip(headers, widths)) + " |\n"
                f.write(header_line)
                sep_parts = []
                for i, w in enumerate(widths):
                    if i < 2:
                        sep_parts.append("-" * w)
                    else:
                        sep_parts.append("-" * (w-1) + ":")
                f.write("| " + " | ".join(sep_parts) + " |\n")
                for row in rows:
                    parts = []
                    for i, (val, w) in enumerate(zip(row, widths)):
                        if i < 2:
                            parts.append(pad_to_width(val, w, 'left'))
                        else:
                            parts.append(pad_to_width(val, w, 'right'))
                    f.write("| " + " | ".join(parts) + " |\n")
                
                # 重构建议部分
                if include_advice:
                    f.write(f"\n---\n\n## {t('refactor_advisor')}\n\n")
                    
                    # 对所有有问题的文件生成建议
                    for stats in sorted_stats:
                        problems = diagnose_file(stats)
                        hotspots = analyze_function_complexity(stats['path'], stats.get('lang', 'Python'))
                        smells = scan_code_smells(stats['path'])
                        
                        # 跳过没有问题的文件
                        if not problems and not hotspots['functions'] and not smells:
                            continue
                        if stats['shit_score'] < 5 and not problems:
                            continue
                        
                        rel_path = os.path.relpath(stats['path'], root_dir)
                        f.write(f"### 📄 `{rel_path}`\n\n")
                        f.write(f"**{t('shit_score')}:** {stats['shit_score']} | ")
                        f.write(f"**{t('complexity')}:** {stats['complexity']} | ")
                        f.write(f"**{t('lines')}:** {stats['total']}\n\n")
                        
                        # 问题诊断
                        if problems:
                            f.write(f"#### {t('problem_diagnosis')}\n\n")
                            for problem_key, severity, value in problems:
                                info = REFACTOR_SUGGESTIONS.get(problem_key, {})
                                emoji = "🔴" if severity > 60 else "🟡"
                                diag = t(problem_key) if problem_key in ['high_complexity', 'high_nesting', 'high_coupling', 'long_file', 'low_comment'] else info.get('diagnosis', problem_key)
                                f.write(f"- {emoji} **{diag}** ({t('complexity')}: {value})\n")
                                for suggestion in info.get('suggestions', [])[:2]:
                                    f.write(f"  - {suggestion.replace('▸ ', '')}\n")
                            f.write("\n")
                        
                        # 函数级热点（最多5个）
                        if hotspots['functions']:
                            f.write(f"#### {t('complexity_hotspots')}\n\n")
                            func_headers = [t('function_name'), t('line_no'), 'CC', t('lines'), t('nesting')]
                            
                            # 构建行数据
                            func_rows = []
                            for func in hotspots['functions'][:5]:
                                func_rows.append([
                                    f"`{func['name']}()`",
                                    f"L{func['line']}",
                                    str(func['complexity']),
                                    str(func['length']),
                                    str(func['nesting'])
                                ])
                            
                            # 计算列宽
                            func_widths = [str_width(h) for h in func_headers]
                            for row in func_rows:
                                for i, val in enumerate(row):
                                    func_widths[i] = max(func_widths[i], str_width(val))
                            
                            # 写表头
                            f.write("| " + " | ".join(pad_to_width(h, w) for h, w in zip(func_headers, func_widths)) + " |\n")
                            # 写分隔符
                            sep_parts = ["-" * w if i == 0 else "-" * (w-1) + ":" for i, w in enumerate(func_widths)]
                            f.write("| " + " | ".join(sep_parts) + " |\n")
                            # 写数据行
                            for row in func_rows:
                                parts = [pad_to_width(val, w, 'left' if i == 0 else 'right') for i, (val, w) in enumerate(zip(row, func_widths))]
                                f.write("| " + " | ".join(parts) + " |\n")
                            f.write("\n")
                        
                        # 代码异味（最多5个）
                        if smells:
                            f.write(f"#### {t('code_smells')}\n\n")
                            for smell in smells[:5]:
                                line_str = ', '.join(f'L{ln}' for ln in smell['lines'][:3])
                                if len(smell['lines']) > 3:
                                    line_str += '...'
                                name = t(smell['key']) if smell['key'] in ['god_function', 'deep_nesting', 'magic_number', 'long_param_list', 'duplicate_string', 'print_debug', 'todo_fixme', 'bare_except', 'hardcoded_path', 'commented_code', 'long_lines', 'long_function'] else smell['name']
                                f.write(f"- ⚠️ **{name}** × {smell['count']} [{line_str}]")
                                if smell['suggestion']:
                                    f.write(f" → {smell['suggestion']}")
                                f.write("\n")
                            f.write("\n")
                        
                        f.write("---\n\n")

        print(f"{Colors.GREEN}{t('report_exported')}: {filename}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}{t('report_failed')}: {e}{Colors.ENDC}")
