#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility for ingesting poker client screenshots into the adaptive UI baseline
library.  The tool batches images, attaches metadata, and delegates storage to
``AdaptiveUIDetector`` so downstream scraping checks have reproducible
reference data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Tuple

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pokertool.modules.adaptive_ui_detector import AdaptiveUIDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest poker client screenshots into the adaptive UI baseline library.",
    )
    parser.add_argument(
        "inputs",
        metavar="IMAGE_OR_DIR",
        nargs="+",
        help="Image files or directories containing screenshots to ingest.",
    )
    parser.add_argument(
        "--site",
        required=True,
        help="Poker site identifier (e.g. betfair, pokerstars).",
    )
    parser.add_argument(
        "--resolution",
        help="Resolution in WIDTHxHEIGHT. If omitted, inferred from each image.",
    )
    parser.add_argument(
        "--theme",
        default="default",
        help="Theme or layout variant for the screenshots (default: %(default)s).",
    )
    parser.add_argument(
        "--baseline-dir",
        dest="baseline_dir",
        help="Override baseline directory (defaults to assets/ui_baselines).",
    )
    parser.add_argument(
        "--reports-dir",
        dest="reports_dir",
        help="Optional directory for alert reports (defaults to reports/ui_changes).",
    )
    parser.add_argument(
        "--metadata",
        metavar="KEY=VALUE",
        nargs="*",
        help="Inline metadata pairs to attach to each baseline.",
    )
    parser.add_argument(
        "--metadata-file",
        help="Path to JSON file containing metadata to merge with inline pairs.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search directories for PNG files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without writing to disk.",
    )

    return parser.parse_args()


def gather_images(inputs: Iterable[str], recursive: bool) -> List[Path]:
    images: List[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Input path not found: {path}")
        if path.is_file():
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                raise ValueError(f"Unsupported image format: {path}")
            images.append(path)
        else:
            pattern = "**/*.png" if recursive else "*.png"
            images.extend(sorted(path.glob(pattern)))
    if not images:
        raise ValueError("No images found for ingestion.")
    return sorted(set(images))


def load_metadata(args: argparse.Namespace) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    if args.metadata_file:
        json_path = Path(args.metadata_file)
        if not json_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {json_path}")
        with open(json_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("Metadata file must contain a JSON object.")
        metadata.update({str(key): str(value) for key, value in data.items()})

    if args.metadata:
        for pair in args.metadata:
            if "=" not in pair:
                raise ValueError(f"Invalid metadata pair (expected key=value): {pair}")
            key, value = pair.split("=", 1)
            metadata[key.strip()] = value.strip()
    return metadata


def infer_resolution(image_path: Path) -> str:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")
    height, width = image.shape[:2]
    return f"{width}x{height}"


def ingest() -> None:
    args = parse_args()
    images = gather_images(args.inputs, args.recursive)
    metadata = load_metadata(args)

    detector = AdaptiveUIDetector(
        baseline_dir=args.baseline_dir,
        reports_dir=args.reports_dir,
    )

    created: List[Tuple[str, Path]] = []
    for img_path in images:
        resolution = args.resolution or infer_resolution(img_path)
        payload = dict(metadata)
        payload.update(
            {
                "source_file": img_path.name,
                "ingested_at": int(Path(img_path).stat().st_mtime),
            }
        )

        if args.dry_run:
            print(
                f"[DRY RUN] Would ingest {img_path} "
                f"as site={args.site}, resolution={resolution}, theme={args.theme}"
            )
            continue

        baseline_id = detector.add_baseline_screenshot(
            str(img_path),
            site_name=args.site,
            resolution=resolution,
            theme=args.theme,
            metadata=payload,
        )
        created.append((baseline_id, img_path))
        print(f"Ingested {img_path} -> baseline_id={baseline_id}")

    if not args.dry_run and created:
        manifest = detector.export_manifest()
        print(f"Wrote baseline manifest with {manifest['baseline_count']} entries.")


if __name__ == "__main__":
    ingest()
