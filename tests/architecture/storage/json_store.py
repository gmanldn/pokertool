#!/usr/bin/env python3
"""
JSON Storage Layer for Architecture Graph Database

Provides persistence and retrieval of the architecture graph using JSON format.
Integrates with NetworkX for graph operations.
"""

import json
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class ArchitectureGraphStore:
    """
    Manages storage and retrieval of architecture graph data.

    Uses NetworkX DiGraph for graph operations and JSON for persistence.
    Stores both nodes (modules, classes, functions) and edges (dependencies, calls, etc.)
    """

    def __init__(self, data_dir: Path):
        """
        Initialize the graph store.

        Args:
            data_dir: Directory for storing graph data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.graph_file = self.data_dir / 'architecture.json'
        self.graphml_file = self.data_dir / 'architecture.graphml'

        self.graph = nx.DiGraph()
        self.metadata = {
            'version': '1.0.0',
            'created': None,
            'last_updated': None,
            'node_count': 0,
            'edge_count': 0,
            'analyzers_run': []
        }

    def add_node(self, node_id: str, node_type: str, **attributes):
        """
        Add a node to the graph.

        Args:
            node_id: Unique identifier for the node
            node_type: Type of node (module, class, function, etc.)
            **attributes: Additional node attributes
        """
        self.graph.add_node(node_id, type=node_type, **attributes)

    def add_edge(self, source: str, target: str, edge_type: str, **attributes):
        """
        Add an edge to the graph.

        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Type of edge (imports, calls, extends, etc.)
            **attributes: Additional edge attributes
        """
        self.graph.add_edge(source, target, type=edge_type, **attributes)

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node data"""
        if node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None

    def get_nodes_by_type(self, node_type: str) -> List[tuple]:
        """Get all nodes of a specific type"""
        return [
            (node_id, data)
            for node_id, data in self.graph.nodes(data=True)
            if data.get('type') == node_type
        ]

    def get_edges_by_type(self, edge_type: str) -> List[tuple]:
        """Get all edges of a specific type"""
        return [
            (source, target, data)
            for source, target, data in self.graph.edges(data=True)
            if data.get('type') == edge_type
        ]

    def find_dependents(self, node_id: str) -> List[str]:
        """Find all nodes that depend on this node"""
        return list(self.graph.predecessors(node_id))

    def find_dependencies(self, node_id: str) -> List[str]:
        """Find all nodes that this node depends on"""
        return list(self.graph.successors(node_id))

    def find_cycles(self) -> List[List[str]]:
        """Find all cycles in the graph"""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except nx.NetworkXNoCycle:
            return []

    def get_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest path between two nodes"""
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return None

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate graph metrics"""
        metrics = {
            'node_count': self.graph.number_of_nodes(),
            'edge_count': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_dag': nx.is_directed_acyclic_graph(self.graph),
        }

        # Degree centrality
        if self.graph.number_of_nodes() > 0:
            metrics['degree_centrality'] = nx.degree_centrality(self.graph)
            metrics['in_degree_centrality'] = nx.in_degree_centrality(self.graph)
            metrics['out_degree_centrality'] = nx.out_degree_centrality(self.graph)

        # Find strongly connected components
        metrics['strongly_connected_components'] = len(
            list(nx.strongly_connected_components(self.graph))
        )

        return metrics

    def save(self):
        """Save graph to JSON and GraphML formats"""
        # Prepare data for JSON
        graph_data = {
            'metadata': {
                **self.metadata,
                'last_updated': datetime.now().isoformat(),
                'node_count': self.graph.number_of_nodes(),
                'edge_count': self.graph.number_of_edges()
            },
            'nodes': [
                {'id': node_id, **data}
                for node_id, data in self.graph.nodes(data=True)
            ],
            'edges': [
                {'source': source, 'target': target, **data}
                for source, target, data in self.graph.edges(data=True)
            ],
            'metrics': self.calculate_metrics()
        }

        # Save JSON
        with open(self.graph_file, 'w') as f:
            json.dump(graph_data, f, indent=2, default=str)

        # Save GraphML for visualization (convert lists to strings for GraphML compatibility)
        try:
            # Create a copy of the graph with lists converted to strings
            graphml_graph = self.graph.copy()
            for node_id, data in graphml_graph.nodes(data=True):
                for key, value in list(data.items()):
                    if isinstance(value, (list, dict, set)):
                        data[key] = json.dumps(value, default=str)
            for source, target, data in graphml_graph.edges(data=True):
                for key, value in list(data.items()):
                    if isinstance(value, (list, dict, set)):
                        data[key] = json.dumps(value, default=str)

            nx.write_graphml(graphml_graph, str(self.graphml_file))
        except Exception as e:
            print(f"Warning: Could not save GraphML format: {e}")

        print(f"Saved architecture graph:")
        print(f"  JSON: {self.graph_file}")
        print(f"  GraphML: {self.graphml_file}")
        print(f"  Nodes: {graph_data['metadata']['node_count']}")
        print(f"  Edges: {graph_data['metadata']['edge_count']}")

    def load(self) -> bool:
        """
        Load graph from JSON file.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.graph_file.exists():
            return False

        try:
            with open(self.graph_file, 'r') as f:
                graph_data = json.load(f)

            self.metadata = graph_data.get('metadata', {})
            self.graph.clear()

            # Load nodes
            for node in graph_data.get('nodes', []):
                node_id = node.pop('id')
                self.graph.add_node(node_id, **node)

            # Load edges
            for edge in graph_data.get('edges', []):
                source = edge.pop('source')
                target = edge.pop('target')
                self.graph.add_edge(source, target, **edge)

            print(f"Loaded architecture graph from {self.graph_file}")
            print(f"  Nodes: {self.graph.number_of_nodes()}")
            print(f"  Edges: {self.graph.number_of_edges()}")

            return True

        except Exception as e:
            print(f"Error loading graph: {e}")
            return False

    def clear(self):
        """Clear the graph"""
        self.graph.clear()
        self.metadata = {
            'version': '1.0.0',
            'created': datetime.now().isoformat(),
            'last_updated': None,
            'node_count': 0,
            'edge_count': 0,
            'analyzers_run': []
        }

    def export_subgraph(self, node_ids: List[str], output_file: Path):
        """
        Export a subgraph containing specific nodes and their relationships.

        Args:
            node_ids: List of node IDs to include
            output_file: Output file path
        """
        subgraph = self.graph.subgraph(node_ids)

        subgraph_data = {
            'metadata': {
                'created': datetime.now().isoformat(),
                'node_count': subgraph.number_of_nodes(),
                'edge_count': subgraph.number_of_edges(),
                'parent_graph': str(self.graph_file)
            },
            'nodes': [
                {'id': node_id, **data}
                for node_id, data in subgraph.nodes(data=True)
            ],
            'edges': [
                {'source': source, 'target': target, **data}
                for source, target, data in subgraph.edges(data=True)
            ]
        }

        with open(output_file, 'w') as f:
            json.dump(subgraph_data, f, indent=2, default=str)

        print(f"Exported subgraph to {output_file}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'nodes_by_type': {},
            'edges_by_type': {},
            'complexity_distribution': {},
            'dependency_depth': {}
        }

        # Count nodes by type
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            stats['nodes_by_type'][node_type] = stats['nodes_by_type'].get(node_type, 0) + 1

        # Count edges by type
        for source, target, data in self.graph.edges(data=True):
            edge_type = data.get('type', 'unknown')
            stats['edges_by_type'][edge_type] = stats['edges_by_type'].get(edge_type, 0) + 1

        # Complexity distribution
        complexities = [
            data.get('complexity', 0)
            for node_id, data in self.graph.nodes(data=True)
            if 'complexity' in data
        ]
        if complexities:
            stats['complexity_distribution'] = {
                'min': min(complexities),
                'max': max(complexities),
                'avg': sum(complexities) / len(complexities),
                'total': len(complexities)
            }

        return stats


if __name__ == '__main__':
    # Example usage
    from pathlib import Path

    store = ArchitectureGraphStore(Path('tests/architecture/data'))

    # Add some example nodes
    store.add_node('pokertool.api', 'module', path='src/pokertool/api.py')
    store.add_node('pokertool.core', 'module', path='src/pokertool/core/__init__.py')
    store.add_node('pokertool.api.FastAPIApp', 'class', module='pokertool.api')

    # Add edges
    store.add_edge('pokertool.api', 'pokertool.core', 'imports')

    # Save
    store.save()

    # Print stats
    print("\nStatistics:")
    print(json.dumps(store.get_statistics(), indent=2))
