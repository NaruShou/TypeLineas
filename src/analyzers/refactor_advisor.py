"""
重构助手模块

分析文件的"Shit Score"成因，通过启发式扫描检测具体代码问题，
给出结合项目代码上下文的针对性重构建议。
"""
import os
import re

from src.config.colors import Colors
from src.config.i18n import t


# 问题诊断阈值
THRESHOLDS = {
    'high_complexity': 25,
    'high_nesting': 5,
    'high_coupling': 15,
    'long_file': 300,
    'low_comment_ratio': 0.05,
    'long_function': 50,        # 函数超过此行数
    'long_line': 120,           # 行超过此字符数
}

# 启发式代码模式检测
CODE_SMELLS = {
    # (pattern, name, suggestion)
    'god_function': {
        'pattern': None,
        'skip': True,
        'name': 'God Function',
        'check': 'line_count',
        'threshold': 50,
    },
    'deep_nesting': {
        # 5层+嵌套才报警（20空格/5Tab），避免正常代码误报
        'pattern': re.compile(r'^(?:\t{5,}|[ ]{20,})\S', re.MULTILINE),
        'name': '深度嵌套',
    },
    'magic_number': {
        # 排除常见的 -1,0,1,2 和字符串/变量中的数字
        'pattern': re.compile(r'(?<!["\'\w])(?!-?[012]\b)-?\b\d{2,}(?:\.\d+)?(?!["\'\w])|0x[0-9a-fA-F]{4,}'),
        'name': '魔法数字',
        'suggestion': '提取为命名常量',
    },
    'long_param_list': {
        # 多语言：Python def / JS function / Java/C# 方法
        'pattern': re.compile(r'(?:def|function|func)\s+\w+\s*\([^)]{80,}\)|(?:public|private|protected)\s+\w+\s+\w+\s*\([^)]{80,}\)'),
        'name': '过长参数列表',
        'suggestion': '考虑使用数据类或字典封装',
    },
    'duplicate_string': {
        # 限制扫描范围到 2000 字符内防止回溯爆炸
        'pattern': re.compile(r'(["\'][^"\']{10,}["\'])(?:.{0,2000}?)\1'),
        'name': '重复字符串',
        'suggestion': '提取为常量',
    },
    'print_debug': {
        # 多语言调试输出：print/console.log/System.out/fmt.Print/var_dump
        'pattern': re.compile(r'\b(?:print|console\.log|System\.out\.print|fmt\.Print|var_dump|dd)\s*\(', re.IGNORECASE),
        'name': '调试代码残留',
        'suggestion': '移除或替换为正式日志',
    },
    'todo_fixme': {
        # 多语言注释：# // /* 都支持
        'pattern': re.compile(r'(?:#|//|/\*)\s*(TODO|FIXME|XXX|HACK|BUG)\b', re.IGNORECASE),
        'name': '未完成标记',
        'suggestion': '处理或创建 issue 跟踪',
    },
    'bare_except': {
        'pattern': re.compile(r'\bexcept\s*:\s*$', re.MULTILINE),
        'name': '裸 except',
        'suggestion': '明确捕获特定异常类型',
    },
    'hardcoded_path': {
        # Windows: C:\ 或 C:\\ / Unix: /home /usr /var /etc
        'pattern': re.compile(r'["\'][A-Za-z]:\\|["\'][A-Za-z]:\\\\|[\'"]/(?:home|usr|var|etc|opt|tmp)/'),
        'name': '硬编码路径',
        'suggestion': '使用配置文件或环境变量',
    },
    'commented_code': {
        # 多语言注释中的代码：# // /* 后跟关键字
        'pattern': re.compile(r'(?:#|//)\s*(if|for|def|class|return|import|function|var|let|const)\s+\w+'),
        'name': '注释掉的代码',
        'suggestion': '删除或使用版本控制',
    },
}

