#!/usr/bin/env python3
"""
Python AST Analyzer for Architecture Graph Database

This module provides comprehensive analysis of Python source code using the
Abstract Syntax Tree (AST) to extract detailed structural information about
modules, classes, functions, and their relationships.

Extracts:
- Module metadata (imports, exports, docstrings, version)
- Class definitions (inheritance, methods, attributes)
- Function signatures (parameters, return types, decorators)
- Type annotations and hints
- Complexity metrics
- Dependencies and call graphs
"""

import ast
import os
import sys
import inspect
import importlib
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
import re


@dataclass
class ParameterInfo:
    """Information about a function parameter"""
    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None
    kind: str = "POSITIONAL_OR_KEYWORD"  # POSITIONAL_ONLY, KEYWORD_ONLY, VAR_POSITIONAL, VAR_KEYWORD


@dataclass
class FunctionInfo:
    """Detailed function/method information"""
    name: str
    qualified_name: str
    signature: str = ""  # Will be built after initialization
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_generator: bool = False
    is_method: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False
    complexity: int = 1
    calls: List[str] = field(default_factory=list)
    raises: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class ClassInfo:
    """Detailed class information"""
    name: str
    qualified_name: str
    bases: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    class_attributes: List[Tuple[str, Optional[str]]] = field(default_factory=list)
    instance_attributes: List[Tuple[str, Optional[str]]] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_abstract: bool = False
    metaclass: Optional[str] = None
    complexity: int = 0
    line_number: int = 0


@dataclass
class ModuleInfo:
    """Comprehensive module information"""
    name: str
    path: str
    docstring: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    imports: List[Dict[str, Any]] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    module_attributes: List[Tuple[str, Optional[str]]] = field(default_factory=list)
    complexity: int = 0
    loc: int = 0
    dependencies: Set[str] = field(default_factory=set)


class ComplexityCalculator(ast.NodeVisitor):
    """Calculate cyclomatic complexity of a function"""

    def __init__(self):
        self.complexity = 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And) or isinstance(node.op, ast.Or):
            self.complexity += len(node.values) - 1
        self.generic_visit(node)


class CallExtractor(ast.NodeVisitor):
    """Extract function calls from a function body"""

    def __init__(self):
        self.calls: List[str] = []
        self.raises: List[str] = []

    def visit_Call(self, node):
        call_name = self._get_call_name(node.func)
        if call_name:
            self.calls.append(call_name)
        self.generic_visit(node)

    def visit_Raise(self, node):
        if node.exc:
            exc_name = self._get_exception_name(node.exc)
            if exc_name:
                self.raises.append(exc_name)
        self.generic_visit(node)

    def _get_call_name(self, node) -> Optional[str]:
        """Extract the name of a called function/method"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return None

    def _get_exception_name(self, node) -> Optional[str]:
        """Extract exception class name"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_call_name(node.func)
        return None


