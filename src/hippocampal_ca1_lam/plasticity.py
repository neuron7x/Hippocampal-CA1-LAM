"""
Plasticity module: Ca²⁺-driven LTP/LTD based on Graupner & Brunel PNAS 2012

Implements calcium-based synaptic plasticity with depression and potentiation
thresholds for modeling learning in CA1 pyramidal neurons.
"""

import numpy as np


class CalciumDynamics:
    """
    Calcium dynamics model for synaptic plasticity.
    
    Implements calcium influx, buffering, and decay dynamics that drive
    synaptic weight changes.
    
    Parameters
    ----------
    tau_Ca : float, default=20.0
        Calcium decay time constant (ms)
    C_pre : float, default=1.0
        Calcium influx per presynaptic spike (μM)
    C_post : float, default=2.0
        Calcium influx per postsynaptic spike (μM)
    seed : int, default=42
        Random seed for reproducibility
    """
    
    def __init__(self, tau_Ca=20.0, C_pre=1.0, C_post=2.0, seed=42):
        self.tau_Ca = tau_Ca
        self.C_pre = C_pre
        self.C_post = C_post
        self.seed = seed
        self.rng = np.random.RandomState(seed)
        
        # Current calcium concentration
        self.Ca = 0.0
        
    def reset(self):
        """Reset calcium concentration to baseline."""
        self.Ca = 0.0
    
    def add_influx(self, is_pre_spike=False, is_post_spike=False):
        """
        Add calcium influx from spike events.
        
        Parameters
        ----------
        is_pre_spike : bool
            Whether presynaptic spike occurred
        is_post_spike : bool
            Whether postsynaptic spike occurred
        """
        if is_pre_spike:
            self.Ca += self.C_pre
        if is_post_spike:
            self.Ca += self.C_post
    
    def step(self, dt, is_pre_spike=False, is_post_spike=False):
        """
        Update calcium concentration for one time step.
        
        Parameters
        ----------
        dt : float
            Time step (ms)
        is_pre_spike : bool
            Whether presynaptic spike occurred
        is_post_spike : bool
            Whether postsynaptic spike occurred
            
        Returns
        -------
        Ca : float
            Current calcium concentration (μM)
        """
        # Add influx from spikes
        self.add_influx(is_pre_spike, is_post_spike)
        
        # Exponential decay
        self.Ca *= np.exp(-dt / self.tau_Ca)
        
        return self.Ca
    
    def get_concentration(self):
        """
        Get current calcium concentration.
        
        Returns
        -------
        Ca : float
            Current calcium concentration (μM)
        """
        return self.Ca


