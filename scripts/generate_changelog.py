#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automated Changelog Generator
==============================

Generates CHANGELOG.md from git commits using conventional commits format.

Supports conventional commit types:
- feat: New features
- fix: Bug fixes
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- perf: Performance improvements
- test: Test additions/changes
- chore: Maintenance tasks
- ci: CI/CD changes
- build: Build system changes

Usage:
    python scripts/generate_changelog.py
    python scripts/generate_changelog.py --version v87.0.2
    python scripts/generate_changelog.py --output custom_changelog.md

Version: 87.0.1
Author: PokerTool Development Team
"""

import subprocess
import re
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
import argparse


class ChangelogGenerator:
    """Generates changelog from git history using conventional commits."""

    # Commit type classifications
    COMMIT_TYPES = {
        'feat': {'title': 'Features', 'emoji': '🚀'},
        'fix': {'title': 'Bug Fixes', 'emoji': '🐛'},
        'docs': {'title': 'Documentation', 'emoji': '📚'},
        'style': {'title': 'Styling', 'emoji': '💎'},
        'refactor': {'title': 'Code Refactoring', 'emoji': '♻️'},
        'perf': {'title': 'Performance Improvements', 'emoji': '⚡'},
        'test': {'title': 'Tests', 'emoji': '✅'},
        'build': {'title': 'Build System', 'emoji': '🔨'},
        'ci': {'title': 'CI/CD', 'emoji': '👷'},
        'chore': {'title': 'Chores', 'emoji': '🧹'},
        'revert': {'title': 'Reverts', 'emoji': '⏪'},
    }

    def __init__(self, output_file: str = 'CHANGELOG.md'):
        self.output_file = output_file
        self.commits_by_type: Dict[str, List[Dict]] = defaultdict(list)

    def get_git_tags(self) -> List[str]:
        """Get all git tags sorted by version."""
        try:
            result = subprocess.run(
                ['git', 'tag', '--sort=-version:refname'],
                capture_output=True,
                text=True,
                check=True
            )
            tags = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
            return tags
        except subprocess.CalledProcessError:
            return []

    def get_commits_between_tags(self, tag1: str = None, tag2: str = None) -> List[str]:
        """Get commits between two tags."""
        if tag1 and tag2:
            range_spec = f'{tag2}..{tag1}'
        elif tag1:
            range_spec = tag1
        else:
            range_spec = 'HEAD'

        try:
            result = subprocess.run(
                ['git', 'log', range_spec, '--pretty=format:%H|||%s|||%an|||%ae|||%ai'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

    def parse_commit(self, commit_line: str) -> Dict:
        """Parse a single commit line into structured data."""
        parts = commit_line.split('|||')
        if len(parts) != 5:
            return None

        commit_hash, subject, author, email, date = parts

        # Parse conventional commit format: type(scope): subject
        pattern = r'^(?P<type>\w+)(?:\((?P<scope>[^\)]+)\))?\s*:\s*(?P<description>.+)$'
        match = re.match(pattern, subject)

        if match:
            commit_type = match.group('type').lower()
            scope = match.group('scope')
            description = match.group('description')
        else:
            # Non-conventional commit
            commit_type = 'other'
            scope = None
            description = subject

        return {
            'hash': commit_hash[:8],
            'type': commit_type,
            'scope': scope,
            'description': description,
            'author': author,
            'email': email,
            'date': date,
            'full_subject': subject
        }

    def categorize_commits(self, commits: List[str]):
        """Categorize commits by type."""
        self.commits_by_type = defaultdict(list)

        for commit_line in commits:
            if not commit_line:
                continue

            commit = self.parse_commit(commit_line)
            if commit:
                self.commits_by_type[commit['type']].append(commit)

    def generate_version_section(self, version: str, date: str, commits: List[str]) -> str:
        """Generate changelog section for a specific version."""
        self.categorize_commits(commits)

        sections = []

        # Version header
        sections.append(f"## [{version}] - {date}\n")

        # Add sections for each commit type
        for commit_type, type_info in self.COMMIT_TYPES.items():
            if commit_type in self.commits_by_type and self.commits_by_type[commit_type]:
                emoji = type_info['emoji']
                title = type_info['title']
                sections.append(f"\n### {emoji} {title}\n")

                for commit in self.commits_by_type[commit_type]:
                    scope = f"**{commit['scope']}**: " if commit['scope'] else ""
                    sections.append(f"- {scope}{commit['description']} ({commit['hash']})")

        # Add uncategorized commits if any
        if 'other' in self.commits_by_type and self.commits_by_type['other']:
            sections.append(f"\n### Other Changes\n")
            for commit in self.commits_by_type['other']:
                sections.append(f"- {commit['full_subject']} ({commit['hash']})")

        sections.append("")  # Empty line after version section
        return '\n'.join(sections)

    def generate_full_changelog(self) -> str:
        """Generate complete changelog from all tags."""
        changelog_lines = [
            "# Changelog\n",
            "All notable changes to this project will be documented in this file.\n",
            "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
            "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n",
            "---\n"
        ]

        tags = self.get_git_tags()

        if not tags:
            # No tags, generate from all commits
            commits = self.get_commits_between_tags()
            if commits:
                date = datetime.now().strftime('%Y-%m-%d')
                changelog_lines.append(self.generate_version_section('Unreleased', date, commits))
        else:
            # Generate for each version
            for i, tag in enumerate(tags):
                next_tag = tags[i + 1] if i + 1 < len(tags) else None
                commits = self.get_commits_between_tags(tag, next_tag)

                if commits:
                    # Get tag date
                    try:
                        result = subprocess.run(
                            ['git', 'log', '-1', '--format=%ai', tag],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        tag_date = result.stdout.strip().split()[0]
                    except:
                        tag_date = datetime.now().strftime('%Y-%m-%d')

                    version_name = tag.lstrip('v')
                    changelog_lines.append(self.generate_version_section(version_name, tag_date, commits))

        return '\n'.join(changelog_lines)

    def write_changelog(self):
        """Write changelog to file."""
        content = self.generate_full_changelog()

        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Changelog generated successfully: {self.output_file}")
        print(f"📊 Total versions: {len(self.get_git_tags())}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate CHANGELOG.md from git commits')
    parser.add_argument(
        '--output',
        '-o',
        default='CHANGELOG.md',
        help='Output file path (default: CHANGELOG.md)'
    )
    parser.add_argument(
        '--version',
        '-v',
        help='Generate changelog for specific version only'
    )

    args = parser.parse_args()

    generator = ChangelogGenerator(output_file=args.output)

    if args.version:
        # Generate for specific version
        tags = generator.get_git_tags()
        if args.version in tags:
            idx = tags.index(args.version)
            next_tag = tags[idx + 1] if idx + 1 < len(tags) else None
            commits = generator.get_commits_between_tags(args.version, next_tag)

            try:
                result = subprocess.run(
                    ['git', 'log', '-1', '--format=%ai', args.version],
                    capture_output=True,
                    text=True,
                    check=True
                )
                tag_date = result.stdout.strip().split()[0]
            except:
                tag_date = datetime.now().strftime('%Y-%m-%d')

            version_name = args.version.lstrip('v')
            content = generator.generate_version_section(version_name, tag_date, commits)
            print(content)
        else:
            print(f"❌ Error: Version {args.version} not found")
            return 1
    else:
        # Generate full changelog
        generator.write_changelog()

    return 0


if __name__ == '__main__':
    exit(main())
