#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tests/test_git_automation.py
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Comprehensive Unit Tests for Git Automation Scripts
Tests git_commit_develop.py and git_commit_main.py functionality
"""

import unittest
import tempfile
import os
import sys
import json
import shutil
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import subprocess

# Add parent directory to path to import git scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGitCommitFunctions(unittest.TestCase):
    """Test common functions used in both git commit scripts"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    @patch('subprocess.run')
    def test_run_git_command_success(self, mock_run):
        """Test successful git command execution"""
        mock_result = MagicMock()
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Import the function
        import git_commit_develop
        stdout, stderr = git_commit_develop.run_git_command("git status")
        
        self.assertEqual(stdout, "test output")
        self.assertEqual(stderr, "")
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_git_command_failure(self, mock_run):
        """Test failed git command execution"""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git status", stderr="fatal: not a git repository"
        )
        
        import git_commit_develop
        stdout, stderr = git_commit_develop.run_git_command("git status")
        
        self.assertIsNone(stdout)
        self.assertIn("fatal: not a git repository", stderr)
    
    def test_count_file_changes(self):
        """Test file change counting logic"""
        import git_commit_develop
        
        status_output = """A  new_file.py
M  modified_file.py
D  deleted_file.py
?? untracked_file.py"""
        
        additions, modifications, deletions = git_commit_develop.count_file_changes(status_output)
        
        self.assertEqual(additions, 2)  # A and ?? files
        self.assertEqual(modifications, 1)  # M files
        self.assertEqual(deletions, 1)  # D files
    
    def test_backup_changed_files(self):
        """Test backup functionality"""
        # Create test files
        test_file = Path(self.temp_dir) / "test_file.py"
        test_file.write_text("test content")
        
        import git_commit_develop
        
        with patch.object(git_commit_develop, 'run_git_command') as mock_git:
            mock_git.side_effect = [
                ("test_file.py", ""),  # git diff --name-only HEAD
                ("", "")  # git ls-files --others --exclude-standard
            ]
            
            backup_dir = git_commit_develop.backup_changed_files(self.temp_dir)
            
            # Check backup directory exists
            self.assertTrue(backup_dir.exists())
            
            # Check backup file exists
            backup_file = backup_dir / "test_file.py"
            self.assertTrue(backup_file.exists())
            self.assertEqual(backup_file.read_text(), "test content")
    
    def test_log_commit_info(self):
        """Test commit logging functionality"""
        import git_commit_develop
        
        changes_summary = {
            "additions": 1,
            "modifications": 2,
            "deletions": 0,
            "total": 3
        }
        
        git_commit_develop.log_commit_info(
            self.temp_dir,
            "abc123def456",
            changes_summary
        )
        
        log_file = Path(self.temp_dir) / "commit_log.json"
        self.assertTrue(log_file.exists())
        
        with open(log_file, 'r') as f:
            logs = json.load(f)
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["commit_hash"], "abc123def456")
        self.assertEqual(logs[0]["changes_summary"]["total"], 3)

