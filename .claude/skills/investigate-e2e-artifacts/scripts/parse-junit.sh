#!/bin/bash
# parse-junit.sh — Extract failures from a JUnit XML file using python3
#
# Usage:  parse-junit.sh <path-to-e2e-report.xml>
# Stdout: human-readable summary of each failed test with truncated messages
# Exit 1: file not found or XML parse error

set -euo pipefail

XML="${1:?Usage: $0 <path-to-e2e-report.xml>}"

if [ ! -f "$XML" ]; then
  echo "ERROR: File not found: $XML" >&2
  exit 1
fi

python3 - "$XML" <<'PYEOF'
import sys
import xml.etree.ElementTree as ET

try:
    tree = ET.parse(sys.argv[1])
except ET.ParseError as e:
    print(f"ERROR: Failed to parse XML: {e}", file=sys.stderr)
    sys.exit(1)

root = tree.getroot()

total, failed = 0, 0
rows = []

# Handle both <testsuites><testsuite> and flat <testsuite> roots
for tc in root.iter('testcase'):
    total += 1
    for tag in ('failure', 'error'):
        node = tc.find(tag)
        if node is not None:
            failed += 1
            msg = (node.get('message') or node.text or '').strip()
            # Collapse whitespace and truncate
            msg = ' '.join(msg.split())[:220]
            rows.append({
                'suite': tc.get('classname', '(no suite)'),
                'name':  tc.get('name', '(no name)'),
                'msg':   msg,
            })
            break

print(f"=== JUnit Results: {failed} FAILED / {total} total ===\n")

if failed == 0:
    print("No failures found in the JUnit report.")
    sys.exit(0)

for i, r in enumerate(rows, 1):
    print(f"[{i:02d}] Suite: {r['suite']}")
    print(f"     Test:  {r['name']}")
    print(f"     FAIL:  {r['msg']}")
    print()
PYEOF
