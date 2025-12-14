"""
Dynamics module: Two-compartment neurons and HCN gradient

Implements two-compartment neuronal model with HCN channel gradient
for realistic CA1 pyramidal cell dynamics.
"""

import numpy as np


class HCNGradient:
    """
    HCN (hyperpolarization-activated cyclic nucleotide-gated) channel gradient.
    
    HCN channels are distributed along the dendritic tree with increasing 
    density distally, implementing a gradient that normalizes temporal summation.
    
    Parameters
    ----------
    g_hcn_soma : float, default=0.5
        HCN conductance at soma (mS/cm²)
    g_hcn_dendrite : float, default=2.0
        HCN conductance at distal dendrite (mS/cm²)
    seed : int, default=42
        Random seed for reproducibility
    """
    
    def __init__(self, g_hcn_soma=0.5, g_hcn_dendrite=2.0, seed=42):
        self.g_hcn_soma = g_hcn_soma
        self.g_hcn_dendrite = g_hcn_dendrite
        self.seed = seed
        self.rng = np.random.RandomState(seed)
        
    def compute_conductance(self, distance):
        """
        Compute HCN conductance at given distance from soma.
        
        Parameters
        ----------
        distance : float or ndarray
            Distance from soma (normalized 0-1)
            
        Returns
        -------
        g_hcn : float or ndarray
            HCN conductance at specified distance
        """
        # Linear gradient from soma to dendrite
        g_hcn = self.g_hcn_soma + distance * (self.g_hcn_dendrite - self.g_hcn_soma)
        return g_hcn
    
    def compute_hcn_current(self, V, distance, h):
        """
        Compute HCN current.
        
        Parameters
        ----------
        V : float or ndarray
            Membrane potential (mV)
        distance : float or ndarray
            Distance from soma (normalized 0-1)
        h : float or ndarray
            HCN activation gating variable
            
        Returns
        -------
        I_hcn : float or ndarray
            HCN current (μA/cm²)
        """
        E_hcn = -45.0  # HCN reversal potential (mV)
        g_hcn = self.compute_conductance(distance)
        I_hcn = g_hcn * h * (V - E_hcn)
        return I_hcn
    
    def compute_h_inf(self, V):
        """
        Steady-state HCN activation.
        
        Parameters
        ----------
        V : float or ndarray
            Membrane potential (mV)
            
        Returns
        -------
        h_inf : float or ndarray
            Steady-state activation
        """
        V_half = -75.0  # Half-activation voltage (mV)
        k = 5.5         # Slope factor (mV)
        h_inf = 1.0 / (1.0 + np.exp((V - V_half) / k))
        return h_inf
    
    def compute_tau_h(self, V):
        """
        HCN activation time constant.
        
        Parameters
        ----------
        V : float or ndarray
            Membrane potential (mV)
            
        Returns
        -------
        tau_h : float or ndarray
            Time constant (ms)
        """
        # Voltage-dependent time constant
        tau_h = 20.0 + 50.0 * np.exp(-((V + 75.0) / 20.0) ** 2)
        return tau_h


