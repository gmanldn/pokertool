# PokerTool Architecture Graph Database

A comprehensive graph database documenting the complete architecture of the PokerTool codebase including modules, classes, functions, dependencies, and their relationships.

## Overview

This system provides:
- **Living Documentation**: Always up-to-date with the codebase
- **Dependency Tracking**: Visualize and query module dependencies
- **Architectural Validation**: Automated tests for circular dependencies and design rules
- **Impact Analysis**: Understand the impact of changes
- **Complexity Metrics**: Track code complexity over time

## Quick Start

### Generate the Architecture Graph

```bash
# From the repository root
python -m tests.architecture.graph_builder

# Or specify custom directories
python -m tests.architecture.graph_builder \
    --source-dir /path/to/source \
    --output-dir tests/architecture/data
```

### Run Architecture Tests

```bash
# Run all architecture tests
pytest tests/test_architecture_graph.py -v

# Run quick tests only (skip slow rebuild)
pytest tests/test_architecture_graph.py -v -m "not slow"

# Rebuild the graph before running tests (useful after code changes)
pytest tests/test_architecture_graph.py -v --update-graph

# Run tests with automatic graph rebuild in CI/CD
pytest tests/test_architecture_graph.py -v --update-graph -m "not slow"
```

### View the Graph

The graph is exported in multiple formats:
- `tests/architecture/data/architecture.json` - Human-readable JSON
- `tests/architecture/data/architecture.graphml` - For visualization tools (Gephi, yEd, Cytoscape)

## Graph Structure

### Node Types

1. **Module** - Python .py files
   ```json
   {
     "id": "pokertool.api",
     "type": "module",
     "path": "src/pokertool/api.py",
     "docstring": "RESTful API module",
     "complexity": 156,
     "dependencies": ["fastapi", "pokertool.core"]
   }
   ```

2. **Class** - Class definitions
   ```json
   {
     "id": "pokertool.api.FastAPIApp",
     "type": "class",
     "name": "FastAPIApp",
     "module": "pokertool.api",
     "bases": ["FastAPI"],
     "methods": ["create_app", "configure_routes"],
     "complexity": 45
   }
   ```

3. **Function** - Functions and methods
   ```json
   {
     "id": "pokertool.api.create_app",
     "type": "function",
     "signature": "def create_app() -> FastAPI",
     "complexity": 12,
     "calls": ["FastAPI", "add_middleware"],
     "raises": ["ValueError"]
   }
   ```

### Edge Types

1. **imports** - Module A imports Module B
2. **depends_on** - Module A depends on Module B
3. **calls** - Function A calls Function B
4. **extends** - Class A extends Class B
5. **contains** - Module/Class contains Function/Class
6. **tests** - Test tests a component

## Usage Examples

### Python API

```python
from tests.architecture.storage.json_store import ArchitectureGraphStore
from pathlib import Path

# Load the graph
store = ArchitectureGraphStore(Path('tests/architecture/data'))
store.load()

# Find all modules
modules = store.get_nodes_by_type('module')
print(f"Found {len(modules)} modules")

# Find dependencies of a module
deps = store.find_dependencies('pokertool.api')
print(f"Dependencies: {deps}")

# Find what depends on a module
dependents = store.find_dependents('pokertool.core')
print(f"Dependents: {dependents}")

# Find circular dependencies
cycles = store.find_cycles()
if cycles:
    print(f"Found {len(cycles)} circular dependencies")

# Get shortest path between modules
path = store.get_shortest_path('pokertool.api', 'pokertool.core')
print(f"Path: {' -> '.join(path)}")

# Get statistics
stats = store.get_statistics()
print(f"Total nodes: {stats['total_nodes']}")
print(f"Total edges: {stats['total_edges']}")
print(f"Nodes by type: {stats['nodes_by_type']}")
```

### Query Examples

```python
# Find all API endpoints
endpoints = store.get_nodes_by_type('endpoint')

# Find highly complex functions
functions = store.get_nodes_by_type('function')
complex_funcs = [
    (node_id, data['complexity'])
    for node_id, data in functions
    if data.get('complexity', 0) > 15
]

# Find all classes that extend a specific base
classes = store.get_nodes_by_type('class')
subclasses = [
    node_id for node_id, data in classes
    if 'BaseModel' in data.get('bases', [])
]

# Find untested modules
modules = store.get_nodes_by_type('module')
tests = store.get_edges_by_type('tests')
tested_modules = {target for _, target, _ in tests}
untested = [
    node_id for node_id, _ in modules
    if node_id not in tested_modules
]
```

