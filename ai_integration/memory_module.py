"""
AI Integration: CA1 Memory Module for LLMs
Inspired by: Gutiérrez et al., HippoRAG, arXiv:2405.14831

Architecture:
1. Event encoding: LLM hidden state → CA1 keys
2. Phase-tagged storage: (event, theta_phase) → memory slot
3. Retrieval: query → top-k similar events
4. Fusion: LLM state + retrieved memory → enhanced output

Mechanisms:
- Online learning (low η, reading mode)
- Offline replay (high η, consolidation)
- OLM gating (controls learning vs retrieval)
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass
class MemoryEntry:
    """Single memory entry"""

    key: np.ndarray  # [key_dim] normalized key
    value: np.ndarray  # [value_dim] content
    theta_phase: float  # Phase at encoding [0, 2π]
    timestamp: float  # Time of encoding
    novelty: float  # Novelty at encoding [0, 1]
    access_count: int = 0  # Number of retrievals
    source_h: Optional[np.ndarray] = None  # Hidden state used to encode the key


class CA1MemoryModule:
    """
    CA1-inspired memory for LLMs

    Features:
    - Phase-coded keys (theta rhythm)
    - Plastic storage (Ca²⁺-based updates)
    - Replay-based consolidation
    - Homeostatic capacity control
    """

    def __init__(self, params, rng: Optional[np.random.Generator] = None):
        """
        Args:
            params: AIIntegrationParams from biophysical_parameters
            rng: Optional numpy random generator for reproducibility.
                 If None, uses np.random.default_rng() for deterministic seeding.
        """
        self.p = params

        # Initialize RNG for reproducibility
        if rng is None:
            self._rng = np.random.default_rng()
        else:
            self._rng = rng

        # Memory slots
        self.memory: List[Optional[MemoryEntry]] = [None] * self.p.memory_size
        self.n_stored = 0

        # Encoder/decoder (simple linear for now, can be neural)
        self.W_encoder = self._init_encoder()
        self.W_decoder = self._init_decoder()

        # Current theta phase
        self.theta_phase = 0.0
        self.theta_freq = 8.0  # Hz
        self.dt = 0.001  # s (1 ms)

        # Learning state
        self.learning_mode = "online"  # "online" or "offline"
        self.eta = self.p.eta_online

    def _init_encoder(self) -> np.ndarray:
        """Initialize encoder: LLM hidden → CA1 key"""
        # Random projection using injectable RNG
        W = self._rng.standard_normal((self.p.key_dim, self.p.d_model)) / np.sqrt(self.p.d_model)
        return W

    def _init_decoder(self) -> np.ndarray:
        """Initialize decoder: retrieved value → LLM dim"""
        W = self._rng.standard_normal((self.p.d_model, self.p.value_dim)) / np.sqrt(
            self.p.value_dim
        )
        return W

    def encode_event(self, h_t: np.ndarray, include_phase: bool = True) -> np.ndarray:
        """
        Encode LLM hidden state to CA1 key

        Args:
            h_t: [d_model] LLM hidden state
            include_phase: Include theta phase in key

        Returns:
            key: [key_dim] normalized key
        """
        theta_phase = self.theta_phase if include_phase else None
        return self._encode_at_phase(h_t, theta_phase)

    def _encode_at_phase(self, h_t: np.ndarray, theta_phase: Optional[float]) -> np.ndarray:
        key = self.W_encoder @ h_t

        if theta_phase is not None and self.p.use_phase_key:
            key[-2] = np.cos(theta_phase)
            key[-1] = np.sin(theta_phase)

        # Normalize
        key = key / (np.linalg.norm(key) + 1e-8)

        return key

    def store(
        self, h_t: np.ndarray, v_t: np.ndarray, novelty: float = 1.0
    ) -> Union[int, np.signedinteger]:
        """
        Store event in memory

        Args:
            h_t: [d_model] LLM hidden state (for key)
            v_t: [value_dim] Value to store
            novelty: Novelty signal [0, 1]

        Returns:
            slot_id: Index where stored
        """
        # Encode key
        key = self.encode_event(h_t)

        # Create entry
        entry = MemoryEntry(
            key=key,
            value=v_t.copy(),
            theta_phase=self.theta_phase,
            timestamp=0.0,  # Will be set externally
            novelty=novelty,
            source_h=h_t.copy(),
        )

        # Find slot
        slot_id: Union[int, np.signedinteger]
        if self.n_stored < self.p.memory_size:
            # Fill empty slot
            slot_id = self.n_stored
            self.n_stored += 1
        else:
            # Replace least accessed (simple eviction policy)
            access_counts = [m.access_count if m is not None else float("inf") for m in self.memory]
            slot_id = np.argmin(access_counts)

        self.memory[slot_id] = entry
        return slot_id

    def retrieve(
        self,
        q_t: np.ndarray,
        top_k: Optional[int] = None,
        *,
        theta_phase: Optional[float] = None,
    ) -> Tuple[np.ndarray, List[int]]:
        """
        Retrieve top-k similar memories

        Args:
            q_t: [d_model] Query (LLM hidden state)
            top_k: Number of memories to retrieve
            theta_phase: Optional query phase in radians. Omit for phase-blind retrieval.

        Returns:
            retrieved: [d_model] Fused retrieved content
            indices: List of retrieved memory indices
        """
        if top_k is None:
            top_k = self.p.top_k

        if theta_phase is not None and self.p.use_phase_key and not np.isfinite(theta_phase):
            raise ValueError("theta_phase must be finite")
        q_key = self._encode_at_phase(q_t, theta_phase)

        # Compute similarities
        similarity_scores = []
        populated_slots = []

        for i, entry in enumerate(self.memory):
            if entry is not None:
                sim = np.dot(q_key, entry.key)
                similarity_scores.append(sim)
                populated_slots.append(i)

        if not similarity_scores:
            # No memories
            return np.zeros(self.p.d_model), []

        similarities = np.array(similarity_scores)
        valid_indices = np.array(populated_slots)

        # Top-k
        k = min(top_k, len(similarities))
        top_idx = np.argsort(similarities)[-k:][::-1]

        # Softmax weights
        top_sims = similarities[top_idx]
        weights = self._softmax(top_sims / self.p.temperature)

        # Retrieve and fuse
        retrieved_values = []
        retrieved_indices = []

        for idx, w in zip(top_idx, weights):
            mem_idx = valid_indices[idx]
            entry = self.memory[mem_idx]
            retrieved_values.append(entry.value * w)
            retrieved_indices.append(mem_idx)

            # Update access count
            entry.access_count += 1

        # Sum weighted values
        fused_value = np.sum(retrieved_values, axis=0)

        # Decode to LLM dimension
        retrieved = self.W_decoder @ fused_value

        return retrieved, retrieved_indices

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Numerically stable softmax"""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def fuse_with_llm(self, h_t: np.ndarray, r_t: np.ndarray) -> np.ndarray:
        """
        Fuse LLM state with retrieved memory

        h̃_t = α·h_t + (1-α)·r_t

        Args:
            h_t: [d_model] Current LLM state
            r_t: [d_model] Retrieved memory

        Returns:
            h_tilde: [d_model] Fused state
        """
        alpha = self.p.alpha_fuse
        return alpha * h_t + (1 - alpha) * r_t

    def update_theta(self, dt: Optional[float] = None):
        """Update theta phase"""
        if dt is None:
            dt = self.dt

        # φ(t+dt) = φ(t) + 2π·f·dt
        self.theta_phase += 2 * np.pi * self.theta_freq * dt
        self.theta_phase = self.theta_phase % (2 * np.pi)

    def set_learning_mode(self, mode: str):
        """
        Set learning mode

        Args:
            mode: "online" (low η) or "offline" (high η for replay)
        """
        self.learning_mode = mode

        if mode == "online":
            self.eta = self.p.eta_online
        elif mode == "offline":
            self.eta = self.p.eta_offline

    def replay(self, n_episodes: int = 10, selection_mode: str = "novelty") -> List[int]:
        """
        Offline replay for consolidation

        Args:
            n_episodes: Number of episodes to replay
            selection_mode: "novelty", "random", "recent"

        Returns:
            replayed_indices: List of memory indices replayed

        Raises:
            ValueError: A stored key lacks a source state for re-encoding.
        """
        valid_entries = [(i, m) for i, m in enumerate(self.memory) if m is not None]

        if not valid_entries or n_episodes == 0:
            return []

        sources = []
        for index, entry in valid_entries:
            if entry.source_h is None:
                raise ValueError(f"cannot replay: stored key is missing source_h at slot {index}")
            sources.append((entry, entry.source_h))

        # Select episodes
        if selection_mode == "novelty":
            # Weight by novelty
            weights = np.array([m.novelty for _, m in valid_entries])
            weights /= weights.sum()
            selected_idx = self._rng.choice(
                len(valid_entries),
                size=min(n_episodes, len(valid_entries)),
                replace=False,
                p=weights,
            )
        elif selection_mode == "recent":
            # Most recent
            selected_idx = np.argsort([m.timestamp for _, m in valid_entries])[-n_episodes:]
        else:  # random
            selected_idx = self._rng.choice(
                len(valid_entries), size=min(n_episodes, len(valid_entries)), replace=False
            )

        replayed = [valid_entries[i] for i in selected_idx]
        if not replayed:
            return []

        # The encoder expects d_model coordinates. Decode values stored in a smaller space.
        for _, entry in replayed:
            update_vector = entry.value[: self.p.d_model]
            if update_vector.size < self.p.d_model:
                update_vector = self.W_decoder @ entry.value
            self.W_encoder += self.eta * np.outer(entry.key, update_vector)

        # Every stored key shares the final encoder, including entries not selected for replay.
        for entry, source_h in sources:
            entry.key = self._encode_at_phase(source_h, entry.theta_phase)

        return [index for index, _ in replayed]

    def save(self, filepath: str):
        """Save memory to disk"""
        data = {
            "n_stored": self.n_stored,
            "theta_phase": self.theta_phase,
            "W_encoder": self.W_encoder.tolist(),
            "W_decoder": self.W_decoder.tolist(),
            "memory": [],
        }

        for entry in self.memory:
            if entry is not None:
                data["memory"].append(
                    {
                        "key": entry.key.tolist(),
                        "value": entry.value.tolist(),
                        "theta_phase": entry.theta_phase,
                        "timestamp": entry.timestamp,
                        "novelty": entry.novelty,
                        "access_count": entry.access_count,
                        "source_h": entry.source_h.tolist()
                        if entry.source_h is not None
                        else None,
                    }
                )
            else:
                data["memory"].append(None)

        with open(filepath, "w") as f:
            json.dump(data, f)

    def load(self, filepath: str):
        """Load memory from disk"""
        with open(filepath, "r") as f:
            data = json.load(f)

        self.n_stored = data["n_stored"]
        self.theta_phase = data["theta_phase"]
        self.W_encoder = np.array(data["W_encoder"])
        self.W_decoder = np.array(data["W_decoder"])

        self.memory = []
        for entry_data in data["memory"]:
            if entry_data is not None:
                source_h = entry_data.get("source_h")
                entry = MemoryEntry(
                    key=np.array(entry_data["key"]),
                    value=np.array(entry_data["value"]),
                    theta_phase=entry_data["theta_phase"],
                    timestamp=entry_data["timestamp"],
                    novelty=entry_data["novelty"],
                    access_count=entry_data["access_count"],
                    source_h=np.array(source_h) if source_h is not None else None,
                )
                self.memory.append(entry)
            else:
                self.memory.append(None)


