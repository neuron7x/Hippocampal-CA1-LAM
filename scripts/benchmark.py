#!/usr/bin/env python3
"""
Performance Benchmarking Script

Tests performance of key operations.
"""
import numpy as np
import time
from data.biophysical_parameters import get_default_parameters
from plasticity.unified_weights import UnifiedWeightMatrix, create_source_type_matrix
from core.hierarchical_laminar import HierarchicalLaminarModel, CellDataHier

def benchmark_weight_update():
    """Benchmark weight matrix operations"""
    np.random.seed(42)
    params = get_default_parameters()
    
    N = 100
    connectivity = np.random.rand(N, N) < 0.1
    np.fill_diagonal(connectivity, False)
    
    layer_assignments = np.random.randint(0, 4, N)
    initial_weights = np.random.lognormal(0, 0.5, (N, N))
    initial_weights = np.clip(initial_weights, 0.01, 10.0)
    source_types = create_source_type_matrix(N, layer_assignments)
    
    W = UnifiedWeightMatrix(connectivity, initial_weights, source_types, params)
    
    # Benchmark
    n_iter = 1000
    start = time.time()
    
    for _ in range(n_iter):
        spikes_pre = np.random.rand(N) < 0.01
        spikes_post = np.random.rand(N) < 0.01
        V_dend = np.random.randn(N) * 10 - 60
        W.update_stp(spikes_pre, spikes_post)
        W.update_calcium(spikes_pre, spikes_post, V_dend)
        if _ % 10 == 0:
            W.update_plasticity_ca_based(M=1.0, G=np.zeros(N))
    
    elapsed = time.time() - start
    return elapsed, n_iter

def benchmark_laminar_em():
    """Benchmark laminar EM"""
    np.random.seed(42)
    
    N = 1000
    cells = []
    for i in range(N):
        z = np.random.rand()
        layer = min(int(z * 4), 3)
        transcripts = np.zeros(4)
        transcripts[layer] = np.random.poisson(5)
        cells.append(CellDataHier(
            cell_id=i, animal_id=0,
            x=np.random.rand(), y=np.random.rand(),
            z=z, s=np.random.rand(),
            transcripts=transcripts
        ))
    
    model = HierarchicalLaminarModel(lambda_mrf=0.0)
    
    start = time.time()
    q = model.fit_em_vectorized(cells, max_iter=10, verbose=False)
    elapsed = time.time() - start
    
    return elapsed, N

if __name__ == "__main__":
    print("="*70)
    print("PERFORMANCE BENCHMARKS")
    print("="*70)
    
    # Weight updates
    print("\n1. Weight Matrix Operations (100 neurons)...")
    elapsed, n_iter = benchmark_weight_update()
    print(f"   {n_iter} iterations in {elapsed:.2f}s")
    print(f"   {elapsed/n_iter*1000:.2f} ms/iteration")
    
    # Laminar EM
    print("\n2. Laminar EM (1000 cells, 10 iterations)...")
    elapsed, N = benchmark_laminar_em()
    print(f"   {N} cells in {elapsed:.2f}s")
    
    print("\n✅ Benchmarks complete!")
    print("\nReference (Intel i7, 16GB RAM):")
    print("  Weight updates: ~10 ms/iteration")
    print("  Laminar EM: ~2.0s")
