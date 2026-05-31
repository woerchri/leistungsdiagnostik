#!/bin/bash
# pytest_baseline.sh — pass^N baseline wrapper for Leistungsdiagnostik
#
# Usage: N=5 FLOW=protocols ./scripts/pytest_baseline.sh
# Defaults: N=5, FLOW=unit, TIMESTAMP=auto
#
# Phase 5 R7 of agentic-fatigue-mitigation epic
# Source: Plans/features/agentic-fatigue-mitigation/phase-5-plan.md Step 1c
#
# Output (stdout): pass^N = passes/N + log file path + per-iteration failure signatures
# Evidence log: /tmp/pytest-baseline-${FLOW}-${TIMESTAMP}.log
#
# IMPORTANT: pytest tests/${FLOW}/ MUST be baseline-clean for pass^N to be meaningful.
# Phase 5 plan Step 0 Gate 3 verifies this precondition. As of 2026-05-31, tests/unit/
# had 14 collection errors — the wrapper still runs, but reports `pass^N = 0/N`.
# Operator should clean the pytest baseline before relying on these numbers.
#
# NO new dependencies: pure shell loop around existing pytest + pytest-snapshot.

# NOTE: deliberately NOT using `set -e` — we want the loop to continue past pytest failures.
set -uo pipefail

N="${N:-5}"
FLOW="${FLOW:-unit}"  # 'unit' | 'protocols' | 'e2e'
TIMESTAMP="${TIMESTAMP:-$(date +%Y%m%dT%H%M%SZ)}"
OUT="/tmp/pytest-baseline-${FLOW}-${TIMESTAMP}.log"

# Validate N is an integer in [1, 25]
if ! [[ "$N" =~ ^[0-9]+$ ]] || (( N < 1 )) || (( N > 25 )); then
    echo "ERROR: N must be an integer in [1, 25], got: $N" >&2
    exit 2
fi

# Validate FLOW maps to an existing directory
if [[ ! -d "tests/${FLOW}" ]]; then
    echo "ERROR: tests/${FLOW}/ does not exist. Valid: unit | protocols | e2e" >&2
    exit 2
fi

PASSES=0
declare -a FAILURES=()

: > "$OUT"  # truncate log

for i in $(seq 1 "$N"); do
    echo "===ITERATION-${i} START $(date +%Y-%m-%dT%H:%M:%SZ)===" >> "$OUT"
    if pytest "tests/${FLOW}/" --tb=short -q >> "$OUT" 2>&1; then
        PASSES=$((PASSES + 1))
        echo "===ITERATION-${i} PASS===" >> "$OUT"
    else
        EXIT_CODE=$?
        # Extract a 1-line failure signature: last FAILED/ERROR line in this iteration's output
        SIG=$(grep -E "^(FAILED|ERROR)" "$OUT" | tail -1 | head -c 200)
        if [[ -z "$SIG" ]]; then
            SIG="pytest exit code ${EXIT_CODE} (no FAILED/ERROR signature parsed)"
        fi
        FAILURES+=("Iteration ${i}: ${SIG}")
        echo "===ITERATION-${i} FAIL exit=${EXIT_CODE}===" >> "$OUT"
    fi
done

# pass^N as 2-decimal float
PASS_N=$(awk "BEGIN { printf \"%.2f\", $PASSES / $N }")

echo "pass^${N} = ${PASSES}/${N} = ${PASS_N}"
echo "Log: ${OUT}"
if [[ ${#FAILURES[@]} -gt 0 ]]; then
    echo ""
    echo "Failure signatures:"
    printf '  %s\n' "${FAILURES[@]}"
fi