# ============================================================================
# LLM WRAPPER WITH CA1 MEMORY
# ============================================================================


class LLMWithCA1Memory:
    """
    Wrapper for LLM with CA1 memory integration

    Usage:
        model = LLMWithCA1Memory(params)

        # Encoding phase (online)
        for token in sequence:
            h_t = llm.forward(token)
            model.process_step(h_t, v_t)

        # Retrieval phase
        query_h = llm.forward(query)
        enhanced_h = model.retrieve_and_fuse(query_h)
        output = llm.decode(enhanced_h)

        # Consolidation (offline)
        model.consolidate()
    """

    def __init__(self, params, rng: Optional[np.random.Generator] = None):
        """
        Args:
            params: AIIntegrationParams
            rng: Optional numpy random generator for reproducibility
        """
        self.memory = CA1MemoryModule(params, rng=rng)
        self.position_history: List[np.ndarray] = []  # For novelty computation

    def process_step(self, h_t: np.ndarray, v_t: np.ndarray, position: Optional[np.ndarray] = None):
        """
        Process one step: encode and store if novel

        Args:
            h_t: [d_model] LLM hidden state
            v_t: [value_dim] Value to store
            position: Optional position for novelty (e.g., [x, y])
        """
        # Compute novelty
        if position is not None:
            from hippocampal_ca1_lam.plasticity.calcium_plasticity import (
                compute_place_field_novelty,
            )

            history = np.array(self.position_history) if self.position_history else np.array([])
            novelty = compute_place_field_novelty(position, history)
            self.position_history.append(position)
        else:
            novelty = 1.0  # Default high novelty

        # Store if novel enough
        if novelty > 0.3:  # Threshold
            self.memory.store(h_t, v_t, novelty)

        # Update theta
        self.memory.update_theta()

    def retrieve_and_fuse(self, query_h: np.ndarray) -> np.ndarray:
        """
        Retrieve memories and fuse with query

        Args:
            query_h: [d_model] Query state

        Returns:
            fused_h: [d_model] Enhanced state
        """
        retrieved, indices = self.memory.retrieve(query_h)
        fused = self.memory.fuse_with_llm(query_h, retrieved)

        return fused

    def consolidate(self, n_episodes: int = 50):
        """
        Offline consolidation via replay

        Args:
            n_episodes: Number of replay episodes
        """
        self.memory.set_learning_mode("offline")
        replayed = self.memory.replay(n_episodes, selection_mode="novelty")
        self.memory.set_learning_mode("online")

        return replayed


