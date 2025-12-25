#!/bin/bash
# SETUP DEVELOPMENT ENVIRONMENT
# Налаштовує повне dev середовище з усіма інструментами
#
# Usage: bash setup_dev_environment.sh

set -e

echo "========================================================================"
echo "🛠️  HIPPOCAMPAL-CA1-LAM - DEVELOPMENT ENVIRONMENT SETUP"
echo "========================================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не знайдено!"
    exit 1
fi

echo "✓ Python: $(python3 --version)"
echo ""

# Create venv
echo "1. Створення віртуального середовища..."
if [ ! -d "venv-dev" ]; then
    python3 -m venv venv-dev
    echo "   ✓ venv-dev створено"
else
    echo "   ✓ venv-dev вже існує"
fi

# Activate
source venv-dev/bin/activate || source venv-dev/Scripts/activate
echo "   ✓ venv-dev активовано"
echo ""

# Upgrade pip
echo "2. Оновлення pip..."
python -m pip install --upgrade pip -q
echo "   ✓ pip оновлено"
echo ""

# Install package + dev dependencies
echo "3. Встановлення пакета та dev інструментів..."
pip install -e ".[dev]" -q
echo "   ✓ Пакет та dev залежності встановлено"
echo ""

# Install pre-commit hooks
echo "4. Налаштування pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    echo "   ✓ Pre-commit hooks встановлено"
else
    echo "   ⚠ .pre-commit-config.yaml не знайдено"
fi
echo ""

# Create useful aliases
echo "5. Створення корисних скриптів..."

# Create test script
cat > run_tests_quick.sh << 'EOF'
#!/bin/bash
# Quick test runner
python -m hippocampal_ca1_lam.cli && echo "✅ Golden tests passed"
EOF
chmod +x run_tests_quick.sh
echo "   ✓ run_tests_quick.sh створено"

# Create format script
cat > format_code.sh << 'EOF'
#!/bin/bash
# Auto-format all code
echo "Formatting with black..."
black . --line-length 100
echo "Sorting imports with isort..."
isort .
echo "✅ Code formatted"
EOF
chmod +x format_code.sh
echo "   ✓ format_code.sh створено"

# Create lint script
cat > lint_code.sh << 'EOF'
#!/bin/bash
# Lint all code
echo "Linting with flake8..."
flake8 . --max-line-length=100 --exclude=venv,venv-dev,build,dist
echo "Type checking with mypy..."
mypy . --ignore-missing-imports
echo "✅ Linting complete"
EOF
chmod +x lint_code.sh
echo "   ✓ lint_code.sh створено"

echo ""

# Run initial tests
echo "6. Запуск початкових тестів..."
python -m hippocampal_ca1_lam.cli
echo ""

# Create .vscode settings (if VSCode is used)
echo "7. Налаштування VSCode (опційно)..."
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "100"],
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true
    }
}
EOF
echo "   ✓ .vscode/settings.json створено"
echo ""

echo "========================================================================"
echo "✅ DEVELOPMENT ENVIRONMENT READY!"
echo "========================================================================"
echo ""
echo "Доступні команди:"
echo "  • bash run_tests_quick.sh      - Швидкі тести"
echo "  • bash format_code.sh           - Автоформатування"
echo "  • bash lint_code.sh             - Перевірка коду"
echo "  • pytest tests/ -v              - Всі unit tests"
echo "  • python examples/demo_*.py     - Приклади"
echo ""
echo "Pre-commit hooks активні - код буде автоматично перевірятися"
echo ""
echo "Середовище: venv-dev (активне)"
echo "Для вимкнення: deactivate"
