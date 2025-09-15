#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: pokertool/apply_headers.py
# version: '20'
# last_commit: '2025-09-15T01:40:48.814921+00:00'
# fixes: []
# ---
# POKERTOOL-HEADER-END
"""
Apply or update machine-readable headers across the repo.

Usage:
  python3 tools/apply_headers.py --version v20.0.0 \
    --fix "Initial v20 header applied"

Optional:
  --dry-run            show changes only
  --include "glob1,glob2"   limit to paths
  --exclude "glob1,glob2"   skip paths
"""
from __future__ import annotations
import argparse, datetime as dt, fnmatch, os, re, subprocess, sys, textwrap, yaml
from pathlib import Path
from typing import Dict, List, Tuple

REPO = Path(__file__).resolve().parents[1]
SCHEMA = "pokerheader.v1"
SIDE_EXT = ".pokerheader.yml"

HASH_EXT = {
    ".py", ".txt", ".yml", ".yaml", ".ini", ".cfg", ".toml",
    ".sh", ".cfg", ".conf", ".ps1", ".bat", ".md"  # .md handled with HTML comment
}
HTML_EXT = {".md", ".html", ".htm"}

HEADER_START = "POKERTOOL-HEADER-START"
HEADER_END   = "POKERTOOL-HEADER-END"

def git_last_commit_iso(path: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", "--", str(path)],
            cwd=REPO,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return out or None
    except Exception:
        return None

def fs_mtime_iso(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).isoformat()

def wants_sidecar(path: Path) -> bool:
    ext = path.suffix.lower()
    if ext == ".json": return True
    if ext in {".png",".jpg",".jpeg",".gif",".pdf",".zip",".gz",".bz2",".xz",".7z",".jar",".bin"}:
        return True
    if path.name == ".DS_Store":
        return True
    return False

def detect_style(path: Path) -> str:
    if wants_sidecar(path): return "sidecar"
    ext = path.suffix.lower()
    if ext in HTML_EXT: return "html"
    return "hash"

def split_shebang(text: str) -> Tuple[str,str]:
    if text.startswith("#!"):
        nl = text.find("\n")
        if nl >= 0:
            return text[:nl+1], text[nl+1:]
    return "", text

def extract_header_block(text: str, style: str) -> Tuple[Dict, Tuple[int,int] | None]:
    # Find our markers and return parsed YAML plus (start,end) line indices
    lines = text.splitlines()
    start_idx = end_idx = None
    for i, line in enumerate(lines):
        if HEADER_START in line:
            start_idx = i
        if HEADER_END in line:
            end_idx = i
            break
    if start_idx is not None and end_idx is not None and end_idx > start_idx:
        block = lines[start_idx:end_idx+1]
        # Strip comment syntax
        cleaned = []
        for l in block:
            l = re.sub(r"^\s*#\s?", "", l)
            l = re.sub(r"^\s*<!--\s?", "", l)
            l = re.sub(r"\s?-->\s?$", "", l)
            cleaned.append(l)
        # Keep only YAML segment between the --- fences
        yaml_text = []
        capture = False
        for l in cleaned:
            if l.strip() == "---":
                capture = not capture
                continue
            if capture:
                yaml_text.append(l)
        try:
            data = yaml.safe_load("\n".join(yaml_text)) or {}
            return data, (start_idx, end_idx)
        except Exception:
            return {}, (start_idx, end_idx)
    return {}, None

def build_yaml_dict(path: Path, version: str, fixes: List[str], last_commit: str) -> Dict:
    rel = str(path.relative_to(REPO))
    nowd = dt.datetime.now(dt.timezone.utc).date().isoformat()
    fixes_list = [{"date": nowd, "summary": f} for f in fixes] if fixes else []
    return {
        "schema": SCHEMA,
        "project": "pokertool",
        "file": rel,
        "version": version,
        "last_commit": last_commit,
        "fixes": fixes_list,
    }

def render_block(style: str, data: Dict) -> str:
    y = yaml.safe_dump(data, sort_keys=False).rstrip()
    if style == "html":
        return textwrap.dedent(f"""\
        <!-- {HEADER_START}
        ---
        {y}
        ---
        {HEADER_END} -->
        """).rstrip()+"\n"
    # default hash
    pref = "# "
    body = "\n".join(pref + line if line else "#"
                     for line in ["---", *y.splitlines(), "---"])
    return f"# {HEADER_START}\n{body}\n# {HEADER_END}\n"

def apply_inline(path: Path, version: str, fixes: List[str], dry: bool=False) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    she, body = split_shebang(text)
    style = detect_style(path)
    existing, span = extract_header_block(text, style)
    last = git_last_commit_iso(path) or fs_mtime_iso(path)
    newdata = build_yaml_dict(path, version, fixes, last)
    if existing:
        # preserve existing fixes, append new
        old_fixes = existing.get("fixes") or []
        if fixes:
            old_fixes.extend(newdata["fixes"])
        existing.update({k:v for k,v in newdata.items() if k != "fixes"})
        existing["fixes"] = old_fixes
        block = render_block(style, existing)
        s,e = span
        lines = body.splitlines()
        new_body = "\n".join(lines[:s] + [block.rstrip()] + lines[e+1:])
    else:
        block = render_block(style, newdata)
        new_body = block + body
    out = she + new_body
    if not dry:
        path.write_text(out, encoding="utf-8")
    return True

def apply_sidecar(path: Path, version: str, fixes: List[str], dry: bool=False) -> bool:
    last = git_last_commit_iso(path) or fs_mtime_iso(path)
    data = build_yaml_dict(path, version, fixes, last)
    side = path.with_suffix(path.suffix + SIDE_EXT)
    if not dry:
        side.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return True

def should_consider(path: Path, includes: List[str], excludes: List[str]) -> bool:
    rel = str(path.relative_to(REPO))
    if includes and not any(fnmatch.fnmatch(rel, g) for g in includes):
        return False
    if any(fnmatch.fnmatch(rel, g) for g in excludes):
        return False
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="e.g., v20.0.0")
    ap.add_argument("--fix", action="append", default=[], help="append a fixes entry; repeatable")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--include", default="", help="comma-separated globs")
    ap.add_argument("--exclude", default=".git/*,*/.git/*,*/__pycache__/*,*"+SIDE_EXT)
    args = ap.parse_args()

    includes = [g.strip() for g in args.include.split(",") if g.strip()]
    excludes = [g.strip() for g in args.exclude.split(",") if g.strip()]

    changed = 0
    for p in REPO.rglob("*"):
        if not p.is_file(): continue
        if not should_consider(p, includes, excludes): continue
        style = detect_style(p)
        if style == "sidecar":
            ok = apply_sidecar(p, args.version, args.fix, args.dry_run)
        else:
            ok = apply_inline(p, args.version, args.fix, args.dry_run)
        if ok:
            changed += 1
            if args.dry_run:
                print(f"[dry] would update: {p}")
            else:
                print(f"[ok] updated: {p}")
    print(f"Done. Files touched: {changed}")

if __name__ == "__main__":
    # Depend only on stdlib + PyYAML
    try:
        import yaml  # type: ignore
    except Exception:
        sys.stderr.write("PyYAML required: pip install pyyaml\n")
        sys.exit(2)
    main()
