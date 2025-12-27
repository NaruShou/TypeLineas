# TypeLineas 📊

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🔍 **代码质量分析工具** - 快速识别代码中的"屎山"(Shit Mountains)，提供多语言复杂度分析和重构建议。

<p align="center">
  <img src="https://img.shields.io/badge/Languages-12+-green.svg" alt="Languages"/>
  <img src="https://img.shields.io/badge/AST-Powered-orange.svg" alt="AST"/>
  <img src="https://img.shields.io/badge/i18n-中文%2FEnglish-purple.svg" alt="i18n"/>
</p>

## ✨ Features

- 🏔️ **屎山检测** - 基于圈复杂度(CC)、嵌套深度、耦合度等指标识别问题代码
- 🔥 **热点函数定位** - 精确到函数级别的复杂度分析，直接告诉你哪个函数最需要重构
- 🧪 **12+ 语言支持** - Python, JavaScript, TypeScript, Java, C/C++, C#, PHP, Go, Rust, Kotlin, Lua...
- 🔧 **智能重构建议** - 启发式代码异味检测 + 针对性重构建议
- 🌍 **中英双语** - 自动检测系统语言，终端和报告全本地化
- 📊 **多格式报告** - Markdown / CSV 导出

## 🚀 Quick Start

```bash
# 分析当前目录
python -m src .

# 分析指定目录 + 导出报告
python -m src /path/to/project --report

# 带重构建议
python -m src . --advice --report report.md
```

## 📖 Output Example

```
扫描中: ./my-project
引擎: Polyglot CC (AST + Regex) | 质量指标: 项目代码质量指数
--------------------------------------------------------------------------------
语言         文件数   行数       代码       注释       耦合度     平均CC
Python       51       5562       3652       776        584        8.1
JavaScript   9        2274       1792       78         0          12.6
--------------------------------------------------------------------------------
合计         88       11203      8041       976        584        -
--------------------------------------------------------------------------------
项目代码质量指数: 89 / 100 (稳健 💎)
总行数: 11203 | 样板代码: 19.5%

=== 🏔️ TOP 10 屎山 (逻辑复杂度) ===
Score    Coder  Comp.  Imp.   行数       文件路径
----------------------------------------
148      11     AST:97   7      429      routers/oauth.py
70       66     AST:49   10     223      analyzers/file_analyzer.py
```

## 🔧 Refactor Advisor

使用 `--advice` 参数获取详细的重构建议：

```
=== 🔧 重构建议 (启发式扫描) ===

📄 routers/oauth.py (Shit分数: 148)
  ■ 🔴 圈复杂度过高 (值: 97)
    ▸ 提取子函数：将复杂逻辑拆分为单一职责的小函数
    ▸ 使用 Guard Clauses：提前 return 减少嵌套

  ▼ 复杂度热点函数:
    🔥 auth_github_callback() [L328] CC=23, 119行, 嵌套4层
    🔥 handle_oauth_flow() [L156] CC=18, 87行, 嵌套5层

  ▼ 代码异味检测:
    ⚠ God Function × 3 [L156, L328, L412]
    ⚠ 深度嵌套 × 45 [L178, L203, L356...]
    ⚠ 魔法数字 × 12 [L89, L234...] → 提取为命名常量
```

## 📦 Installation

```bash
git clone https://github.com/yourname/TypeLineas.git
cd TypeLineas
python -m src .  # 运行！
```

无需安装依赖，纯标准库实现。

## 🌐 Language Switch

```bash
# 强制英文
export TYPELINEAS_LANG=en
python -m src .

# 强制中文
export TYPELINEAS_LANG=zh
```

## 📄 License

MIT License

---

**如果这个工具帮到你了，请给个 Star 🌟**
