#!/bin/bash
# QUICK START - Миттєвий запуск Hippocampal-CA1-LAM
# Одна команда для повної установки та перевірки
#
# Usage: bash quick_start.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OS="unknown"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-venv}"
INSTALL_DEV="${INSTALL_DEV:-0}"

echo "========================================================================"
echo "🚀 HIPPOCAMPAL-CA1-LAM - QUICK START"
echo "========================================================================"
echo ""

# Detect OS
if [[ "${OSTYPE:-}" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "${OSTYPE:-}" == "darwin"* ]]; then
    OS="macos"
elif [[ "${OSTYPE:-}" == "msys" ]] || [[ "${OSTYPE:-}" == "cygwin" ]]; then
    OS="windows"
fi

echo "✓ Detected OS: $OS"
echo ""

# Check Python
echo "1. Перевірка Python..."
if ! command -v "$PYTHON_BIN" &> /dev/null; then
    echo "❌ Python 3.10+ не знайдено!"
    echo "   Встановіть Python 3.10+ з https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$("$PYTHON_BIN" --version | cut -d' ' -f2)
echo "   ✓ Python $PYTHON_VERSION знайдено"
echo ""

# Create virtual environment
echo "2. Створення віртуального середовища..."
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    echo "   ✓ $VENV_DIR створено"
else
    echo "   ✓ $VENV_DIR вже існує"
fi
echo ""

# Activate virtual environment
echo "3. Активація віртуального середовища..."
if [[ "$OS" == "windows" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/Scripts/activate"
else
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
fi
echo "   ✓ $VENV_DIR активовано"
echo ""

# Upgrade pip
echo "4. Оновлення pip..."
python -m pip install --upgrade pip -q
echo "   ✓ pip оновлено"
echo ""

# Install package
echo "5. Встановлення Hippocampal-CA1-LAM..."
cd "$ROOT_DIR"
if [[ "$INSTALL_DEV" == "1" ]]; then
    python -m pip install -e ".[dev]" -q
    echo "   ✓ Встановлено у режимі dev"
else
    python -m pip install -e "." -q
    echo "   ✓ Встановлено у режимі користувача"
fi
echo ""

# Run golden tests
echo "6. Запуск golden tests (перевірка установки)..."
python -m hippocampal_ca1_lam.cli

echo ""
echo "========================================================================"
echo "✅ ГОТОВО! Hippocampal-CA1-LAM встановлено та перевірено"
echo "========================================================================"
echo ""
echo "Наступні кроки:"
echo "  • Приклади: python examples/demo_basic_usage.py"
echo "  • Всі тести: bash scripts/run_all_tests.sh"
echo "  • Документація: docs/"
echo ""
echo "Віртуальне середовище активне. Для вимкнення: deactivate"
