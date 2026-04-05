"""
TypeLineas 重构规则配置

包含启发式扫描所需的阈值、代码异味模式、语言提取器定义和重构建议库。
"""
import re

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
        'function': re.compile(r'(?:^|\s)\w[\w\s\*]+\s+(?P<name>\w+)\s*\([^)]*\)\s*\{', re.MULTILINE),
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
        'class': re.compile(r'type\s+(\w+)\s+struct', re.MULTILINE),
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
    'Swift': {
        'function': re.compile(r'(?:public|private|internal|fileprivate|open|override|\s)*func\s+(?P<name>\w+)\s*\(|<', re.MULTILINE),
        'class': re.compile(r'(?:public|private|internal|fileprivate|open|override|\s)*(?:class|struct|enum|actor|protocol)\s+(\w+)', re.MULTILINE),
        'indent_based': False,
    },
    'Ruby': {
        'function': re.compile(r'^(?P<indent> *)def\s+(?P<name>\w+)(?:[\s\(]|$)', re.MULTILINE),
        'class': re.compile(r'^( *)class\s+(\w+)', re.MULTILINE),
        'indent_based': True,
        'name_group': 'name',
    },
    'Dart': {
        'function': re.compile(r'(?:[\w<>]*\s+)?(?P<name>\w+)\s*\([^)]*\)\s*(?:async)?\s*\{', re.MULTILINE),
        'class': re.compile(r'(?:abstract\s+)?class\s+(\w+)', re.MULTILINE),
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
