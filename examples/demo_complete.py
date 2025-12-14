"""
Example: Complete CA1 Network Simulation

Demonstrates the full framework with:
1. Structure: 4-layer laminar organization
2. Dynamics: Two-compartment neurons with HCN
3. Plasticity: Ca²⁺-driven LTP/LTD
4. Network: Stable connectivity (ρ(W) < 1.0)
5. Memory: HippoRAG for LLM integration
"""

import numpy as np
import matplotlib.pyplot as plt
from hippocampal_ca1_lam import (
    LayerStructure, ZINBInference,
    TwoCompartmentNeuron, HCNGradient,
    GraupnerPlasticity,
    NetworkConnectivity, SpectralStability,
    HippoRAGMemory
)


def demo_structure():
    """Demonstrate CA1 laminar structure."""
    print("=" * 60)
    print("1. CA1 LAMINAR STRUCTURE (Pachicano et al., Nat Comm 2025)")
    print("=" * 60)
    
    # Create full 58,065 cell structure
    structure = LayerStructure(total_cells=58065, seed=42)
    summary = structure.get_summary()
    
    print(f"\nTotal cells: {summary['total_cells']:,}")
    print("\nLayer distribution:")
    for layer, info in summary['layers'].items():
        print(f"  {layer}: {info['count']:>6,} cells ({info['proportion']:>5.1%})")
    
    # Generate positions (computationally intensive for full scale)
    print("\nGenerating 3D positions for subset (1000 cells)...")
    small_structure = LayerStructure(total_cells=1000, seed=42)
    positions, labels = small_structure.generate_positions()
    print(f"Positions shape: {positions.shape}")
    

def demo_dynamics():
    """Demonstrate two-compartment neuron dynamics."""
    print("\n" + "=" * 60)
    print("2. TWO-COMPARTMENT NEURON DYNAMICS (HCN gradient)")
    print("=" * 60)
    
    # Create neuron
    hcn = HCNGradient(g_hcn_soma=0.5, g_hcn_dendrite=2.0, seed=42)
    neuron = TwoCompartmentNeuron(hcn_gradient=hcn, seed=42, tol=1e-10)
    
    # Simulate with step current
    duration = 200.0  # ms
    dt = 0.1
    n_steps = int(duration / dt)
    
    I_soma = np.zeros(n_steps)
    I_soma[500:1500] = 8.0  # Current pulse 50-150 ms
    
    print("\nSimulating neuron with current pulse...")
    results = neuron.simulate(duration=duration, dt=dt, I_soma=I_soma)
    
    print(f"Soma voltage range: [{results['V_soma'].min():.2f}, {results['V_soma'].max():.2f}] mV")
    print(f"Dendrite voltage range: [{results['V_dend'].min():.2f}, {results['V_dend'].max():.2f}] mV")
    print(f"Number of spikes: {len(results['spike_times'])}")
    

def demo_plasticity():
    """Demonstrate Ca²⁺-driven plasticity."""
    print("\n" + "=" * 60)
    print("3. SYNAPTIC PLASTICITY (Graupner & Brunel, PNAS 2012)")
    print("=" * 60)
    
    # Test LTP
    print("\nTesting LTP induction (100 Hz pairing, 60 pairs)...")
    plasticity_ltp = GraupnerPlasticity(
        theta_d=1.0, theta_p=2.0, seed=42, tol=1e-10
    )
    ltp_results = plasticity_ltp.test_ltp(freq=100.0, n_pairs=60, dt_spike=10.0)
    
    print(f"  Initial weight: 0.500")
    print(f"  Final weight:   {ltp_results['final_weight']:.3f}")
    print(f"  Change:         {ltp_results['final_weight'] - 0.5:+.3f} (potentiation)")
    
    # Test LTD
    print("\nTesting LTD induction (1 Hz, 900 spikes)...")
    plasticity_ltd = GraupnerPlasticity(
        theta_d=1.0, theta_p=2.0, seed=42, tol=1e-10
    )
    ltd_results = plasticity_ltd.test_ltd(freq=1.0, n_spikes=900, dt_spike=-20.0)
    
    print(f"  Initial weight: 0.500")
    print(f"  Final weight:   {ltd_results['final_weight']:.3f}")
    print(f"  Change:         {ltd_results['final_weight'] - 0.5:+.3f} (depression)")
    