## Directory Structure

```
tests/architecture/
├── analyzers/
│   ├── __init__.py
│   ├── python_analyzer.py      # AST-based Python analyzer
│   ├── typescript_analyzer.py  # TSX/TS analyzer (future)
│   ├── api_analyzer.py         # API endpoint extractor (future)
│   └── test_analyzer.py        # Test coverage mapping (future)
├── storage/
│   ├── __init__.py
│   ├── json_store.py           # JSON + NetworkX storage
│   ├── graphml_store.py        # GraphML export (future)
│   └── sqlite_store.py         # SQLite queries (future)
├── queries/
│   ├── __init__.py
│   ├── query_builder.py        # Query interface (future)
│   └── common_queries.py       # Pre-built queries (future)
├── validators/
│   ├── __init__.py
│   ├── dependency_validator.py # Dependency rules (future)
│   └── contract_validator.py   # Contract validation (future)
├── visualizers/
│   ├── __init__.py
│   └── graphviz_renderer.py    # Graph visualization (future)
├── data/
│   ├── schema.json             # Graph schema definition
│   ├── architecture.json       # Main graph (generated)
│   └── architecture.graphml    # GraphML export (generated)
├── graph_builder.py            # Main orchestrator
└── README.md                   # This file
```

## Schema

The graph follows a strict schema defined in `data/schema.json`. This includes:
- Valid node types and their required/optional attributes
- Valid edge types and their relationships
- Complexity metrics definitions
- Validation rules

## Metrics

The system tracks several metrics:

### Complexity Metrics
- **Cyclomatic Complexity**: Number of linearly independent paths
- **LOC**: Lines of code
- **Coupling**: Afferent/Efferent coupling

### Graph Metrics
- **Density**: How connected the graph is
- **Centrality**: Most important nodes
- **Components**: Strongly connected components

## Integration

### Pytest Integration

The architecture graph can be automatically validated in your test suite:

```python
# tests/test_architecture_graph.py
def test_no_circular_dependencies(graph_store):
    cycles = graph_store.find_cycles()
    assert len(cycles) == 0, "Circular dependencies found"

def test_complexity_limits(graph_store):
    functions = graph_store.get_nodes_by_type('function')
    complex_funcs = [
        (node_id, data['complexity'])
        for node_id, data in functions
        if data.get('complexity', 0) > 20
    ]
    assert len(complex_funcs) == 0, "Functions exceeding complexity limit"
```

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/tests.yml
- name: Validate Architecture
  run: |
    # Option 1: Rebuild graph explicitly, then test
    python -m tests.architecture.graph_builder
    pytest tests/test_architecture_graph.py -v

    # Option 2: Use --update-graph flag (recommended)
    pytest tests/test_architecture_graph.py -v --update-graph -m "not slow"
```

The `--update-graph` flag is recommended for CI/CD as it automatically rebuilds the graph before running tests, ensuring the graph is always up-to-date with the latest code changes.

## Future Enhancements

Planned features:
- [ ] TypeScript/React component analyzer
- [ ] API endpoint extraction from FastAPI
- [ ] Test coverage mapping
- [ ] Interactive visualization (D3.js)
- [ ] Cypher-like query language
- [ ] Architecture rule enforcement
- [ ] Change impact analysis
- [ ] Automatic documentation generation
- [ ] SQLite query interface
- [ ] Watch mode for auto-rebuild

## Troubleshooting

### Graph generation fails
```bash
# Check Python path
echo $PYTHONPATH

# Run with debugging
python -m tests.architecture.graph_builder --source-dir . -v
```

### Missing dependencies
```bash
# Install NetworkX if not present
pip install networkx
```

### Circular dependencies detected
The graph will warn about circular dependencies. To investigate:

```python
from tests.architecture.storage.json_store import ArchitectureGraphStore

store = ArchitectureGraphStore(Path('tests/architecture/data'))
store.load()

cycles = store.find_cycles()
for cycle in cycles:
    print(" -> ".join(cycle))
```

## Contributing

When adding new features:
1. Update the schema in `data/schema.json`
2. Add corresponding analyzer
3. Update `graph_builder.py` to use the analyzer
4. Add tests in `test_architecture_graph.py`
5. Update this README

## License

Part of the PokerTool project. See repository LICENSE file.
