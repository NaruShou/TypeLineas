"""
代码异味扫描器
"""
import os
import re
from src.config.constants import LANG_DEFINITIONS
from src.config.refactor_rules import CODE_SMELLS, THRESHOLDS
from src.analyzers.checkers.complexity_checker import ComplexityChecker

class SmellScanner:
    """负责扫描代码异味"""

    def scan(self, file_path, extractor=None):
        """
        启发式扫描代码异味
        
        Args:
            file_path: 文件路径
            extractor: 解析器正则组
            
        Returns:
            list: 检测到的代码异味列表 [(smell_name, count, line_samples)]
        """
        # 跳过非代码文件（Markdown 等），避免误报
        ext = os.path.splitext(file_path)[1].lstrip('.')
        lang_def = LANG_DEFINITIONS.get(ext)
        if lang_def and not lang_def[4]:  # is_logic = False
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except:
            return []
        
        smells = []
        
        # 获取函数范围（用于深度嵌套的函数定位）
        func_ranges = self.get_function_ranges(content, lines, extractor)
        
        # 检测各种代码异味
        smells.extend(self._check_pattern_smells(content, func_ranges))
        
        # 检测长行
        smells.extend(self._check_long_lines(lines))
        
        # 检测函数长度
        smells.extend(self._check_long_functions(content, lines, extractor, func_ranges))
        
        return smells

    def _check_pattern_smells(self, content, func_ranges):
        """检测基于模式的代码异味"""
        smells = []
        for smell_key, smell_info in CODE_SMELLS.items():
            # 跳过标记了 skip 的项或没有 pattern 的项
            if smell_info.get('skip') or not smell_info.get('pattern'):
                continue
            pattern = smell_info['pattern']
            matches = list(pattern.finditer(content))
            
            if matches:
                # 深度嵌套特殊处理：按函数分组并合并行号
                if smell_key == 'deep_nesting':
                    all_line_nums, formatted_lines = self._format_deep_nesting(matches, content, func_ranges)
                    
                    smells.append({
                        'key': smell_key,
                        'name': smell_info['name'],
                        'count': len(matches),
                        'lines': all_line_nums[:5],  # 保留原始行号用于兼容
                        'formatted_lines': formatted_lines[:5],  # 新增格式化的位置
                        'suggestion': smell_info.get('suggestion', ''),
                    })
                else:
                    # 普通代码异味处理
                    line_nums = []
                    for match in matches[:5]:
                        start = match.start()
                        line_num = content[:start].count('\n') + 1
                        line_nums.append(line_num)
                    
                    smells.append({
                        'key': smell_key,
                        'name': smell_info['name'],
                        'count': len(matches),
                        'lines': line_nums,
                        'suggestion': smell_info.get('suggestion', ''),
                    })
        return smells

    def _check_long_lines(self, lines):
        """检测过长代码行"""
        smells = []
        long_lines = [(i+1, len(line)) for i, line in enumerate(lines) if len(line) > THRESHOLDS['long_line']]
        if long_lines:
            smells.append({
                'key': 'long_lines',
                'name': f'过长代码行 (>{THRESHOLDS["long_line"]}字符)',
                'count': len(long_lines),
                'lines': [ln for ln, _ in long_lines[:5]],
                'suggestion': '拆分或格式化',
            })
        return smells

    def _check_long_functions(self, content, lines, extractor, func_ranges):
        """检测过长函数"""
        smells = []
        if not func_ranges:
            return smells
            
        long_funcs = []
        for func_name, start_line, end_line in func_ranges:
            func_len = end_line - start_line
            if func_len > THRESHOLDS['long_function']:
                long_funcs.append((func_name, start_line, func_len))
        
        if long_funcs:
            smells.append({
                'key': 'long_function',
                'name': f'过长函数 (>{THRESHOLDS["long_function"]}行)',
                'count': len(long_funcs),
                'lines': [ln for _, ln, _ in long_funcs[:3]],
                'suggestion': '拆分为多个小函数',
                'details': [(name, length) for name, _, length in long_funcs[:3]],
            })
        return smells

    def _format_deep_nesting(self, matches, content, func_ranges):
        """格式化深度嵌套报告"""
        all_line_nums = []
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            all_line_nums.append(line_num)
        
        # 按函数分组
        func_groups = {}
        global_lines = []
        for ln in all_line_nums:
            func_name = self.find_function_for_line(ln, func_ranges)
            if func_name:
                func_groups.setdefault(func_name, []).append(ln)
            else:
                global_lines.append(ln)
                
        # 生成格式化的位置信息
        formatted_lines = []
        for func_name, func_lines in func_groups.items():
            ranges = self.merge_line_ranges(func_lines)
            formatted_lines.append(f"[{func_name}]{','.join(ranges[:2])}")
        if global_lines:
            ranges = self.merge_line_ranges(global_lines)
            formatted_lines.append(f"[global]{','.join(ranges[:2])}")
            
        return all_line_nums, formatted_lines

    def get_function_ranges(self, content, lines, extractor):
        """获取文件中所有函数的行号范围"""
        if not extractor or not extractor.get('function'):
            return []
            
        func_pattern = extractor.get('function')
        func_matches = list(func_pattern.finditer(content))
        
        ranges = []
        checker = ComplexityChecker()
        
        for i, match in enumerate(func_matches):
            gd = match.groupdict()
            func_name = gd.get('name') or gd.get('name2') or gd.get('name3')
            if not func_name:
                groups = [g for g in match.groups() if g and not g.isspace() and len(g) < 50]
                func_name = groups[0] if groups else 'unknown'
            if not func_name or func_name.strip() == '':
                continue
                
            start_line = content[:match.start()].count('\n') + 1
            next_start = func_matches[i+1].start() if i + 1 < len(func_matches) else None
            end_line = checker._find_function_end(lines, start_line, extractor, match, content, next_start)
            ranges.append((func_name, start_line, end_line))
        return ranges

    def find_function_for_line(self, line_num, func_ranges):
        """根据行号查找所属函数名"""
        for func_name, start, end in func_ranges:
            if start <= line_num <= end:
                return func_name
        return None

    def merge_line_ranges(self, line_nums):
        """将连续行号合并为范围格式，如 [49, 50, 51, 55] -> ['49-51', '55']"""
        if not line_nums:
            return []
        
        sorted_nums = sorted(set(line_nums))
        ranges = []
        start = end = sorted_nums[0]
        
        for num in sorted_nums[1:]:
            if num == end + 1:
                end = num
            else:
                ranges.append(f"L{start}-{end}" if start != end else f"L{start}")
                start = end = num
        ranges.append(f"L{start}-{end}" if start != end else f"L{start}")
        return ranges
