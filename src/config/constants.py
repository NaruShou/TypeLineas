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
    'swift': ('Swift', ['//'], ['/*'], ['*/'], True),
    'm': ('Objective-C', ['//'], ['/*'], ['*/'], True),
    'mm': ('Objective-C++', ['//'], ['/*'], ['*/'], True),
    'scala': ('Scala', ['//'], ['/*'], ['*/'], True),
    'sc': ('Scala', ['//'], ['/*'], ['*/'], True),
    'dart': ('Dart', ['//', '///'], ['/*'], ['*/'], True),
    'r': ('R', ['#'], [], [], True),
    'pl': ('Perl', ['#'], ['='], ['=cut'], True),
    'pm': ('Perl', ['#'], ['='], ['=cut'], True),
    'sql': ('SQL', ['--'], ['/*'], ['*/'], True),
    'vue': ('Vue', ['//', '<!--'], ['/*'], ['*/', '-->'], True),
    'svelte': ('Svelte', ['//', '<!--'], ['/*'], ['*/', '-->'], True),
    'yaml': ('YAML', ['#'], [], [], False),
    'yml': ('YAML', ['#'], [], [], False),
    'toml': ('TOML', ['#'], [], [], False),
    'json': ('JSON', [], [], [], False),
    'xml': ('XML', [], ['<!--'], ['-->'], False),
    'graphql': ('GraphQL', ['#'], [], [], False),
    'gql': ('GraphQL', ['#'], [], [], False),
    'hs': ('Haskell', ['--'], ['{-'], ['-}'], True),
    'erl': ('Erlang', ['%'], [], [], True),
    'hrl': ('Erlang Header', ['%'], [], [], True),
    'ex': ('Elixir', ['#'], [], [], True),
    'exs': ('Elixir Script', ['#'], [], [], True),
    'clj': ('Clojure', [';'], [], [], True),
    'cljs': ('ClojureScript', [';'], [], [], True),
    'cljc': ('Clojure Common', [';'], [], [], True),
    'fs': ('F#', ['//'], ['(*'], ['*)'], True),
    'fsi': ('F# Signature', ['//'], ['(*'], ['*)'], True),
    'fsx': ('F# Script', ['//'], ['(*'], ['*)'], True),
    'jl': ('Julia', ['#'], ['#='], ['=#'], True),
    'vbs': ('VBScript', ["'", 'REM '], [], [], True),
    'vb': ('VB.NET', ["'", 'REM '], [], [], True),
    'asm': ('Assembly', [';', '#', '//'], ['/*'], ['*/'], True),
    's': ('Assembly', [';', '#', '//'], ['/*'], ['*/'], True),
    'dockerfile': ('Dockerfile', ['#'], [], [], False),
    'mk': ('Makefile', ['#'], [], [], False),
    'zig': ('Zig', ['//'], [], [], True),
    'nim': ('Nim', ['#'], ['#['], [']#'], True),
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
    'Swift': re.compile(r'^\s*import\s+'),
    'Objective-C': re.compile(r'^\s*#(import|include)\s+'),
    'Objective-C++': re.compile(r'^\s*#(import|include)\s+'),
    'Scala': re.compile(r'^\s*import\s+'),
    'Dart': re.compile(r'^\s*import\s+'),
    'R': re.compile(r'^\s*(library|require)\s*\('),
    'Perl': re.compile(r'^\s*(use|require)\s+'),
    'Vue': re.compile(r'^\s*(import|require|export.*from)\s+'),
    'Svelte': re.compile(r'^\s*(import|require|export.*from)\s+'),
    'Haskell': re.compile(r'^\s*import\s+'),
    'Elixir': re.compile(r'^\s*(import|require|use|alias)\s+'),
    'Clojure': re.compile(r'^\s*\(\s*(require|use)\s+'),
    'F#': re.compile(r'^\s*open\s+'),
    'Julia': re.compile(r'^\s*(using|import)\s+'),
    'Zig': re.compile(r'^\s*const\s+\w+\s*=\s*@import\s*\('),
    'Nim': re.compile(r'^\s*import\s+'),
}

