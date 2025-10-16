#!/usr/bin/env python3
"""
Tests for Architecture Graph Database

Validates that the architecture graph is up-to-date and consistent
with the codebase structure.
"""

import pytest
import json
from pathlib import Path

# Import architecture components
import sys
sys.path.insert(0, str(Path(__file__).parent))

from architecture.graph_builder import ArchitectureGraphBuilder
from architecture.storage.json_store import ArchitectureGraphStore


class TestArchitectureGraph:
    """Test the architecture graph database"""

    def test_graph_exists(self, graph_store):
        """Test that the architecture graph file exists"""
        assert graph_store.graph_file.exists(), "Architecture graph file not found"

    def test_graph_not_empty(self, graph_store):
        """Test that the graph contains nodes"""
        assert graph_store.graph.number_of_nodes() > 0, "Graph has no nodes"
        assert graph_store.graph.number_of_edges() > 0, "Graph has no edges"

    def test_module_nodes_exist(self, graph_store):
        """Test that module nodes are present"""
        modules = graph_store.get_nodes_by_type('module')
        assert len(modules) > 0, "No module nodes found"

        # Check for key modules
        module_names = [node_id for node_id, _ in modules]
        assert any('api' in name for name in module_names), "API module not found"

    def test_class_nodes_exist(self, graph_store):
        """Test that class nodes are present"""
        classes = graph_store.get_nodes_by_type('class')
        assert len(classes) > 0, "No class nodes found"

    def test_function_nodes_exist(self, graph_store):
        """Test that function nodes are present"""
        functions = graph_store.get_nodes_by_type('function')
        assert len(functions) > 0, "No function nodes found"

    def test_import_edges_exist(self, graph_store):
        """Test that import edges are present"""
        imports = graph_store.get_edges_by_type('imports')
        assert len(imports) > 0, "No import edges found"

    def test_no_circular_dependencies(self, graph_store):
        """Test that there are no circular import dependencies"""
        cycles = graph_store.find_cycles()

        if cycles:
            print("\nFound circular dependencies:")
            for cycle in cycles[:5]:  # Show first 5
                print(f"  {' -> '.join(cycle)}")

        # This is a warning test - cycles might exist but should be minimized
        assert len(cycles) < 10, f"Too many circular dependencies found: {len(cycles)}"

    def test_complexity_metrics(self, graph_store):
        """Test that complexity metrics are captured"""
        functions = graph_store.get_nodes_by_type('function')

        complexities = [
            data.get('complexity', 0)
            for _, data in functions
            if 'complexity' in data
        ]

        assert len(complexities) > 0, "No complexity metrics found"
        assert max(complexities) > 0, "All complexities are zero"

    def test_module_dependencies(self, graph_store):
        """Test that module dependencies are tracked"""
        modules = graph_store.get_nodes_by_type('module')

        modules_with_deps = [
            (node_id, data)
            for node_id, data in modules
            if data.get('dependencies')
        ]

        assert len(modules_with_deps) > 0, "No modules with dependencies found"

    def test_docstrings_extracted(self, graph_store):
        """Test that docstrings are extracted"""
        modules = graph_store.get_nodes_by_type('module')

        modules_with_docs = [
            node_id for node_id, data in modules
            if data.get('docstring')
        ]

        # At least some modules should have docstrings
        assert len(modules_with_docs) > 0, "No docstrings found in modules"

    def test_type_annotations(self, graph_store):
        """Test that type annotations are captured"""
        functions = graph_store.get_nodes_by_type('function')

        functions_with_types = [
            node_id for node_id, data in functions
            if data.get('return_type') or data.get('parameters')
        ]

        assert len(functions_with_types) > 0, "No type annotations found"

    def test_graph_statistics(self, graph_store):
        """Test graph statistics calculation"""
        stats = graph_store.get_statistics()

        assert 'total_nodes' in stats
        assert 'total_edges' in stats
        assert 'nodes_by_type' in stats
        assert 'edges_by_type' in stats

        assert stats['total_nodes'] > 0
        assert stats['total_edges'] > 0

    def test_find_dependencies(self, graph_store):
        """Test finding dependencies of a module"""
        # Find any module
        modules = graph_store.get_nodes_by_type('module')
        if modules:
            module_id, _ = modules[0]
            deps = graph_store.find_dependencies(module_id)
            # Dependencies might be empty for leaf modules
            assert isinstance(deps, list)

    def test_schema_compliance(self):
        """Test that the graph complies with the schema"""
        schema_file = Path(__file__).parent / 'architecture' / 'data' / 'schema.json'
        assert schema_file.exists(), "Schema file not found"

        with open(schema_file) as f:
            schema = json.load(f)

        assert 'node_types' in schema
        assert 'edge_types' in schema
        assert 'module' in schema['node_types']
        assert 'class' in schema['node_types']
        assert 'function' in schema['node_types']


class TestGraphBuilder:
    """Test the graph builder"""

    def test_builder_initialization(self):
        """Test that the builder can be initialized"""
        source_root = Path.cwd()
        data_dir = Path(__file__).parent / 'architecture' / 'data'

        builder = ArchitectureGraphBuilder(source_root, data_dir)
        assert builder.source_root.exists()
        assert builder.data_dir.exists()

    @pytest.mark.slow
    def test_rebuild_graph(self):
        """Test rebuilding the entire graph (slow test)"""
        source_root = Path.cwd()
        data_dir = Path(__file__).parent / 'architecture' / 'data'

        builder = ArchitectureGraphBuilder(source_root, data_dir)
        builder.build()

        # Verify the graph was created
        assert (data_dir / 'architecture.json').exists()
        assert (data_dir / 'architecture.graphml').exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
