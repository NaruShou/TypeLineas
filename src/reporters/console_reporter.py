"""
控制台报告生成器
"""
import os
import unicodedata
from src.config.colors import Colors
from src.config.i18n import t

class ConsoleReporter:
    """负责将分析结果输出到控制台"""
    
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.col_widths = [12, 8, 10, 10, 10, 10, 8]

    def print_header(self, show_all=False):
        """打印头部信息"""
        all_mode_text = f" ({t('scanning')} - All)" if show_all else ""
        print(f"{Colors.HEADER}{t('scanning')}: {self.root_dir}{all_mode_text}{Colors.ENDC}")
        print(f"{Colors.CYAN}{t('engine')}: Polyglot CC (AST + Regex) | {t('quality_metric')}: {t('project_coder_index')}{Colors.ENDC}")

    def print_summary(self, summary, project_score):
        """打印项目汇总统计"""
        print("-" * 80)
        
        # 表头
        headers = [t('language'), t('files'), t('lines'), t('code'), t('comments'), t('coupling'), t('avg_cc')]
        header_row = ' '.join(self._pad_cjk(h, w) for h, w in zip(headers, self.col_widths))
        print(header_row)
        print("-" * 80)
        
        # 各语言统计
        grand_totals = {'files': 0, 'total': 0, 'code': 0, 'imports': 0, 'comments': 0, 'boilerplate': 0}
        for lang, s in sorted(summary.items(), key=lambda x: x[1]['code'], reverse=True):
            avg_cc = f"{s['cc'] / s['files']:.1f}" if s['files'] > 0 and s['cc'] > 0 else "-"
            row = [lang, s['files'], s['total'], s['code'], s['comments'], s['imports'], avg_cc]
            print(f"{Colors.BOLD}{self._pad_cjk(row[0], self.col_widths[0])}{Colors.ENDC} " + 
                  ' '.join(self._pad_cjk(row[i], self.col_widths[i]) for i in range(1, len(row))))
            for k in grand_totals:
                grand_totals[k] += s[k]
        
        print("-" * 80)
        
        # 总计行
        total_row = [t('total'), grand_totals['files'], grand_totals['total'], 
                     grand_totals['code'], grand_totals['comments'], grand_totals['imports'], '-']
        print(f"{Colors.GREEN}{self._pad_cjk(total_row[0], self.col_widths[0])} " + 
              ' '.join(self._pad_cjk(total_row[i], self.col_widths[i]) for i in range(1, len(total_row))) + 
              f"{Colors.ENDC}")
        print("-" * 80)
        
        # 项目评分
        self._print_project_verdict(project_score, grand_totals)
        print("")

    def print_top_shit(self, all_stats, show_all=False):
        """打印 Top 10 问题文件"""
        print(f"{Colors.WARNING}{Colors.BOLD}=== {t('top_shit_mountains')} ==={Colors.ENDC}")
        print(f"{'Score':<8} {'Coder':<6} {'Comp.':<6} {'Imp.':<6} {t('lines'):<8} {t('file_path')}")
        print("-" * 115)
        
        display_stats = [s for s in all_stats if show_all or s['is_logic'] or s.get('logic_lines', 0) >= 5]
        if show_all:
            for s in display_stats:
                if not s['is_logic'] and s.get('logic_lines', 0) < 5:
                    s['shit_score'] = int(s['total']/50 + (s['max_nesting']-4)*10)
        
        candidates = [s for s in display_stats if not s['is_exempt']]
        top_shit = sorted(candidates, key=lambda x: x['shit_score'], reverse=True)[:10]
        
        for s in top_shit:
            self._print_file_row(s)
            
        self._print_exempts(display_stats)
        
        return top_shit

    def _print_file_row(self, s):
        """打印单行文件统计"""
        rel_p = os.path.relpath(s['path'], self.root_dir)
        color = Colors.FAIL if s['shit_score'] > 80 else (Colors.WARNING if s['shit_score'] > 40 else Colors.ENDC)
        comp_src = "AST" if s['ast_success'] else "Rgx"
        comp_str = f"{comp_src}:{s['complexity']}" if s['complexity'] > 0 else f"Dp:{s['max_nesting']}"
        suffix = f" {Colors.CYAN}[JavaScript]{Colors.ENDC}" if (not s['is_logic'] and s.get('logic_lines', 0) >= 5) else ""
        c_score = str(s['coder_score']) if s['coder_score'] >= 0 else '--'
        c_color = Colors.GREEN if s['coder_score'] >= 80 else (Colors.WARNING if s['coder_score'] >= 50 else Colors.FAIL)
        if s['coder_score'] == -1:
            c_color = Colors.ENDC
        
        print(f"{color}{s['shit_score']:<8}{Colors.ENDC} {c_color}{c_score:<6}{Colors.ENDC} "
              f"{comp_str:<8} {s['imports']:<6} {s['total']:<8} {rel_p}{suffix}{Colors.ENDC}")

    def _print_exempts(self, display_stats):
        """打印豁免文件"""
        exempts = [s for s in display_stats if s['is_exempt'] and s['shit_score'] > 20]
        if exempts:
            print("-" * 115)
            print(f"{Colors.PURPLE}=== {t('exempted_aggregators')} ==={Colors.ENDC}")
            for s in sorted(exempts, key=lambda x: x['shit_score'], reverse=True):
                rel_p = os.path.relpath(s['path'], self.root_dir)
                comp_src = "AST" if s['ast_success'] else "Rgx"
                comp_str = f"{comp_src}:{s['complexity']}" if s['complexity'] > 0 else f"Dp:{s['max_nesting']}"
                c_score = str(s['coder_score']) if s['coder_score'] >= 0 else '--'
                print(f"{Colors.PURPLE}{s['shit_score']:<8} {c_score:<6} {comp_str:<8} "
                      f"{s['imports']:<6} {s['total']:<8} {rel_p} [Exempt]{Colors.ENDC}")

    def _print_project_verdict(self, score, grand_totals):
        """打印项目结论"""
        if score >= 90:
            verdict, v_color = t('legendary'), Colors.GREEN
        elif score >= 80:
            verdict, v_color = t('solid'), Colors.GREEN
        elif score >= 65:
            verdict, v_color = t('average'), Colors.WARNING
        elif score >= 50:
            verdict, v_color = t('shaky'), Colors.WARNING
        else:
            verdict, v_color = t('toxic'), Colors.FAIL
            
        print(f"{t('project_coder_index')}: {v_color}{score} / 100 ({verdict}){Colors.ENDC}")
        boilerplate_ratio = (grand_totals['boilerplate']/grand_totals['total']*100) if grand_totals['total'] > 0 else 0
        print(f"{t('total_lines')}: {grand_totals['total']} | {t('boilerplate')}: {boilerplate_ratio:.1f}%")

    def _str_width(self, s):
        """计算字符串显示宽度"""
        width = 0
        for char in str(s):
            if unicodedata.east_asian_width(char) in ('F', 'W'):
                width += 2
            else:
                width += 1
        return width

    def _pad_cjk(self, s, width, align='left'):
        """填充字符串到指定显示宽度"""
        s = str(s)
        current = self._str_width(s)
        padding = width - current
        if padding <= 0:
            return s
        if align == 'right':
            return ' ' * padding + s
        return s + ' ' * padding
