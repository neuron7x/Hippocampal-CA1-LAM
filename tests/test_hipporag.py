"""
Tests for HippoRAG module: LLM memory integration
"""

import numpy as np
import pytest
from hippocampal_ca1_lam.hipporag import HippoRAGMemory


class TestHippoRAGMemory:
    """Tests for hippocampal-inspired RAG memory."""
    
    def test_initialization(self):
        """Test HippoRAG memory initialization."""
        memory = HippoRAGMemory(
            embedding_dim=512, sparsity=0.1, n_layers=4, seed=42, tol=1e-10
        )
        
        assert memory.embedding_dim == 512
        assert memory.sparsity == 0.1
        assert memory.n_layers == 4
        assert memory.seed == 42
        assert memory.tol == 1e-10
        assert len(memory.memories) == 0
    
    def test_encode_memory(self):
        """Test memory encoding with pattern separation."""
        memory = HippoRAGMemory(embedding_dim=128, seed=42, tol=1e-10)
        
        # Create test embedding
        embedding = np.random.rand(128)
        metadata = {'text': 'test memory', 'timestamp': 0}
        
        memory_id = memory.encode(embedding, metadata)
        
        assert memory_id == 0
        assert len(memory.memories) == 1
        assert len(memory.metadata) == 1
    
    def test_pattern_separation_sparsity(self):
        """Test pattern separation produces sparse representations."""
        memory = HippoRAGMemory(embedding_dim=128, sparsity=0.1, seed=42)
        
        # Encode a memory
        embedding = np.random.rand(128)
        memory.encode(embedding)
        
        # Check sparsity of stored memory
        stored = memory.memories[0]
        n_nonzero = np.count_nonzero(stored)
        sparsity_actual = n_nonzero / len(stored)
        
        # Should be approximately the target sparsity
        assert sparsity_actual <= 0.15  # Allow some tolerance
    
    def test_retrieve_memory(self):
        """Test memory retrieval with pattern completion."""
        memory = HippoRAGMemory(embedding_dim=128, seed=42, tol=1e-10)
        
        # Encode some memories
        for i in range(5):
            embedding = np.random.rand(128)
            metadata = {'id': i}
            memory.encode(embedding, metadata)
        
        # Retrieve with query
        query = np.random.rand(128)
        results = memory.retrieve(query, top_k=3)
        
        assert len(results) == 3
        assert all('memory_id' in r for r in results)
        assert all('similarity' in r for r in results)
        assert all('metadata' in r for r in results)
    
    def test_retrieve_similarity_ordering(self):
        """Test retrieved memories are ordered by similarity."""
        memory = HippoRAGMemory(embedding_dim=128, seed=42)
        
        # Encode memories
        for i in range(10):
            embedding = np.random.rand(128)
            memory.encode(embedding)
        
        # Retrieve
        query = np.random.rand(128)
        results = memory.retrieve(query, top_k=5)
        
        # Check ordering: similarities should be decreasing
        similarities = [r['similarity'] for r in results]
        assert all(similarities[i] >= similarities[i+1] 
                  for i in range(len(similarities)-1))
    
    def test_layer_distribution(self):
        """Test embedding distribution across 4 layers."""
        memory = HippoRAGMemory(embedding_dim=128, n_layers=4, seed=42)
        
        # Encode a memory
        embedding = np.random.rand(128)
        memory.encode(embedding)
        
        # Check all layers have representations
        assert len(memory.layer_memories) == 4
        for layer in memory.layer_memories:
            assert len(layer) == 1
    
    def test_empty_retrieval(self):
        """Test retrieval on empty memory returns empty list."""
        memory = HippoRAGMemory(embedding_dim=128, seed=42)
        
        query = np.random.rand(128)
        results = memory.retrieve(query)
        
        assert len(results) == 0
    
    def test_clear_memory(self):
        """Test clearing all memories."""
        memory = HippoRAGMemory(embedding_dim=128, seed=42)
        
        # Add memories
        for i in range(5):
            memory.encode(np.random.rand(128))
        
        assert len(memory.memories) > 0
        
        # Clear
        memory.clear()
        
        assert len(memory.memories) == 0
        assert len(memory.metadata) == 0
        assert all(len(layer) == 0 for layer in memory.layer_memories)
        assert memory.W_recurrent is None
    
    def test_get_memory_stats(self):
        """Test memory statistics."""
        memory = HippoRAGMemory(embedding_dim=128, seed=42, tol=1e-10)
        
        # Empty stats
        stats = memory.get_memory_stats()
        assert stats['n_memories'] == 0
        
        # Add memories
        for i in range(10):
            memory.encode(np.random.rand(128))
        
        stats = memory.get_memory_stats()
        assert stats['n_memories'] == 10
        assert stats['embedding_dim'] == 128
        assert stats['n_layers'] == 4
        assert 'mean_sparsity' in stats
    
    def test_recurrent_weights_update(self):
        """Test recurrent weight matrix updates with memories."""
        memory = HippoRAGMemory(embedding_dim=64, seed=42)
        
        # Initially no recurrent weights
        assert memory.W_recurrent is None
        
        # Encode first memory
        memory.encode(np.random.rand(64))
        
        # Should have recurrent weights now
        assert memory.W_recurrent is not None
        assert memory.W_recurrent.shape == (64, 64)
    
    def test_reproducibility(self):
        """Test reproducibility with same seed."""
        # First instance
        m1 = HippoRAGMemory(embedding_dim=64, seed=42, tol=1e-10)
        embedding = np.random.RandomState(123).rand(64)
        m1.encode(embedding.copy())
        
        query = np.random.RandomState(456).rand(64)
        r1 = m1.retrieve(query.copy(), top_k=1)
        
        # Second instance
        m2 = HippoRAGMemory(embedding_dim=64, seed=42, tol=1e-10)
        m2.encode(embedding.copy())
        r2 = m2.retrieve(query.copy(), top_k=1)
        
        # Results should be identical
        assert len(r1) == len(r2)
        if len(r1) > 0:
            assert np.abs(r1[0]['similarity'] - r2[0]['similarity']) < 1e-10
    
    def test_dimension_mismatch_error(self):
        """Test error on embedding dimension mismatch."""
        memory = HippoRAGMemory(embedding_dim=128, seed=42)
        
        # Wrong dimension
        wrong_embedding = np.random.rand(64)
        
        with pytest.raises(ValueError):
            memory.encode(wrong_embedding)
    
    def test_tolerance_parameter(self):
        """Test numerical tolerance parameter (tol < 1e-10 or equal)."""
        memory = HippoRAGMemory(embedding_dim=128, seed=42, tol=1e-10)
        
        assert memory.tol <= 1e-10
        assert memory.tol == 1e-10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
