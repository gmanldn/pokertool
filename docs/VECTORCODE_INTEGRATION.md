# VectorCode Integration for PokerTool

This document describes the integration of VectorCode into the PokerTool codebase, providing intelligent code search and context retrieval capabilities.

## Overview

VectorCode is a code repository indexing tool that uses vector embeddings to provide semantic search capabilities across your codebase. This integration allows you to:

- **Search for poker-specific logic** using natural language queries
- **Find related code** when refactoring or extending functionality
- **Discover similar implementations** for code patterns
- **Locate GUI components** and database operations efficiently
- **Get contextual code examples** for development

## Installation Status

✅ **VectorCode Tool**: Installed via `uv tool install "vectorcode[legacy]<1.0.0"`  
✅ **Configuration**: Optimized for PokerTool project structure  
✅ **Fallback System**: Text-based search when embeddings aren't available  
✅ **Integration Module**: `vectorcode_integration.py` provides Python API  

## Current Status

The integration is **functional with fallback capabilities**. While there are some compatibility issues with the embedding models on this system, the integration provides a robust fallback text search that works well for finding relevant code.

### Embedding Status
- **Primary**: VectorCode embedding functions have compatibility issues with the current system
- **Fallback**: Text-based search is active and working well
- **Files Indexed**: 35 key files from PokerTool codebase (optimized selection)

## Usage

### Command Line Interface

```bash
# Search for poker-related code
python vectorcode_integration.py query --query "hand evaluation" -n 5

# Search for specific poker concepts
python vectorcode_integration.py poker-search --concept "GTO strategy"

# Check integration status
python vectorcode_integration.py query --query "poker" -n 3
```

### Python API

```python
from vectorcode_integration import VectorCodeIntegration, PokerToolVectorSearch

# Basic integration
vc = VectorCodeIntegration()

# Search for code
results = vc.query("poker hand evaluation", num_results=5)
for result in results:
    print(f"File: {result.path}")
    print(f"Code: {result.document[:200]}...")

# Specialized poker search
search = PokerToolVectorSearch()

# Find poker logic
gto_code = search.find_poker_logic("GTO")
gui_code = search.find_gui_components("table")
db_code = search.find_database_operations("insert")
ml_code = search.find_ml_models("neural network")
tests = search.find_test_cases("core")
```

## File Scope

The integration indexes these key files:

### Python Core
- `src/pokertool/*.py` - All main PokerTool modules
- `tests/test_*.py` - Test files for validation
- `tools/poker_main.py` - Main application entry
- `tools/verify_build.py` - Build verification

### Documentation
- `README.md` - Project overview
- `docs/*.md` - All documentation files

### Configuration
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
- `poker_config.json` - Poker-specific settings

### Frontend (Selected)
- `pokertool-frontend/src/App.tsx` - Main React app
- `pokertool-frontend/src/components/*.tsx` - React components
- `pokertool-frontend/package.json` - Frontend dependencies

### Integration
- `vectorcode_integration.py` - This integration module

## Configuration

### VectorCode Settings (`.vectorcode/config.json`)
```json
{
  "embedding_function": "DefaultEmbeddingFunction",
  "chunk_size": 1500,
  "overlap_ratio": 0.1,
  "query_multiplier": 5,
  "reranker": "NaiveReranker",
  "filetype_map": {
    "python": ["^py$", "^pyi$"],
    "typescript": ["^ts$", "^tsx$"],
    "javascript": ["^js$", "^jsx$"]
  }
}
```

### File Inclusion (`.vectorcode/vectorcode.include`)
Optimized to include only essential files, avoiding the 16,000+ files that would slow down indexing.

## Integration Features

### 1. Intelligent Code Search
```python
# Find all code related to hand analysis
results = vc.query("hand analysis poker evaluation")

# Search for specific implementations
results = vc.find_related_code("gto_solver")
```

### 2. Refactoring Support
```python
# Get context for refactoring a specific file
context = vc.get_context_for_refactoring("src/pokertool/core.py")
# Returns code that imports or depends on core.py
```

### 3. Specialized Poker Searches
```python
search = PokerToolVectorSearch()

# Find poker algorithms
poker_logic = search.find_poker_logic("pot odds")

# Find GUI components
table_widgets = search.find_gui_components("table")

# Find database operations
db_queries = search.find_database_operations("select")
```

### 4. Fallback Functionality
When VectorCode embeddings fail, the system automatically falls back to:
- **Text-based search** with relevance scoring
- **Context extraction** around query matches
- **Multi-file search** across the indexed file set

## Troubleshooting

### Embedding Issues
If you encounter embedding function errors:

1. **Try different embedding functions**:
   ```json
   {
     "embedding_function": "DefaultEmbeddingFunction"
   }
   ```

2. **Use fallback mode** (automatically activated when embeddings fail)

3. **Reinstall with different dependencies**:
   ```bash
   uv tool install "vectorcode[legacy]<1.0.0" --reinstall
   ```

### Performance Issues
If vectorization is slow:

1. **Check file count**: The include file is optimized to ~35 files instead of 16,000+
2. **Adjust chunk size**: Smaller chunks = more granular search but slower indexing
3. **Use manual file selection**: `vectorcode vectorise specific_file.py`

## Development Workflow

### Daily Usage
1. **Search for examples**: Use the integration to find similar code patterns
2. **Refactoring guidance**: Get context about code dependencies
3. **Feature discovery**: Find existing implementations to build upon

### Updating Index
```bash
# Update embeddings after significant changes
vectorcode update

# Re-vectorize specific files
vectorcode vectorise src/pokertool/new_module.py

# Full re-index (if needed)
vectorcode drop && vectorcode vectorise
```

## Examples

### Find Hand Evaluation Code
```python
from vectorcode_integration import VectorCodeIntegration

vc = VectorCodeIntegration()
results = vc.query("hand evaluation strength calculation")

for result in results:
    print(f"📁 {result.path}")
    print(f"📄 {result.document[:300]}...")
    print("-" * 60)
```

### Find GUI Table Components
```python
from vectorcode_integration import PokerToolVectorSearch

search = PokerToolVectorSearch()
components = search.find_gui_components("table display")

for comp in components:
    print(f"🎨 GUI Component: {comp.path}")
    print(f"💻 Code: {comp.document[:200]}...")
```

### Get Refactoring Context
```python
# Before refactoring core.py, find what depends on it
context = vc.get_context_for_refactoring("src/pokertool/core.py")

print("🔄 Files that might be affected by refactoring:")
for ctx in context:
    print(f"   - {ctx.path}")
```

## Benefits

1. **Enhanced Development**: Quickly find relevant code examples and patterns
2. **Better Refactoring**: Understand code dependencies before making changes
3. **Knowledge Discovery**: Explore the codebase using natural language queries
4. **Robust Fallback**: Works even when advanced embeddings are not available
5. **Poker-Specific**: Specialized search functions for poker development

## Future Improvements

1. **Embedding Resolution**: Fix compatibility issues with embedding models
2. **Real-time Updates**: Automatic re-indexing on file changes
3. **IDE Integration**: VSCode extension for direct editor integration
4. **Enhanced Fallbacks**: More sophisticated text search algorithms
5. **Caching**: Improve performance with intelligent caching

## Support

For issues with the VectorCode integration:

1. **Check logs**: Enable logging to see what's happening
2. **Test fallback**: The text search should always work
3. **File an issue**: If the integration breaks completely
4. **Manual search**: Use `grep` or IDE search as ultimate fallback

The integration is designed to enhance your development workflow while providing reliable fallback options when advanced features are not available.
