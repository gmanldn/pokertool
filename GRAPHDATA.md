# Architecture Graph Database Schema

This document describes all elements captured by the PokerTool architecture graph database. The graph provides a comprehensive, queryable representation of the entire codebase structure, dependencies, and relationships.

## Overview

The architecture graph database is a directed graph stored in two formats:
- **JSON** (`tests/architecture/data/architecture.json`) - Human-readable, full data
- **GraphML** (`tests/architecture/data/architecture.graphml`) - For visualization tools

**Current Statistics** (as of latest build):
- **Nodes**: 1,067 (116 modules, 653 classes, 298 functions)
- **Edges**: 1,054 (951 contains, 100 calls, 2 extends, 1 imports)
- **Complexity Range**: 0-561 (average 14.72)
- **Circular Dependencies**: 7 detected

---

## Node Types

### 1. Module Nodes

Represents Python `.py` files in the codebase.

**Type**: `module`

**Attributes**:
```json
{
  "id": "pokertool.api",                    // Unique identifier (Python module path)
  "type": "module",                         // Node type
  "path": "src/pokertool/api.py",          // Filesystem path
  "docstring": "RESTful API module...",    // Module docstring
  "complexity": 156,                        // Cyclomatic complexity
  "dependencies": [                         // List of imported modules
    "fastapi",
    "pokertool.core",
    "pokertool.models"
  ],
  "imports": [                              // Detailed import information
    {
      "module": "fastapi",
      "names": ["FastAPI", "HTTPException"],
      "alias": null
    }
  ]
}
```

**Key Metrics**:
- `complexity`: Sum of all functions/methods in the module
- `dependencies`: Direct imports only (not transitive)
- `imports`: Full AST-parsed import details

**Example Queries**:
```python
# Find all modules
modules = store.get_nodes_by_type('module')

# Find highly complex modules
complex_modules = [
    (node_id, data['complexity'])
    for node_id, data in modules
    if data.get('complexity', 0) > 100
]

# Find modules with external dependencies
external_deps = [
    (node_id, data['dependencies'])
    for node_id, data in modules
    if any(not dep.startswith('pokertool') for dep in data.get('dependencies', []))
]
```

---

### 2. Class Nodes

Represents class definitions within modules.

**Type**: `class`

**Attributes**:
```json
{
  "id": "pokertool.api.FastAPIApp",        // Fully qualified name
  "type": "class",
  "name": "FastAPIApp",                     // Simple class name
  "module": "pokertool.api",                // Parent module
  "bases": ["FastAPI"],                     // Base classes
  "methods": [                              // List of method names
    "__init__",
    "create_app",
    "configure_routes"
  ],
  "decorators": ["dataclass"],              // Class decorators
  "complexity": 45,                         // Sum of all method complexities
  "docstring": "Main FastAPI application..." // Class docstring
}
```

**Key Metrics**:
- `complexity`: Sum of all method complexities
- `bases`: Direct parent classes (not full MRO)
- `methods`: Method names only (detailed info in function nodes)

**Example Queries**:
```python
# Find all classes extending a specific base
subclasses = [
    node_id for node_id, data in store.get_nodes_by_type('class')
    if 'BaseModel' in data.get('bases', [])
]

# Find classes with high complexity
complex_classes = [
    (node_id, data['complexity'])
    for node_id, data in store.get_nodes_by_type('class')
    if data.get('complexity', 0) > 50
]

# Find dataclasses
dataclasses = [
    node_id for node_id, data in store.get_nodes_by_type('class')
    if 'dataclass' in data.get('decorators', [])
]
```

---

### 3. Function Nodes

Represents functions and methods (both standalone and class methods).

**Type**: `function`

**Attributes**:
```json
{
  "id": "pokertool.api.create_app",        // Fully qualified name
  "type": "function",
  "name": "create_app",                     // Function name
  "signature": "def create_app() -> FastAPI", // Full signature
  "parameters": [                           // Parameter details
    {
      "name": "self",
      "annotation": null,
      "default": null,
      "kind": "POSITIONAL_OR_KEYWORD"
    },
    {
      "name": "config",
      "annotation": "Optional[Config]",
      "default": "None",
      "kind": "POSITIONAL_OR_KEYWORD"
    }
  ],
  "return_type": "FastAPI",                 // Return type annotation
  "decorators": ["staticmethod"],           // Function decorators
  "is_async": false,                        // Whether async function
  "complexity": 12,                         // Cyclomatic complexity
  "calls": [                                // Functions called
    "FastAPI",
    "add_middleware",
    "include_router"
  ],
  "raises": ["ValueError", "RuntimeError"], // Exceptions raised
  "docstring": "Create and configure..."    // Function docstring
}
```

