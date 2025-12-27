"""
Python AST 复杂度分析器

使用 AST 精确计算 Python 文件的圈复杂度。
"""
import ast


class ComplexityVisitor(ast.NodeVisitor):
    """遍历 Python AST 计算圈复杂度、import 数量和 docstring 数量"""
    
    def __init__(self):
        self.complexity = 1
        self.imports = 0
        self.docstrings = 0

    def visit_If(self, node): 
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node): 
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_AsyncFor(self, node): 
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node): 
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Try(self, node): 
        self.complexity += len(node.handlers)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node): 
        if ast.get_docstring(node): 
            self.docstrings += 1
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        if ast.get_docstring(node): 
            self.docstrings += 1
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        if ast.get_docstring(node): 
            self.docstrings += 1
        self.generic_visit(node)
    
    def visit_Import(self, node): 
        self.imports += len(node.names)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node): 
        self.imports += len(node.names)
        self.generic_visit(node)
    
    def visit_BoolOp(self, node): 
        self.complexity += (len(node.values) - 1)
        self.generic_visit(node)


def analyze_python_ast(file_path):
    """使用 AST 精确分析 Python 文件的复杂度"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        visitor = ComplexityVisitor()
        if ast.get_docstring(tree):
            visitor.docstrings += 1
        visitor.visit(tree)
        return {
            'success': True, 
            'complexity': visitor.complexity, 
            'imports': visitor.imports, 
            'docstrings': visitor.docstrings
        }
    except:
        return {'success': False}
