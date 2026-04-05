"""
Gitignore 解析工具模块

提供对 .gitignore 文件的解析和路径匹配功能。
"""
import os
import fnmatch

class GitIgnore:
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)
        self.patterns = []
        self._load_gitignore()

    def _load_gitignore(self):
        gitignore_path = os.path.join(self.root_dir, '.gitignore')
        if not os.path.exists(gitignore_path):
            return

        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                self.patterns.append(line)

    def is_ignored(self, path):
        """
        判断路径是否被忽略
        
        Args:
            path: 绝对路径或相对于 root_dir 的路径
        """
        if not self.patterns:
            return False

        # 转换为相对于 root 的路径，统一使用 forward slash
        if os.path.isabs(path):
            rel_path = os.path.relpath(path, self.root_dir)
        else:
            rel_path = path

        rel_path = rel_path.replace(os.sep, '/')
        path_segments = rel_path.split('/')
        basename = os.path.basename(rel_path)
        
        ignored = False
        
        for pattern in self.patterns:
            orig_pattern = pattern
            negative = False
            if pattern.startswith('!'):
                negative = True
                pattern = pattern[1:]
            
            # 移除目录标记符
            if pattern.endswith('/'):
                pattern = pattern[:-1]
            
            is_match = False
            
            # 根目录锚定 (以 / 开头)
            if pattern.startswith('/'):
                p = pattern[1:]
                if fnmatch.fnmatch(rel_path, p):
                    is_match = True
            
            # 包含路径分隔符 (但非开头)，视为相对路径匹配
            elif '/' in pattern:
                if fnmatch.fnmatch(rel_path, pattern):
                    is_match = True
            
            # 不包含 /，匹配文件名或路径中的任意目录名
            else:
                # 匹配当前文件名
                if fnmatch.fnmatch(basename, pattern):
                    is_match = True
                # 匹配路径中的任意部分 (针对目录被忽略的情况)
                elif any(fnmatch.fnmatch(seg, pattern) for seg in path_segments):
                    is_match = True

            if is_match:
                ignored = not negative
        
        return ignored