# ============================================================================
# METRICS & BENCHMARKING
# ============================================================================


def evaluate_retrieval_quality(
    memory: CA1MemoryModule, test_queries: List[np.ndarray], ground_truth: List[int]
) -> Dict[str, float]:
    """
    Evaluate retrieval quality

    Args:
        memory: CA1MemoryModule
        test_queries: List of query vectors
        ground_truth: List of correct memory indices

    Returns:
        metrics: {"precision@k", "recall@k", "ndcg@k"}
    """
    k = memory.p.top_k

    precisions = []
    recalls = []

    for query, gt in zip(test_queries, ground_truth):
        _, retrieved_indices = memory.retrieve(query, top_k=k)

        # Precision@k
        n_correct = sum(1 for idx in retrieved_indices if idx == gt)
        precision = n_correct / k
        precisions.append(precision)

        # Recall@k
        recall = 1.0 if gt in retrieved_indices else 0.0
        recalls.append(recall)

    return {
        "precision@k": np.mean(precisions),
        "recall@k": np.mean(recalls),
        "mean_retrieval_size": k,
    }


if __name__ == "__main__":
    from hippocampal_ca1_lam.data.biophysical_parameters import get_default_parameters

    params = get_default_parameters()

    # Test memory module
    print("Testing CA1 Memory Module...")
    memory = CA1MemoryModule(params.ai)

    # Store some events
    np.random.seed(42)
    n_events = 100

    for i in range(n_events):
        h_t = np.random.randn(params.ai.d_model)
        v_t = np.random.randn(params.ai.value_dim)
        novelty = np.random.rand()

        memory.store(h_t, v_t, novelty)
        memory.update_theta()

    print(f"Stored {memory.n_stored} events")

    # Retrieve
    query = np.random.randn(params.ai.d_model)
    retrieved, indices = memory.retrieve(query, top_k=5)

    print(f"Retrieved {len(indices)} memories")
    print(f"Indices: {indices}")

    # Replay
    print("\nTesting offline replay...")
    memory.set_learning_mode("offline")
    replayed = memory.replay(n_episodes=10, selection_mode="novelty")
    print(f"Replayed {len(replayed)} episodes")

    # Test full LLM wrapper
    print("\nTesting LLM wrapper...")
    model = LLMWithCA1Memory(params.ai)

    # Simulate sequence
    for i in range(50):
        h_t = np.random.randn(params.ai.d_model)
        v_t = np.random.randn(params.ai.value_dim)
        position = np.random.rand(2)

        model.process_step(h_t, v_t, position)

    # Query
    query_h = np.random.randn(params.ai.d_model)
    enhanced_h = model.retrieve_and_fuse(query_h)

    print(f"Query shape: {query_h.shape}")
    print(f"Enhanced shape: {enhanced_h.shape}")
    print(f"Fusion successful: {enhanced_h.shape == query_h.shape}")

    # Consolidate
    replayed = model.consolidate(n_episodes=20)
    print(f"Consolidation: replayed {len(replayed)} episodes")
