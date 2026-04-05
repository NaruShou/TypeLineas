"""
分析管道基类
"""

class BasePipe:
    """管道处理单元基类"""
    
    def process(self, context):
        """
        处理上下文
        Args:
            context: AnalysisContext 对象
        """
        raise NotImplementedError
