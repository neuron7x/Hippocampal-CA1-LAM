"""
Structure module: ZINB inference and 4-layer laminar organization

Implements the structural model from Pachicano et al., Nature Communications 2025
with 58,065 cells distributed across 4 laminar layers using Zero-Inflated 
Negative Binomial (ZINB) inference.
"""

import numpy as np
from scipy import stats
from scipy.special import gammaln, logsumexp


class ZINBInference:
    """
    Zero-Inflated Negative Binomial inference for cell distribution.
    
    The ZINB model accounts for excess zeros and overdispersion in count data,
    suitable for RNAscope cell counting data.
    
    Parameters
    ----------
    seed : int, default=42
        Random seed for reproducibility
    tol : float, default=1e-10
        Convergence tolerance for parameter estimation
    """
    
    def __init__(self, seed=42, tol=1e-10):
        self.seed = seed
        self.tol = tol
        self.rng = np.random.RandomState(seed)
        self.params = {}
        
    def fit(self, counts, max_iter=1000):
        """
        Fit ZINB model to observed counts using EM algorithm.
        
        Parameters
        ----------
        counts : array-like
            Observed cell counts
        max_iter : int
            Maximum iterations for EM algorithm
            
        Returns
        -------
        params : dict
            Fitted parameters (mu, r, pi)
        """
        counts = np.asarray(counts)
        n = len(counts)
        
        # Initialize parameters
        mu = np.mean(counts) + self.tol
        r = 1.0
        pi = np.sum(counts == 0) / n
        
        for iteration in range(max_iter):
            # E-step: compute posterior probabilities
            log_p_zero = np.log(pi + self.tol)
            log_p_count = np.log(1 - pi + self.tol) + self._nbinom_logpmf(counts, mu, r)
            
            # Probability that zero comes from zero-inflation
            zero_mask = counts == 0
            if np.any(zero_mask):
                log_gamma = np.full(n, -np.inf)
                # Stack log probabilities for logsumexp
                log_probs = np.vstack([
                    np.full(np.sum(zero_mask), log_p_zero),
                    log_p_count[zero_mask]
                ])
                log_gamma[zero_mask] = log_p_zero - logsumexp(log_probs, axis=0)
            else:
                log_gamma = np.full(n, -np.inf)
                
            gamma = np.exp(log_gamma)
            
            # M-step: update parameters
            pi_new = np.mean(gamma)
            
            # Update mu using non-zero-inflated observations
            weights = 1 - gamma
            mu_new = np.sum(weights * counts) / np.sum(weights) + self.tol
            
            # Update r using moment matching
            var_empirical = np.var(counts)
            r_new = mu_new ** 2 / (var_empirical - mu_new + self.tol)
            r_new = max(r_new, self.tol)
            
            # Check convergence
            if (abs(mu_new - mu) < self.tol and 
                abs(r_new - r) < self.tol and 
                abs(pi_new - pi) < self.tol):
                break
                
            mu, r, pi = mu_new, r_new, pi_new
        
        self.params = {'mu': mu, 'r': r, 'pi': pi}
        return self.params
    
    def _nbinom_logpmf(self, k, mu, r):
        """Negative binomial log probability mass function."""
        k = np.asarray(k)
        n = r
        p = r / (r + mu)
        
        logpmf = (gammaln(k + n) - gammaln(k + 1) - gammaln(n) +
                  n * np.log(p + self.tol) + k * np.log(1 - p + self.tol))
        return logpmf
    
    def sample(self, size):
        """
        Sample from fitted ZINB distribution.
        
        Parameters
        ----------
        size : int
            Number of samples to generate
            
        Returns
        -------
        samples : ndarray
            Generated samples
        """
        if not self.params:
            raise ValueError("Model must be fitted before sampling")
            
        mu = self.params['mu']
        r = self.params['r']
        pi = self.params['pi']
        
        # Sample zero-inflation indicator
        zero_inflated = self.rng.binomial(1, pi, size=size)
        
        # Sample from negative binomial
        p = r / (r + mu)
        nb_samples = self.rng.negative_binomial(r, p, size=size)
        
        # Combine: zero-inflated samples are 0, others from NB
        samples = np.where(zero_inflated, 0, nb_samples)
        return samples
    
    def cross_entropy(self, counts):
        """
        Compute cross-entropy loss for model validation.
        
        Parameters
        ----------
        counts : array-like
            Observed counts
            
        Returns
        -------
        ce : float
            Cross-entropy value
        """
        counts = np.asarray(counts)
        mu = self.params['mu']
        r = self.params['r']
        pi = self.params['pi']
        
        # Compute log-likelihood
        zero_mask = counts == 0
        log_lik = np.zeros_like(counts, dtype=float)
        
        # For zeros: mixture of zero-inflation and NB
        if np.any(zero_mask):
            log_p_zero = np.log(pi + self.tol)
            log_nb_zero = np.log(1 - pi + self.tol) + self._nbinom_logpmf(0, mu, r)
            log_lik[zero_mask] = logsumexp([log_p_zero, log_nb_zero])
        
        # For non-zeros: only from NB component
        non_zero_mask = ~zero_mask
        if np.any(non_zero_mask):
            log_lik[non_zero_mask] = (np.log(1 - pi + self.tol) + 
                                      self._nbinom_logpmf(counts[non_zero_mask], mu, r))
        
        # Cross-entropy is negative mean log-likelihood
        ce = -np.mean(log_lik)
        return ce


