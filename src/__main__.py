"""
TypeLineas 主程序入口

命令行参数解析和分析流程控制。

Usage:
    python -m src <directory> [--all] [--report [filename]] [--advice]
"""
import os
import sys
import unicodedata
from collections import defaultdict

from src.config.colors import Colors
from src.config.i18n import t
from src.config.constants import LANG_DEFINITIONS, DEFAULT_IGNORES
from src.analyzers.file_analyzer import analyze_file
from src.analyzers.refactor_advisor import print_refactor_advice
from src.reporters.exporter import export_report


def str_width(s):
    """计算字符串显示宽度（中文占2格）"""
    width = 0
    for char in str(s):
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width


def pad_cjk(s, width, align='left'):
    """填充字符串到指定显示宽度"""
    s = str(s)
    current = str_width(s)
    padding = width - current
    if padding <= 0:
        return s
    if align == 'right':
        return ' ' * padding + s
    return s + ' ' * padding


def main():
    raw_args = sys.argv[1:]
    show_all = False
    show_advice = False
    
    if "--all" in raw_args:
        show_all = True
        raw_args.remove("--all")
    
    if "--advice" in raw_args:
        show_advice = True
        raw_args.remove("--advice")
        
    report_file = None
    if "--report" in raw_args:
        idx = raw_args.index("--report")
        if idx + 1 < len(raw_args) and not raw_args[idx+1].startswith("-"):
            report_file = raw_args[idx+1]
            raw_args.pop(idx)
            raw_args.pop(idx)
        else:
            report_file = "AUTO"
            raw_args.pop(idx)
            
    root_dir = raw_args[0] if raw_args else os.getcwd()
    
    if report_file == "AUTO":
        project_name = os.path.basename(os.path.abspath(root_dir))
        report_file = f"{project_name}_report.md"

    all_mode_text = f" ({t('scanning')} - All)" if show_all else ""
    print(f"{Colors.HEADER}{t('scanning')}: {root_dir}{all_mode_text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{t('engine')}: Polyglot CC (AST + Regex) | {t('quality_metric')}: {t('project_coder_index')}{Colors.ENDC}")
    
    all_file_stats = []
    project_summary = defaultdict(lambda: {'files': 0, 'total': 0, 'code': 0, 'comments': 0, 'imports': 0, 'boilerplate': 0, 'cc': 0})
    total_weighted_score = 0
    total_weight = 0

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORES]
        for file in files:
            ext = file.split('.')[-1].lower() if '.' in file else ''
            if ext in LANG_DEFINITIONS:
                f_stats = analyze_file(os.path.join(root, file), LANG_DEFINITIONS[ext])
                all_file_stats.append(f_stats)
                l_name = f_stats['lang']
                project_summary[l_name]['files'] += 1
                for k in ['total', 'code', 'comments', 'boilerplate']:
                    project_summary[l_name][k] += f_stats[k]
                project_summary[l_name]['imports'] += f_stats['imports']
                project_summary[l_name]['cc'] += f_stats['complexity']
                
                if f_stats['coder_score'] >= 0 and not f_stats['is_exempt']:
                    weight = f_stats['code']
                    total_weighted_score += f_stats['coder_score'] * weight
                    total_weight += weight

    # 表格列宽定义
    col_widths = [12, 8, 10, 10, 10, 10, 8]
    print("-" * 80)
    # 表头本地化（考虑中文宽度）
    headers = [t('language'), t('files'), t('lines'), t('code'), t('comments'), t('coupling'), t('avg_cc')]
    header_row = ' '.join(pad_cjk(h, w) for h, w in zip(headers, col_widths))
    print(header_row)
    print("-" * 80)
    grand_totals = {'files': 0, 'total': 0, 'code': 0, 'imports': 0, 'comments': 0, 'boilerplate': 0}
    for lang, s in sorted(project_summary.items(), key=lambda x: x[1]['code'], reverse=True):
        avg_cc = f"{s['cc'] / s['files']:.1f}" if s['files'] > 0 and s['cc'] > 0 else "-"
        row = [lang, s['files'], s['total'], s['code'], s['comments'], s['imports'], avg_cc]
        print(f"{Colors.BOLD}{pad_cjk(row[0], col_widths[0])}{Colors.ENDC} " + ' '.join(pad_cjk(row[i], col_widths[i]) for i in range(1, len(row))))
        for k in grand_totals:
            grand_totals[k] += s[k]
    print("-" * 80)
    total_row = [t('total'), grand_totals['files'], grand_totals['total'], grand_totals['code'], grand_totals['comments'], grand_totals['imports'], '-']
    print(f"{Colors.GREEN}{pad_cjk(total_row[0], col_widths[0])} " + ' '.join(pad_cjk(total_row[i], col_widths[i]) for i in range(1, len(total_row))) + f"{Colors.ENDC}")
    print("-" * 80)
    
    if total_weight > 0:
        project_score = int(total_weighted_score / total_weight)
        if project_score >= 90:
            verdict, v_color = t('legendary'), Colors.GREEN
        elif project_score >= 80:
            verdict, v_color = t('solid'), Colors.GREEN
        elif project_score >= 65:
            verdict, v_color = t('average'), Colors.WARNING
        elif project_score >= 50:
            verdict, v_color = t('shaky'), Colors.WARNING
        else:
            verdict, v_color = t('toxic'), Colors.FAIL
        print(f"{t('project_coder_index')}: {v_color}{project_score} / 100 ({verdict}){Colors.ENDC}")
        print(f"{t('total_lines')}: {grand_totals['total']} | {t('boilerplate')}: {(grand_totals['boilerplate']/grand_totals['total']*100):.1f}%")
    print("")

    print(f"{Colors.WARNING}{Colors.BOLD}=== {t('top_shit_mountains')} ==={Colors.ENDC}")
    print(f"{'Score':<8} {'Coder':<6} {'Comp.':<6} {'Imp.':<6} {t('lines'):<8} {t('file_path')}")
    print("-" * 115)
    display_stats = [s for s in all_file_stats if show_all or s['is_logic'] or s.get('logic_lines', 0) >= 5]
    if show_all:
        for s in display_stats:
            if not s['is_logic'] and s.get('logic_lines', 0) < 5:
                s['shit_score'] = int(s['total']/50 + (s['max_nesting']-4)*10)
    
    candidates = [s for s in display_stats if not s['is_exempt']]
    top_shit = sorted(candidates, key=lambda x: x['shit_score'], reverse=True)[:10]
    for s in top_shit:
        rel_p = os.path.relpath(s['path'], root_dir)
        color = Colors.FAIL if s['shit_score'] > 80 else (Colors.WARNING if s['shit_score'] > 40 else Colors.ENDC)
        comp_src = "AST" if s['ast_success'] else "Rgx"
        comp_str = f"{comp_src}:{s['complexity']}" if s['complexity'] > 0 else f"Dp:{s['max_nesting']}"
        suffix = f" {Colors.CYAN}[JavaScript]{Colors.ENDC}" if (not s['is_logic'] and s.get('logic_lines', 0) >= 5) else ""
        c_score = str(s['coder_score']) if s['coder_score'] >= 0 else '--'
        c_color = Colors.GREEN if s['coder_score'] >= 80 else (Colors.WARNING if s['coder_score'] >= 50 else Colors.FAIL)
        if s['coder_score'] == -1:
            c_color = Colors.ENDC
        
        print(f"{color}{s['shit_score']:<8}{Colors.ENDC} {c_color}{c_score:<6}{Colors.ENDC} {comp_str:<8} {s['imports']:<6} {s['total']:<8} {rel_p}{suffix}{Colors.ENDC}")

    exempts = [s for s in display_stats if s['is_exempt'] and s['shit_score'] > 20]
    if exempts:
        print("-" * 115)
        print(f"{Colors.PURPLE}=== {t('exempted_aggregators')} ==={Colors.ENDC}")
        for s in sorted(exempts, key=lambda x: x['shit_score'], reverse=True):
            rel_p = os.path.relpath(s['path'], root_dir)
            comp_src = "AST" if s['ast_success'] else "Rgx"
            comp_str = f"{comp_src}:{s['complexity']}" if s['complexity'] > 0 else f"Dp:{s['max_nesting']}"
            c_score = str(s['coder_score']) if s['coder_score'] >= 0 else '--'
            print(f"{Colors.PURPLE}{s['shit_score']:<8} {c_score:<6} {comp_str:<8} {s['imports']:<6} {s['total']:<8} {rel_p} [Exempt]{Colors.ENDC}")
            
    if report_file:
        export_report(all_stats=all_file_stats, filename=report_file, root_dir=root_dir, include_advice=show_advice)
    
    # 重构建议
    if show_advice:
        print_refactor_advice(top_shit, root_dir)


if __name__ == "__main__":
    main()
