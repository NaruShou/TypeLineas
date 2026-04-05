"""
管道运行器
"""
from .context import AnalysisContext
from .stages import ReaderStage, LanguageStage, ASTStage, ScannerStage, ScoringStage

class PipelineRunner:
    """负责按顺序执行分析管道"""
    
    def __init__(self):
        self.stages = [
            ReaderStage(),
            LanguageStage(),
            ASTStage(),
            ScannerStage(),
            ScoringStage()
        ]

    def run(self, file_path):
        """
        运行分析管道
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 分析结果统计
        """
        context = AnalysisContext(file_path)
        
        # 按顺序执行各阶段
        for stage in self.stages:
            stage.process(context)
            
        return context.stats