class LayerStructure:
    """
    4-layer laminar CA1 organization based on Pachicano et al., Nat Comm 2025.
    
    Organizes 58,065 cells across four layers:
    - Stratum Oriens (SO)
    - Stratum Pyramidale (SP) 
    - Stratum Radiatum (SR)
    - Stratum Lacunosum-Moleculare (SLM)
    
    Parameters
    ----------
    total_cells : int, default=58065
        Total number of cells in the model
    seed : int, default=42
        Random seed for reproducibility
    """
    
    LAYER_NAMES = ['SO', 'SP', 'SR', 'SLM']
    
    # Layer proportions from Pachicano et al., Nat Comm 2025
    # Based on RNAscope analysis of CA1 laminar structure
    LAYER_PROPORTIONS = {
        'SO': 0.15,   # Stratum Oriens: interneurons, basal dendrites
        'SP': 0.25,   # Stratum Pyramidale: pyramidal cell bodies
        'SR': 0.40,   # Stratum Radiatum: apical dendrites, Schaffer collaterals
        'SLM': 0.20   # Stratum Lacunosum-Moleculare: perforant path inputs
    }
    
    def __init__(self, total_cells=58065, seed=42):
        self.total_cells = total_cells
        self.seed = seed
        self.rng = np.random.RandomState(seed)
        self.layer_counts = {}
        self.cell_positions = None
        self._initialize_layers()
        
    def _initialize_layers(self):
        """Initialize cell distribution across layers."""
        for layer_name in self.LAYER_NAMES:
            proportion = self.LAYER_PROPORTIONS[layer_name]
            self.layer_counts[layer_name] = int(self.total_cells * proportion)
        
        # Adjust for rounding errors
        total_assigned = sum(self.layer_counts.values())
        if total_assigned != self.total_cells:
            # Add/remove cells from largest layer
            diff = self.total_cells - total_assigned
            self.layer_counts['SR'] += diff
    
    def generate_positions(self):
        """
        Generate 3D spatial positions for all cells.
        
        Returns
        -------
        positions : ndarray, shape (total_cells, 3)
            Cell positions (x, y, z) where z indicates layer depth
        layer_labels : ndarray, shape (total_cells,)
            Layer assignment for each cell
        """
        positions = []
        layer_labels = []
        
        # Layer depth boundaries (normalized 0-1)
        depth_ranges = {
            'SO': (0.0, 0.15),
            'SP': (0.15, 0.40),
            'SR': (0.40, 0.80),
            'SLM': (0.80, 1.0)
        }
        
        for i, layer_name in enumerate(self.LAYER_NAMES):
            n_cells = self.layer_counts[layer_name]
            
            # Generate random positions within layer boundaries
            z_min, z_max = depth_ranges[layer_name]
            x = self.rng.uniform(0, 1, n_cells)
            y = self.rng.uniform(0, 1, n_cells)
            z = self.rng.uniform(z_min, z_max, n_cells)
            
            layer_positions = np.column_stack([x, y, z])
            positions.append(layer_positions)
            layer_labels.extend([i] * n_cells)
        
        self.cell_positions = np.vstack(positions)
        self.layer_labels = np.array(layer_labels)
        
        return self.cell_positions, self.layer_labels
    
    def get_layer_cells(self, layer_name):
        """
        Get indices of cells in specified layer.
        
        Parameters
        ----------
        layer_name : str
            Layer name ('SO', 'SP', 'SR', 'SLM')
            
        Returns
        -------
        indices : ndarray
            Indices of cells in the layer
        """
        if layer_name not in self.LAYER_NAMES:
            raise ValueError(f"Invalid layer name. Must be one of {self.LAYER_NAMES}")
        
        if self.cell_positions is None:
            self.generate_positions()
        
        layer_idx = self.LAYER_NAMES.index(layer_name)
        return np.where(self.layer_labels == layer_idx)[0]
    
    def get_summary(self):
        """
        Get summary statistics of layer structure.
        
        Returns
        -------
        summary : dict
            Summary statistics including cell counts per layer
        """
        summary = {
            'total_cells': self.total_cells,
            'layers': {}
        }
        
        for layer_name in self.LAYER_NAMES:
            summary['layers'][layer_name] = {
                'count': self.layer_counts[layer_name],
                'proportion': self.layer_counts[layer_name] / self.total_cells
            }
        
        return summary
