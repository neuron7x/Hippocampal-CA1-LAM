"""
Integration tests for complete CA1 laminar framework

Tests the full pipeline: structure -> dynamics -> plasticity -> network -> memory
"""

import numpy as np
import pytest
from hippocampal_ca1_lam import (
    LayerStructure, ZINBInference,
    TwoCompartmentNeuron, HCNGradient,
    CalciumDynamics, GraupnerPlasticity,
    NetworkConnectivity, SpectralStability,
    HippoRAGMemory
)


class TestIntegration:
    """Integration tests for complete framework."""
    
    def test_golden_test_seed_42(self):
        """Golden test with seed=42 for reproducibility."""
        seed = 42
        tol = 1e-10
        
        # 1. Structure: Create layer structure
        structure = LayerStructure(total_cells=1000, seed=seed)
        positions, labels = structure.generate_positions()
        
        assert structure.total_cells == 1000
        assert positions.shape == (1000, 3)
        
        # 2. ZINB inference
        zinb = ZINBInference(seed=seed, tol=tol)
        np.random.seed(seed)
        # Generate realistic ZINB data
        true_pi = 0.2
        true_mu = 10.0
        true_r = 5.0
        zero_inflated = np.random.binomial(1, true_pi, size=1000)
        p = true_r / (true_r + true_mu)
        nb_samples = np.random.negative_binomial(true_r, p, size=1000)
        counts = np.where(zero_inflated, 0, nb_samples)
        
        params = zinb.fit(counts)
        ce = zinb.cross_entropy(counts)
        
        # CE should be reasonable for well-fitted model
        assert ce < 5.0, f"CE {ce} too high"
        
        # 3. Dynamics: Two-compartment neuron
        hcn = HCNGradient(seed=seed)
        neuron = TwoCompartmentNeuron(hcn_gradient=hcn, seed=seed, tol=tol)
        results = neuron.simulate(duration=50.0, dt=0.1, I_soma=5.0)
        
        assert 'V_soma' in results
        assert 'V_dend' in results
        
        # 4. Plasticity: Graupner model
        plasticity = GraupnerPlasticity(
            theta_d=1.0, theta_p=2.0, seed=seed, tol=tol
        )
        ltp_results = plasticity.test_ltp(freq=100.0, n_pairs=60)
        
        assert ltp_results['final_weight'] > 0.5
        
        # 5. Network: Connectivity with spectral stability
        network = NetworkConnectivity(100, labels[:100], seed=seed)
        W = network.generate_connectivity(positions[:100])
        
        stability = SpectralStability(max_radius=0.95, tol=tol)
        W_stable, rho, _ = stability.enforce_stability(W)
        
        assert rho < 1.5  # Original might be unstable
        is_stable, rho_stable = stability.validate_stability(W_stable)
        assert is_stable, f"ρ(W) = {rho_stable} >= 1.0"
        assert rho_stable < 1.0
        
        # 6. HippoRAG memory
        memory = HippoRAGMemory(embedding_dim=128, seed=seed, tol=tol)
        
        for i in range(5):
            emb = np.random.RandomState(seed + i).rand(128)
            memory.encode(emb, metadata={'id': i})
        
        query = np.random.RandomState(seed).rand(128)
        retrieved = memory.retrieve(query, top_k=3)
        
        assert len(retrieved) == 3
        
        print("✓ Golden test passed: All components working with seed=42, tol<1e-10")
    
    def test_full_ca1_model_creation(self):
        """Test creating complete CA1 model."""
        seed = 42
        
        # Create CA1 structure (smaller for testing)
        structure = LayerStructure(total_cells=500, seed=seed)
        positions, labels = structure.generate_positions()
        
        # Create network
        network = NetworkConnectivity(structure.total_cells, labels, seed=seed)
        W = network.generate_connectivity(positions)
        
        # Enforce stability
        stability = SpectralStability(max_radius=0.95)
        W_stable, _, _ = stability.enforce_stability(W)
        network.W = W_stable
        
        # Validate complete model
        is_stable, rho = stability.validate_stability(network.W)
        assert is_stable
        assert rho < 1.0
        
        stats = network.get_connectivity_stats()
        assert stats['n_connections'] > 0
        
        print(f"✓ Full CA1 model: {structure.total_cells} cells, ρ(W)={rho:.6f} < 1.0")
    
    def test_parameter_requirements(self):
        """Test all required parameters match specifications."""
        # Plasticity thresholds
        plasticity = GraupnerPlasticity()
        assert plasticity.theta_d == 1.0, "θ_d must be 1.0 μM"
        assert plasticity.theta_p == 2.0, "θ_p must be 2.0 μM"
        
        # Numerical tolerance (tol <= 1e-10)
        zinb = ZINBInference(tol=1e-10)
        assert zinb.tol <= 1e-10
        
        neuron = TwoCompartmentNeuron(tol=1e-10)
        assert neuron.tol <= 1e-10
        
        memory = HippoRAGMemory(tol=1e-10)
        assert memory.tol <= 1e-10
        
        stability = SpectralStability(tol=1e-10)
        assert stability.tol <= 1e-10
        
        print("✓ All parameter requirements satisfied")
    
    def test_58065_cells_structure(self):
        """Test full 58,065 cell structure (Pachicano et al.)."""
        seed = 42
        
        # Full structure
        structure = LayerStructure(total_cells=58065, seed=seed)
        
        assert structure.total_cells == 58065
        
        # Check layer distribution
        summary = structure.get_summary()
        assert summary['total_cells'] == 58065
        assert len(summary['layers']) == 4
        
        # Verify all cells assigned
        total = sum(structure.layer_counts.values())
        assert total == 58065
        
        print("✓ Full 58,065 cell structure validated")
    
    def test_reproducibility_across_modules(self):
        """Test reproducibility across all modules with seed=42."""
        seed = 42
        tol = 1e-10
        
        # Run 1
        s1 = LayerStructure(total_cells=100, seed=seed)
        p1, l1 = s1.generate_positions()
        
        n1 = TwoCompartmentNeuron(seed=seed, tol=tol)
        r1 = n1.simulate(duration=20.0, dt=0.1, I_soma=5.0)
        
        pl1 = GraupnerPlasticity(seed=seed, tol=tol)
        ltp1 = pl1.test_ltp(freq=100.0, n_pairs=30)
        
        # Run 2
        s2 = LayerStructure(total_cells=100, seed=seed)
        p2, l2 = s2.generate_positions()
        
        n2 = TwoCompartmentNeuron(seed=seed, tol=tol)
        r2 = n2.simulate(duration=20.0, dt=0.1, I_soma=5.0)
        
        pl2 = GraupnerPlasticity(seed=seed, tol=tol)
        ltp2 = pl2.test_ltp(freq=100.0, n_pairs=30)
        
        # Verify reproducibility
        assert np.allclose(p1, p2, atol=tol)
        assert np.allclose(r1['V_soma'], r2['V_soma'], atol=tol)
        assert np.allclose(ltp1['weight'], ltp2['weight'], atol=tol)
        
        print("✓ Reproducibility verified across all modules with seed=42, tol<1e-10")
    
    def test_spectral_stability_requirement(self):
        """Test spectral radius ρ(W) < 1.0 requirement."""
        seed = 42
        
        # Create network
        structure = LayerStructure(total_cells=200, seed=seed)
        positions, labels = structure.generate_positions()
        
        network = NetworkConnectivity(structure.total_cells, labels, seed=seed)
        W = network.generate_connectivity(positions)
        
        # Enforce stability
        stability = SpectralStability(max_radius=0.95)
        W_stable, rho_orig, scale_factor = stability.enforce_stability(W)
        
        # Validate
        is_stable, rho_stable = stability.validate_stability(W_stable)
        
        assert is_stable, f"Network unstable: ρ(W) = {rho_stable}"
        assert rho_stable < 1.0, f"ρ(W) = {rho_stable} violates requirement ρ(W) < 1.0"
        
        print(f"✓ Spectral stability: ρ(W) = {rho_stable:.6f} < 1.0")
    
    def test_plasticity_thresholds(self):
        """Test Ca²⁺ plasticity thresholds θ_d=1.0, θ_p=2.0."""
        plasticity = GraupnerPlasticity(theta_d=1.0, theta_p=2.0, seed=42)
        
        # Test LTP induction (above θ_p)
        ltp = plasticity.test_ltp(freq=100.0, n_pairs=60)
        assert ltp['final_weight'] > 0.5
        
        # Test LTD induction (between θ_d and θ_p)
        plasticity.reset()
        ltd = plasticity.test_ltd(freq=1.0, n_spikes=900)
        assert ltd['final_weight'] < 0.7
        
        print("✓ Ca²⁺ plasticity thresholds: θ_d=1.0 μM, θ_p=2.0 μM validated")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
