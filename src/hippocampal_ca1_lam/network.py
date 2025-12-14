"""
Network module: Connectivity and spectral stability

Implements network connectivity patterns and spectral radius control
for stable network dynamics (ρ(W) < 1.0).
"""

import numpy as np
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import eigs


class NetworkConnectivity:
    """
    Network connectivity for CA1 laminar structure.
    
    Implements layer-specific connectivity patterns with distance-dependent
    connection probabilities.
    
    Parameters
    ----------
    n_neurons : int
        Total number of neurons
    layer_labels : array-like
        Layer assignment for each neuron
    seed : int, default=42
        Random seed for reproducibility
    """
    
    def __init__(self, n_neurons, layer_labels, seed=42):
        self.n_neurons = n_neurons
        self.layer_labels = np.asarray(layer_labels)
        self.seed = seed
        self.rng = np.random.RandomState(seed)
        
        # Connectivity matrix (sparse)
        self.W = None
        
        # Connection probabilities between layers
        # Rows: source layer, Cols: target layer
        # Based on known CA1 connectivity patterns
        self.p_connect = np.array([
            [0.10, 0.05, 0.02, 0.01],  # SO -> SO, SP, SR, SLM
            [0.15, 0.20, 0.10, 0.05],  # SP -> SO, SP, SR, SLM
            [0.05, 0.15, 0.15, 0.08],  # SR -> SO, SP, SR, SLM
            [0.02, 0.05, 0.10, 0.10]   # SLM -> SO, SP, SR, SLM
        ])
        
    def generate_connectivity(self, positions=None, distance_scale=0.1):
        """
        Generate connectivity matrix with distance-dependent probabilities.
        
        Parameters
        ----------
        positions : ndarray, optional
            Cell positions (n_neurons, 3)
        distance_scale : float, default=0.1
            Spatial scale for distance-dependent connections
            
        Returns
        -------
        W : sparse matrix
            Connectivity matrix (n_neurons, n_neurons)
        """
        # Initialize sparse matrix
        W = lil_matrix((self.n_neurons, self.n_neurons))
        
        # Generate connections
        for i in range(self.n_neurons):
            source_layer = self.layer_labels[i]
            
            for j in range(self.n_neurons):
                if i == j:
                    continue
                    
                target_layer = self.layer_labels[j]
                
                # Base connection probability from layer pair
                p_base = self.p_connect[source_layer, target_layer]
                
                # Modulate by distance if positions provided
                if positions is not None:
                    dist = np.linalg.norm(positions[i] - positions[j])
                    p_conn = p_base * np.exp(-dist / distance_scale)
                else:
                    p_conn = p_base
                
                # Create connection probabilistically
                if self.rng.random() < p_conn:
                    # Random weight from normal distribution
                    weight = abs(self.rng.normal(1.0, 0.2))
                    W[i, j] = weight
        
        # Convert to CSR format for efficient operations
        self.W = W.tocsr()
        
        return self.W
    
    def get_connectivity_stats(self):
        """
        Compute connectivity statistics.
        
        Returns
        -------
        stats : dict
            Dictionary with connectivity statistics
        """
        if self.W is None:
            raise ValueError("Connectivity matrix not generated yet")
        
        # Convert to dense for easier computation (only for stats)
        W_dense = self.W.toarray()
        
        # Compute statistics
        n_connections = np.count_nonzero(W_dense)
        connection_prob = n_connections / (self.n_neurons * (self.n_neurons - 1))
        
        in_degrees = np.sum(W_dense > 0, axis=0)
        out_degrees = np.sum(W_dense > 0, axis=1)
        
        weights = W_dense[W_dense > 0]
        
        stats = {
            'n_connections': n_connections,
            'connection_probability': connection_prob,
            'mean_in_degree': np.mean(in_degrees),
            'mean_out_degree': np.mean(out_degrees),
            'mean_weight': np.mean(weights),
            'std_weight': np.std(weights)
        }
        
        return stats
    
    def scale_weights(self, scale_factor):
        """
        Scale all synaptic weights by a factor.
        
        Parameters
        ----------
        scale_factor : float
            Multiplicative scaling factor
        """
        if self.W is None:
            raise ValueError("Connectivity matrix not generated yet")
        
        self.W = self.W.multiply(scale_factor)


