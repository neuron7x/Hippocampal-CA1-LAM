# Hippocampal-CA1-LAM
# Hippocampal-CA1-LAM

A neuromathematical framework for modeling 4-layer laminar CA1 hippocampal organization based on **Pachicano et al., Nature Communications 2025**. This framework implements biologically realistic CA1 dynamics with 58,065 cells organized across four laminar layers, featuring ZINB inference, two-compartment biophysics, calcium-driven plasticity, and spectral stability control for in silico neuroscience and AI applications.

## Key Features

### 🧠 Biological Structure
- **4-layer laminar organization**: SO (Stratum Oriens), SP (Stratum Pyramidale), SR (Stratum Radiatum), SLM (Stratum Lacunosum-Moleculare)
- **58,065 cells** distributed using RNAscope-based proportions (Pachicano et al., Nat Comm 2025)
- **ZINB inference** (Zero-Inflated Negative Binomial) for cell distribution modeling
- **Cross-entropy validation** (CE ≤ 0.05 for real data)

### ⚡ Neuronal Dynamics
- **Two-compartment neuron model**: Soma and dendritic compartments with coupling
- **HCN channel gradient**: Increasing conductance from soma to distal dendrites
- **Biophysical realism**: Hodgkin-Huxley style dynamics with validated parameters

### 🔄 Synaptic Plasticity
- **Calcium-driven LTP/LTD** based on Graupner & Brunel, PNAS 2012
- **Thresholds**: θ_d = 1.0 μM (depression), θ_p = 2.0 μM (potentiation)
- **Bistable weight dynamics** with validated plasticity protocols

### 🕸️ Network Dynamics
- **Layer-specific connectivity** patterns matching CA1 anatomy
- **Distance-dependent** connection probabilities
- **Spectral stability**: ρ(W) < 1.0 enforced for stable network dynamics

### 🤖 LLM Integration
- **HippoRAG Memory**: Hippocampal-inspired Retrieval Augmented Generation
- **Pattern separation**: Sparse encoding for orthogonal memory representations
- **Pattern completion**: Recurrent processing for robust retrieval
- **4-layer memory hierarchy** matching CA1 laminar structure

## Installation

```bash
# Clone the repository
git clone https://github.com/neuron7x/Hippocampal-CA1-LAM.git
cd Hippocampal-CA1-LAM

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

## Quick Start

```python
from hippocampal_ca1_lam import (
    LayerStructure, TwoCompartmentNeuron, GraupnerPlasticity,
    NetworkConnectivity, SpectralStability, HippoRAGMemory
)

# 1. Create 4-layer CA1 structure (58,065 cells)
structure = LayerStructure(total_cells=58065, seed=42)
summary = structure.get_summary()

# 2. Simulate two-compartment neuron with HCN gradient
neuron = TwoCompartmentNeuron(seed=42, tol=1e-10)
results = neuron.simulate(duration=100.0, dt=0.1, I_soma=5.0)

# 3. Test Ca²⁺-driven plasticity (θ_d=1.0, θ_p=2.0)
plasticity = GraupnerPlasticity(theta_d=1.0, theta_p=2.0, seed=42)
ltp = plasticity.test_ltp(freq=100.0, n_pairs=60)

# 4. Build stable network (ρ(W) < 1.0)
structure_small = LayerStructure(total_cells=500, seed=42)
positions, labels = structure_small.generate_positions()
network = NetworkConnectivity(500, labels, seed=42)
W = network.generate_connectivity(positions)
stability = SpectralStability(max_radius=0.95, tol=1e-10)
W_stable, rho, _ = stability.enforce_stability(W)

# 5. LLM memory integration
memory = HippoRAGMemory(embedding_dim=512, seed=42, tol=1e-10)
memory.encode(embedding, metadata={'text': 'memory content'})
results = memory.retrieve(query_embedding, top_k=5)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific tests
pytest tests/test_structure.py -v    # ZINB, layer structure
pytest tests/test_dynamics.py -v     # Two-compartment neurons
pytest tests/test_plasticity.py -v   # Ca²⁺ LTP/LTD
pytest tests/test_network.py -v      # Connectivity, stability
pytest tests/test_hipporag.py -v     # LLM memory
pytest tests/test_integration.py -v  # Full framework

# Golden test (seed=42, tol<1e-10)
pytest tests/test_integration.py::TestIntegration::test_golden_test_seed_42 -v
```

## Parameter Reference

### Structure (Pachicano et al., Nat Comm 2025)
- **Total cells**: 58,065
- **Layer proportions**: SO (15%), SP (25%), SR (40%), SLM (20%)
- **ZINB validation**: CE ≤ 0.05

### Plasticity (Graupner & Brunel, PNAS 2012)
- **Depression threshold**: θ_d = 1.0 μM
- **Potentiation threshold**: θ_p = 2.0 μM
- **Rates**: γ_d = 200 s⁻¹, γ_p = 1000 s⁻¹

### Dynamics
- **HCN gradient**: 0.5 → 2.0 mS/cm² (soma → dendrite)
- **Membrane**: C_m = 1.0 μF/cm², g_L = 0.1 mS/cm², E_L = -70 mV

### Network
- **Stability constraint**: ρ(W) < 1.0
- **Connectivity**: Layer-specific (2-20%)

### Reproducibility
- **Seed**: 42 (all modules)
- **Tolerance**: tol = 1e-10

## Architecture

```
hippocampal_ca1_lam/
├── structure.py      # ZINB inference, 4-layer organization  
├── dynamics.py       # Two-compartment neurons, HCN gradient
├── plasticity.py     # Ca²⁺-driven LTP/LTD (Graupner 2012)
├── network.py        # Connectivity, spectral stability
└── hipporag.py       # LLM memory integration
```

## Applications

- **In Silico Neuroscience**: Hypothesis testing, drug effects, disease models
- **AI & LLM**: Biologically-inspired memory, efficient retrieval, RAG systems
- **Computational Psychiatry**: Memory consolidation, learning disorders

## Citation

```bibtex
@software{hippocampal_ca1_lam_2025,
  title={Hippocampal CA1 Laminar Framework},
  author={Neuron7x},
  year={2025},
  url={https://github.com/neuron7x/Hippocampal-CA1-LAM}
}
```

## License

MIT License - see LICENSE file for details.