class PythonAnalyzer:
    """
    Comprehensive Python source code analyzer using AST.

    Analyzes Python modules to extract detailed structural information including:
    - Imports and dependencies
    - Class definitions with inheritance
    - Function/method signatures with type hints
    - Decorators and metadata
    - Complexity metrics
    - Call graphs
    """

    def __init__(self, source_root: Path):
        self.source_root = Path(source_root)
        self.modules: Dict[str, ModuleInfo] = {}

    def analyze_file(self, file_path: Path) -> Optional[ModuleInfo]:
        """
        Analyze a single Python file and extract comprehensive information.

        Args:
            file_path: Path to Python file

        Returns:
            ModuleInfo object with extracted data, or None if analysis fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))

            # Get module name from path
            rel_path = file_path.relative_to(self.source_root)
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            if module_parts[-1] == '__init__':
                module_parts = module_parts[:-1]
            module_name = '.'.join(module_parts)

            module_info = ModuleInfo(
                name=module_name,
                path=str(file_path.relative_to(self.source_root)),
                docstring=ast.get_docstring(tree),
                loc=len(source.splitlines())
            )

            # Extract module-level attributes
            self._extract_module_attributes(tree, module_info)

            # Analyze module structure
            self._analyze_module(tree, module_info)

            # Calculate total complexity
            module_info.complexity = sum(f.complexity for f in module_info.functions)
            module_info.complexity += sum(c.complexity for c in module_info.classes)

            return module_info

        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return None
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None

    def _extract_module_attributes(self, tree: ast.Module, module_info: ModuleInfo):
        """Extract module-level attributes like __version__, __author__"""
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        attr_name = target.id
                        value = self._get_value(node.value)

                        # Store special attributes
                        if attr_name == '__version__':
                            module_info.version = value
                        elif attr_name == '__author__':
                            module_info.author = value
                        elif attr_name == '__all__':
                            if isinstance(node.value, (ast.List, ast.Tuple)):
                                module_info.exports = [
                                    self._get_value(elt) for elt in node.value.elts
                                ]

                        # Store all attributes
                        type_annotation = self._get_annotation(target)
                        module_info.module_attributes.append((attr_name, type_annotation))

    def _analyze_module(self, tree: ast.Module, module_info: ModuleInfo):
        """Analyze the module structure"""
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_info.imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'alias': alias.asname,
                        'symbols': []
                    })
                    module_info.dependencies.add(alias.name.split('.')[0])

            elif isinstance(node, ast.ImportFrom):
                imported_module = node.module or ''
                symbols = [alias.name for alias in node.names]
                module_info.imports.append({
                    'type': 'from',
                    'module': imported_module,
                    'symbols': symbols,
                    'level': node.level
                })
                if imported_module:
                    module_info.dependencies.add(imported_module.split('.')[0])

            elif isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node, module_info.name)
                module_info.classes.append(class_info)

            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_info = self._analyze_function(node, module_info.name)
                module_info.functions.append(func_info)

    def _analyze_class(self, node: ast.ClassDef, module_name: str) -> ClassInfo:
        """Analyze a class definition"""
        qualified_name = f"{module_name}.{node.name}"

        class_info = ClassInfo(
            name=node.name,
            qualified_name=qualified_name,
            docstring=ast.get_docstring(node),
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            line_number=node.lineno
        )

        # Extract base classes
        for base in node.bases:
            base_name = self._get_name(base)
            if base_name:
                class_info.bases.append(base_name)

        # Check for metaclass
        for keyword in node.keywords:
            if keyword.arg == 'metaclass':
                class_info.metaclass = self._get_name(keyword.value)

        # Check if abstract
        class_info.is_abstract = any(
            'ABC' in base or 'Abstract' in base for base in class_info.bases
        )

        # Analyze class body
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._analyze_function(item, qualified_name, is_method=True)
                class_info.methods.append(method_info.name)
                class_info.complexity += method_info.complexity

            elif isinstance(item, ast.Assign):
                # Class attributes
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        type_annotation = self._get_annotation(target)
                        class_info.class_attributes.append((target.id, type_annotation))

            elif isinstance(item, ast.AnnAssign):
                # Annotated class attributes
                if isinstance(item.target, ast.Name):
                    annotation = self._get_annotation_from_node(item.annotation)
                    class_info.class_attributes.append((item.target.id, annotation))

        return class_info

    def _analyze_function(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        parent_name: str,
        is_method: bool = False
    ) -> FunctionInfo:
        """Analyze a function or method definition"""
        qualified_name = f"{parent_name}.{node.name}"

        func_info = FunctionInfo(
            name=node.name,
            qualified_name=qualified_name,
            docstring=ast.get_docstring(node),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            line_number=node.lineno
        )

        # Check for special method types
        for decorator in func_info.decorators:
            if decorator == 'classmethod':
                func_info.is_classmethod = True
            elif decorator == 'staticmethod':
                func_info.is_staticmethod = True
            elif decorator == 'property':
                func_info.is_property = True

        # Extract parameters
        func_info.parameters = self._extract_parameters(node.args)

        # Extract return type
        if node.returns:
            func_info.return_type = self._get_annotation_from_node(node.returns)

        # Build signature
        params_str = ', '.join(
            f"{p.name}: {p.annotation}" if p.annotation else p.name
            for p in func_info.parameters
        )
        return_str = f" -> {func_info.return_type}" if func_info.return_type else ""
        func_info.signature = f"def {node.name}({params_str}){return_str}"

        # Calculate complexity
        complexity_calc = ComplexityCalculator()
        complexity_calc.visit(node)
        func_info.complexity = complexity_calc.complexity

        # Extract calls and raises
        call_extractor = CallExtractor()
        call_extractor.visit(node)
        func_info.calls = call_extractor.calls
        func_info.raises = call_extractor.raises

        # Check if generator
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                func_info.is_generator = True
                break

        return func_info

    def _extract_parameters(self, args: ast.arguments) -> List[ParameterInfo]:
        """Extract parameter information from function arguments"""
        params = []

        # Positional-only (Python 3.8+)
        for i, arg in enumerate(args.posonlyargs if hasattr(args, 'posonlyargs') else []):
            default = None
            params.append(ParameterInfo(
                name=arg.arg,
                annotation=self._get_annotation_from_node(arg.annotation),
                default=default,
                kind="POSITIONAL_ONLY"
            ))

        # Regular positional or keyword
        defaults_offset = len(args.args) - len(args.defaults)
        for i, arg in enumerate(args.args):
            default = None
            if i >= defaults_offset:
                default = self._get_value(args.defaults[i - defaults_offset])
            params.append(ParameterInfo(
                name=arg.arg,
                annotation=self._get_annotation_from_node(arg.annotation),
                default=default,
                kind="POSITIONAL_OR_KEYWORD"
            ))

        # *args
        if args.vararg:
            params.append(ParameterInfo(
                name=args.vararg.arg,
                annotation=self._get_annotation_from_node(args.vararg.annotation),
                kind="VAR_POSITIONAL"
            ))

        # Keyword-only
        for i, arg in enumerate(args.kwonlyargs):
            default = None
            if i < len(args.kw_defaults) and args.kw_defaults[i]:
                default = self._get_value(args.kw_defaults[i])
            params.append(ParameterInfo(
                name=arg.arg,
                annotation=self._get_annotation_from_node(arg.annotation),
                default=default,
                kind="KEYWORD_ONLY"
            ))

        # **kwargs
        if args.kwarg:
            params.append(ParameterInfo(
                name=args.kwarg.arg,
                annotation=self._get_annotation_from_node(args.kwarg.annotation),
                kind="VAR_KEYWORD"
            ))

        return params

    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get decorator name"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_name(node)
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return str(node)

    def _get_name(self, node: ast.expr) -> Optional[str]:
        """Get full name from an expression node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        return None

    def _get_annotation(self, node: ast.expr) -> Optional[str]:
        """Get type annotation if present"""
        if hasattr(node, 'annotation') and node.annotation:
            return self._get_annotation_from_node(node.annotation)
        return None

    def _get_annotation_from_node(self, node: Optional[ast.expr]) -> Optional[str]:
        """Convert annotation node to string"""
        if node is None:
            return None
        return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)

    def _get_value(self, node: ast.expr) -> Optional[str]:
        """Extract value from an expression node"""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Num):  # Python < 3.8
            return str(node.n)
        elif isinstance(node, ast.Str):  # Python < 3.8
            return repr(node.s)
        elif isinstance(node, ast.Name):
            return node.id
        elif hasattr(ast, 'unparse'):
            return ast.unparse(node)
        return None

    def analyze_directory(self, directory: Path) -> Dict[str, ModuleInfo]:
        """
        Recursively analyze all Python files in a directory.

        Args:
            directory: Root directory to analyze

        Returns:
            Dictionary mapping module names to ModuleInfo objects
        """
        python_files = directory.rglob('*.py')

        for file_path in python_files:
            # Skip __pycache__ and other generated directories
            if '__pycache__' in file_path.parts:
                continue

            module_info = self.analyze_file(file_path)
            if module_info:
                self.modules[module_info.name] = module_info

        return self.modules

    def to_dict(self) -> Dict[str, Any]:
        """Convert all analyzed modules to dictionary format"""
        return {
            name: {
                **asdict(info),
                'dependencies': list(info.dependencies)
            }
            for name, info in self.modules.items()
        }


if __name__ == '__main__':
    # Example usage
    import json
    from pathlib import Path

    if len(sys.argv) > 1:
        source_dir = Path(sys.argv[1])
    else:
        source_dir = Path.cwd() / 'src' / 'pokertool'

    analyzer = PythonAnalyzer(source_dir.parent)
    analyzer.analyze_directory(source_dir)

    # Print summary
    print(f"Analyzed {len(analyzer.modules)} modules")
    print(f"Total classes: {sum(len(m.classes) for m in analyzer.modules.values())}")
    print(f"Total functions: {sum(len(m.functions) for m in analyzer.modules.values())}")

    # Save to JSON
    output_file = Path('architecture_data.json')
    with open(output_file, 'w') as f:
        json.dump(analyzer.to_dict(), f, indent=2)
    print(f"\nSaved analysis to {output_file}")
