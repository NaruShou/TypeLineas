"""
国际化支持模块

根据环境自动选择中文或英文显示。
"""
import locale
import os

# 检测语言环境
def get_language():
    """检测系统语言，返回 'zh' 或 'en'"""
    # 优先检查环境变量
    lang = os.environ.get('TYPELINEAS_LANG', '').lower()
    if lang in ('zh', 'cn', 'chinese'):
        return 'zh'
    if lang in ('en', 'english'):
        return 'en'
    
    # 检测系统 locale
    try:
        # 尝试新的 API
        system_lang = locale.getlocale()[0] or ''
        if not system_lang:
            # Windows 回退
            system_lang = os.environ.get('LANG', '') or os.environ.get('LC_ALL', '')
        if 'zh' in system_lang.lower() or 'chinese' in system_lang.lower():
            return 'zh'
    except:
        pass
    
    return 'en'


CURRENT_LANG = get_language()


# 文本资源
TEXTS = {
    # 通用
    'scanning': {'zh': '扫描中', 'en': 'Scanning'},
    'engine': {'zh': '引擎', 'en': 'Engine'},
    'quality_metric': {'zh': '质量指标', 'en': 'Quality Metric'},
    'total': {'zh': '合计', 'en': 'TOTAL'},
    'project_coder_index': {'zh': '项目代码质量指数', 'en': 'Project Coder Index'},
    'total_lines': {'zh': '总行数', 'en': 'Total Lines'},
    'boilerplate': {'zh': '样板代码', 'en': 'Boilerplate'},
    
    # 表头
    'language': {'zh': '语言', 'en': 'Language'},
    'files': {'zh': '文件数', 'en': 'Files'},
    'lines': {'zh': '行数', 'en': 'Lines'},
    'code': {'zh': '代码', 'en': 'Code'},
    'comments': {'zh': '注释', 'en': 'Comments'},
    'coupling': {'zh': '耦合度', 'en': 'Coupling'},
    'avg_cc': {'zh': '平均CC', 'en': 'Avg-CC'},
    'file_path': {'zh': '文件路径', 'en': 'File Path'},
    'shit_score': {'zh': 'Shit分数', 'en': 'Shit Score'},
    'coder_score': {'zh': 'Coder分数', 'en': 'Coder Score'},
    'complexity': {'zh': '复杂度', 'en': 'Complexity'},
    'imports': {'zh': '导入数', 'en': 'Imports'},
    
    # 评级
    'legendary': {'zh': '传奇 🏆', 'en': 'LEGENDARY 🏆'},
    'solid': {'zh': '稳健 💎', 'en': 'SOLID 💎'},
    'average': {'zh': '一般 🚧', 'en': 'AVERAGE 🚧'},
    'shaky': {'zh': '脆弱 🏚️', 'en': 'SHAKY 🏚️'},
    'toxic': {'zh': '有毒 ☢️', 'en': 'TOXIC ☢️'},
    
    # 区块标题
    'top_shit_mountains': {'zh': '🏔️ TOP 10 屎山 (逻辑复杂度)', 'en': '🏔️ TOP 10 SHIT MOUNTAINS (Logic Complexity)'},
    'refactor_advisor': {'zh': '🔧 重构建议 (启发式扫描)', 'en': '🔧 REFACTOR ADVISOR (Heuristic Scan)'},
    'exempted_aggregators': {'zh': '🛡️ 豁免的聚合文件 (高复杂度但允许)', 'en': '🛡️ EXEMPTED AGGREGATORS (High Complexity but Allowed)'},
    'report_exported': {'zh': '报告已导出到', 'en': 'Report exported to'},
    'report_failed': {'zh': '报告导出失败', 'en': 'Failed to export report'},
    
    # 诊断
    'high_complexity': {'zh': '圈复杂度过高', 'en': 'High Cyclomatic Complexity'},
    'high_nesting': {'zh': '嵌套层级过深', 'en': 'Deep Nesting'},
    'high_coupling': {'zh': '模块耦合度高', 'en': 'High Module Coupling'},
    'long_file': {'zh': '文件过长', 'en': 'Long File'},
    'low_comment': {'zh': '注释严重不足', 'en': 'Insufficient Comments'},
    
    # 建议
    'extract_functions': {'zh': '提取子函数：将复杂逻辑拆分为单一职责的小函数', 'en': 'Extract sub-functions: Split complex logic into single-responsibility functions'},
    'guard_clauses': {'zh': '使用 Guard Clauses：提前 return 减少嵌套', 'en': 'Use Guard Clauses: Early returns to reduce nesting'},
    'strategy_pattern': {'zh': '策略模式：用字典或类替代 switch/if-else 链', 'en': 'Strategy Pattern: Use dict or classes instead of switch/if-else chains'},
    'dependency_injection': {'zh': '依赖注入：将依赖通过参数传入', 'en': 'Dependency Injection: Pass dependencies as parameters'},
    'split_by_responsibility': {'zh': '按职责拆分：一个文件一个核心职责', 'en': 'Split by Responsibility: One core responsibility per file'},
    'add_docstrings': {'zh': '添加模块 docstring：说明模块职责', 'en': 'Add module docstring: Describe module purpose'},
    
    # 代码异味
    'god_function': {'zh': 'God Function', 'en': 'God Function'},
    'deep_nesting': {'zh': '深度嵌套', 'en': 'Deep Nesting'},
    'magic_number': {'zh': '魔法数字', 'en': 'Magic Number'},
    'long_param_list': {'zh': '过长参数列表', 'en': 'Long Parameter List'},
    'duplicate_string': {'zh': '重复字符串', 'en': 'Duplicate String'},
    'print_debug': {'zh': '调试代码残留', 'en': 'Debug Code Residue'},
    'todo_fixme': {'zh': '未完成标记', 'en': 'TODO/FIXME Marker'},
    'bare_except': {'zh': '裸 except', 'en': 'Bare Except'},
    'hardcoded_path': {'zh': '硬编码路径', 'en': 'Hardcoded Path'},
    'commented_code': {'zh': '注释掉的代码', 'en': 'Commented Code'},
    'long_lines': {'zh': '过长代码行', 'en': 'Long Code Lines'},
    'long_function': {'zh': '过长函数', 'en': 'Long Function'},
    
    # 报告
    'code_quality_report': {'zh': '代码质量报告', 'en': 'Code Quality Report'},
    'generated_by': {'zh': '由 TypeLineas 生成', 'en': 'Generated by TypeLineas'},
    'file_analysis': {'zh': '文件分析', 'en': 'File Analysis'},
    'problem_diagnosis': {'zh': '问题诊断', 'en': 'Problem Diagnosis'},
    'complexity_hotspots': {'zh': '复杂度热点函数', 'en': 'Complexity Hotspot Functions'},
    'code_smells': {'zh': '代码异味', 'en': 'Code Smells'},
    'function_name': {'zh': '函数名', 'en': 'Function'},
    'line_no': {'zh': '行号', 'en': 'Line'},
    'nesting': {'zh': '嵌套', 'en': 'Nesting'},
    
    # 异味建议
    'extract_constant': {'zh': '提取为命名常量', 'en': 'Extract as named constant'},
    'use_data_class': {'zh': '考虑使用数据类或字典封装', 'en': 'Consider using data class or dict'},
    'remove_or_log': {'zh': '移除或替换为正式日志', 'en': 'Remove or replace with proper logging'},
    'create_issue': {'zh': '处理或创建 issue 跟踪', 'en': 'Handle or create tracking issue'},
    'specify_exception': {'zh': '明确捕获特定异常类型', 'en': 'Catch specific exception types'},
    'use_config': {'zh': '使用配置文件或环境变量', 'en': 'Use config file or environment variable'},
    'delete_or_vcs': {'zh': '删除或使用版本控制', 'en': 'Delete or use version control'},
    'split_or_format': {'zh': '拆分或格式化', 'en': 'Split or format'},
    'split_to_functions': {'zh': '拆分为多个小函数', 'en': 'Split into smaller functions'},
}


def t(key):
    """获取本地化文本"""
    text = TEXTS.get(key, {})
    return text.get(CURRENT_LANG, text.get('en', key))


def set_language(lang):
    """设置语言"""
    global CURRENT_LANG
    CURRENT_LANG = lang if lang in ('zh', 'en') else 'en'
