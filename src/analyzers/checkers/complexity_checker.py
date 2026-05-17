"""
复杂度检查器
"""
from src.config.constants import CC_PATTERNS, LANG_FAMILY

class ComplexityChecker:
    """负责分析代码复杂度"""

    def check(self, content, lines, extractor, lang_name='Python'):
        """分析内容中的函数和类复杂度"""
        result = {'functions': [], 'classes': []}
        
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
                
                # 确定结束行
                next_start = func_matches[i+1].start() if i + 1 < len(func_matches) else None
                end_line = self._find_function_end(lines, start_line, extractor, match, content, next_start)
                
                func_len = end_line - start_line
                func_cc, max_indent = self._calculate_func_metrics(lines, start_line, end_line, lang_name)
                
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

    def _find_function_end(self, lines, start_line, extractor, match, content, next_match_start):
        """查找函数结束行"""
        if extractor.get('indent_based'):
            gd = match.groupdict()
            indent_str = gd.get('indent', '') or ''
            indent = len(indent_str)
            
            for j in range(start_line, min(start_line + 200, len(lines))):
                line = lines[j] if j < len(lines) else ''
                if line.strip() and not line.startswith(' ' * (indent + 1)) and j > start_line:
                    if not line.strip().startswith('#'):
                        return j
            return min(start_line + 100, len(lines))
        
        # 大括号语言处理（含 Java C/C++ C# Go Rust Kotlin Swift 等）
        scan_end = next_match_start if next_match_start else len(content)
        brace_count = 0
        in_string = False
        string_char = None
        escaped = False
        in_line_comment = False   # 单行注释 //
        in_block_comment = False   # 多行注释 /* */
        
        for char_idx in range(match.start(), scan_end):
            if char_idx >= len(content):
                break
            char = content[char_idx]
            next_char = content[char_idx + 1] if char_idx + 1 < len(content) else ''
            
            # 字符串转义处理
            if escaped:
                escaped = False
                continue
            if char == '\\' and (in_string or in_line_comment or in_block_comment):
                # 仅在字符串/注释中处理转义
                pass
            elif char == '\\' and in_string:
                escaped = True
                continue
            
            # 注释结束检测（先于其他处理，确保 /* */ 内的一切被忽略）
            if in_block_comment:
                if char == '*' and next_char == '/':
                    in_block_comment = False
                    # 跳过 '/' 字符，下一轮循环处理
                    continue
                continue
            
            # 单行注释行尾重置（由外层的换行遍历保证，此处防止 \n 处继续）
            if in_line_comment and char == '\n':
                in_line_comment = False
                continue
            if in_line_comment:
                continue
            
            # 注释开始检测
            if not in_string:
                if char == '/' and next_char == '/':
                    in_line_comment = True
                    continue
                if char == '/' and next_char == '*':
                    in_block_comment = True
                    continue
            
            # 字符串字面量检测
            if char in '"\'' and not in_line_comment and not in_block_comment:
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
                continue
            if in_string:
                continue
            
            # 花括号计数
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[:char_idx + 1].count('\n') + 1
                    
        return content[:scan_end].count('\n') + 1

    def _calculate_func_metrics(self, lines, start_line, end_line, lang_name):
        """计算函数复杂度和嵌套深度"""
        func_body = '\n'.join(lines[start_line-1:end_line])
        
        family = LANG_FAMILY.get(lang_name)
        pattern = CC_PATTERNS.get(family)
        if pattern:
            cc_matches = pattern.findall(func_body)
            func_cc = len(cc_matches) + 1
        else:
            func_cc = 1
        
        max_indent = 0
        for line in lines[start_line-1:end_line]:
            if line.strip():
                indent_level = (len(line) - len(line.lstrip())) // 4
                max_indent = max(max_indent, indent_level)
                
        return func_cc, max_indent