**Key Metrics**:
- `complexity`: Cyclomatic complexity (branches, loops, conditions)
- `calls`: AST-extracted function calls (may include false positives)
- `parameters`: Full parameter info including type hints and defaults

**Example Queries**:
```python
# Find async functions
async_funcs = [
    node_id for node_id, data in store.get_nodes_by_type('function')
    if data.get('is_async')
]

# Find functions with high complexity
complex_funcs = [
    (node_id, data['complexity'])
    for node_id, data in store.get_nodes_by_type('function')
    if data.get('complexity', 0) > 15
]

# Find functions with type annotations
typed_funcs = [
    node_id for node_id, data in store.get_nodes_by_type('function')
    if data.get('return_type') or any(
        p.get('annotation') for p in data.get('parameters', [])
    )
]
```

---

## Edge Types

### 1. `imports` Edges

Represents module import relationships.

**Direction**: Source module → Imported module

**Attributes**:
```json
{
  "source": "pokertool.api",
  "target": "pokertool.core",
  "type": "imports",
  "names": ["Strategy", "Player"],   // Specific imports (if from X import Y)
  "alias": null                      // Import alias (if import X as Y)
}
```

**Example Query**:
```python
# Find all modules that import a specific module
importers = store.find_dependents('pokertool.core')

# Find import cycles
cycles = store.find_cycles()
```

---

### 2. `depends_on` Edges

Represents dependency relationships (broader than imports).

**Direction**: Dependent module → Dependency

**Attributes**:
```json
{
  "source": "pokertool.api",
  "target": "pokertool.models",
  "type": "depends_on"
}
```

---

### 3. `contains` Edges

Represents containment relationships (module contains class, class contains method).

**Direction**: Container → Contained

**Attributes**:
```json
{
  "source": "pokertool.api",           // Module
  "target": "pokertool.api.FastAPIApp", // Class
  "type": "contains"
}
```

**Example Query**:
```python
# Find all classes in a module
classes_in_module = [
    target for source, target, data in store.graph.edges(data=True)
    if source == 'pokertool.api' and data.get('type') == 'contains'
]
```

---

### 4. `calls` Edges

Represents function call relationships.

**Direction**: Caller → Callee

**Attributes**:
```json
{
  "source": "pokertool.api.create_app",
  "target": "pokertool.api.configure_routes",
  "type": "calls"
}
```

**Note**: Call extraction is AST-based and may include:
- False positives (method calls on dynamic types)
- Missing calls (dynamic imports, reflection)

---

### 5. `extends` Edges

Represents class inheritance relationships.

**Direction**: Subclass → Base class

**Attributes**:
```json
{
  "source": "pokertool.api.FastAPIApp",
  "target": "FastAPI",
  "type": "extends"
}
```

**Example Query**:
```python
# Find all subclasses of a class
subclasses = [
    source for source, target, data in store.graph.edges(data=True)
    if target == 'BaseException' and data.get('type') == 'extends'
]
```

---

## Complexity Metrics

### Cyclomatic Complexity

**Definition**: Number of linearly independent paths through code.

**Calculation**:
```
Complexity = 1 (base)
  + number of if/elif statements
  + number of for/while loops
  + number of except clauses
  + number of and/or operators
  + number of ternary operators
```

**Thresholds**:
- **1-10**: Simple, low risk
- **11-20**: Moderate complexity, medium risk
- **21-50**: High complexity, high risk
- **50+**: Very high complexity, very high risk

**Example**:
```python
def calculate_pot_odds(pot, bet):  # Complexity = 1
    if bet <= 0:                   # +1 = 2
        raise ValueError()
    if pot <= 0:                   # +1 = 3
        raise ValueError()

    odds = pot / bet

    if odds > 10:                  # +1 = 4
        return "Strong"
    elif odds > 5:                 # +1 = 5
        return "Medium"
    else:
        return "Weak"

    # Total Complexity: 5
```

---

## Graph Metadata

The graph includes metadata about the analysis:

```json
{
  "metadata": {
    "version": "1.0.0",
    "created": "2025-10-16T20:30:00",
    "last_updated": "2025-10-16T20:45:00",
    "node_count": 1067,
    "edge_count": 1054,
    "analyzers_run": ["PythonAnalyzer"]
  }
}
```

---

## Graph Metrics

Calculated graph-level metrics:

