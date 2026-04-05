"""
命令行参数解析器
"""
import sys
import os

class ArgsParser:
    """负责解析命令行参数"""
    
    @staticmethod
    def parse():
        """
        解析命令行参数
        
        Returns:
            dict: 包含解析后的参数配置
            - root_dir: 扫描根目录
            - show_all: 是否显示所有文件
            - show_advice: 是否显示重构建议
            - report_file: 报告文件名 (None, "AUTO", or specific path)
        """
        raw_args = sys.argv[1:]
        config = {
            'show_all': False,
            'show_advice': False,
            'report_file': None,
            'root_dir': os.getcwd()
        }
        
        if "--all" in raw_args:
            config['show_all'] = True
            raw_args.remove("--all")
        
        if "--advice" in raw_args:
            config['show_advice'] = True
            raw_args.remove("--advice")
            
        if "--report" in raw_args:
            idx = raw_args.index("--report")
            if idx + 1 < len(raw_args) and not raw_args[idx+1].startswith("-"):
                config['report_file'] = raw_args[idx+1]
                raw_args.pop(idx)
                raw_args.pop(idx)
            else:
                config['report_file'] = "AUTO"
                raw_args.pop(idx)
                
        if raw_args:
            config['root_dir'] = raw_args[0]
            
        # 自动生成报告文件名
        if config['report_file'] == "AUTO":
            project_name = os.path.basename(os.path.abspath(config['root_dir']))
            config['report_file'] = f"{project_name}_report.md"
            
        return config
