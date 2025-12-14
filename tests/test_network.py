"""
Tests for network module: Connectivity and spectral stability
"""

import numpy as np
import pytest
from hippocampal_ca1_lam.network import (
    NetworkConnectivity, SpectralStability, create_ca1_network
)
from hippocampal_ca1_lam.structure import LayerStructure


class TestNetworkConnectivity:
    """Tests for network connectivity."""
    
    def test_initialization(self):
        """Test network connectivity initialization."""
        n_neurons = 100
        layer_labels = np.random.randint(0, 4, size=n_neurons)
        
        network = NetworkConnectivity(n_neurons, layer_labels, seed=42)
        
        assert network.n_neurons == 100
        assert network.seed == 42
        assert network.W is None
    
    def test_generate_connectivity(self):
        """Test connectivity matrix generation."""
        n_neurons = 100
        layer_labels = np.random.randint(0, 4, size=n_neurons)
        
        network = NetworkConnectivity(n_neurons, layer_labels, seed=42)
        W = network.generate_connectivity()
        
        assert W.shape == (100, 100)
        
        # Check no self-connections
        assert np.all(W.diagonal() == 0)
    
    def test_connectivity_with_positions(self):
        """Test distance-dependent connectivity."""
        n_neurons = 50
        layer_labels = np.random.randint(0, 4, size=n_neurons)
        positions = np.random.rand(n_neurons, 3)
        
        network = NetworkConnectivity(n_neurons, layer_labels, seed=42)
        W = network.generate_connectivity(positions=positions, distance_scale=0.1)
        
        assert W.shape == (50, 50)
    
    def test_connectivity_stats(self):
        """Test connectivity statistics computation."""
        n_neurons = 100
        layer_labels = np.random.randint(0, 4, size=n_neurons)
        
        network = NetworkConnectivity(n_neurons, layer_labels, seed=42)
        network.generate_connectivity()
        
        stats = network.get_connectivity_stats()
        
        assert 'n_connections' in stats
        assert 'connection_probability' in stats
        assert 'mean_in_degree' in stats
        assert 'mean_out_degree' in stats
        assert 'mean_weight' in stats
        assert 'std_weight' in stats
        
        assert stats['n_connections'] > 0
        assert 0 < stats['connection_probability'] < 1
    
    def test_scale_weights(self):
        """Test weight scaling."""
        n_neurons = 50
        layer_labels = np.random.randint(0, 4, size=n_neurons)
        
        network = NetworkConnectivity(n_neurons, layer_labels, seed=42)
        network.generate_connectivity()
        
        original_stats = network.get_connectivity_stats()
        original_mean = original_stats['mean_weight']
        
        # Scale weights
        scale_factor = 0.5
        network.scale_weights(scale_factor)
        
        scaled_stats = network.get_connectivity_stats()
        scaled_mean = scaled_stats['mean_weight']
        
        # Mean should be scaled
        assert np.abs(scaled_mean - original_mean * scale_factor) < 1e-6
    
    def test_reproducibility(self):
        """Test reproducibility with same seed."""
        n_neurons = 50
        layer_labels = np.random.randint(0, 4, size=n_neurons)
        
        n1 = NetworkConnectivity(n_neurons, layer_labels, seed=42)
        W1 = n1.generate_connectivity()
        
        n2 = NetworkConnectivity(n_neurons, layer_labels, seed=42)
        W2 = n2.generate_connectivity()
        
        # Matrices should be identical
        assert np.allclose(W1.toarray(), W2.toarray(), atol=1e-10)