# 多语言函数/类提取模式（用命名捕获组提取函数名）
LANG_EXTRACTORS = {
    'Python': {
        'function': re.compile(r'^(?P<indent> *)(?:async\s+)?def\s+(?P<name>\w+)\s*\([^)]*\)', re.MULTILINE),
        'class': re.compile(r'^( *)class\s+(\w+)', re.MULTILINE),
        'indent_based': True,
        'name_group': 'name',
    },
    'JavaScript': {
        'function': re.compile(r'(?:function\s+(?P<name>\w+)|(?:const|let|var)\s+(?P<name2>\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))', re.MULTILINE),
        'class': re.compile(r'class\s+(\w+)', re.MULTILINE),
        'indent_based': False,
    },
    'TypeScript': {
        'function': re.compile(r'(?:function\s+(?P<name>\w+)|(?:const|let|var)\s+(?P<name2>\w+)\s*(?::\s*[^=]+)?\s*=|(?P<name3>\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{)', re.MULTILINE),
        'class': re.compile(r'class\s+(\w+)', re.MULTILINE),
        'indent_based': False,
    },
    'Java': {
        'function': re.compile(r'(?:public|private|protected|static|\s)+\s+\w+(?:<[^>]*>)?\s+(?P<name>\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{', re.MULTILINE),
        'class': re.compile(r'(?:public|private|protected)?\s*(?:abstract)?\s*class\s+(\w+)', re.MULTILINE),
        'indent_based': False,
    },
    'C': {
        'function': re.compile(r'^\w[\w\s\*]+\s+(?P<name>\w+)\s*\([^)]*\)\s*\{', re.MULTILINE),
        'class': None,
        'indent_based': False,
    },
    'C++': {
        'function': re.compile(r'(?:[\w:]+\s+)?(?P<name>\w+)\s*\([^)]*\)\s*(?:const)?\s*(?:override)?\s*\{', re.MULTILINE),
        'class': re.compile(r'class\s+(\w+)', re.MULTILINE),
        'indent_based': False,
    },
    'C#': {
        'function': re.compile(r'(?:public|private|protected|internal|static|async|virtual|override|\s)+\s+\w+(?:<[^>]*>)?\s+(?P<name>\w+)\s*\([^)]*\)', re.MULTILINE),
        'class': re.compile(r'(?:public|private|protected|internal)?\s*(?:partial|abstract|sealed)?\s*class\s+(\w+)', re.MULTILINE),
        'indent_based': False,
    },
    'PHP': {
        'function': re.compile(r'(?:public|private|protected|static|\s)*function\s+(?P<name>\w+)\s*\([^)]*\)', re.MULTILINE),
        'class': re.compile(r'class\s+(\w+)', re.MULTILINE),
        'indent_based': False,
    },
    'Go': {
        'function': re.compile(r'func\s+(?:\([^)]*\)\s*)?(?P<name>\w+)\s*\([^)]*\)', re.MULTILINE),
        'class': None,
        'indent_based': False,
    },
    'Rust': {
        'function': re.compile(r'(?:pub\s+)?(?:async\s+)?fn\s+(?P<name>\w+)', re.MULTILINE),
        'class': re.compile(r'(?:pub\s+)?(?:struct|enum|trait)\s+(\w+)', re.MULTILINE),
        'indent_based': False,
    },
    'Kotlin': {
        'function': re.compile(r'(?:fun|suspend\s+fun)\s+(?P<name>\w+)\s*\(', re.MULTILINE),
        'class': re.compile(r'(?:class|object|interface)\s+(\w+)', re.MULTILINE),
        'indent_based': False,
    },
    'Lua': {
        'function': re.compile(r'(?:local\s+)?function\s+(?P<name>\w+)\s*\(|(?P<name2>\w+)\s*=\s*function\s*\(', re.MULTILINE),
        'class': None,
        'indent_based': False,
    },
}