class SpectralStability:
    """
    Spectral radius control for network stability.
    
    Ensures network weight matrix has spectral radius ρ(W) < 1.0
    for stable dynamics.
    
    Parameters
    ----------
    max_radius : float, default=0.95
        Target maximum spectral radius
    tol : float, default=1e-10
        Numerical tolerance
    """
    
    def __init__(self, max_radius=0.95, tol=1e-10):
        self.max_radius = max_radius
        self.tol = tol
        
    def compute_spectral_radius(self, W):
        """
        Compute spectral radius (largest eigenvalue magnitude).
        
        Parameters
        ----------
        W : ndarray or sparse matrix
            Weight matrix
            
        Returns
        -------
        rho : float
            Spectral radius ρ(W)
        """
        # For sparse matrices, use sparse eigenvalue solver
        if hasattr(W, 'toarray'):
            # Get largest eigenvalues in magnitude
            try:
                eigenvalues = eigs(W, k=min(6, min(W.shape) - 2), 
                                  which='LM', return_eigenvectors=False)
                rho = np.max(np.abs(eigenvalues))
            except:
                # Fall back to dense computation for small matrices
                W_dense = W.toarray()
                eigenvalues = np.linalg.eigvals(W_dense)
                rho = np.max(np.abs(eigenvalues))
        else:
            # Dense matrix
            eigenvalues = np.linalg.eigvals(W)
            rho = np.max(np.abs(eigenvalues))
        
        return rho
    
    def enforce_stability(self, W):
        """
        Scale weight matrix to enforce spectral radius constraint.
        
        Parameters
        ----------
        W : ndarray or sparse matrix
            Weight matrix
            
        Returns
        -------
        W_stable : ndarray or sparse matrix
            Scaled weight matrix with ρ(W) ≤ max_radius
        rho : float
            Original spectral radius
        scale_factor : float
            Applied scaling factor
        """
        # Compute current spectral radius
        rho = self.compute_spectral_radius(W)
        
        # Scale if necessary
        if rho > self.max_radius:
            scale_factor = self.max_radius / (rho + self.tol)
            
            # Scale matrix
            if hasattr(W, 'multiply'):
                W_stable = W.multiply(scale_factor)
            else:
                W_stable = W * scale_factor
        else:
            W_stable = W
            scale_factor = 1.0
        
        return W_stable, rho, scale_factor
    
    def validate_stability(self, W):
        """
        Check if weight matrix satisfies stability constraint.
        
        Parameters
        ----------
        W : ndarray or sparse matrix
            Weight matrix
            
        Returns
        -------
        is_stable : bool
            Whether ρ(W) < 1.0
        rho : float
            Spectral radius
        """
        rho = self.compute_spectral_radius(W)
        is_stable = rho < 1.0
        
        return is_stable, rho


def create_ca1_network(layer_structure, seed=42):
    """
    Create CA1 network with laminar connectivity and spectral stability.
    
    Parameters
    ----------
    layer_structure : LayerStructure
        Layer structure object with cell positions
    seed : int, default=42
        Random seed
        
    Returns
    -------
    network : NetworkConnectivity
        Network connectivity object
    stability : SpectralStability
        Spectral stability controller
    """
    # Generate positions if not already done
    if layer_structure.cell_positions is None:
        layer_structure.generate_positions()
    
    # Create network connectivity
    network = NetworkConnectivity(
        layer_structure.total_cells,
        layer_structure.layer_labels,
        seed=seed
    )
    
    # Generate connectivity with positions
    W = network.generate_connectivity(
        positions=layer_structure.cell_positions,
        distance_scale=0.1
    )
    
    # Create stability controller
    stability = SpectralStability(max_radius=0.95)
    
    # Enforce spectral stability
    W_stable, rho_orig, scale_factor = stability.enforce_stability(W)
    network.W = W_stable
    
    print(f"Network created: {network.n_neurons} neurons")
    print(f"Original spectral radius: ρ(W) = {rho_orig:.6f}")
    print(f"Scaled by factor: {scale_factor:.6f}")
    print(f"Final spectral radius: ρ(W) = {stability.compute_spectral_radius(W_stable):.6f}")
    
    return network, stability