class TestSpectralStability:
    """Tests for spectral stability control."""
    
    def test_initialization(self):
        """Test spectral stability initialization."""
        stability = SpectralStability(max_radius=0.95, tol=1e-10)
        
        assert stability.max_radius == 0.95
        assert stability.tol == 1e-10
    
    def test_compute_spectral_radius(self):
        """Test spectral radius computation."""
        stability = SpectralStability(tol=1e-10)
        
        # Simple test matrix
        W = np.array([[0.5, 0.1], [0.2, 0.4]])
        rho = stability.compute_spectral_radius(W)
        
        # Compute eigenvalues directly
        eigenvalues = np.linalg.eigvals(W)
        expected_rho = np.max(np.abs(eigenvalues))
        
        assert np.abs(rho - expected_rho) < 1e-6
    
    def test_enforce_stability(self):
        """Test spectral stability enforcement."""
        stability = SpectralStability(max_radius=0.95, tol=1e-10)
        
        # Create unstable matrix (eigenvalues > 1)
        W = np.array([[1.5, 0.3], [0.4, 1.2]])
        
        W_stable, rho_orig, scale_factor = stability.enforce_stability(W)
        rho_stable = stability.compute_spectral_radius(W_stable)
        
        # Original should be unstable
        assert rho_orig > 1.0
        
        # Stabilized should be stable
        assert rho_stable <= 0.95
        
        # Scale factor should be < 1
        assert scale_factor < 1.0
    
    def test_stability_constraint(self):
        """Test spectral radius < 1.0 constraint."""
        stability = SpectralStability(max_radius=0.95, tol=1e-10)
        
        # Create random matrix and stabilize
        np.random.seed(42)
        W = np.random.rand(50, 50)
        
        W_stable, _, _ = stability.enforce_stability(W)
        
        # Check constraint
        is_stable, rho = stability.validate_stability(W_stable)
        
        assert is_stable, f"Spectral radius {rho} >= 1.0"
        assert rho < 1.0
    
    def test_validate_stability(self):
        """Test stability validation."""
        stability = SpectralStability(tol=1e-10)
        
        # Stable matrix
        W_stable = 0.5 * np.eye(10)
        is_stable, rho = stability.validate_stability(W_stable)
        
        assert is_stable
        assert rho < 1.0
        
        # Unstable matrix
        W_unstable = 2.0 * np.eye(10)
        is_unstable, rho = stability.validate_stability(W_unstable)
        
        assert not is_unstable
        assert rho >= 1.0
    
    def test_already_stable(self):
        """Test enforcement on already stable matrix."""
        stability = SpectralStability(max_radius=0.95, tol=1e-10)
        
        # Already stable matrix
        W = 0.5 * np.eye(10)
        
        W_stable, rho_orig, scale_factor = stability.enforce_stability(W)
        
        # Should not scale if already stable
        assert scale_factor == 1.0
        assert np.allclose(W, W_stable, atol=1e-10)


class TestCA1NetworkCreation:
    """Tests for integrated CA1 network creation."""
    
    def test_create_ca1_network(self):
        """Test CA1 network creation with stability."""
        # Create small network for testing
        structure = LayerStructure(total_cells=200, seed=42)
        
        network, stability = create_ca1_network(structure, seed=42)
        
        assert network.n_neurons == 200
        assert network.W is not None
        
        # Check stability
        is_stable, rho = stability.validate_stability(network.W)
        assert is_stable, f"Network spectral radius {rho} >= 1.0"
        assert rho < 1.0
    
    def test_network_spectral_radius_constraint(self):
        """Test network satisfies ρ(W) < 1.0 constraint."""
        structure = LayerStructure(total_cells=100, seed=42)
        network, stability = create_ca1_network(structure, seed=42)
        
        rho = stability.compute_spectral_radius(network.W)
        
        # Must satisfy requirement: ρ(W) < 1.0
        assert rho < 1.0, f"Spectral radius {rho} violates constraint ρ(W) < 1.0"
    
    def test_network_reproducibility(self):
        """Test network creation reproducibility."""
        s1 = LayerStructure(total_cells=100, seed=42)
        n1, _ = create_ca1_network(s1, seed=42)
        
        s2 = LayerStructure(total_cells=100, seed=42)
        n2, _ = create_ca1_network(s2, seed=42)
        
        # Networks should be identical
        W1 = n1.W.toarray()
        W2 = n2.W.toarray()
        
        assert np.allclose(W1, W2, atol=1e-10)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