# 重构建议库
REFACTOR_SUGGESTIONS = {
    'high_complexity': {
        'diagnosis': '圈复杂度过高',
        'causes': ['过多的条件分支', '嵌套的 if-else 链', '复杂的循环逻辑'],
        'suggestions': [
            '▸ 提取子函数：将复杂逻辑拆分为单一职责的小函数',
            '▸ 使用 Guard Clauses：提前 return 减少嵌套',
            '▸ 策略模式：用字典或类替代 switch/if-else 链',
        ]
    },
    'high_nesting': {
        'diagnosis': '嵌套层级过深',
        'causes': ['多层 if 嵌套', '回调地狱', '过度的 try-except'],
        'suggestions': [
            '▸ 提前返回：用 Guard Clauses 扁平化逻辑',
            '▸ 提取方法：将深层逻辑移到独立函数',
        ]
    },
    'high_coupling': {
        'diagnosis': '模块耦合度高',
        'causes': ['import 过多', '依赖关系复杂', '违反单一职责'],
        'suggestions': [
            '▸ 依赖注入：将依赖通过参数传入',
            '▸ 模块拆分：按功能领域拆分为独立模块',
        ]
    },
    'long_file': {
        'diagnosis': '文件过长',
        'causes': ['功能堆积', '缺乏模块化', 'God Class'],
        'suggestions': [
            '▸ 按职责拆分：一个文件一个核心职责',
            '▸ 分层架构：拆分为 Controller/Service/Repository',
        ]
    },
    'low_comment': {
        'diagnosis': '注释严重不足',
        'causes': ['赶进度忽略文档', '认为代码自解释'],
        'suggestions': [
            '▸ 添加模块 docstring：说明模块职责',
            '▸ 函数注释：说明参数、返回值、异常',
        ]
    },
}


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
    
    result = {'functions': [], 'classes': []}
    
    # 复杂度关键字模式
    complexity_keywords = re.compile(r'\b(if|else|elif|for|while|switch|case|catch|except|try|and|or|&&|\|\|)\b')
    
    # 提取函数
    func_pattern = extractor.get('function')
    if func_pattern:
        func_matches = list(func_pattern.finditer(content))
        
        for i, match in enumerate(func_matches):
            # 获取函数名（优先从命名捕获组获取）
            gd = match.groupdict()
            func_name = gd.get('name') or gd.get('name2') or gd.get('name3')
            if not func_name:
                # 回退到位置捕获组
                groups = [g for g in match.groups() if g and not g.isspace() and len(g) < 50]
                func_name = groups[0] if groups else 'unknown'
            if not func_name or func_name.strip() == '':
                continue
            
            start_pos = match.start()
            start_line = content[:start_pos].count('\n') + 1
            
            # 估算函数结束位置
            if extractor.get('indent_based'):
                # Python: 基于缩进
                indent_str = gd.get('indent', '') or ''
                indent = len(indent_str)
                end_line = start_line
                for j in range(start_line, min(start_line + 200, len(lines))):
                    line = lines[j] if j < len(lines) else ''
                    if line.strip() and not line.startswith(' ' * (indent + 1)) and j > start_line:
                        # 同级或更少缩进的非空行
                        if not line.strip().startswith('#'):
                            end_line = j
                            break
                else:
                    end_line = min(start_line + 100, len(lines))
            else:
                # 大括号语言：用大括号状态机精确定位函数结束位置
                # 设置扫描上界来平衡精度和性能
                if i + 1 < len(func_matches):
                    # 用下一个函数的位置作为扫描天花板
                    scan_end = func_matches[i + 1].start()
                else:
                    scan_end = len(content)
                
                brace_count = 0
                in_string = False
                string_char = None
                escaped = False
                end_line = content[:scan_end].count('\n') + 1  # 默认用扫描上界
                
                for char_idx in range(match.start(), scan_end):
                    char = content[char_idx]
                    
                    # 处理转义字符
                    if escaped:
                        escaped = False
                        continue
                    if char == '\\':
                        escaped = True
                        continue
                    
                    # 处理字符串（跳过字符串内的大括号）
                    if char in '"\'':
                        if not in_string:
                            in_string = True
                            string_char = char
                        elif char == string_char:
                            in_string = False
                            string_char = None
                        continue
                    
                    if in_string:
                        continue
                    
                    # 追踪大括号状态
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # 找到函数结束位置
                            end_line = content[:char_idx + 1].count('\n') + 1
                            break
            
            func_len = end_line - start_line
            func_body = '\n'.join(lines[start_line-1:end_line])
            
            # 计算函数内复杂度
            cc_matches = complexity_keywords.findall(func_body)
            func_cc = len(cc_matches) + 1
            
            # 计算最大嵌套（简化）
            max_indent = 0
            for line in lines[start_line-1:end_line]:
                if line.strip():
                    indent_level = (len(line) - len(line.lstrip())) // 4
                    max_indent = max(max_indent, indent_level)
            
            if func_len > 30 or func_cc > 10:  # 只记录可能有问题的函数
                result['functions'].append({
                    'name': func_name,
                    'line': start_line,
                    'length': func_len,
                    'complexity': func_cc,
                    'nesting': max_indent,
                })
    
    # 提取类
    class_pattern = extractor.get('class')
    if class_pattern:
        class_matches = list(class_pattern.finditer(content))
        for match in class_matches:
            groups = [g for g in match.groups() if g and not g.isspace()]
            class_name = groups[-1] if groups else 'unknown'
            start_line = content[:match.start()].count('\n') + 1
            result['classes'].append({
                'name': class_name,
                'line': start_line,
            })
    
    # 按复杂度排序
    result['functions'].sort(key=lambda x: x['complexity'], reverse=True)
    
    return result