class TestGitCommitDevelop(unittest.TestCase):
    """Test git_commit_develop.py specific functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    @patch('git_commit_develop.run_git_command')
    @patch('builtins.print')
    def test_main_no_changes(self, mock_print, mock_git):
        """Test main function when no changes exist"""
        mock_git.side_effect = [
            ("On branch develop", ""),  # git status
            ("develop", ""),  # git branch --show-current
            ("", ""),  # git pull origin develop
            ("", "")  # git status --porcelain
        ]
        
        import git_commit_develop
        git_commit_develop.main()
        
        # Check that it exits early when no changes
        mock_print.assert_any_call("✅ No changes to commit.")
    
    @patch('git_commit_develop.run_git_command')
    @patch('git_commit_develop.backup_changed_files')
    @patch('git_commit_develop.log_commit_info')
    @patch('builtins.print')
    def test_main_with_changes(self, mock_print, mock_log, mock_backup, mock_git):
        """Test main function with changes to commit"""
        mock_backup.return_value = Path(self.temp_dir) / "backup"
        
        mock_git.side_effect = [
            ("On branch develop", ""),  # git status
            ("develop", ""),  # git branch --show-current
            ("", ""),  # git pull origin develop
            ("M  test.py", ""),  # git status --porcelain
            ("", ""),  # git add .
            ("", ""),  # git commit
            ("abc123", ""),  # git rev-parse HEAD
            ("", "")  # git push origin develop
        ]
        
        import git_commit_develop
        git_commit_develop.main()
        
        mock_print.assert_any_call("✅ Successfully committed and pushed to develop branch!")

class TestGitCommitMain(unittest.TestCase):
    """Test git_commit_main.py specific functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    @patch('git_commit_main.run_git_command')
    def test_run_tests_success(self, mock_git):
        """Test successful test execution"""
        mock_git.return_value = ("All tests passed", "")
        
        import git_commit_main
        result = git_commit_main.run_tests(self.temp_dir)
        
        self.assertTrue(result)
    
    @patch('git_commit_main.run_git_command')
    def test_run_tests_failure(self, mock_git):
        """Test failed test execution"""
        mock_git.return_value = (None, "Tests failed")
        
        import git_commit_main
        result = git_commit_main.run_tests(self.temp_dir)
        
        self.assertFalse(result)
    
    @patch('git_commit_main.run_git_command')
    def test_check_branch_sync_in_sync(self, mock_git):
        """Test branch synchronization check when in sync"""
        mock_git.side_effect = [
            ("abc123", ""),  # git rev-parse main
            ("abc123", "")   # git rev-parse develop
        ]
        
        import git_commit_main
        result = git_commit_main.check_branch_sync(self.temp_dir)
        
        self.assertTrue(result)
    
    @patch('git_commit_main.run_git_command')
    def test_check_branch_sync_out_of_sync(self, mock_git):
        """Test branch synchronization check when out of sync"""
        mock_git.side_effect = [
            ("abc123", ""),  # git rev-parse main
            ("def456", ""),  # git rev-parse develop
            ("2\t1", "")     # git rev-list --left-right --count
        ]
        
        import git_commit_main
        result = git_commit_main.check_branch_sync(self.temp_dir)
        
        self.assertFalse(result)
    
    @patch('git_commit_main.run_git_command')
    def test_create_release_tag_new(self, mock_git):
        """Test creating new release tag"""
        mock_git.side_effect = [
            ("", ""),  # git tag -l v25 (tag doesn't exist)
            ("", "")   # git tag -a v25
        ]
        
        import git_commit_main
        tag_name = git_commit_main.create_release_tag(self.temp_dir, "25")
        
        self.assertEqual(tag_name, "v25")
    
    @patch('git_commit_main.run_git_command')
    def test_create_release_tag_exists(self, mock_git):
        """Test creating release tag when it already exists"""
        mock_git.side_effect = [
            ("v25", ""),  # git tag -l v25 (tag exists)
            ("", "")      # git tag -a v25-timestamp
        ]
        
        import git_commit_main
        tag_name = git_commit_main.create_release_tag(self.temp_dir, "25")
        
        self.assertTrue(tag_name.startswith("v25-"))
    
    @patch('git_commit_main.run_git_command')
    @patch('builtins.print')
    def test_safety_abort_too_many_deletions(self, mock_print, mock_git):
        """Test safety abort with too many deletions"""
        mock_git.side_effect = [
            ("On branch main", ""),  # git status
            ("main", ""),  # git branch --show-current
            ("", ""),  # git pull origin main
            ("abc123", ""),  # git rev-parse main
            ("def456", ""),  # git rev-parse develop
            ("D  " + "\nD  ".join([f"file{i}.py" for i in range(15)]), "")  # 15 deletions
        ]
        
        import git_commit_main
        with self.assertRaises(SystemExit):
            git_commit_main.main()
        
        mock_print.assert_any_call("🚨 PRODUCTION SAFETY ABORT: 15 file deletions detected!")

