"""Example: Running the neuro service."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up environment variables for testing
os.environ['MLSDM_SECURITY__AUTH_MODE'] = 'none'
os.environ['MLSDM_NEURO__N_NEURONS'] = '50'

from src.mlsdm.serve import serve
import click.testing


def run_neuro_service():
    """Run neuro service using the canonical CLI."""
    runner = click.testing.CliRunner()
    result = runner.invoke(serve, ['--mode', 'neuro', '--port', '8001'])
    print(result.output)
    if result.exit_code != 0:
        print(f"Error: {result.exception}")


if __name__ == "__main__":
    print("Starting neuro service via canonical CLI...")
    print("Use: python -m src.mlsdm.serve serve --mode neuro")
    print("\nFor manual testing:")
    print("  python -m src.mlsdm.serve serve --mode neuro --port 8001")
