"""
TypeLineas 主程序入口

命令行参数解析和分析流程控制。

Usage:
    python -m src <directory> [--all] [--report [filename]] [--advice]
"""
from src.utils.args_parser import ArgsParser
from src.analyzers.project_scanner import ProjectScanner
from src.reporters.console_reporter import ConsoleReporter
from src.reporters.exporter import export_report
from src.analyzers.refactor_advisor import print_refactor_advice

def main():
    # 解析参数
    config = ArgsParser.parse()
    
    # 初始化组件
    scanner = ProjectScanner(config['root_dir'])
    reporter = ConsoleReporter(config['root_dir'])
    
    # 打印头部
    reporter.print_header(show_all=config['show_all'])
    
    # 执行扫描
    all_file_stats, summary, project_score = scanner.scan()
    
    # 打印汇总报告
    reporter.print_summary(summary, project_score)
    
    # 打印 Top 问题文件
    top_shit = reporter.print_top_shit(all_file_stats, show_all=config['show_all'])
    
    # 导出报告文件
    if config['report_file']:
        export_report(
            all_stats=all_file_stats, 
            filename=config['report_file'], 
            root_dir=config['root_dir'], 
            include_advice=config['show_advice']
        )
    
    # 打印重构建议
    if config['show_advice']:
        print_refactor_advice(top_shit, config['root_dir'])

if __name__ == "__main__":
    main()
