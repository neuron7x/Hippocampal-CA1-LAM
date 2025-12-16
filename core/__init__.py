"""
Core Module for Hippocampal CA1

Implements core neural network components:
- CA1 network scaffold
- Two-compartment neuron model
- Laminar structure inference
- Hierarchical laminar model with MRF
- Theta-SWR state switching
"""

from .ca1_network import CA1Network, SimulationResult
from .hierarchical_laminar import (
    CellDataHier,
    HierarchicalLaminarModel,
    build_knn_neighbors,
)
from .laminar_structure import (
    CellData,
    SubregionClassifier,
    ZINBLayerModel,
    compute_coexpression_rate,
    validate_laminar_structure as validate_zinb_structure,
)
from .neuron_model import (
    CA1Population,
    NetworkMode,
    NeuronState,
    TwoCompartmentNeuron,
    extract_theta_phase,
)
from .theta_swr_switching import (
    NetworkState,
    NetworkStateController,
    ReplayDetector,
    ReplayEvent,
    StateTransitionParams,
    compute_replay_metrics,
    validate_replay_vs_template,
)

__all__ = [
    # CA1 Network
    "CA1Network",
    "SimulationResult",
    # Hierarchical Laminar
    "CellDataHier",
    "HierarchicalLaminarModel",
    "build_knn_neighbors",
    # Laminar Structure
    "CellData",
    "SubregionClassifier",
    "ZINBLayerModel",
    "compute_coexpression_rate",
    "validate_zinb_structure",
    # Neuron Model
    "CA1Population",
    "NetworkMode",
    "NeuronState",
    "TwoCompartmentNeuron",
    "extract_theta_phase",
    # Theta-SWR
    "NetworkState",
    "NetworkStateController",
    "ReplayDetector",
    "ReplayEvent",
    "StateTransitionParams",
    "compute_replay_metrics",
    "validate_replay_vs_template",
]
