#!/usr/bin/env bash
# Dev container post-create setup for the Model Mastery Foundry workshops.
# Installs the Python packages required to run the notebooks and Foundry tooling.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Installing system tools (ripgrep)"
if ! command -v rg >/dev/null 2>&1; then
  sudo apt-get update && sudo apt-get install -y ripgrep || echo "ripgrep install skipped"
fi

echo "==> Upgrading pip"
python -m pip install --upgrade pip

if [[ -f requirements.txt ]]; then
  echo "==> Installing Python requirements from requirements.txt"
  python -m pip install -r requirements.txt
else
  echo "==> No root requirements.txt found; skipping Python package install"
fi

echo "==> Verifying notebook kernel (ipykernel)"
python -c "import ipykernel; print('ipykernel', ipykernel.__version__)" || echo "ipykernel not available"

echo "==> Tool versions"
python --version || true
az version --output table 2>/dev/null || echo "az not available yet"
azd version 2>/dev/null || echo "azd not available yet"

echo "==> post-create complete"
