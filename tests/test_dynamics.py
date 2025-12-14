"""
Tests for dynamics module: Two-compartment neurons and HCN gradient
"""

import numpy as np
import pytest
from hippocampal_ca1_lam.dynamics import HCNGradient, TwoCompartmentNeuron


class TestHCNGradient:
    """Tests for HCN channel gradient."""
    
    def test_initialization(self):
        """Test HCN gradient initialization."""
        hcn = HCNGradient(g_hcn_soma=0.5, g_hcn_dendrite=2.0, seed=42)
        
        assert hcn.g_hcn_soma == 0.5
        assert hcn.g_hcn_dendrite == 2.0
        assert hcn.seed == 42
    
    def test_conductance_gradient(self):
        """Test HCN conductance increases with distance."""
        hcn = HCNGradient(g_hcn_soma=0.5, g_hcn_dendrite=2.0, seed=42)
        
        g_soma = hcn.compute_conductance(0.0)
        g_mid = hcn.compute_conductance(0.5)
        g_dend = hcn.compute_conductance(1.0)
        
        # Check gradient: soma < mid < dendrite
        assert g_soma < g_mid < g_dend
        assert np.abs(g_soma - 0.5) < 1e-10
        assert np.abs(g_dend - 2.0) < 1e-10
    
    def test_h_inf_properties(self):
        """Test HCN steady-state activation properties."""
        hcn = HCNGradient(seed=42)
        
        # At hyperpolarized potentials, h_inf should be high
        h_hyper = hcn.compute_h_inf(-90.0)
        h_rest = hcn.compute_h_inf(-70.0)
        h_depol = hcn.compute_h_inf(-50.0)
        
        # More hyperpolarized -> higher h_inf
        assert h_hyper > h_rest > h_depol
        
        # Values should be in [0, 1]
        assert 0 <= h_hyper <= 1
        assert 0 <= h_rest <= 1
        assert 0 <= h_depol <= 1
    
    def test_tau_h_positive(self):
        """Test HCN time constant is positive."""
        hcn = HCNGradient(seed=42)
        
        voltages = np.linspace(-100, -50, 10)
        for V in voltages:
            tau = hcn.compute_tau_h(V)
            assert tau > 0


class TestTwoCompartmentNeuron:
    """Tests for two-compartment neuron model."""
    
    def test_initialization(self):
        """Test neuron initialization."""
        neuron = TwoCompartmentNeuron(seed=42, tol=1e-10)
        
        assert neuron.seed == 42
        assert neuron.tol == 1e-10
        assert neuron.V_soma == neuron.E_L
        assert neuron.V_dend == neuron.E_L
    
    def test_reset(self):
        """Test neuron reset to resting state."""
        neuron = TwoCompartmentNeuron(seed=42)
        
        # Change state
        neuron.V_soma = -50.0
        neuron.V_dend = -60.0
        
        # Reset
        neuron.reset()
        
        assert neuron.V_soma == neuron.E_L
        assert neuron.V_dend == neuron.E_L
        assert len(neuron.spike_times) == 0
    
    def test_step_integration(self):
        """Test single step integration."""
        neuron = TwoCompartmentNeuron(seed=42, tol=1e-10)
        
        dt = 0.1  # ms
        I_soma = 5.0  # μA/cm²
        
        V_soma_before = neuron.V_soma
        V_soma, V_dend, spike = neuron.step(dt, I_soma=I_soma)
        
        # Voltage should change with current injection
        assert V_soma != V_soma_before
        assert isinstance(spike, (bool, np.bool_))
    
    def test_resting_potential_stability(self):
        """Test neuron stays near rest without input."""
        neuron = TwoCompartmentNeuron(seed=42, tol=1e-10)
        
        # Simulate without input
        results = neuron.simulate(duration=100.0, dt=0.1)
        
        # Should stay relatively stable (HCN can cause some drift)
        # Allow drift within 20 mV of rest
        assert np.abs(np.mean(results['V_soma']) - neuron.E_L) < 20.0
        assert len(results['spike_times']) == 0
    
    def test_current_response(self):
        """Test neuron responds to current injection."""
        neuron = TwoCompartmentNeuron(seed=42, tol=1e-10)
        
        # Create step current
        duration = 50.0
        dt = 0.1
        n_steps = int(duration / dt)
        I_soma = np.zeros(n_steps)
        I_soma[100:400] = 10.0  # Strong current pulse
        
        results = neuron.simulate(duration=duration, dt=dt, I_soma=I_soma)
        
        # Voltage should increase during current injection
        V_during_current = np.mean(results['V_soma'][100:400])
        assert V_during_current > neuron.E_L
    
    def test_compartment_coupling(self):
        """Test soma and dendrite are coupled."""
        neuron = TwoCompartmentNeuron(seed=42)
        
        # Inject current only in dendrite
        duration = 50.0
        dt = 0.1
        n_steps = int(duration / dt)
        I_dend = np.zeros(n_steps)
        I_dend[100:400] = 10.0
        
        results = neuron.simulate(duration=duration, dt=dt, I_dend=I_dend)
        
        # Both compartments should respond due to coupling
        V_soma_response = np.max(results['V_soma']) - neuron.E_L
        V_dend_response = np.max(results['V_dend']) - neuron.E_L
        
        assert V_soma_response > 0  # Soma responds to dendritic input
        assert V_dend_response > V_soma_response  # But dendrite more
    
    def test_reproducibility(self):
        """Test simulation reproducibility with same seed."""
        n1 = TwoCompartmentNeuron(seed=42, tol=1e-10)
        r1 = n1.simulate(duration=50.0, dt=0.1, I_soma=5.0)
        
        n2 = TwoCompartmentNeuron(seed=42, tol=1e-10)
        r2 = n2.simulate(duration=50.0, dt=0.1, I_soma=5.0)
        
        # Results should be identical with tolerance
        assert np.allclose(r1['V_soma'], r2['V_soma'], atol=1e-10)
        assert np.allclose(r1['V_dend'], r2['V_dend'], atol=1e-10)
    
    def test_output_structure(self):
        """Test simulation output structure."""
        neuron = TwoCompartmentNeuron(seed=42)
        results = neuron.simulate(duration=10.0, dt=0.1)
        
        assert 'time' in results
        assert 'V_soma' in results
        assert 'V_dend' in results
        assert 'spike_times' in results
        
        # Check lengths
        assert len(results['time']) == len(results['V_soma'])
        assert len(results['time']) == len(results['V_dend'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
