#!/usr/bin/env python3
"""
Check for version drift between main backend and api-gateway.

This script parses both requirements.txt files and identifies packages
that have different versions or use different version constraints
(pinned vs loose).

Usage:
    python scripts/check_version_drift.py

Exit codes:
    0 - All versions aligned
    1 - Version drift detected
"""

import re
import sys
from pathlib import Path
from typing import Dict, Tuple


def parse_requirements(file_path: Path) -> Dict[str, Tuple[str, str]]:
    """
    Parse requirements.txt and return package:version dict.

    Args:
        file_path: Path to requirements.txt file

    Returns:
        Dict mapping package name to (operator, version) tuple
        Example: {"fastapi": ("==", "0.111.0")}
    """
    packages = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Match package specifications like:
                # fastapi==0.111.0
                # uvicorn[standard]>=0.24.0
                # python-jose[cryptography]==3.3.0
                match = re.match(r'([a-zA-Z0-9_\-\[\]]+)(==|>=|<=|>|<|~=)(.+)', line)

                if match:
                    package_name = match.group(1)
                    operator = match.group(2)
                    version = match.group(3).strip()

                    packages[package_name] = (operator, version)
                else:
                    # Warn about unparseable lines
                    print(f"[WARN] Could not parse line {line_num} in {file_path.name}: {line}")

    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] Reading {file_path}: {e}")
        sys.exit(2)

    return packages


def compare_versions(
    backend: Dict[str, Tuple[str, str]],
    gateway: Dict[str, Tuple[str, str]]
) -> Tuple[bool, list]:
    """
    Compare package versions between backend and gateway.

    Args:
        backend: Backend packages dict
        gateway: Gateway packages dict

    Returns:
        Tuple of (all_aligned: bool, drift_details: list)
    """
    # Find common packages
    common = set(backend.keys()) & set(gateway.keys())

    if not common:
        print("[WARN] No common packages found between services")
        return False, []

    drift_details = []

    for pkg in sorted(common):
        b_operator, b_version = backend[pkg]
        g_operator, g_version = gateway[pkg]

        # Check for operator mismatch (pinned vs loose)
        if b_operator == '==' and g_operator != '==':
            drift_details.append({
                'package': pkg,
                'backend': f"{b_operator}{b_version}",
                'gateway': f"{g_operator}{g_version}",
                'type': 'operator_mismatch'
            })

        # Check for version mismatch
        elif b_version != g_version:
            drift_details.append({
                'package': pkg,
                'backend': f"{b_operator}{b_version}",
                'gateway': f"{g_operator}{g_version}",
                'type': 'version_mismatch'
            })

    return len(drift_details) == 0, drift_details


def print_drift_report(drift_details: list) -> None:
    """Print formatted drift report."""
    if not drift_details:
        print("[OK] All versions aligned!")
        print("\nBoth services use identical package versions with pinned constraints.")
        return

    print("[WARN] Version Drift Detected\n")
    print(f"{'Package':<30} {'Backend':<20} {'Gateway':<20} {'Issue'}")
    print("-" * 90)

    for item in drift_details:
        issue_type = "Loose version" if item['type'] == 'operator_mismatch' else "Different version"
        print(f"{item['package']:<30} {item['backend']:<20} {item['gateway']:<20} {issue_type}")

    print("\n" + "=" * 90)
    print(f"Total issues found: {len(drift_details)}")
    print("\nRecommendation: Align api-gateway/requirements.txt with main backend")
    print("See docs/PACKAGE_COMPATIBILITY.md for update process")


def main() -> int:
    """Main entry point."""
    # Define paths
    project_root = Path(__file__).parent.parent
    backend_req = project_root / "requirements.txt"
    gateway_req = project_root / "api-gateway" / "requirements.txt"

    print("[Version Drift Analysis]")
    print("=" * 90)
    print(f"Backend:     {backend_req.relative_to(project_root)}")
    print(f"API Gateway: {gateway_req.relative_to(project_root)}")
    print("=" * 90)
    print()

    # Parse requirements files
    backend_packages = parse_requirements(backend_req)
    gateway_packages = parse_requirements(gateway_req)

    print(f"Backend packages:     {len(backend_packages)}")
    print(f"API Gateway packages: {len(gateway_packages)}")
    print(f"Common packages:      {len(set(backend_packages.keys()) & set(gateway_packages.keys()))}")
    print()

    # Compare versions
    all_aligned, drift_details = compare_versions(backend_packages, gateway_packages)

    # Print report
    print_drift_report(drift_details)

    # Return exit code
    return 0 if all_aligned else 1


if __name__ == '__main__':
    sys.exit(main())
