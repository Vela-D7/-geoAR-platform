"""Run the optimisation pipeline end-to-end and print the quality report.

Usage:
    python -m pipeline.cli [--input path/to/scan.glb] [--out output/]

With no --input, the procedural placeholder chapel is used (tonight's mode).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import optimise, quality_checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=None, help="Path to real LiDAR mesh export; omit for placeholder")
    parser.add_argument("--out", default="output", help="Output directory for LOD GLBs + reports")
    args = parser.parse_args()

    mesh = optimise.clean_mesh(optimise.load_input_mesh(args.input))
    result = optimise.run_pipeline(args.input, args.out)
    report = quality_checks.run_all(mesh, result)

    report_path = Path(args.out) / "quality_report.json"
    report_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(result.to_manifest(), indent=2))
    print(json.dumps(report, indent=2))
    print(f"\nquality report: {report_path} — overall {'PASS' if report['passed'] else 'FAIL'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
