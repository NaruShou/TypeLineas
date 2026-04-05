"""
多语言文件分析器 (Pipeline Version)

对各种编程语言文件进行复杂度分析，计算代码行数、注释行数、
嵌套深度、import 耦合度等指标，并生成质量评分。
"""
from src.analyzers.pipeline.runner import PipelineRunner

def analyze_file(file_path, lang_info=None):
    """分析单个文件的各项指标"""
    # lang_info 参数保留是为了兼容旧调用，但在 Pipeline 模式下不再需要
    runner = PipelineRunner()
    return runner.run(file_path)
