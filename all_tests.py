#!/usr/bin/env python3
"""
Comprehensive Test Runner for PokerTool Project
Discovers and runs all tests, logging results and providing detailed reporting.
"""

import os
import sys
import unittest
import subprocess
import logging
import time
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Any

class TestRunner:
    def __init__(self, log_file: str = None):
        """Initialize the test runner with logging configuration."""
        self.start_time = datetime.now()
        self.log_file = log_file or f"test_results_{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Test results storage
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'test_files': [],
            'failed_tests': [],
            'error_tests': [],
            'start_time': self.start_time.isoformat(),
            'end_time': None,
            'duration': None
        }
        
        # Test directories and patterns - focus on project tests only
        self.test_dirs = [
            'tests/',
            'src/test/',
            '.',  # Root directory for standalone test files
        ]
        
        self.test_patterns = [
            'test_*.py',
            '*_test.py',
            '*test*.py'
        ]
        
        # Directories to exclude
        self.exclude_dirs = [
            'venv/',
            'node_modules/',
            '.git/',
            '__pycache__/',
            'VectorCode/',
            'evals/',
            'backups/',
            'webview-ui/',
            'standalone/',
            'docs/',
            'build_reports/',
            'k8s/',
            'locales/',
            'proto/',
            'scripts/',
            'src/core/',
            'src/api/',
            'src/dev/',
            'src/exports/',
            'src/hosts/',
            'src/integrations/',
            'src/packages/',
            'src/services/',
            'src/shared/',
            'src/standalone/',
            'src/utils/',
            'testing-platform/',
            'tools/',
            'walkthrough/',
            'pokertool-frontend/'
        ]
        
        self.standalone_tests = [
            'test_gui_fix.py',
            'test_onnx_fix.py',
            'test_poker_gui_enhanced.py',
            'test_screen_scraper.py',
            'final_test_validation.py',
            'security_validation_tests.py'
        ]

    def discover_test_files(self) -> List[Path]:
        """Discover all test files in the project."""
        test_files = []
        root_path = Path('.')
        
        # Find test files in specified directories
        for test_dir in self.test_dirs:
            test_path = Path(test_dir)
            if test_path.exists():
                for pattern in self.test_patterns:
                    found_files = test_path.rglob(pattern)
                    # Filter out excluded directories
                    for test_file in found_files:
                        excluded = False
                        for exclude_dir in self.exclude_dirs:
                            if exclude_dir.rstrip('/') in str(test_file.parent):
                                excluded = True
                                break
                        if not excluded:
                            test_files.append(test_file)
        
        # Add standalone test files from root
        for test_file in self.standalone_tests:
            test_path = Path(test_file)
            if test_path.exists():
                test_files.append(test_path)
        
        # Remove duplicates and sort
        test_files = list(set(test_files))
        test_files.sort()
        
        self.logger.info(f"Discovered {len(test_files)} test files:")
        for test_file in test_files:
            self.logger.info(f"  - {test_file}")
        
        return test_files

    def run_unittest_file(self, test_file: Path) -> Dict[str, Any]:
        """Run a single test file using unittest."""
        result = {
            'file': str(test_file),
            'framework': 'unittest',
            'tests_run': 0,
            'failures': 0,
            'errors': 0,
            'skipped': 0,
            'success': False,
            'output': '',
            'duration': 0
        }
        
        start_time = time.time()
        self.logger.info(f"Running unittest file: {test_file}")
        
        try:
            # Try to run with unittest
            cmd = [sys.executable, '-m', 'unittest', str(test_file).replace('.py', '').replace('/', '.').replace('\\', '.')]
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per test file
                cwd=str(Path.cwd())
            )
            
            result['output'] = process.stdout + process.stderr
            result['duration'] = time.time() - start_time
            
            # Parse unittest output
            if process.returncode == 0:
                result['success'] = True
                # Try to extract test count from output
                output_lines = result['output'].split('\n')
                for line in output_lines:
                    if 'Ran' in line and 'test' in line:
                        try:
                            parts = line.split()
                            result['tests_run'] = int(parts[1])
                        except (IndexError, ValueError):
                            result['tests_run'] = 1
                        break
            else:
                # Parse failures and errors
                output_lines = result['output'].split('\n')
                for line in output_lines:
                    if 'FAILED' in line or 'ERROR' in line:
                        if 'failures=' in line:
                            try:
                                failures = int(line.split('failures=')[1].split(',')[0].split(')')[0])
                                result['failures'] = failures
                            except (IndexError, ValueError):
                                pass
                        if 'errors=' in line:
                            try:
                                errors = int(line.split('errors=')[1].split(',')[0].split(')')[0])
                                result['errors'] = errors
                            except (IndexError, ValueError):
                                pass
                
        except subprocess.TimeoutExpired:
            result['output'] = f"Test timed out after 5 minutes"
            result['errors'] = 1
            result['duration'] = 300
        except Exception as e:
            result['output'] = f"Error running test: {str(e)}"
            result['errors'] = 1
            result['duration'] = time.time() - start_time
        
        return result

    def run_pytest_file(self, test_file: Path) -> Dict[str, Any]:
        """Run a single test file using pytest if available."""
        result = {
            'file': str(test_file),
            'framework': 'pytest',
            'tests_run': 0,
            'failures': 0,
            'errors': 0,
            'skipped': 0,
            'success': False,
            'output': '',
            'duration': 0
        }
        
        start_time = time.time()
        self.logger.info(f"Running pytest file: {test_file}")
        
        try:
            # Check if pytest is available
            subprocess.run([sys.executable, '-m', 'pytest', '--version'], 
                         capture_output=True, check=True)
            
            # Run with pytest
            cmd = [sys.executable, '-m', 'pytest', str(test_file), '-v', '--tb=short']
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(Path.cwd())
            )
            
            result['output'] = process.stdout + process.stderr
            result['duration'] = time.time() - start_time
            
            if process.returncode == 0:
                result['success'] = True
            
            # Parse pytest output for statistics
            output_lines = result['output'].split('\n')
            for line in output_lines:
                if ' passed' in line or ' failed' in line or ' error' in line:
                    try:
                        if ' passed' in line:
                            result['tests_run'] = int(line.split()[0])
                        if ' failed' in line:
                            result['failures'] = int(line.split()[0])
                        if ' error' in line:
                            result['errors'] = int(line.split()[0])
                    except (IndexError, ValueError):
                        pass
                
        except subprocess.CalledProcessError:
            # pytest not available, fall back to direct execution
            return self.run_direct_execution(test_file)
        except subprocess.TimeoutExpired:
            result['output'] = f"Test timed out after 5 minutes"
            result['errors'] = 1
            result['duration'] = 300
        except Exception as e:
            result['output'] = f"Error running test: {str(e)}"
            result['errors'] = 1
            result['duration'] = time.time() - start_time
        
        return result

    def run_direct_execution(self, test_file: Path) -> Dict[str, Any]:
        """Run a test file by direct execution."""
        result = {
            'file': str(test_file),
            'framework': 'direct',
            'tests_run': 1,
            'failures': 0,
            'errors': 0,
            'skipped': 0,
            'success': False,
            'output': '',
            'duration': 0
        }
        
        start_time = time.time()
        self.logger.info(f"Running direct execution: {test_file}")
        
        try:
            cmd = [sys.executable, str(test_file)]
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(Path.cwd())
            )
            
            result['output'] = process.stdout + process.stderr
            result['duration'] = time.time() - start_time
            
            if process.returncode == 0:
                result['success'] = True
            else:
                result['errors'] = 1
                
        except subprocess.TimeoutExpired:
            result['output'] = f"Test timed out after 5 minutes"
            result['errors'] = 1
            result['duration'] = 300
        except Exception as e:
            result['output'] = f"Error running test: {str(e)}"
            result['errors'] = 1
            result['duration'] = time.time() - start_time
        
        return result

    def run_single_test(self, test_file: Path) -> Dict[str, Any]:
        """Run a single test file with fallback strategies."""
        self.logger.info(f"Starting test: {test_file}")
        
        # Try pytest first, then unittest, then direct execution
        strategies = [
            self.run_pytest_file,
            self.run_unittest_file,
            self.run_direct_execution
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                result = strategy(test_file)
                if result['success'] or i == len(strategies) - 1:
                    self.logger.info(f"Test completed: {test_file} - Success: {result['success']}")
                    return result
            except Exception as e:
                self.logger.error(f"Strategy {i+1} failed for {test_file}: {str(e)}")
                if i == len(strategies) - 1:
                    # Last strategy failed
                    return {
                        'file': str(test_file),
                        'framework': 'failed',
                        'tests_run': 0,
                        'failures': 0,
                        'errors': 1,
                        'skipped': 0,
                        'success': False,
                        'output': f"All strategies failed. Last error: {str(e)}",
                        'duration': 0
                    }
        
        return result

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all discovered tests and compile results."""
        self.logger.info("=" * 80)
        self.logger.info("POKERTOOL COMPREHENSIVE TEST RUNNER")
        self.logger.info("=" * 80)
        self.logger.info(f"Started at: {self.start_time}")
        self.logger.info(f"Log file: {self.log_file}")
        
        # Discover test files
        test_files = self.discover_test_files()
        
        if not test_files:
            self.logger.warning("No test files found!")
            return self.results
        
        # Run each test file
        for i, test_file in enumerate(test_files, 1):
            self.logger.info(f"\n[{i}/{len(test_files)}] Processing: {test_file}")
            
            try:
                result = self.run_single_test(test_file)
                self.results['test_files'].append(result)
                
                # Update totals
                self.results['total_tests'] += result['tests_run']
                self.results['passed'] += (result['tests_run'] - result['failures'] - result['errors'])
                self.results['failed'] += result['failures']
                self.results['errors'] += result['errors']
                self.results['skipped'] += result['skipped']
                
                # Track failed/error tests
                if result['failures'] > 0:
                    self.results['failed_tests'].append(result)
                if result['errors'] > 0:
                    self.results['error_tests'].append(result)
                
                # Log result
                status = "PASS" if result['success'] else "FAIL"
                self.logger.info(f"  Result: {status} ({result['tests_run']} tests, "
                               f"{result['failures']} failures, {result['errors']} errors)")
                
            except Exception as e:
                self.logger.error(f"  Failed to run {test_file}: {str(e)}")
                self.logger.error(f"  Traceback: {traceback.format_exc()}")
                
                # Add to error results
                error_result = {
                    'file': str(test_file),
                    'framework': 'error',
                    'tests_run': 0,
                    'failures': 0,
                    'errors': 1,
                    'skipped': 0,
                    'success': False,
                    'output': f"Runner error: {str(e)}",
                    'duration': 0
                }
                self.results['test_files'].append(error_result)
                self.results['errors'] += 1
                self.results['error_tests'].append(error_result)
        
        # Finalize results
        self.results['end_time'] = datetime.now().isoformat()
        self.results['duration'] = (datetime.now() - self.start_time).total_seconds()
        
        return self.results

    def print_summary(self):
        """Print a detailed summary of test results."""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("TEST SUMMARY")
        self.logger.info("=" * 80)
        
        self.logger.info(f"Total test files: {len(self.results['test_files'])}")
        self.logger.info(f"Total tests run: {self.results['total_tests']}")
        self.logger.info(f"Passed: {self.results['passed']}")
        self.logger.info(f"Failed: {self.results['failed']}")
        self.logger.info(f"Errors: {self.results['errors']}")
        self.logger.info(f"Skipped: {self.results['skipped']}")
        self.logger.info(f"Duration: {self.results['duration']:.2f} seconds")
        
        # Success rate
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed'] / self.results['total_tests']) * 100
            self.logger.info(f"Success rate: {success_rate:.1f}%")
        
        # Failed tests details
        if self.results['failed_tests']:
            self.logger.info(f"\nFAILED TESTS ({len(self.results['failed_tests'])}):")
            for test in self.results['failed_tests']:
                self.logger.info(f"  - {test['file']}: {test['failures']} failures")
        
        # Error tests details
        if self.results['error_tests']:
            self.logger.info(f"\nERROR TESTS ({len(self.results['error_tests'])}):")
            for test in self.results['error_tests']:
                self.logger.info(f"  - {test['file']}: {test['errors']} errors")
        
        # Detailed output for failed/error tests
        if self.results['failed_tests'] or self.results['error_tests']:
            self.logger.info(f"\nDETAILED OUTPUT:")
            self.logger.info("-" * 80)
            
            for test in self.results['failed_tests'] + self.results['error_tests']:
                self.logger.info(f"\n{test['file']} ({test['framework']}):")
                self.logger.info(f"Output:\n{test['output']}")
                self.logger.info("-" * 40)

    def save_json_report(self):
        """Save detailed results to JSON file."""
        json_file = self.log_file.replace('.log', '_report.json')
        try:
            with open(json_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            self.logger.info(f"\nDetailed JSON report saved to: {json_file}")
        except Exception as e:
            self.logger.error(f"Failed to save JSON report: {str(e)}")

def main():
    """Main entry point."""
    print("PokerTool Comprehensive Test Runner")
    print("=" * 50)
    
    # Create test runner
    runner = TestRunner()
    
    try:
        # Run all tests
        results = runner.run_all_tests()
        
        # Print summary
        runner.print_summary()
        
        # Save JSON report
        runner.save_json_report()
        
        # Exit with appropriate code
        if results['failed'] > 0 or results['errors'] > 0:
            print(f"\n❌ Tests completed with failures/errors!")
            print(f"Log file: {runner.log_file}")
            sys.exit(1)
        else:
            print(f"\n✅ All tests passed!")
            print(f"Log file: {runner.log_file}")
            sys.exit(0)
            
    except KeyboardInterrupt:
        runner.logger.info("\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        runner.logger.error(f"Fatal error: {str(e)}")
        runner.logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
