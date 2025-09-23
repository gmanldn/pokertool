#!/usr/bin/env python3
"""
VectorCode Integration for PokerTool

This module provides integration between VectorCode and the PokerTool codebase,
allowing for intelligent code search and context retrieval using vector embeddings.
Includes fallback functionality when VectorCode is not available.
"""

import os
import re
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VectorCodeQuery:
    """Represents a query result from VectorCode."""
    path: str
    document: str
    relevance_score: Optional[float] = None


class VectorCodeIntegration:
    """Main integration class for VectorCode with PokerTool."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize VectorCode integration.
        
        Args:
            project_root: Path to the project root. Defaults to current directory.
        """
        self.project_root = project_root or Path.cwd()
        self.vectorcode_dir = self.project_root / ".vectorcode"
        self.vectorcode_available = self._check_vectorcode_availability()
        
        if not self.vectorcode_dir.exists():
            logger.warning(f"VectorCode not initialized at {self.project_root}")
            self.vectorcode_available = False
    
    def _check_vectorcode_availability(self) -> bool:
        """Check if VectorCode is available and working."""
        try:
            result = subprocess.run(
                ["vectorcode", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def vectorize_codebase(self, force: bool = False) -> Dict[str, Any]:
        """Vectorize the entire codebase according to vectorcode.include file.
        
        Args:
            force: If True, force re-vectorization even for unchanged files.
            
        Returns:
            Dictionary with vectorization statistics.
        """
        cmd = ["vectorcode", "vectorise"]
        if force:
            cmd.append("-f")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Try to parse JSON output if in pipe mode
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {
                    "status": "success",
                    "output": result.stdout
                }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error": e.stderr
            }
    
    def update_embeddings(self) -> Dict[str, Any]:
        """Update embeddings for all indexed files."""
        try:
            result = subprocess.run(
                ["vectorcode", "update"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "status": "success",
                "output": result.stdout
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error": e.stderr
            }
    
    def query(self, query_text: str, num_results: int = 5) -> List[VectorCodeQuery]:
        """Query the vectorized codebase for relevant code.
        
        Args:
            query_text: The search query.
            num_results: Number of results to return.
            
        Returns:
            List of VectorCodeQuery objects with relevant code snippets.
        """
        if not self.vectorcode_available:
            logger.info("VectorCode not available, using fallback text search")
            return self._fallback_search(query_text, num_results)
        
        cmd = [
            "vectorcode", "query",
            query_text,
            "-n", str(num_results),
            "--pipe"  # Get JSON output
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            
            # Parse JSON output
            results_json = json.loads(result.stdout)
            
            queries = []
            for item in results_json:
                queries.append(VectorCodeQuery(
                    path=item.get("path", ""),
                    document=item.get("document", "")
                ))
            
            return queries
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            logger.warning(f"VectorCode query failed: {e}, falling back to text search")
            return self._fallback_search(query_text, num_results)
    
    def _fallback_search(self, query_text: str, num_results: int = 5) -> List[VectorCodeQuery]:
        """Fallback text-based search when VectorCode is not available.
        
        Args:
            query_text: The search query.
            num_results: Number of results to return.
            
        Returns:
            List of VectorCodeQuery objects with relevant code snippets.
        """
        results = []
        query_words = query_text.lower().split()
        
        # Define search paths based on the include file
        search_paths = [
            "src/pokertool/*.py",
            "tests/test_*.py", 
            "tools/poker_main.py",
            "tools/verify_build.py",
            "README.md",
            "docs/*.md",
            "vectorcode_integration.py"
        ]
        
        file_scores = {}
        
        for pattern in search_paths:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        
                        # Simple scoring based on query word frequency
                        score = 0
                        content_lower = content.lower()
                        
                        for word in query_words:
                            # Count occurrences of each query word
                            word_count = content_lower.count(word)
                            score += word_count
                            
                            # Bonus for exact phrase matches
                            if query_text.lower() in content_lower:
                                score += 10
                        
                        if score > 0:
                            relative_path = str(file_path.relative_to(self.project_root))
                            file_scores[relative_path] = (score, content)
                    
                    except (UnicodeDecodeError, PermissionError):
                        continue
        
        # Sort by score and return top results
        sorted_files = sorted(file_scores.items(), key=lambda x: x[1][0], reverse=True)
        
        for file_path, (score, content) in sorted_files[:num_results]:
            # Extract relevant snippet around query words
            snippet = self._extract_relevant_snippet(content, query_words)
            
            results.append(VectorCodeQuery(
                path=file_path,
                document=snippet,
                relevance_score=float(score)
            ))
        
        return results
    
    def _extract_relevant_snippet(self, content: str, query_words: List[str], max_length: int = 2000) -> str:
        """Extract relevant code snippet containing query words.
        
        Args:
            content: Full file content.
            query_words: List of query words to search for.
            max_length: Maximum length of the snippet.
            
        Returns:
            Relevant code snippet.
        """
        lines = content.split('\n')
        relevant_lines = []
        
        # Find lines containing query words
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(word in line_lower for word in query_words):
                # Include context: 2 lines before and after
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                relevant_lines.extend(range(start, end))
        
        # Remove duplicates and sort
        relevant_lines = sorted(set(relevant_lines))
        
        # If we found relevant lines, return them
        if relevant_lines:
            snippet_lines = [lines[i] for i in relevant_lines[:50]]  # Limit to 50 lines
            snippet = '\n'.join(snippet_lines)
        else:
            # If no specific matches, return beginning of file
            snippet = '\n'.join(lines[:30])
        
        # Truncate if too long
        if len(snippet) > max_length:
            snippet = snippet[:max_length] + "\n... [truncated]"
        
        return snippet
    
    def find_related_code(self, module_name: str) -> List[VectorCodeQuery]:
        """Find code related to a specific module or feature.
        
        Args:
            module_name: Name of the module or feature to search for.
            
        Returns:
            List of related code snippets.
        """
        # Create context-aware query
        query = f"code related to {module_name} implementation functions classes"
        return self.query(query, num_results=10)
    
    def find_similar_implementations(self, code_snippet: str) -> List[VectorCodeQuery]:
        """Find similar code implementations in the codebase.
        
        Args:
            code_snippet: Code snippet to find similar implementations for.
            
        Returns:
            List of similar code snippets.
        """
        return self.query(code_snippet, num_results=5)
    
    def get_context_for_refactoring(self, file_path: str) -> List[VectorCodeQuery]:
        """Get relevant context for refactoring a specific file.
        
        Args:
            file_path: Path to the file being refactored.
            
        Returns:
            List of related code that might be affected by refactoring.
        """
        # Extract module/class names from file path
        module_name = Path(file_path).stem
        query = f"imports {module_name} uses {module_name} depends on {module_name}"
        return self.query(query, num_results=10)
    
    def list_collections(self) -> Dict[str, Any]:
        """List all VectorCode collections in the database."""
        try:
            result = subprocess.run(
                ["vectorcode", "ls", "--pipe"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error": e.stderr
            }
    
    def drop_collection(self) -> bool:
        """Drop the current project's collection from the database."""
        try:
            subprocess.run(
                ["vectorcode", "drop"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


# Specialized search functions for PokerTool
class PokerToolVectorSearch:
    """Specialized vector search functionality for PokerTool components."""
    
    def __init__(self):
        self.vc = VectorCodeIntegration()
    
    def find_poker_logic(self, concept: str) -> List[VectorCodeQuery]:
        """Find poker-related logic implementations.
        
        Args:
            concept: Poker concept like 'hand evaluation', 'pot odds', 'GTO', etc.
            
        Returns:
            List of relevant code snippets.
        """
        query = f"poker {concept} calculate compute evaluate algorithm"
        return self.vc.query(query, num_results=10)
    
    def find_gui_components(self, component_type: str) -> List[VectorCodeQuery]:
        """Find GUI components in the codebase.
        
        Args:
            component_type: Type of GUI component (e.g., 'table', 'button', 'overlay')
            
        Returns:
            List of relevant GUI code.
        """
        query = f"GUI tkinter widget {component_type} display render draw"
        return self.vc.query(query, num_results=8)
    
    def find_database_operations(self, operation: str) -> List[VectorCodeQuery]:
        """Find database-related operations.
        
        Args:
            operation: Database operation like 'insert', 'query', 'update', etc.
            
        Returns:
            List of database operation code.
        """
        query = f"database SQL {operation} table session query storage"
        return self.vc.query(query, num_results=8)
    
    def find_ml_models(self, model_type: str = "") -> List[VectorCodeQuery]:
        """Find machine learning model implementations.
        
        Args:
            model_type: Specific model type or empty for all ML code.
            
        Returns:
            List of ML-related code.
        """
        query = f"machine learning ML model {model_type} train predict neural network"
        return self.vc.query(query, num_results=10)
    
    def find_test_cases(self, module: str) -> List[VectorCodeQuery]:
        """Find test cases for a specific module.
        
        Args:
            module: Module name to find tests for.
            
        Returns:
            List of test code snippets.
        """
        query = f"test pytest unittest {module} assert test_"
        return self.vc.query(query, num_results=10)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VectorCode Integration for PokerTool")
    parser.add_argument("action", choices=["vectorize", "update", "query", "poker-search"],
                       help="Action to perform")
    parser.add_argument("--query", help="Query text for search operations")
    parser.add_argument("--concept", help="Poker concept for specialized search")
    parser.add_argument("-n", "--num-results", type=int, default=5,
                       help="Number of results to return")
    parser.add_argument("--force", action="store_true",
                       help="Force re-vectorization")
    
    args = parser.parse_args()
    
    # Initialize integration
    vc = VectorCodeIntegration()
    
    if args.action == "vectorize":
        print("Vectorizing codebase...")
        result = vc.vectorize_codebase(force=args.force)
        print(json.dumps(result, indent=2))
    
    elif args.action == "update":
        print("Updating embeddings...")
        result = vc.update_embeddings()
        print(json.dumps(result, indent=2))
    
    elif args.action == "query":
        if not args.query:
            parser.error("--query is required for query action")
        
        results = vc.query(args.query, args.num_results)
        for i, result in enumerate(results, 1):
            print(f"\n{'='*60}")
            print(f"Result {i}: {result.path}")
            print(f"{'='*60}")
            print(result.document[:500] + "..." if len(result.document) > 500 else result.document)
    
    elif args.action == "poker-search":
        if not args.concept:
            parser.error("--concept is required for poker-search action")
        
        search = PokerToolVectorSearch()
        results = search.find_poker_logic(args.concept)
        
        for i, result in enumerate(results, 1):
            print(f"\n{'='*60}")
            print(f"Result {i}: {result.path}")
            print(f"{'='*60}")
            print(result.document[:500] + "..." if len(result.document) > 500 else result.document)


if __name__ == "__main__":
    main()
