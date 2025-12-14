"""
Hippocampal CA1 Laminar Framework

A neuromathematical framework for modeling 4-layer laminar CA1 organization
based on Pachicano et al., Nature Communications 2025.

Features:
- ZINB inference for sublayer structure (58,065 cells)
- Two-compartment biophysics with HCN gradient
- Ca²⁺-driven plasticity (Graupner PNAS 2012)
- Spectral stability control
- HippoRAG memory integration
"""

__version__ = "0.1.0"

from .structure import LayerStructure, ZINBInference
from .dynamics import TwoCompartmentNeuron, HCNGradient
from .plasticity import CalciumDynamics, GraupnerPlasticity
from .network import NetworkConnectivity, SpectralStability
from .hipporag import HippoRAGMemory

__all__ = [
    "LayerStructure",
    "ZINBInference",
    "TwoCompartmentNeuron",
    "HCNGradient",
    "CalciumDynamics",
    "GraupnerPlasticity",
    "NetworkConnectivity",
    "SpectralStability",
    "HippoRAGMemory",
]
