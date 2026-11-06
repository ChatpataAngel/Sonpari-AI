#!/usr/bin/env python3
"""Run AIKO's repeatable local release checks; non-zero exit means do not ship."""
from __future__ import annotations
import subprocess
import sys

STEPS = [
    ("Python syntax", [sys.executable, "-m", "compileall", "-q", "aiko", "scripts", "tests"]),
    ("Dialogue rules", [sys.executable, "scripts/check_dialogue_rules.py"]),
    ("Romance bank", [sys.executable, "scripts/validate_romance_bank.py"]),
    ("Full regression suite", [sys.executable, "-m", "pytest", "-q"]),
]

def main() -> int:
    failures = []
    for label, command in STEPS:
        print(f"\\n=== {label} ===", flush=True)
        result = subprocess.run(command, check=False)
        if result.returncode:
            failures.append((label, result.returncode))
            print(f"FAILED: {label} (exit {result.returncode})", flush=True)
            # Continue to reveal all independent check results.
        else:
            print(f"PASSED: {label}", flush=True)
    if failures:
        print("\\nRelease checks failed:", flush=True)
        for label, code in failures: print(f"- {label}: exit {code}", flush=True)
        print("Do not release until all required dependencies are installed and failing checks are resolved.", flush=True)
        return 1
    print("\\nAll release checks passed.", flush=True)
    return 0

if __name__ == "__main__": raise SystemExit(main())