def merge_line_ranges(line_nums):
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


def find_function_for_line(line_num, func_ranges):
    """根据行号查找所属函数名"""
    for func_name, start, end in func_ranges:
        if start <= line_num <= end:
            return func_name
    return None


def get_function_ranges(content):
    """获取文件中所有函数的行号范围"""
    lines = content.split('\n')
    func_pattern = re.compile(r'^(    )*def\s+(\w+)\s*\(', re.MULTILINE)
    func_matches = list(func_pattern.finditer(content))
    
    ranges = []
    for i, match in enumerate(func_matches):
        func_name = match.group(2)
        start_line = content[:match.start()].count('\n') + 1
        if i + 1 < len(func_matches):
            end_line = content[:func_matches[i+1].start()].count('\n')
        else:
            end_line = len(lines)
        ranges.append((func_name, start_line, end_line))
    return ranges


def scan_code_smells(file_path):
    """
    启发式扫描代码异味
    
    Args:
        file_path: 文件路径
        
    Returns:
        list: 检测到的代码异味列表 [(smell_name, count, line_samples)]
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
    except:
        return []
    
    smells = []
    
    # 获取函数范围（用于深度嵌套的函数定位）
    func_ranges = get_function_ranges(content)
    
    # 检测各种代码异味
    for smell_key, smell_info in CODE_SMELLS.items():
        # 跳过标记了 skip 的项或没有 pattern 的项
        if smell_info.get('skip') or not smell_info.get('pattern'):
            continue
        pattern = smell_info['pattern']
        matches = list(pattern.finditer(content))
        
        if matches:
            # 深度嵌套特殊处理：按函数分组并合并行号
            if smell_key == 'deep_nesting':
                all_line_nums = []
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    all_line_nums.append(line_num)
                
                # 按函数分组
                func_groups = {}
                global_lines = []
                for ln in all_line_nums:
                    func_name = find_function_for_line(ln, func_ranges)
                    if func_name:
                        func_groups.setdefault(func_name, []).append(ln)
                    else:
                        global_lines.append(ln)
                
                # 生成格式化的位置信息
                formatted_lines = []
                for func_name, func_lines in func_groups.items():
                    ranges = merge_line_ranges(func_lines)
                    formatted_lines.append(f"[{func_name}]{','.join(ranges[:2])}")
                if global_lines:
                    ranges = merge_line_ranges(global_lines)
                    formatted_lines.append(f"[global]{','.join(ranges[:2])}")
                
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
    
    # 检测长行
    long_lines = [(i+1, len(line)) for i, line in enumerate(lines) if len(line) > THRESHOLDS['long_line']]
    if long_lines:
        smells.append({
            'key': 'long_lines',
            'name': f'过长代码行 (>{THRESHOLDS["long_line"]}字符)',
            'count': len(long_lines),
            'lines': [ln for ln, _ in long_lines[:5]],
            'suggestion': '拆分或格式化',
        })
    
    # 检测函数长度
    func_pattern = re.compile(r'^(    )*def\s+(\w+)\s*\(', re.MULTILINE)
    func_matches = list(func_pattern.finditer(content))
    long_funcs = []
    for i, match in enumerate(func_matches):
        start_line = content[:match.start()].count('\n') + 1
        if i + 1 < len(func_matches):
            end_line = content[:func_matches[i+1].start()].count('\n')
        else:
            end_line = len(lines)
        func_len = end_line - start_line
        if func_len > THRESHOLDS['long_function']:
            long_funcs.append((match.group(2), start_line, func_len))
    
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
    
    # 代码异味扫描
    if include_smells:
        smells = scan_code_smells(stats['path'])
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