# 圈复杂度关键字匹配
CC_PATTERNS = {
    'C-Family': re.compile(r'\b(if|else|for|while|switch|case|catch|try)\b|&&|\|\|'),
    'Java': re.compile(
        r'\b(if|else|for|while|switch|case|catch|try|throw|do|instanceof|finally)\b'
        r'|&&|\|\|'
    ),
    'Go': re.compile(r'\b(if|else|for|select|case|default)\b|&&|\|\|'),
    'Rust': re.compile(r'\b(if|else|for|while|loop|match|None|Some|Err|Ok)\b|&&|\|\|'),
    'Lua': re.compile(r'\b(if|else|elseif|for|while|repeat)\b|\band\b|\bor\b'),
    'Swift': re.compile(r'\b(if|else|for|while|switch|case|catch|try|guard|defer)\b|&&|\|\|'),
    'Ruby': re.compile(r'\b(if|else|elsif|unless|for|while|until|case|when|rescue|ensure)\b|\band\b|\bor\b'),
    'Python-Regex': re.compile(r'\b(if|elif|else|for|while|try|except|finally|with|match|case)\b|\band\b|\bor\b'),
    'SQL': re.compile(r'\b(IF|ELSE|ELSEIF|WHILE|CASE|WHEN|THEN|CATCH)\b|(AND|OR)\b', re.IGNORECASE),
}

# 语言到语言家族的映射（用于复杂度计算）
LANG_FAMILY = {
    'JavaScript': 'C-Family', 'TypeScript': 'C-Family', 'React': 'C-Family', 'React TS': 'C-Family',
    'Java': 'Java', 'C': 'C-Family', 'C++': 'C-Family', 'C#': 'C-Family', 'PHP': 'C-Family',
    'Kotlin': 'C-Family', 'Kotlin Script': 'C-Family', 'Objective-C': 'C-Family', 'Objective-C++': 'C-Family',
    'Scala': 'C-Family', 'Dart': 'C-Family', 'Vue': 'C-Family', 'Svelte': 'C-Family',
    'Go': 'Go', 'Rust': 'Rust', 'Lua': 'Lua',
    'Swift': 'Swift', 'Ruby': 'Ruby', 'Python': 'Python-Regex', 'SQL': 'SQL'
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
DEFAULT_IGNORES = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', '.next', '.nuxt', 'migrations', '.gitignore', '.gitkeep'}

# 豁免文件：这些是常见的包聚合文件，即使复杂度高也不标记
EXEMPT_FILES = {'__init__.py', 'index.js', 'index.ts', 'mod.rs', 'package.go', 'Package.swift', 'Cargo.toml', 'pubspec.yaml', 'package.json'}

# Java 样板代码识别模式（用于准确区分逻辑代码和机械代码）
JAVA_BOILERPLATE_PATTERNS = {
    # package 声明
    'package': re.compile(r'^\s*package\s+[\w.]+;'),
    # Lombok 注解（标记属性的常见场景，生成 getter/setter/constructor 等）
    'lombok': re.compile(r'^\s*@(Data|Getter|Setter|Builder|ToString|EqualsAndHashCode|NoArgsConstructor|AllArgsConstructor|RequiredArgsConstructor|Value|Slf4j|Log4j2|Log)\b'),
    # 标准 getter 单行体: return this.field;
    'getter': re.compile(r'^\s*public\s+\w+(?:<[^>]*>)?\s+(?:is|get)\w+\s*\(\s*\)\s*\{\s*return\s+(?:this\.)?\w+;\s*\}\s*$'),
    # 标准 setter 单行体: this.field = field;
    'setter': re.compile(r'^\s*public\s+void\s+set\w+\s*\(\s*\w+(?:<[^>]*>)?\s+\w+\s*\)\s*\{\s*this\.\w+\s*=\s*\w+;\s*\}\s*$'),
    # 空方法体 / 占位实现
    'empty_method': re.compile(r'^\s*(?:public|private|protected)?\s*(?:static|final|synchronized|abstract)?\s*(?:\w+(?:<[^>]*>)?\s+)?\w+\s*\([^)]*\)\s*\{\s*\}'),
    # 接口默认方法桩（default void foo() {} 且方法体空）
    'default_stub': re.compile(r'^\s*default\s+\w+(?:<[^>]*>)?\s+\w+\s*\([^)]*\)\s*\{\s*\}'),
    # @Override 仅注解行
    'override_annotation': re.compile(r'^\s*@Override\s*$'),
    # 序列化版本 ID
    'serial_version': re.compile(r'^\s*(?:private|public|protected)?\s*static\s+final\s+long\s+serialVersionUID\s*='),
    # 纯括号行（大括号/分号单独一行）
    'bare_brace_semicolon': re.compile(r'^\s*[{};]\s*$'),
}
