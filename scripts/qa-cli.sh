#!/usr/bin/env sh
set -eu

MODE="${1:-full}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
PYTHON_BIN="python"

if [ -x "$REPO_ROOT/.venv/Scripts/python.exe" ]; then
  PYTHON_BIN="$REPO_ROOT/.venv/Scripts/python.exe"
elif [ -x "$REPO_ROOT/backend/.venv/Scripts/python.exe" ]; then
  PYTHON_BIN="$REPO_ROOT/backend/.venv/Scripts/python.exe"
fi

run_frontend_lint() {
  echo "[qa-cli] frontend lint"
  cd "$REPO_ROOT/frontend"
  corepack pnpm lint
}

run_frontend_tests() {
  echo "[qa-cli] frontend tests"
  cd "$REPO_ROOT/frontend"
  corepack pnpm test
}

run_frontend_build() {
  echo "[qa-cli] frontend build"
  cd "$REPO_ROOT/frontend"
  corepack pnpm build
}

run_backend_tests() {
  echo "[qa-cli] backend tests"
  cd "$REPO_ROOT"
  "$PYTHON_BIN" -m pytest backend -q
}

case "$MODE" in
  pre-commit)
    run_frontend_lint
    run_backend_tests
    ;;
  pre-push)
    run_frontend_lint
    run_frontend_tests
    run_backend_tests
    ;;
  full)
    run_frontend_lint
    run_frontend_tests
    run_frontend_build
    run_backend_tests
    ;;
  *)
    echo "Usage: scripts/qa-cli.sh [pre-commit|pre-push|full]"
    exit 2
    ;;
esac

echo "[qa-cli] done"