class TwoCompartmentNeuron:
    """
    Two-compartment neuron model for CA1 pyramidal cells.
    
    Implements soma and dendritic compartments with coupling conductance,
    HCN gradient, and basic Hodgkin-Huxley channels.
    
    Parameters
    ----------
    C_m : float, default=1.0
        Membrane capacitance (μF/cm²)
    g_L : float, default=0.1
        Leak conductance (mS/cm²)
    E_L : float, default=-70.0
        Leak reversal potential (mV)
    g_couple : float, default=0.5
        Coupling conductance between compartments (mS/cm²)
    hcn_gradient : HCNGradient, optional
        HCN channel gradient object
    seed : int, default=42
        Random seed for reproducibility
    tol : float, default=1e-10
        Numerical tolerance
    """
    
    def __init__(self, C_m=1.0, g_L=0.1, E_L=-70.0, g_couple=0.5, 
                 hcn_gradient=None, seed=42, tol=1e-10):
        self.C_m = C_m
        self.g_L = g_L
        self.E_L = E_L
        self.g_couple = g_couple
        self.hcn_gradient = hcn_gradient if hcn_gradient else HCNGradient(seed=seed)
        self.seed = seed
        self.tol = tol
        self.rng = np.random.RandomState(seed)
        
        # State variables
        self.V_soma = E_L
        self.V_dend = E_L
        self.h_soma = self.hcn_gradient.compute_h_inf(E_L)
        self.h_dend = self.hcn_gradient.compute_h_inf(E_L)
        
        # Spike detection
        self.V_threshold = -50.0
        self.spike_times = []
        
    def reset(self):
        """Reset neuron to resting state."""
        self.V_soma = self.E_L
        self.V_dend = self.E_L
        self.h_soma = self.hcn_gradient.compute_h_inf(self.E_L)
        self.h_dend = self.hcn_gradient.compute_h_inf(self.E_L)
        self.spike_times = []
    
    def step(self, dt, I_soma=0.0, I_dend=0.0):
        """
        Integrate one time step using forward Euler method.
        
        Parameters
        ----------
        dt : float
            Time step (ms)
        I_soma : float, default=0.0
            External current to soma (μA/cm²)
        I_dend : float, default=0.0
            External current to dendrite (μA/cm²)
            
        Returns
        -------
        V_soma : float
            Soma membrane potential (mV)
        V_dend : float
            Dendrite membrane potential (mV)
        spike : bool
            Whether a spike occurred
        """
        # HCN currents
        I_hcn_soma = self.hcn_gradient.compute_hcn_current(
            self.V_soma, 0.0, self.h_soma
        )
        I_hcn_dend = self.hcn_gradient.compute_hcn_current(
            self.V_dend, 1.0, self.h_dend
        )
        
        # Leak currents
        I_L_soma = self.g_L * (self.V_soma - self.E_L)
        I_L_dend = self.g_L * (self.V_dend - self.E_L)
        
        # Coupling currents
        I_couple_soma = self.g_couple * (self.V_soma - self.V_dend)
        I_couple_dend = self.g_couple * (self.V_dend - self.V_soma)
        
        # Voltage updates
        dV_soma = (I_soma - I_L_soma - I_hcn_soma - I_couple_soma) / self.C_m
        dV_dend = (I_dend - I_L_dend - I_hcn_dend - I_couple_dend) / self.C_m
        
        self.V_soma += dt * dV_soma
        self.V_dend += dt * dV_dend
        
        # HCN gating variable updates
        h_inf_soma = self.hcn_gradient.compute_h_inf(self.V_soma)
        tau_h_soma = self.hcn_gradient.compute_tau_h(self.V_soma)
        dh_soma = (h_inf_soma - self.h_soma) / tau_h_soma
        self.h_soma += dt * dh_soma
        
        h_inf_dend = self.hcn_gradient.compute_h_inf(self.V_dend)
        tau_h_dend = self.hcn_gradient.compute_tau_h(self.V_dend)
        dh_dend = (h_inf_dend - self.h_dend) / tau_h_dend
        self.h_dend += dt * dh_dend
        
        # Spike detection
        spike = self.V_soma > self.V_threshold
        
        return self.V_soma, self.V_dend, spike
    
    def simulate(self, duration, dt, I_soma=None, I_dend=None):
        """
        Simulate neuron for specified duration.
        
        Parameters
        ----------
        duration : float
            Simulation duration (ms)
        dt : float
            Time step (ms)
        I_soma : array-like or float, optional
            External current to soma (μA/cm²)
        I_dend : array-like or float, optional
            External current to dendrite (μA/cm²)
            
        Returns
        -------
        results : dict
            Dictionary containing time series of V_soma, V_dend, and spike times
        """
        n_steps = int(duration / dt)
        
        # Initialize input currents
        if I_soma is None:
            I_soma = np.zeros(n_steps)
        elif np.isscalar(I_soma):
            I_soma = np.full(n_steps, I_soma)
        else:
            I_soma = np.asarray(I_soma)
            
        if I_dend is None:
            I_dend = np.zeros(n_steps)
        elif np.isscalar(I_dend):
            I_dend = np.full(n_steps, I_dend)
        else:
            I_dend = np.asarray(I_dend)
        
        # Initialize output arrays
        V_soma_trace = np.zeros(n_steps)
        V_dend_trace = np.zeros(n_steps)
        spike_times = []
        
        # Reset neuron
        self.reset()
        
        # Simulation loop
        for i in range(n_steps):
            V_soma, V_dend, spike = self.step(dt, I_soma[i], I_dend[i])
            V_soma_trace[i] = V_soma
            V_dend_trace[i] = V_dend
            
            if spike:
                spike_times.append(i * dt)
        
        results = {
            'time': np.arange(n_steps) * dt,
            'V_soma': V_soma_trace,
            'V_dend': V_dend_trace,
            'spike_times': np.array(spike_times)
        }
        
        return results
