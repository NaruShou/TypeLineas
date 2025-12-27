#!/usr/bin/env python3
"""
TypeLineas 构建脚本
将 src/ 下的模块合并为单文件 dist/TypeLineas.py
"""
import os
import re
from pathlib import Path

# 按依赖顺序排列的模块文件
MODULE_ORDER = [
    'src/config/colors.py',
    'src/config/i18n.py',
    'src/config/constants.py',
    'src/analyzers/python_ast.py',
    'src/analyzers/file_analyzer.py',
    'src/analyzers/refactor_advisor.py',
    'src/reporters/exporter.py',
    'src/__main__.py',
]

# 需要保留的标准库 import（放在文件头部）
STDLIB_IMPORTS = """import os
import re
import sys
import ast
import csv
import locale
import unicodedata
from collections import defaultdict
"""

# 匹配 src 内部 import 的模式（包括多行 from ... import (...)）
INTERNAL_IMPORT_PATTERN = re.compile(
    r'^from src\.[\w.]+\s+import\s+\([\s\S]*?\)|'  # 多行 from src.xx import (...)
    r'^from src\.[\w.]+\s+import\s+[^(].*$|'       # 单行 from src.xx import xxx
    r'^import src\..*$',                            # import src.xxx
    re.MULTILINE
)

# 匹配标准库 import（用于移除，因为统一放在头部）
STDLIB_PATTERN = re.compile(r'^(import (os|re|sys|ast|csv|locale|unicodedata)|from collections import).*$', re.MULTILINE)


def read_module(filepath):
    """读取模块文件内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def strip_imports(content):
    """移除内部和标准库 import 语句"""
    # 移除 src 内部 import
    content = INTERNAL_IMPORT_PATTERN.sub('', content)
    # 移除标准库 import（后面统一添加）
    content = STDLIB_PATTERN.sub('', content)
    return content


def strip_main_guard(content):
    """移除 __main__ 入口判断（只保留 main 函数定义）"""
    # 移除 if __name__ == "__main__": main() 部分
    content = re.sub(r'\nif __name__ == ["\']__main__["\']:\s*\n\s*main\(\)\s*$', '', content)
    return content


def clean_content(content):
    """清理多余空行"""
    # 将连续3个以上空行合并为2个
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    return content.strip()


def build():
    """执行构建"""
    project_root = Path(__file__).parent
    dist_dir = project_root / 'dist'
    dist_dir.mkdir(exist_ok=True)
    output_file = dist_dir / 'TypeLineas.py'
    
    print("Building TypeLineas...")
    
    parts = [STDLIB_IMPORTS]
    
    for module_path in MODULE_ORDER:
        full_path = project_root / module_path
        if not full_path.exists():
            print(f"  [WARN] Module not found: {module_path}")
            continue
        
        print(f"  Processing: {module_path}")
        content = read_module(full_path)
        content = strip_imports(content)
        content = strip_main_guard(content)
        content = clean_content(content)
        
        if content:
            # 添加模块分隔注释
            module_name = module_path.replace('src/', '').replace('.py', '').replace('/', '.')
            parts.append(f"\n# === {module_name} ===\n")
            parts.append(content)
    
    # 添加入口
    parts.append('\n\nif __name__ == "__main__":\n    main()\n')
    
    final_content = '\n'.join(parts)
    final_content = clean_content(final_content) + '\n'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"\nBuild complete: {output_file}")
    print(f"Output size: {os.path.getsize(output_file)} bytes")


if __name__ == "__main__":
    build()
