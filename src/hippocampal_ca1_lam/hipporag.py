"""
HippoRAG module: LLM memory integration for hippocampal-inspired retrieval

Implements memory encoding and retrieval interface inspired by hippocampal
pattern separation and completion mechanisms for LLM applications.
"""

import numpy as np
from typing import List, Dict, Any, Optional


class HippoRAGMemory:
    """
    Hippocampal-inspired Retrieval Augmented Generation (RAG) memory system.
    
    Implements pattern separation in encoding and pattern completion in retrieval,
    mimicking CA1 computational principles for LLM memory integration.
    
    Parameters
    ----------
    embedding_dim : int, default=512
        Dimension of memory embeddings
    sparsity : float, default=0.1
        Target sparsity for pattern separation
    n_layers : int, default=4
        Number of hierarchical memory layers (matching CA1 laminar structure)
    seed : int, default=42
        Random seed for reproducibility
    tol : float, default=1e-10
        Numerical tolerance
    """
    
    def __init__(self, embedding_dim=512, sparsity=0.1, n_layers=4, 
                 seed=42, tol=1e-10):
        self.embedding_dim = embedding_dim
        self.sparsity = sparsity
        self.n_layers = n_layers
        self.seed = seed
        self.tol = tol
        self.rng = np.random.RandomState(seed)
        
        # Memory storage
        self.memories = []  # List of memory embeddings
        self.metadata = []  # List of metadata dictionaries
        
        # Layer-specific memory representations
        self.layer_memories = [[] for _ in range(n_layers)]
        
        # Recurrent weight matrix for pattern completion (CA3-like)
        self.W_recurrent = None
        
    def _pattern_separate(self, embedding):
        """
        Apply pattern separation (dentate gyrus-like processing).
        
        Parameters
        ----------
        embedding : ndarray, shape (embedding_dim,)
            Input embedding vector
            
        Returns
        -------
        separated : ndarray, shape (embedding_dim,)
            Pattern-separated sparse representation
        """
        # Winner-take-all sparsification
        k = int(self.embedding_dim * self.sparsity)
        
        # Add noise for variability
        noisy = embedding + self.rng.normal(0, 0.01, size=embedding.shape)
        
        # Keep only top-k values
        threshold = np.partition(noisy, -k)[-k]
        separated = np.where(noisy >= threshold, noisy, 0)
        
        # Normalize
        norm = np.linalg.norm(separated)
        if norm > self.tol:
            separated = separated / norm
        
        return separated
    
    def _pattern_complete(self, query, n_iterations=5):
        """
        Apply pattern completion (CA3-like recurrent processing).
        
        Parameters
        ----------
        query : ndarray, shape (embedding_dim,)
            Query embedding (possibly partial)
        n_iterations : int, default=5
            Number of recurrent iterations
            
        Returns
        -------
        completed : ndarray, shape (embedding_dim,)
            Pattern-completed representation
        """
        completed = query.copy()
        
        if self.W_recurrent is not None:
            for _ in range(n_iterations):
                # Recurrent update
                activation = self.W_recurrent @ completed
                
                # Non-linearity (threshold linear)
                completed = np.maximum(0, activation)
                
                # Normalize
                norm = np.linalg.norm(completed)
                if norm > self.tol:
                    completed = completed / norm
        
        return completed
    
    def _distribute_to_layers(self, embedding):
        """
        Distribute embedding across CA1-like layers.
        
        Parameters
        ----------
        embedding : ndarray, shape (embedding_dim,)
            Memory embedding
            
        Returns
        -------
        layer_reps : list of ndarray
            Layer-specific representations
        """
        layer_reps = []
        
        # Each layer gets a different projection/view
        chunk_size = self.embedding_dim // self.n_layers
        
        for i in range(self.n_layers):
            start = i * chunk_size
            end = start + chunk_size if i < self.n_layers - 1 else self.embedding_dim
            
            # Layer-specific representation with some overlap
            layer_rep = embedding.copy()
            
            # Emphasize layer-specific region
            mask = np.zeros(self.embedding_dim)
            mask[start:end] = 1.0
            
            # Add partial overlap with neighboring layers
            if i > 0:
                prev_start = (i - 1) * chunk_size
                mask[prev_start:start] = 0.5
            if i < self.n_layers - 1:
                next_end = min((i + 2) * chunk_size, self.embedding_dim)
                mask[end:next_end] = 0.5
            
            layer_rep = layer_rep * mask
            
            # Normalize
            norm = np.linalg.norm(layer_rep)
            if norm > self.tol:
                layer_rep = layer_rep / norm
            
            layer_reps.append(layer_rep)
        
        return layer_reps
    
    def encode(self, embedding, metadata=None):
        """
        Encode a memory with pattern separation.
        
        Parameters
        ----------
        embedding : array-like, shape (embedding_dim,)
            Input embedding to store
        metadata : dict, optional
            Associated metadata (text, timestamp, etc.)
            
        Returns
        -------
        memory_id : int
            Index of stored memory
        """
        embedding = np.asarray(embedding)
        
        if embedding.shape[0] != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, "
                           f"got {embedding.shape[0]}")
        
        # Apply pattern separation
        separated = self._pattern_separate(embedding)
        
        # Distribute to layers
        layer_reps = self._distribute_to_layers(separated)
        
        # Store memory
        memory_id = len(self.memories)
        self.memories.append(separated)
        self.metadata.append(metadata if metadata is not None else {})
        
        # Store layer-specific representations
        for i, layer_rep in enumerate(layer_reps):
            self.layer_memories[i].append(layer_rep)
        
        # Update recurrent weights (Hebbian-like)
        self._update_recurrent_weights()
        
        return memory_id
    
    def _update_recurrent_weights(self):
        """Update recurrent weight matrix based on stored memories."""
        if len(self.memories) == 0:
            return
        
        # Initialize or update recurrent matrix
        if self.W_recurrent is None:
            self.W_recurrent = np.zeros((self.embedding_dim, self.embedding_dim))
        
        # Simple Hebbian rule: W += η * m * m^T
        # Use most recent memory
        memory = self.memories[-1]
        eta = 0.01 / len(self.memories)  # Decay learning rate
        
        self.W_recurrent += eta * np.outer(memory, memory)
        
        # Normalize to prevent explosion
        norm = np.linalg.norm(self.W_recurrent, ord='fro')
        if norm > self.tol:
            self.W_recurrent = self.W_recurrent / norm
    
    def retrieve(self, query_embedding, top_k=5, layer_weights=None):
        """
        Retrieve most similar memories with pattern completion.
        
        Parameters
        ----------
        query_embedding : array-like, shape (embedding_dim,)
            Query embedding
        top_k : int, default=5
            Number of top matches to return
        layer_weights : array-like, optional
            Weights for each layer in retrieval
            
        Returns
        -------
        results : list of dict
            Retrieved memories with similarity scores and metadata
        """
        query_embedding = np.asarray(query_embedding)
        
        if len(self.memories) == 0:
            return []
        
        # Apply pattern completion
        completed_query = self._pattern_complete(query_embedding)
        
        # Distribute query to layers
        query_layer_reps = self._distribute_to_layers(completed_query)
        
        # Default layer weights
        if layer_weights is None:
            layer_weights = np.ones(self.n_layers) / self.n_layers
        else:
            layer_weights = np.asarray(layer_weights)
            layer_weights = layer_weights / np.sum(layer_weights)
        
        # Compute similarities across layers
        n_memories = len(self.memories)
        total_similarities = np.zeros(n_memories)
        
        for layer_idx in range(self.n_layers):
            if len(self.layer_memories[layer_idx]) == 0:
                continue
                
            query_layer = query_layer_reps[layer_idx]
            
            # Compute cosine similarities for this layer
            layer_sims = []
            for memory_layer in self.layer_memories[layer_idx]:
                dot_prod = np.dot(query_layer, memory_layer)
                similarity = np.clip(dot_prod, -1.0, 1.0)
                layer_sims.append(similarity)
            
            # Weight by layer
            total_similarities += layer_weights[layer_idx] * np.array(layer_sims)
        
        # Get top-k most similar
        top_k = min(top_k, n_memories)
        top_indices = np.argpartition(total_similarities, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(-total_similarities[top_indices])]
        
        # Prepare results
        results = []
        for idx in top_indices:
            results.append({
                'memory_id': int(idx),
                'similarity': float(total_similarities[idx]),
                'embedding': self.memories[idx],
                'metadata': self.metadata[idx]
            })
        
        return results
    
    def get_memory_stats(self):
        """
        Get statistics about stored memories.
        
        Returns
        -------
        stats : dict
            Memory statistics
        """
        if len(self.memories) == 0:
            return {
                'n_memories': 0,
                'embedding_dim': self.embedding_dim,
                'n_layers': self.n_layers
            }
        
        memories_array = np.array(self.memories)
        
        stats = {
            'n_memories': len(self.memories),
            'embedding_dim': self.embedding_dim,
            'n_layers': self.n_layers,
            'mean_sparsity': np.mean(np.sum(memories_array != 0, axis=1) / self.embedding_dim),
            'memory_norm_mean': np.mean(np.linalg.norm(memories_array, axis=1)),
            'memory_norm_std': np.std(np.linalg.norm(memories_array, axis=1))
        }
        
        return stats
    
    def clear(self):
        """Clear all stored memories."""
        self.memories = []
        self.metadata = []
        self.layer_memories = [[] for _ in range(self.n_layers)]
        self.W_recurrent = None
