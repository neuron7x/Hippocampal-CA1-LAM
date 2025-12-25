import subprocess
import sys

import numpy as np

from hippocampal_ca1_lam import (
    CA1Network,
    NetworkStateController,
    StateTransitionParams,
    UnifiedWeightMatrix,
    __version__,
    get_default_parameters,
)


def test_version_and_public_api():
    assert __version__.startswith("2.")

    net = CA1Network(3, seed=1, dt=1.0)
    result = net.simulate(duration_ms=10)
    assert result["spikes"].shape == (10, 3)

    params = get_default_parameters()
    connectivity = np.zeros((3, 3), dtype=bool)
    weights = np.ones((3, 3))
    sources = np.zeros((3, 3), dtype=object)
    UnifiedWeightMatrix(connectivity, weights, sources, params)

    controller = NetworkStateController(StateTransitionParams(), dt=0.1)
    controller.step()


def test_cli_lists_golden_tests():
    completed = subprocess.run(
        [sys.executable, "-m", "hippocampal_ca1_lam.cli", "--list"],
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    assert len(lines) >= 6
    assert any("Reproducibility" in line for line in lines)