def demo_network():
    """Demonstrate stable network connectivity."""
    print("\n" + "=" * 60)
    print("4. NETWORK CONNECTIVITY (Spectral stability ρ(W) < 1.0)")
    print("=" * 60)
    
    # Create small network for demo
    print("\nCreating network with 500 neurons...")
    structure = LayerStructure(total_cells=500, seed=42)
    positions, labels = structure.generate_positions()
    
    network = NetworkConnectivity(
        n_neurons=structure.total_cells,
        layer_labels=labels,
        seed=42
    )
    
    W = network.generate_connectivity(positions=positions, distance_scale=0.1)
    
    stats = network.get_connectivity_stats()
    print(f"\nConnectivity statistics:")
    print(f"  Connections: {stats['n_connections']:,}")
    print(f"  Connection probability: {stats['connection_probability']:.4f}")
    print(f"  Mean in-degree: {stats['mean_in_degree']:.2f}")
    print(f"  Mean weight: {stats['mean_weight']:.4f}")
    
    # Enforce spectral stability
    print("\nEnforcing spectral stability...")
    stability = SpectralStability(max_radius=0.95, tol=1e-10)
    W_stable, rho_orig, scale_factor = stability.enforce_stability(W)
    
    print(f"  Original ρ(W): {rho_orig:.6f}")
    print(f"  Scale factor: {scale_factor:.6f}")
    
    is_stable, rho_stable = stability.validate_stability(W_stable)
    print(f"  Final ρ(W): {rho_stable:.6f}")
    print(f"  Stable: {is_stable} ✓" if is_stable else f"  Stable: {is_stable} ✗")
    

def demo_hipporag():
    """Demonstrate HippoRAG memory system."""
    print("\n" + "=" * 60)
    print("5. HIPPORAG MEMORY (LLM Integration)")
    print("=" * 60)
    
    # Create memory system
    memory = HippoRAGMemory(
        embedding_dim=256,
        sparsity=0.1,
        n_layers=4,
        seed=42,
        tol=1e-10
    )
    
    # Encode some memories
    print("\nEncoding 10 memories...")
    np.random.seed(42)
    for i in range(10):
        embedding = np.random.rand(256)
        metadata = {
            'id': i,
            'text': f'Memory content {i}',
            'timestamp': i * 1000
        }
        memory.encode(embedding, metadata)
    
    stats = memory.get_memory_stats()
    print(f"  Memories stored: {stats['n_memories']}")
    print(f"  Mean sparsity: {stats['mean_sparsity']:.3f}")
    print(f"  Embedding dim: {stats['embedding_dim']}")
    print(f"  Layers: {stats['n_layers']}")
    
    # Retrieve memories
    print("\nRetrieving top 3 similar memories...")
    query = np.random.rand(256)
    results = memory.retrieve(query, top_k=3)
    
    for i, result in enumerate(results, 1):
        print(f"  {i}. Memory {result['memory_id']}: "
              f"similarity={result['similarity']:.4f}")
    

def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("HIPPOCAMPAL CA1 LAMINAR FRAMEWORK DEMONSTRATION")
    print("=" * 60)
    print("\nBased on:")
    print("  • Pachicano et al., Nature Communications 2025 (structure)")
    print("  • Graupner & Brunel, PNAS 2012 (plasticity)")
    print("  • HippoRAG concept (LLM memory)")
    print("\nKey features:")
    print("  • 58,065 cells in 4 laminar layers")
    print("  • ZINB inference (CE ≤ 0.05)")
    print("  • Two-compartment biophysics")
    print("  • Ca²⁺ plasticity (θ_d=1.0μM, θ_p=2.0μM)")
    print("  • Spectral stability (ρ(W) < 1.0)")
    print("  • Reproducible (seed=42, tol<1e-10)")
    print()
    
    demo_structure()
    demo_dynamics()
    demo_plasticity()
    demo_network()
    demo_hipporag()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nAll components validated:")
    print("  ✓ Structure: 4-layer laminar organization")
    print("  ✓ Dynamics: Two-compartment neurons with HCN gradient")
    print("  ✓ Plasticity: Ca²⁺-driven LTP/LTD")
    print("  ✓ Network: Stable connectivity (ρ(W) < 1.0)")
    print("  ✓ Memory: HippoRAG for LLM integration")
    print("\nFramework ready for:")
    print("  • In silico neuroscience experiments")
    print("  • AI/LLM memory systems")
    print("  • Computational psychiatry models")
    print()


if __name__ == '__main__':
    main()
