"""
TypeLineas - 多语言代码质量分析工具

一个轻量级的代码复杂度分析器，支持多种编程语言。
计算圈复杂度 (Cyclomatic Complexity)、代码行数、注释比例等指标，
并生成 Shit Score 和 Coder Score 评分。

Usage:
    python -m src <directory>           # 开发模式
    python TypeLineas.py <directory>    # 单文件模式
    python TypeLineas.py . --report     # 生成报告
"""
