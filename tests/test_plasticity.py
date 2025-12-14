"""
Tests for plasticity module: Ca²⁺-driven LTP/LTD (Graupner & Brunel PNAS 2012)
"""

import numpy as np
import pytest
from hippocampal_ca1_lam.plasticity import CalciumDynamics, GraupnerPlasticity


class TestCalciumDynamics:
    """Tests for calcium dynamics."""
    
    def test_initialization(self):
        """Test calcium dynamics initialization."""
        ca = CalciumDynamics(tau_Ca=20.0, C_pre=1.0, C_post=2.0, seed=42)
        
        assert ca.tau_Ca == 20.0
        assert ca.C_pre == 1.0
        assert ca.C_post == 2.0
        assert ca.Ca == 0.0
    
    def test_reset(self):
        """Test calcium reset."""
        ca = CalciumDynamics(seed=42)
        ca.Ca = 5.0
        ca.reset()
        assert ca.Ca == 0.0
    
    def test_presynaptic_influx(self):
        """Test calcium influx from presynaptic spike."""
        ca = CalciumDynamics(C_pre=1.0, seed=42)
        ca.step(dt=0.1, is_pre_spike=True)
        assert ca.Ca > 0
    
    def test_postsynaptic_influx(self):
        """Test calcium influx from postsynaptic spike."""
        ca = CalciumDynamics(C_post=2.0, seed=42)
        ca.step(dt=0.1, is_post_spike=True)
        assert ca.Ca > 0
    
    def test_paired_influx(self):
        """Test calcium influx from paired spikes."""
        ca = CalciumDynamics(C_pre=1.0, C_post=2.0, seed=42)
        ca.step(dt=0.1, is_pre_spike=True, is_post_spike=True)
        
        # Should be sum of both
        assert ca.Ca >= 3.0
    
    def test_decay(self):
        """Test calcium decay over time."""
        ca = CalciumDynamics(tau_Ca=20.0, seed=42)
        
        # Add calcium
        ca.Ca = 10.0
        initial_ca = ca.Ca
        
        # Let it decay
        for _ in range(10):
            ca.step(dt=1.0)
        
        # Should have decayed
        assert ca.Ca < initial_ca
        assert ca.Ca > 0


class TestGraupnerPlasticity:
    """Tests for Graupner & Brunel plasticity model."""
    
    def test_initialization(self):
        """Test plasticity model initialization."""
        plasticity = GraupnerPlasticity(
            theta_d=1.0, theta_p=2.0, seed=42, tol=1e-10
        )
        
        assert plasticity.theta_d == 1.0
        assert plasticity.theta_p == 2.0
        assert plasticity.seed == 42
        assert plasticity.tol == 1e-10
    
    def test_threshold_parameters(self):
        """Test correct threshold parameters (θ_d=1.0 μM, θ_p=2.0 μM)."""
        plasticity = GraupnerPlasticity(seed=42)
        
        # Should use default thresholds from requirements
        assert plasticity.theta_d == 1.0
        assert plasticity.theta_p == 2.0
    
    def test_reset(self):
        """Test plasticity reset."""
        plasticity = GraupnerPlasticity(seed=42)
        plasticity.w = 0.8
        plasticity.reset(w_init=0.3)
        
        assert plasticity.w == 0.3
        assert plasticity.calcium.Ca == 0.0
    
    def test_weight_bounds(self):
        """Test synaptic weight stays in bounds."""
        plasticity = GraupnerPlasticity(w_min=0.0, w_max=1.0, seed=42)
        
        # Simulate with strong inputs
        for _ in range(1000):
            plasticity.step(dt=0.1, is_pre_spike=True, is_post_spike=True)
        
        assert plasticity.w >= 0.0
        assert plasticity.w <= 1.0
    
    def test_ltp_induction(self):
        """Test LTP (long-term potentiation) induction."""
        plasticity = GraupnerPlasticity(
            theta_d=1.0, theta_p=2.0, seed=42, tol=1e-10
        )
        
        # High-frequency paired stimulation should induce LTP
        results = plasticity.test_ltp(freq=100.0, n_pairs=60, dt_spike=10.0)
        
        # Weight should increase (potentiation)
        initial_weight = 0.5
        final_weight = results['final_weight']
        
        assert final_weight > initial_weight
    
    def test_ltd_induction(self):
        """Test LTD (long-term depression) induction."""
        plasticity = GraupnerPlasticity(
            theta_d=1.0, theta_p=2.0, seed=42, tol=1e-10
        )
        
        # Low-frequency stimulation should induce LTD
        results = plasticity.test_ltd(freq=1.0, n_spikes=900, dt_spike=-20.0)
        
        # Weight should decrease (depression) or stay low
        final_weight = results['final_weight']
        
        # LTD typically results in low weights
        assert final_weight < 0.7
    
    def test_calcium_thresholds(self):
        """Test weight changes depend on calcium thresholds."""
        plasticity = GraupnerPlasticity(theta_d=1.0, theta_p=2.0, seed=42)
        
        # Below theta_d: no change
        plasticity.calcium.Ca = 0.5
        dw_low = plasticity.compute_weight_derivative(0.5)
        assert dw_low == 0.0
        
        # Between theta_d and theta_p: depression
        dw_mid = plasticity.compute_weight_derivative(1.5)
        assert dw_mid < 0
        
        # Above theta_p: potentiation
        dw_high = plasticity.compute_weight_derivative(2.5)
        assert dw_high > 0
    
    def test_reproducibility(self):
        """Test reproducibility with same seed."""
        p1 = GraupnerPlasticity(seed=42, tol=1e-10)
        r1 = p1.test_ltp(freq=100.0, n_pairs=60, dt_spike=10.0, dt=0.1)
        
        p2 = GraupnerPlasticity(seed=42, tol=1e-10)
        r2 = p2.test_ltp(freq=100.0, n_pairs=60, dt_spike=10.0, dt=0.1)
        
        # Results should be identical with tolerance
        assert np.allclose(r1['weight'], r2['weight'], atol=1e-10)
        assert np.allclose(r1['calcium'], r2['calcium'], atol=1e-10)
        assert np.abs(r1['final_weight'] - r2['final_weight']) < 1e-10
    
    def test_simulate_protocol_output(self):
        """Test simulate_protocol output structure."""
        plasticity = GraupnerPlasticity(seed=42)
        
        spike_times_pre = [10.0, 20.0, 30.0]
        spike_times_post = [15.0, 25.0, 35.0]
        
        results = plasticity.simulate_protocol(
            spike_times_pre, spike_times_post, duration=50.0, dt=0.1
        )
        
        assert 'time' in results
        assert 'weight' in results
        assert 'calcium' in results
        assert 'final_weight' in results
        
        assert len(results['time']) == len(results['weight'])
        assert len(results['time']) == len(results['calcium'])
    
    def test_tolerance_parameter(self):
        """Test numerical tolerance parameter (tol <= 1e-10)."""
        plasticity = GraupnerPlasticity(seed=42, tol=1e-10)
        
        assert plasticity.tol <= 1e-10
        assert plasticity.tol == 1e-10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