class GraupnerPlasticity:
    """
    Calcium-based synaptic plasticity model (Graupner & Brunel, PNAS 2012).
    
    Implements bistable synaptic weight dynamics driven by calcium concentration
    with depression threshold θ_d and potentiation threshold θ_p.
    
    Parameters
    ----------
    theta_d : float, default=1.0
        Depression threshold (μM)
    theta_p : float, default=2.0
        Potentiation threshold (μM)
    gamma_d : float, default=200.0
        Depression rate (1/s)
    gamma_p : float, default=1000.0
        Potentiation rate (1/s)
    tau_w : float, default=1000.0
        Weight time constant (ms)
    w_min : float, default=0.0
        Minimum synaptic weight
    w_max : float, default=1.0
        Maximum synaptic weight
    sigma : float, default=0.0
        Noise strength (for stochastic version)
    seed : int, default=42
        Random seed for reproducibility
    tol : float, default=1e-10
        Numerical tolerance
    """
    
    def __init__(self, theta_d=1.0, theta_p=2.0, gamma_d=200.0, gamma_p=1000.0,
                 tau_w=1000.0, w_min=0.0, w_max=1.0, sigma=0.0, seed=42, tol=1e-10):
        self.theta_d = theta_d
        self.theta_p = theta_p
        self.gamma_d = gamma_d
        self.gamma_p = gamma_p
        self.tau_w = tau_w
        self.w_min = w_min
        self.w_max = w_max
        self.sigma = sigma
        self.seed = seed
        self.tol = tol
        self.rng = np.random.RandomState(seed)
        
        # Initialize calcium dynamics
        self.calcium = CalciumDynamics(seed=seed)
        
        # Synaptic weight
        self.w = 0.5
        
    def reset(self, w_init=0.5):
        """
        Reset plasticity model.
        
        Parameters
        ----------
        w_init : float, default=0.5
            Initial synaptic weight
        """
        self.calcium.reset()
        self.w = w_init
    
    def compute_weight_derivative(self, Ca):
        """
        Compute weight change rate based on calcium concentration.
        
        Parameters
        ----------
        Ca : float
            Calcium concentration (μM)
            
        Returns
        -------
        dw_dt : float
            Rate of weight change (1/ms)
        """
        # Depression term (active when Ca > theta_d)
        if Ca > self.theta_d:
            depression = -self.gamma_d * (1.0 - self.w)
        else:
            depression = 0.0
        
        # Potentiation term (active when Ca > theta_p)
        if Ca > self.theta_p:
            potentiation = self.gamma_p * self.w
        else:
            potentiation = 0.0
        
        # Combined dynamics (convert from 1/s to 1/ms)
        dw_dt = (depression + potentiation) / 1000.0
        
        return dw_dt
    
    def step(self, dt, is_pre_spike=False, is_post_spike=False):
        """
        Update synaptic weight for one time step.
        
        Parameters
        ----------
        dt : float
            Time step (ms)
        is_pre_spike : bool
            Whether presynaptic spike occurred
        is_post_spike : bool
            Whether postsynaptic spike occurred
            
        Returns
        -------
        w : float
            Current synaptic weight
        Ca : float
            Current calcium concentration (μM)
        """
        # Update calcium concentration
        Ca = self.calcium.step(dt, is_pre_spike, is_post_spike)
        
        # Compute weight derivative
        dw_dt = self.compute_weight_derivative(Ca)
        
        # Add noise if specified
        if self.sigma > 0:
            noise = self.rng.normal(0, self.sigma * np.sqrt(dt))
        else:
            noise = 0.0
        
        # Update weight
        self.w += dt * dw_dt + noise
        
        # Enforce bounds
        self.w = np.clip(self.w, self.w_min, self.w_max)
        
        return self.w, Ca
    
    def simulate_protocol(self, spike_times_pre, spike_times_post, duration, dt):
        """
        Simulate plasticity protocol with given spike trains.
        
        Parameters
        ----------
        spike_times_pre : array-like
            Presynaptic spike times (ms)
        spike_times_post : array-like
            Postsynaptic spike times (ms)
        duration : float
            Simulation duration (ms)
        dt : float
            Time step (ms)
            
        Returns
        -------
        results : dict
            Dictionary containing time series of weight and calcium
        """
        n_steps = int(duration / dt)
        
        # Convert spike times to arrays
        spike_times_pre = np.asarray(spike_times_pre)
        spike_times_post = np.asarray(spike_times_post)
        
        # Initialize output arrays
        time = np.arange(n_steps) * dt
        w_trace = np.zeros(n_steps)
        Ca_trace = np.zeros(n_steps)
        
        # Reset model
        self.reset()
        
        # Convert spike times to indices
        spike_indices_pre = (spike_times_pre / dt).astype(int)
        spike_indices_post = (spike_times_post / dt).astype(int)
        
        # Simulation loop
        for i in range(n_steps):
            # Check for spikes at current time
            is_pre_spike = i in spike_indices_pre
            is_post_spike = i in spike_indices_post
            
            # Update plasticity
            w, Ca = self.step(dt, is_pre_spike, is_post_spike)
            
            # Store values
            w_trace[i] = w
            Ca_trace[i] = Ca
        
        results = {
            'time': time,
            'weight': w_trace,
            'calcium': Ca_trace,
            'final_weight': self.w
        }
        
        return results
    
    def test_ltp(self, freq=100.0, n_pairs=60, dt_spike=10.0, dt=0.1):
        """
        Test LTP induction with paired pre-post spikes.
        
        Parameters
        ----------
        freq : float
            Pairing frequency (Hz)
        n_pairs : int
            Number of spike pairs
        dt_spike : float
            Pre-post spike timing (ms, positive for post after pre)
        dt : float
            Simulation time step (ms)
            
        Returns
        -------
        results : dict
            Plasticity protocol results
        """
        interval = 1000.0 / freq  # ms
        
        # Generate spike times
        spike_times_pre = np.arange(n_pairs) * interval
        spike_times_post = spike_times_pre + dt_spike
        
        duration = n_pairs * interval + 100.0
        
        return self.simulate_protocol(spike_times_pre, spike_times_post, duration, dt)
    
    def test_ltd(self, freq=1.0, n_spikes=900, dt_spike=-20.0, dt=0.1):
        """
        Test LTD induction with low frequency stimulation.
        
        Parameters
        ----------
        freq : float
            Stimulation frequency (Hz)
        n_spikes : int
            Number of spikes
        dt_spike : float
            Pre-post spike timing (ms, negative for post before pre)
        dt : float
            Simulation time step (ms)
            
        Returns
        -------
        results : dict
            Plasticity protocol results
        """
        interval = 1000.0 / freq  # ms
        
        # Generate spike times
        spike_times_pre = np.arange(n_spikes) * interval
        spike_times_post = spike_times_pre + dt_spike
        
        duration = n_spikes * interval + 100.0
        
        return self.simulate_protocol(spike_times_pre, spike_times_post, duration, dt)
