import json

import numpy as np
import pytest

from ai_integration.memory_module import CA1MemoryModule
from data.biophysical_parameters import AIIntegrationParams


def test_memory_store_and_retrieve_topk_deterministic():
    np.random.seed(0)
    params = AIIntegrationParams(
        d_model=4,
        d_CA1=4,
        memory_size=4,
        key_dim=4,
        value_dim=4,
        top_k=2,
        use_phase_key=False,
        temperature=0.1,
    )
    memory = CA1MemoryModule(params)
    # Make encoding/decoding deterministic and identity-like
    memory.W_encoder = np.eye(params.key_dim, params.d_model)
    memory.W_decoder = np.eye(params.d_model, params.value_dim)

    vectors = [
        np.array([1.0, 0.0, 0.0, 0.0]),
        np.array([0.9, 0.1, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0, 0.0]),
    ]
    for v in vectors:
        memory.store(h_t=v, v_t=v, novelty=1.0)

    query = np.array([1.0, 0.0, 0.0, 0.0])
    retrieved, indices = memory.retrieve(query, top_k=2)

    assert indices == [0, 1]
    assert retrieved.shape == (params.d_model,)
    # Highest weight on the first vector
    assert np.isclose(retrieved[0], retrieved.max())


@pytest.mark.parametrize("use_phase_key", [False, True])
def test_explicit_phase_matches_duplicate_cues_without_changing_default(use_phase_key):
    params = AIIntegrationParams(
        d_model=4, key_dim=4, value_dim=4, memory_size=2, use_phase_key=use_phase_key
    )
    memory = CA1MemoryModule(params, rng=np.random.default_rng(5))
    cue = np.array([1., 0., 0., 0.])
    memory.W_encoder = np.eye(4)
    memory.store(cue, np.array([1., 0., 0., 0.]))
    memory.theta_phase = np.pi
    memory.store(cue, np.array([0., 1., 0., 0.]))
    phase_blind = memory.retrieve(cue, top_k=1)[1]
    phase_zero = memory.retrieve(cue, top_k=1, theta_phase=0.0)[1]
    phase_pi = memory.retrieve(cue, top_k=1, theta_phase=np.pi)[1]
    assert memory.theta_phase == np.pi
    if use_phase_key:
        assert phase_zero == [0]
        assert phase_pi == [1]
    else:
        assert phase_zero == phase_pi == phase_blind

    memory.theta_phase = 0.0
    assert memory.retrieve(cue, top_k=1)[1] == phase_blind


def test_explicit_nonfinite_phase_cannot_rank_memories():
    params = AIIntegrationParams(d_model=4, key_dim=4, value_dim=4, memory_size=2)
    memory = CA1MemoryModule(params, rng=np.random.default_rng(5))
    cue = np.ones(4)
    memory.store(cue, cue)
    with pytest.raises(ValueError, match="theta_phase must be finite"):
        memory.retrieve(cue, theta_phase=np.nan)


def test_replay_refreshes_selected_and_unselected_keys_after_loading(tmp_path):
    params = AIIntegrationParams(
        d_model=4, key_dim=4, value_dim=2, memory_size=4, eta_offline=0.5
    )
    memory = CA1MemoryModule(params, rng=np.random.default_rng(42))
    cues = [np.array([1., 1., 0., 0.]), np.array([0., 1., 1., 0.]), np.ones(4)]
    for cue, phase in zip(cues, [0.25, 1.0, 2.75]):
        memory.theta_phase = phase
        memory.store(cue.copy(), np.array([1., 2.]))
    memory.theta_phase = 0.5
    snapshot = tmp_path / "memory.json"
    memory.save(str(snapshot))

    restored = CA1MemoryModule(params, rng=np.random.default_rng(1))
    restored.load(str(snapshot))
    restored.set_learning_mode("offline")
    populated = [entry for entry in restored.memory if entry is not None]
    old_keys = [entry.key.copy() for entry in populated]
    encoder_before = restored.W_encoder.copy()
    replayed = restored.replay(n_episodes=2, selection_mode="recent")
    assert len(replayed) == 2
    assert not np.allclose(restored.W_encoder, encoder_before)
    assert restored.theta_phase == 0.5
    for index, (entry, cue, old_key) in enumerate(zip(populated, cues, old_keys)):
        restored.theta_phase = entry.theta_phase
        np.testing.assert_allclose(entry.key, restored.encode_event(cue))
        if index not in replayed:
            assert not np.allclose(entry.key, old_key)


def test_legacy_snapshot_stays_retrievable_and_blocks_replay_without_mutation(tmp_path):
    params = AIIntegrationParams(d_model=4, key_dim=4, value_dim=4, memory_size=2)
    memory = CA1MemoryModule(params, rng=np.random.default_rng(42))
    cue = np.array([1., 1., 0., 0.])
    memory.store(cue, cue)
    memory.theta_phase = np.pi
    memory.store(cue, cue)
    snapshot = tmp_path / "memory.json"
    memory.save(str(snapshot))
    data = json.loads(snapshot.read_text())
    data["memory"][0].pop("source_h", None)
    snapshot.write_text(json.dumps(data))

    restored = CA1MemoryModule(params, rng=np.random.default_rng(42))
    restored.load(str(snapshot))
    assert restored.retrieve(cue, top_k=1, theta_phase=0.0)[1] == [0]
    populated = [entry for entry in restored.memory if entry is not None]
    populated[1].timestamp = 1.0
    old_keys = [entry.key.copy() for entry in populated]
    old_encoder = restored.W_encoder.copy()
    old_phase = restored.theta_phase

    assert restored.replay(n_episodes=0, selection_mode="recent") == []
    with pytest.raises(ValueError, match="cannot replay: stored key is missing source_h"):
        restored.replay(n_episodes=1, selection_mode="recent")
    np.testing.assert_array_equal(restored.W_encoder, old_encoder)
    for entry, old_key in zip(populated, old_keys):
        np.testing.assert_array_equal(entry.key, old_key)
    assert restored.theta_phase == old_phase
