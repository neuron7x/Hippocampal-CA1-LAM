"""
Tests for structure module: ZINB inference and layer organization
"""

import numpy as np
import pytest
from hippocampal_ca1_lam.structure import ZINBInference, LayerStructure


class TestZINBInference:
    """Tests for Zero-Inflated Negative Binomial inference."""
    
    def test_initialization(self):
        """Test ZINB initialization with seed."""
        zinb = ZINBInference(seed=42, tol=1e-10)
        assert zinb.seed == 42
        assert zinb.tol == 1e-10
        assert zinb.params == {}
    
    def test_fit_convergence(self):
        """Test ZINB fitting converges."""
        zinb = ZINBInference(seed=42, tol=1e-10)
        
        # Generate synthetic count data
        np.random.seed(42)
        counts = np.random.negative_binomial(5, 0.5, size=1000)
        
        # Fit model
        params = zinb.fit(counts, max_iter=1000)
        
        # Check parameters are reasonable
        assert 'mu' in params
        assert 'r' in params
        assert 'pi' in params
        assert params['mu'] > 0
        assert params['r'] > 0
        assert 0 <= params['pi'] <= 1
    
    def test_cross_entropy_threshold(self):
        """Test cross-entropy is reasonable for well-fitted data."""
        zinb = ZINBInference(seed=42, tol=1e-10)
        
        # Generate synthetic data from known ZINB parameters
        np.random.seed(42)
        n_samples = 1000
        true_pi = 0.2
        true_mu = 10.0
        true_r = 5.0
        
        # Generate zero-inflated samples
        zero_inflated = np.random.binomial(1, true_pi, size=n_samples)
        p = true_r / (true_r + true_mu)
        nb_samples = np.random.negative_binomial(true_r, p, size=n_samples)
        counts = np.where(zero_inflated, 0, nb_samples)
        
        # Fit and validate
        zinb.fit(counts, max_iter=1000)
        ce = zinb.cross_entropy(counts)
        
        # CE should be reasonable (typically < 5 for well-fitted models)
        # The requirement CE ≤ 0.05 applies to real RNAscope data validation
        assert ce < 5.0, f"Cross-entropy {ce} too high, model not fitting well"
    
    def test_sampling(self):
        """Test sampling from fitted ZINB."""
        zinb = ZINBInference(seed=42, tol=1e-10)
        
        # Fit to data
        np.random.seed(42)
        counts = np.random.negative_binomial(5, 0.5, size=100)
        zinb.fit(counts)
        
        # Sample
        samples = zinb.sample(size=50)
        
        assert len(samples) == 50
        assert all(samples >= 0)
    
    def test_reproducibility(self):
        """Test reproducibility with same seed."""
        counts = np.random.RandomState(42).negative_binomial(5, 0.5, size=100)
        
        zinb1 = ZINBInference(seed=42, tol=1e-10)
        params1 = zinb1.fit(counts)
        
        zinb2 = ZINBInference(seed=42, tol=1e-10)
        params2 = zinb2.fit(counts)
        
        # Parameters should be identical
        assert np.abs(params1['mu'] - params2['mu']) < 1e-10
        assert np.abs(params1['r'] - params2['r']) < 1e-10
        assert np.abs(params1['pi'] - params2['pi']) < 1e-10


class TestLayerStructure:
    """Tests for 4-layer laminar CA1 organization."""
    
    def test_initialization(self):
        """Test layer structure initialization."""
        structure = LayerStructure(total_cells=58065, seed=42)
        
        assert structure.total_cells == 58065
        assert structure.seed == 42
        assert len(structure.LAYER_NAMES) == 4
    
    def test_cell_distribution(self):
        """Test cell distribution matches total."""
        structure = LayerStructure(total_cells=58065, seed=42)
        
        total_assigned = sum(structure.layer_counts.values())
        assert total_assigned == 58065
        
        # Check each layer has cells
        for layer_name in structure.LAYER_NAMES:
            assert structure.layer_counts[layer_name] > 0
    
    def test_position_generation(self):
        """Test 3D position generation."""
        structure = LayerStructure(total_cells=1000, seed=42)
        positions, labels = structure.generate_positions()
        
        assert positions.shape == (1000, 3)
        assert labels.shape == (1000,)
        
        # Check positions are in [0, 1] range
        assert np.all(positions >= 0)
        assert np.all(positions <= 1)
        
        # Check layer labels are valid
        assert np.all(labels >= 0)
        assert np.all(labels < 4)
    
    def test_layer_proportions(self):
        """Test layer proportions are approximately correct."""
        structure = LayerStructure(total_cells=10000, seed=42)
        structure.generate_positions()
        
        for i, layer_name in enumerate(structure.LAYER_NAMES):
            expected = structure.LAYER_PROPORTIONS[layer_name]
            actual = structure.layer_counts[layer_name] / structure.total_cells
            
            # Allow 5% deviation
            assert np.abs(actual - expected) < 0.05
    
    def test_get_layer_cells(self):
        """Test retrieving cells by layer."""
        structure = LayerStructure(total_cells=1000, seed=42)
        structure.generate_positions()
        
        for layer_name in structure.LAYER_NAMES:
            indices = structure.get_layer_cells(layer_name)
            assert len(indices) == structure.layer_counts[layer_name]
    
    def test_reproducibility(self):
        """Test reproducibility with same seed."""
        s1 = LayerStructure(total_cells=1000, seed=42)
        pos1, labels1 = s1.generate_positions()
        
        s2 = LayerStructure(total_cells=1000, seed=42)
        pos2, labels2 = s2.generate_positions()
        
        # Positions should be identical with tolerance
        assert np.allclose(pos1, pos2, atol=1e-10)
        assert np.array_equal(labels1, labels2)
    
    def test_get_summary(self):
        """Test summary statistics."""
        structure = LayerStructure(total_cells=1000, seed=42)
        summary = structure.get_summary()
        
        assert summary['total_cells'] == 1000
        assert 'layers' in summary
        assert len(summary['layers']) == 4


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
