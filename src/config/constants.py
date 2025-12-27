"""
TypeLineas 配置常量

定义支持的语言、注释模式、复杂度计算规则等核心配置。
"""
import re

# 多行字符串标记
TRIPLE_DOUBLE = '"""'
TRIPLE_SINGLE = "'''"

# 语言定义: ext -> (name, single_comments, multi_start, multi_end, is_logic)
LANG_DEFINITIONS = {
    'py': ('Python', ['#'], [TRIPLE_DOUBLE, TRIPLE_SINGLE], [TRIPLE_DOUBLE, TRIPLE_SINGLE], True),
    'js': ('JavaScript', ['//'], ['/*'], ['*/'], True),
    'ts': ('TypeScript', ['//'], ['/*'], ['*/'], True),
    'jsx': ('React', ['//'], ['/*'], ['*/'], True),
    'tsx': ('React TS', ['//'], ['/*'], ['*/'], True),
    'java': ('Java', ['//'], ['/*'], ['*/'], True),
    'c': ('C', ['//'], ['/*'], ['*/'], True),
    'cpp': ('C++', ['//'], ['/*'], ['*/'], True),
    'h': ('C/C++ Header', ['//'], ['/*'], ['*/'], True),
    'hpp': ('C++ Header', ['//'], ['/*'], ['*/'], True),
    'cs': ('C#', ['//'], ['/*'], ['*/'], True),
    'go': ('Go', ['//'], ['/*'], ['*/'], True),
    'rs': ('Rust', ['//', '///', '//!'], ['/*'], ['*/'], True),  
    'kt': ('Kotlin', ['//'], ['/*'], ['*/'], True),
    'kts': ('Kotlin Script', ['//'], ['/*'], ['*/'], True),
    'rb': ('Ruby', ['#'], ['=begin'], ['=end'], True),
    'php': ('PHP', ['//', '#'], ['/*'], ['*/'], True),
    'lua': ('Lua', ['--'], ['--[['], [']]'], True),
    'html': ('HTML', [], ['<!--'], ['-->'], False),
    'css': ('CSS', [], ['/*'], ['*/'], False),
    'scss': ('SCSS', ['//'], ['/*'], ['*/'], False),
    'md': ('Markdown', [], ['<!--'], ['-->'], False),
    'sh': ('Shell', ['#'], [], [], False),
    'ps1': ('PowerShell', ['#'], ['<#'], ['#>'], False),
}

# 各语言的 import 语句匹配模式
IMPORT_PATTERNS = {
    'JavaScript': re.compile(r'^\s*(import|require|export.*from)\s+'),
    'TypeScript': re.compile(r'^\s*(import|require|export.*from)\s+'),
    'Java': re.compile(r'^\s*import\s+'),
    'C': re.compile(r'^\s*#include'),
    'C++': re.compile(r'^\s*#include'),
    'Go': re.compile(r'^\s*import\s+'),
    'Rust': re.compile(r'^\s*(use|mod|extern crate|pub use)\s+'),
    'Kotlin': re.compile(r'^\s*import\s+'),
    'Kotlin Script': re.compile(r'^\s*import\s+'),
    'PHP': re.compile(r'^\s*(require|include|use)\s+'),
}

# 圈复杂度关键字匹配
CC_PATTERNS = {
    'C-Family': re.compile(r'\b(if|else|for|while|switch|case|catch|try)\b|&&|\|\|'),
    'Go': re.compile(r'\b(if|else|for|select|case|default)\b|&&|\|\|'),
    'Rust': re.compile(r'\b(if|else|for|while|loop|match|None|Some|Err|Ok)\b|&&|\|\|'),
    'Lua': re.compile(r'\b(if|else|elseif|for|while|repeat)\b|\band\b|\bor\b'),
}

# 语言到语言家族的映射（用于复杂度计算）
LANG_FAMILY = {
    'JavaScript': 'C-Family', 'TypeScript': 'C-Family', 'React': 'C-Family', 'React TS': 'C-Family',
    'Java': 'C-Family', 'C': 'C-Family', 'C++': 'C-Family', 'C#': 'C-Family', 'PHP': 'C-Family',
    'Kotlin': 'C-Family', 'Kotlin Script': 'C-Family',  
    'Go': 'Go', 'Rust': 'Rust', 'Lua': 'Lua'
}

# HTML 中 script 标签匹配
# 匹配内联 JS：排除 src= 外链，排除 type="application/json" 等非 JS 类型
# 支持 type="module" 和 type="text/javascript"
SCRIPT_START = re.compile(
    r'<script\b'                                    # 标签开始
    r'(?![^>]*\bsrc\s*=)'                           # 负向预查：排除外链脚本
    r'(?![^>]*\btype\s*=\s*["\']?(?:'               # 负向预查：排除非 JS 类型
        r'application/(?:json|ld\+json)'            # JSON 数据
        r'|text/(?:template|html|x-template)'       # 模板类型  
        r'|importmap'                               # Import map
    r')["\']?[^>]*>)'
    r'[^>]*>',                                      # 匹配到 > 结束
    re.IGNORECASE
)
SCRIPT_END = re.compile(r'</script\s*>', re.IGNORECASE)

# 字符串字面量匹配（用于在计算复杂度时剔除字符串内容）
STRING_LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')

# 默认忽略的目录
DEFAULT_IGNORES = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', '.next', '.nuxt', 'migrations'}

# 豁免文件：这些是常见的包聚合文件，即使复杂度高也不标记
EXEMPT_FILES = {'__init__.py', 'index.js', 'index.ts', 'mod.rs', 'package.go'}
