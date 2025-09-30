#!/usr/bin/env python3
from __future__ import annotations

"""
POKERTOOL-HEADER-START
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: update_v24_2.py
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""

import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent
THIS_FILE = Path(__file__).resolve()

HEADER_START = "POKERTOOL-HEADER-START"
HEADER_END = "POKERTOOL-HEADER-END"

def run_git(args: list[str]) -> str:
    try:
        out = subprocess.check_output(["git", *args], cwd=REPO_ROOT)
        return out.decode("utf-8", errors="replace").strip()
    except Exception:
        return ""

def get_git_metadata() -> dict[str, str]:
    # ISO timestamp of HEAD commit (fall back to now if missing)
    iso = run_git(["show", "-s", "--format=%cI", "HEAD"])
    if not iso:
        iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    return {
        "branch": run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown",
        "commit": run_git(["rev-parse", "HEAD"])[:12] or "unknown",
        "tag": run_git(["describe", "--tags", "--abbrev=0"]) or "",
        "last_commit_iso": iso,
    }

def extract_existing_header(text: str) -> tuple[str, dict]:
    """Returns (new_text_without_header, parsed_header_dict or {})."""
    start_idx = text.find(HEADER_START)
    end_idx = text.find(HEADER_END)
    if start_idx == -1 or end_idx == -1:
        return text, {}

    # Expand to include the docstring markers if present
    docstring_match = re.search(
        r'^[ \t]*("""|\'\'\')[\r\n]+.*?POKERTOOL-HEADER-START.*?POKERTOOL-HEADER-END.*?^[ \t]*\1[ \t]*\r?$',
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    header_block = docstring_match.group(0) if docstring_match else text[start_idx:end_idx + len(HEADER_END)]
    cleaned = text.replace(header_block, "").lstrip()

    # Parse simple key: value fields we care about (best-effort)
    header_dict = {}
    for line in header_block.splitlines():
        line = line.strip()
        if line.startswith("file:"):
            header_dict["file"] = line.split("file:", 1)[1].strip()
        elif line.startswith("version:"):
            header_dict["version"] = line.split("version:", 1)[1].strip().strip("'\"")
        elif line.startswith("fixes:"):
            # capture the entire list block if present
            fixes_match = re.search(r"fixes:\s*(\[[^\]]*\])", header_block, flags=re.DOTALL)
            if fixes_match:
                header_dict["fixes"] = fixes_match.group(1)
            else:
                header_dict["fixes"] = "[]"
    return cleaned, header_dict

def render_header(file_path: Path, last_commit_iso: str, version_guess: str, fixes_block: str) -> str:
    # Ensure the fixes block is valid-ish YAML list
    if not fixes_block or not fixes_block.startswith("["):
        fixes_block = "[]"

    return f'''"""
{HEADER_START}
---
schema: pokerheader.v1
project: pokertool
file: {file_path.as_posix()}
version: '{version_guess}'
last_commit: '{last_commit_iso}'
fixes: {fixes_block}
---
{HEADER_END}
"""
'''

def compute_version(existing_version: str | None, git_tag: str) -> str:
    """
    If a tag exists, prefer it. Else keep existing_version if valid, else default to 24.2.
    """
    tag = git_tag.strip()
    if tag:
        # Allow tags like v24.2 or 24.2. Normalize to digits and dots.
        m = re.search(r"(\d+(?:\.\d+)*)", tag)
        if m:
            return m.group(1)
    if existing_version:
        v = existing_version.strip("'\" ")
        if re.fullmatch(r"\d+(?:\.\d+)*", v):
            return v
    return "24.2"

def ensure_filename_typo_fix():
    """
    If this file was accidentally named 'upate_v24_2.py', rename to 'update_v24_2.py'.
    """
    if THIS_FILE.name == "upate_v24_2.py":
        new_path = THIS_FILE.with_name("update_v24_2.py")
        try:
            THIS_FILE.rename(new_path)
            print(f"[info] Renamed {THIS_FILE.name} -> {new_path.name}")
        except Exception as e:
            print(f"[warn] Could not rename file: {e}")

def main() -> int:
    ensure_filename_typo_fix()
    # After potential rename, recompute THIS_FILE
    file_path = Path(__file__).resolve()
    src = file_path.read_text(encoding="utf-8")

    body_without_header, prev = extract_existing_header(src)
    git = get_git_metadata()

    version = compute_version(prev.get("version"), git.get("tag", ""))
    fixes_block = prev.get("fixes", "[]")
    new_header = render_header(file_path.relative_to(REPO_ROOT), git["last_commit_iso"], version, fixes_block)

    # Keep a shebang and __future__ import at top if present
    shebang = ""
    future = ""
    rest = body_without_header

    m_shebang = re.match(r"^#!.*\n", rest)
    if m_shebang:
        shebang = m_shebang.group(0)
        rest = rest[len(shebang):]

    m_future = re.match(r'^from __future__ import [^\n]+\n', rest)
    if m_future:
        future = m_future.group(0)
        rest = rest[len(future):]

    new_text = f"{shebang}{future}{new_header}\n{rest.lstrip()}"
    file_path.write_text(new_text, encoding="utf-8")

    # Log what we pulled from git
    print("[update_v24_2] Repo:", REPO_ROOT)
    print("[update_v24_2] Branch:", git["branch"])
    print("[update_v24_2] Commit:", git["commit"])
    if git["tag"]:
        print("[update_v24_2] Tag:", git["tag"])
    print("[update_v24_2] last_commit:", git["last_commit_iso"])
    print("[update_v24_2] version:", version)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