class TestVersionUpdate(unittest.TestCase):
    """Test version update functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = {}
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename, content):
        """Helper to create test files with version strings"""
        file_path = Path(self.temp_dir) / filename
        file_path.write_text(content)
        self.test_files[filename] = file_path
        return file_path
    
    def test_version_string_detection(self):
        """Test detection of various version string formats"""
        version_patterns = [
            'version = "25"',
            'VERSION = "25"',
            '__version__ = "25"',
            '"version": "24"',
            'version: 24',
            'v25',
            'version-24'
        ]
        
        for pattern in version_patterns:
            with self.subTest(pattern=pattern):
                file_path = self.create_test_file("test.py", f"# Test file\n{pattern}\n# End")
                content = file_path.read_text()
                self.assertIn("24", content)
    
    def test_version_update_python_files(self):
        """Test updating version in Python files"""
        python_content = '''#!/usr/bin/env python3
"""
Pokertool Application
Version 25
"""

__version__ = "25"
VERSION = "25"

def get_version():
    return "25"
'''
        
        file_path = self.create_test_file("pokertool.py", python_content)
        
        # Simulate version update
        updated_content = python_content.replace("24", "25")
        file_path.write_text(updated_content)
        
        final_content = file_path.read_text()
        self.assertIn('__version__ = "25"', final_content)
        self.assertIn('VERSION = "25"', final_content)
        self.assertIn('Version 25', final_content)
        self.assertNotIn('24', final_content)
    
    def test_version_update_json_files(self):
        """Test updating version in JSON files"""
        json_content = '''{
    "name": "pokertool",
    "version": "24",
    "description": "Advanced poker analysis tool"
}'''
        
        file_path = self.create_test_file("package.json", json_content)
        
        # Load, update, and save JSON
        import json as json_module
        data = json_module.loads(json_content)
        data["version"] = "25"
        
        with open(file_path, 'w') as f:
            json_module.dump(data, f, indent=2)
        
        final_content = file_path.read_text()
        self.assertIn('"version": "25"', final_content)
    
    def test_version_update_markdown_files(self):
        """Test updating version in Markdown files"""
        markdown_content = '''# Pokertool v25

## Version 25 Release Notes

- Enhanced GTO solver
- Improved ML opponent modeling
- Version 25 stability improvements
'''
        
        file_path = self.create_test_file("README.md", markdown_content)
        
        # Simulate version update
        updated_content = markdown_content.replace("24", "25")
        file_path.write_text(updated_content)
        
        final_content = file_path.read_text()
        self.assertIn('# Pokertool v25', final_content)
        self.assertIn('## Version 25 Release Notes', final_content)

class TestScriptIntegration(unittest.TestCase):
    """Test integration between git commit scripts and other components"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_backup_system_integration(self):
        """Test that backup system works with real files"""
        # Create test files
        (Path(self.temp_dir) / "src").mkdir()
        (Path(self.temp_dir) / "src" / "test.py").write_text("print('hello')")
        (Path(self.temp_dir) / "README.md").write_text("# Test Project")
        
        import git_commit_develop
        
        with patch.object(git_commit_develop, 'run_git_command') as mock_git:
            mock_git.side_effect = [
                ("src/test.py\nREADME.md", ""),  # git diff --name-only HEAD
                ("", "")  # git ls-files --others --exclude-standard
            ]
            
            backup_dir = git_commit_develop.backup_changed_files(self.temp_dir)
            
            # Verify backups
            self.assertTrue((backup_dir / "src" / "test.py").exists())
            self.assertTrue((backup_dir / "README.md").exists())
            self.assertEqual(
                (backup_dir / "src" / "test.py").read_text(),
                "print('hello')"
            )
    
    def test_commit_log_persistence(self):
        """Test that commit logs persist across multiple commits"""
        import git_commit_develop
        
        # First commit
        changes1 = {"additions": 1, "modifications": 0, "deletions": 0, "total": 1}
        git_commit_develop.log_commit_info(self.temp_dir, "hash1", changes1)
        
        # Second commit
        changes2 = {"additions": 0, "modifications": 2, "deletions": 1, "total": 3}
        git_commit_develop.log_commit_info(self.temp_dir, "hash2", changes2)
        
        # Verify log contains both commits
        log_file = Path(self.temp_dir) / "commit_log.json"
        with open(log_file, 'r') as f:
            logs = json.load(f)
        
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0]["commit_hash"], "hash1")
        self.assertEqual(logs[1]["commit_hash"], "hash2")

class TestErrorScenarios(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    @patch('git_commit_develop.run_git_command')
    def test_not_git_repository(self, mock_git):
        """Test behavior when not in a git repository"""
        mock_git.return_value = (None, "fatal: not a git repository")
        
        import git_commit_develop
        with self.assertRaises(SystemExit):
            git_commit_develop.main()
    
    @patch('git_commit_develop.run_git_command')
    @patch('builtins.print')
    def test_failed_branch_switch(self, mock_print, mock_git):
        """Test handling of failed branch switch"""
        mock_git.side_effect = [
            ("On branch main", ""),  # git status
            ("main", ""),  # git branch --show-current
            (None, "error: pathspec 'develop' did not match")  # git checkout develop
        ]
        
        import git_commit_develop
        with self.assertRaises(SystemExit):
            git_commit_develop.main()
        
        mock_print.assert_any_call("❌ Failed to switch to develop branch")
    
    def test_backup_permission_error(self):
        """Test backup creation with permission errors"""
        import git_commit_develop
        
        # Create read-only file
        test_file = Path(self.temp_dir) / "readonly.txt"
        test_file.write_text("content")
        test_file.chmod(0o444)
        
        with patch.object(git_commit_develop, 'run_git_command') as mock_git:
            mock_git.side_effect = [
                ("readonly.txt", ""),
                ("", "")
            ]
            
            # Should handle permission errors gracefully
            backup_dir = git_commit_develop.backup_changed_files(self.temp_dir)
            
            # Backup directory should still be created
            self.assertTrue(backup_dir.exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
