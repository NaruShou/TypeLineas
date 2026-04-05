"""
分析上下文
"""
import os
from src.config.constants import EXEMPT_FILES

class AnalysisContext:
    """保存文件分析的上下文信息"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.lang_name = None
        self.content = ""
        self.lines = []
        self.stats = {
            'path': file_path, 
            'lang': 'Unknown', 
            'is_logic': False,
            'total': 0, 
            'code': 0, 
            'comments': 0, 
            'boilerplate': 0,
            'imports': 0, 
            'max_nesting': 0, 
            'shit_score': 0, 
            'coder_score': -1,
            'logic_lines': 0, 
            'complexity': 0, 
            'ast_success': False,
            'is_exempt': False
        }
        
        # 检查是否豁免
        if os.path.basename(file_path) in EXEMPT_FILES:
            self.stats['is_exempt'] = True
