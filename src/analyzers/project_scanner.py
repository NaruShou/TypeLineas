"""
项目扫描器
"""
import os
from collections import defaultdict
from src.config.constants import LANG_DEFINITIONS, DEFAULT_IGNORES
from src.analyzers.file_analyzer import analyze_file
from src.utils.gitignore import GitIgnore

class ProjectScanner:
    """负责扫描项目文件并收集统计信息"""
    
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.gitignore = GitIgnore(root_dir)
        self.stats = []
        self.summary = defaultdict(lambda: {
            'files': 0, 'total': 0, 'code': 0, 'comments': 0, 
            'imports': 0, 'boilerplate': 0, 'cc': 0
        })
        self.total_weighted_score = 0
        self.total_weight = 0

    def scan(self):
        """执行扫描"""
        import sys
        if os.path.isfile(self.root_dir):
            file = os.path.basename(self.root_dir)
            ext = file.split('.')[-1].lower() if '.' in file else ''
            if ext in LANG_DEFINITIONS:
                self._analyze_file(self.root_dir, ext)
            return self.stats, self.summary, self._calculate_project_score()

        target_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORES and not self.gitignore.is_ignored(os.path.join(root, d))]
            
            for file in files:
                if file in DEFAULT_IGNORES:
                    continue
                    
                full_path = os.path.join(root, file)
                if self.gitignore.is_ignored(full_path):
                    continue
                    
                ext = file.split('.')[-1].lower() if '.' in file else ''
                if ext in LANG_DEFINITIONS:
                    target_files.append((full_path, ext))
                    
        total = len(target_files)
        for i, (full_path, ext) in enumerate(target_files):
            percentage = int((i / total) * 100) if total > 0 else 100
            bar_len = 30
            filled_len = int(bar_len * i // total) if total > 0 else bar_len
            bar = '=' * filled_len + '-' * (bar_len - filled_len)
            
            short_path = os.path.relpath(full_path, self.root_dir)
            if len(short_path) > 40:
                short_path = '...' + short_path[-37:]
                
            sys.stdout.write(f"\r[{bar}] {percentage}% | {i}/{total} | {short_path}\033[K")
            sys.stdout.flush()
            self._analyze_file(full_path, ext)
            
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
                    
        return self.stats, self.summary, self._calculate_project_score()

    def _analyze_file(self, file_path, ext):
        """分析单个文件并更新统计"""
        # Pipeline 模式下不再需要传入详细的 lang_info
        f_stats = analyze_file(file_path)
        self.stats.append(f_stats)
        
        l_name = f_stats['lang']
        self.summary[l_name]['files'] += 1
        for k in ['total', 'code', 'comments', 'boilerplate']:
            self.summary[l_name][k] += f_stats[k]
        self.summary[l_name]['imports'] += f_stats['imports']
        self.summary[l_name]['cc'] += f_stats['complexity']
        
        if f_stats['coder_score'] >= 0 and not f_stats['is_exempt']:
            weight = f_stats['code']
            self.total_weighted_score += f_stats['coder_score'] * weight
            self.total_weight += weight

    def _calculate_project_score(self):
        """计算项目总体评分"""
        if self.total_weight > 0:
            return int(self.total_weighted_score / self.total_weight)
        return 0
