#!/usr/bin/env python3
"""
Architecture Graph Builder

Main orchestrator that builds the complete architecture graph by:
1. Analyzing Python source code
2. Extracting module, class, and function information
3. Building dependency relationships
4. Creating graph nodes and edges
5. Persisting to storage

Usage:
    python graph_builder.py [--source-dir DIR] [--output-dir DIR]
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import our components
try:
    from .analyzers.python_analyzer import PythonAnalyzer, ModuleInfo, ClassInfo, FunctionInfo
    from .storage.json_store import ArchitectureGraphStore
except ImportError:
    # Allow running as standalone script
    sys.path.insert(0, str(Path(__file__).parent))
    from analyzers.python_analyzer import PythonAnalyzer, ModuleInfo, ClassInfo, FunctionInfo
    from storage.json_store import ArchitectureGraphStore


class ArchitectureGraphBuilder:
    """
    Orchestrates the building of the complete architecture graph.

    Coordinates analyzers and storage to create a comprehensive
    representation of the codebase structure.
    """

    def __init__(self, source_root: Path, data_dir: Path):
        """
        Initialize the graph builder.

        Args:
            source_root: Root directory of source code
            data_dir: Directory for storing graph data
        """
        self.source_root = Path(source_root)
        self.data_dir = Path(data_dir)

        self.python_analyzer = PythonAnalyzer(self.source_root)
        self.store = ArchitectureGraphStore(self.data_dir)

        self.modules: Dict[str, ModuleInfo] = {}

    def build(self):
        """Build the complete architecture graph"""
        print(f"Building architecture graph from {self.source_root}")
        print("=" * 70)

        # Clear existing graph
        self.store.clear()
        self.store.metadata['created'] = datetime.now().isoformat()

        # Step 1: Analyze Python source
        print("\n[1/4] Analyzing Python source code...")
        self._analyze_python_source()

        # Step 2: Build nodes
        print("\n[2/4] Building graph nodes...")
        self._build_nodes()

        # Step 3: Build edges
        print("\n[3/4] Building graph edges...")
        self._build_edges()

        # Step 4: Save graph
        print("\n[4/4] Saving architecture graph...")
        self.store.save()

        # Print summary
        self._print_summary()

    def _analyze_python_source(self):
        """Analyze all Python source files"""
        python_dir = self.source_root / 'src' / 'pokertool'

        if not python_dir.exists():
            # Fallback: try to find pokertool directory
            python_dir = self.source_root / 'pokertool'

        if not python_dir.exists():
            print(f"Warning: Could not find pokertool directory in {self.source_root}")
            return

        self.modules = self.python_analyzer.analyze_directory(python_dir)
        print(f"  Analyzed {len(self.modules)} modules")

        total_classes = sum(len(m.classes) for m in self.modules.values())
        total_functions = sum(len(m.functions) for m in self.modules.values())
        print(f"  Found {total_classes} classes, {total_functions} functions")

    def _build_nodes(self):
        """Build all graph nodes from analyzed data"""
        node_count = 0

        for module_name, module_info in self.modules.items():
            # Add module node
            self.store.add_node(
                node_id=module_name,
                node_type='module',
                path=module_info.path,
                docstring=module_info.docstring,
                version=module_info.version,
                author=module_info.author,
                complexity=module_info.complexity,
                loc=module_info.loc,
                dependencies=list(module_info.dependencies)
            )
            node_count += 1

            # Add class nodes
            for class_info in module_info.classes:
                self.store.add_node(
                    node_id=class_info.qualified_name,
                    node_type='class',
                    name=class_info.name,
                    module=module_name,
                    docstring=class_info.docstring,
                    bases=class_info.bases,
                    methods=class_info.methods,
                    decorators=class_info.decorators,
                    is_abstract=class_info.is_abstract,
                    complexity=class_info.complexity,
                    line_number=class_info.line_number
                )
                node_count += 1

            # Add function nodes
            for func_info in module_info.functions:
                self.store.add_node(
                    node_id=func_info.qualified_name,
                    node_type='function',
                    name=func_info.name,
                    module=module_name,
                    signature=func_info.signature,
                    docstring=func_info.docstring,
                    parameters=[p.__dict__ for p in func_info.parameters],
                    return_type=func_info.return_type,
                    decorators=func_info.decorators,
                    is_async=func_info.is_async,
                    is_generator=func_info.is_generator,
                    is_method=func_info.is_method,
                    complexity=func_info.complexity,
                    calls=func_info.calls,
                    raises=func_info.raises,
                    line_number=func_info.line_number
                )
                node_count += 1

        print(f"  Created {node_count} nodes")

    def _build_edges(self):
        """Build all graph edges (relationships)"""
        edge_count = 0

        for module_name, module_info in self.modules.items():
            # Import edges
            for import_info in module_info.imports:
                imported_module = import_info['module']
                if imported_module in self.modules:
                    self.store.add_edge(
                        source=module_name,
                        target=imported_module,
                        edge_type='imports',
                        import_type=import_info['type'],
                        symbols=import_info.get('symbols', [])
                    )
                    edge_count += 1

            # Dependency edges
            for dep in module_info.dependencies:
                # Find if dependency is in our analyzed modules
                dep_module = self._find_module_by_name(dep)
                if dep_module:
                    self.store.add_edge(
                        source=module_name,
                        target=dep_module,
                        edge_type='depends_on',
                        strength='required'
                    )
                    edge_count += 1

            # Contains edges (module contains classes/functions)
            for class_info in module_info.classes:
                self.store.add_edge(
                    source=module_name,
                    target=class_info.qualified_name,
                    edge_type='contains',
                    visibility='public' if not class_info.name.startswith('_') else 'private'
                )
                edge_count += 1

                # Inheritance edges
                for base in class_info.bases:
                    base_qualified = self._resolve_class_name(base, module_name)
                    if base_qualified and base_qualified in [
                        c.qualified_name
                        for m in self.modules.values()
                        for c in m.classes
                    ]:
                        self.store.add_edge(
                            source=class_info.qualified_name,
                            target=base_qualified,
                            edge_type='extends'
                        )
                        edge_count += 1

            for func_info in module_info.functions:
                self.store.add_edge(
                    source=module_name,
                    target=func_info.qualified_name,
                    edge_type='contains',
                    visibility='public' if not func_info.name.startswith('_') else 'private'
                )
                edge_count += 1

                # Function call edges
                for called_func in func_info.calls:
                    # Try to resolve to a fully qualified name
                    resolved = self._resolve_function_call(called_func, module_name)
                    if resolved:
                        self.store.add_edge(
                            source=func_info.qualified_name,
                            target=resolved,
                            edge_type='calls'
                        )
                        edge_count += 1

        print(f"  Created {edge_count} edges")

    def _find_module_by_name(self, name: str) -> Optional[str]:
        """Find module by partial name match"""
        # Direct match
        if name in self.modules:
            return name

        # Try with pokertool prefix
        if f"pokertool.{name}" in self.modules:
            return f"pokertool.{name}"

        return None

    def _resolve_class_name(self, class_name: str, current_module: str) -> Optional[str]:
        """Resolve a class name to fully qualified name"""
        # If already qualified
        if class_name in [c.qualified_name for m in self.modules.values() for c in m.classes]:
            return class_name

        # Try in current module
        qualified = f"{current_module}.{class_name}"
        if qualified in [c.qualified_name for m in self.modules.values() for c in m.classes]:
            return qualified

        return None

    def _resolve_function_call(self, func_call: str, current_module: str) -> Optional[str]:
        """Resolve a function call to fully qualified name"""
        # Skip built-ins and standard library
        if func_call in {'print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter'}:
            return None

        # Try to find in all functions
        all_functions = [
            f.qualified_name
            for m in self.modules.values()
            for f in m.functions
        ]

        # Exact match
        if func_call in all_functions:
            return func_call

        # Try with current module prefix
        qualified = f"{current_module}.{func_call}"
        if qualified in all_functions:
            return qualified

        return None

    def _print_summary(self):
        """Print summary statistics"""
        print("\n" + "=" * 70)
        print("Architecture Graph Summary")
        print("=" * 70)

        stats = self.store.get_statistics()

        print(f"\nNodes: {stats['total_nodes']}")
        for node_type, count in stats['nodes_by_type'].items():
            print(f"  {node_type}: {count}")

        print(f"\nEdges: {stats['total_edges']}")
        for edge_type, count in stats['edges_by_type'].items():
            print(f"  {edge_type}: {count}")

        if 'complexity_distribution' in stats and stats['complexity_distribution']:
            comp = stats['complexity_distribution']
            print(f"\nComplexity:")
            print(f"  Min: {comp['min']}")
            print(f"  Max: {comp['max']}")
            print(f"  Avg: {comp['avg']:.2f}")

        # Check for issues
        cycles = self.store.find_cycles()
        if cycles:
            print(f"\n⚠️  Warning: Found {len(cycles)} circular dependencies!")
            print("  First few cycles:")
            for cycle in cycles[:3]:
                print(f"    {' -> '.join(cycle[:4])}{'...' if len(cycle) > 4 else ''}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Build architecture graph database')
    parser.add_argument(
        '--source-dir',
        type=Path,
        default=Path.cwd(),
        help='Source code root directory'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).parent / 'data',
        help='Output directory for graph data'
    )

    args = parser.parse_args()

    builder = ArchitectureGraphBuilder(args.source_dir, args.output_dir)
    builder.build()

    print("\n✓ Architecture graph built successfully!")
    print(f"  Data saved to: {args.output_dir}")


if __name__ == '__main__':
    main()