```json
{
  "metrics": {
    "node_count": 1067,
    "edge_count": 1054,
    "density": 0.000928,              // How connected the graph is
    "is_dag": false,                  // Whether acyclic (no circular deps)
    "degree_centrality": {...},       // Most connected nodes
    "in_degree_centrality": {...},    // Most depended-upon nodes
    "out_degree_centrality": {...},   // Nodes with most dependencies
    "strongly_connected_components": 115  // Number of SCCs
  }
}
```

---

## Usage Examples

### Finding Circular Dependencies

```python
from tests.architecture.storage.json_store import ArchitectureGraphStore
from pathlib import Path

store = ArchitectureGraphStore(Path('tests/architecture/data'))
store.load()

cycles = store.find_cycles()
for cycle in cycles:
    print(" -> ".join(cycle))
```

### Finding High-Complexity Functions

```python
functions = store.get_nodes_by_type('function')
complex_funcs = [
    (node_id, data['complexity'])
    for node_id, data in functions
    if data.get('complexity', 0) > 20
]

# Sort by complexity
complex_funcs.sort(key=lambda x: x[1], reverse=True)

for func, complexity in complex_funcs[:10]:
    print(f"{func}: {complexity}")
```

### Finding Dependency Chains

```python
# Find shortest path from API to database
path = store.get_shortest_path('pokertool.api', 'pokertool.database')
if path:
    print(" -> ".join(path))
```

### Finding Untested Modules

```python
modules = store.get_nodes_by_type('module')
test_edges = store.get_edges_by_type('tests')

tested_modules = {target for _, target, _ in test_edges}
untested = [
    node_id for node_id, _ in modules
    if node_id not in tested_modules and 'test' not in node_id
]

print(f"Untested modules: {len(untested)}")
for module in untested:
    print(f"  - {module}")
```

### Module Statistics

```python
stats = store.get_statistics()

print(f"Total Nodes: {stats['total_nodes']}")
print(f"Total Edges: {stats['total_edges']}")
print("\nNodes by Type:")
for node_type, count in stats['nodes_by_type'].items():
    print(f"  {node_type}: {count}")

print("\nEdges by Type:")
for edge_type, count in stats['edges_by_type'].items():
    print(f"  {edge_type}: {count}")

if 'complexity_distribution' in stats:
    print("\nComplexity Distribution:")
    print(f"  Min: {stats['complexity_distribution']['min']}")
    print(f"  Max: {stats['complexity_distribution']['max']}")
    print(f"  Avg: {stats['complexity_distribution']['avg']:.2f}")
```

---

## Updating the Graph

The graph is automatically updated during the test cycle:

```bash
# Manual update
python -m tests.architecture.graph_builder

# Automatic update with tests
python test.py

# Skip graph update
python test.py --no-graph
```

---

## Visualization

The GraphML export can be visualized using:

- **Gephi** (https://gephi.org/) - Network visualization
- **yEd** (https://www.yworks.com/products/yed) - Graph editor
- **Cytoscape** (https://cytoscape.org/) - Network analysis

**Recommended Layout Algorithms**:
- **Hierarchical Layout**: For module dependencies (shows layers)
- **Force-Directed Layout**: For general exploration
- **Circular Layout**: For finding cycles

---

## Future Enhancements

Planned additions to the graph schema:

### TypeScript/React Nodes
- Component nodes with props
- Hook usage tracking
- Component composition relationships

### API Endpoint Nodes
- FastAPI endpoint extraction
- Request/response models
- Route dependencies

### Test Coverage Nodes
- Test → Code mapping
- Coverage percentages
- Test categories (unit, integration, e2e)

### Configuration Nodes
- Environment variables
- Config file dependencies
- Feature flags

---

## File Locations

```
tests/architecture/
├── data/
│   ├── architecture.json     # Main graph data (JSON format)
│   ├── architecture.graphml  # Visualization format
│   └── schema.json           # Schema definition
├── analyzers/
│   └── python_analyzer.py    # AST-based Python analyzer
├── storage/
│   └── json_store.py         # NetworkX storage layer
├── graph_builder.py          # Main orchestrator
└── README.md                 # Usage documentation
```

---

## Contributing

When extending the graph schema:

1. Update `tests/architecture/data/schema.json`
2. Add analyzer in `tests/architecture/analyzers/`
3. Update `graph_builder.py` to use the analyzer
4. Add tests in `tests/test_architecture_graph.py`
5. Update this document (GRAPHDATA.md)
6. Run `python test.py --architecture` to verify

---

## License

Part of the PokerTool project. See repository LICENSE file.
