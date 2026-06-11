#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# run-tests.sh — Test runner for AI Assist Lab
# ─────────────────────────────────────────────────────────────────────────
#
# Usage:
#   ./scripts/run-tests.sh                  # Unit tests only (default)
#   ./scripts/run-tests.sh --integration    # Integration tests only
#   ./scripts/run-tests.sh --all            # All tests
#   ./scripts/run-tests.sh --eval           # Run evaluation harness (mock)
#
# ─────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Colours for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Colour

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Parse arguments ─────────────────────────────────────────────────────
MODE="unit"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --integration)
            MODE="integration"
            shift
            ;;
        --all)
            MODE="all"
            shift
            ;;
        --eval)
            MODE="eval"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--integration | --all | --eval]"
            echo ""
            echo "Options:"
            echo "  (default)       Run unit tests only"
            echo "  --integration   Run integration tests only"
            echo "  --all           Run all tests (unit + integration)"
            echo "  --eval          Run evaluation harness with mock pipeline"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ── Run tests ────────────────────────────────────────────────────────────
case "$MODE" in
    unit)
        info "Running unit tests..."
        python -m pytest tests/unit/ -v --tb=short
        ;;
    integration)
        info "Running integration tests..."
        python -m pytest tests/integration/ -v --tb=short -m integration
        ;;
    all)
        info "Running all tests (unit + integration)..."
        python -m pytest tests/ -v --tb=short -m ""
        ;;
    eval)
        info "Running evaluation harness (mock mode)..."
        python -m evals.harness.eval_runner --mock
        ;;
esac

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    info "All tests passed! ✅"
else
    error "Some tests failed. ❌"
fi

exit $EXIT_CODE
