import matplotlib
import numpy as np
import pytest

from core import CA1Network


def test_ca1network_public_api_shapes_and_keys():
    net = CA1Network(N=5, seed=42, dt=0.5)
    result = net.simulate(duration_ms=5, dt=1.0)

    assert set(result.keys()) == {"time", "spikes", "voltages", "weights"}

    time = result["time"]
    spikes = result["spikes"]
    voltages = result["voltages"]
    weights = result["weights"]

    assert time.ndim == 1 and time.size > 0
    assert spikes.shape == (time.size, 5)
    assert voltages.shape == (time.size, 5)
    assert weights.shape == (5, 5)
    assert np.all(weights.diagonal() == 0.0)


def test_ca1network_reproducibility_with_seed():
    net_a = CA1Network(N=3, seed=42, dt=0.5)
    net_b = CA1Network(N=3, seed=42, dt=0.5)

    res_a = net_a.simulate(duration_ms=10)
    res_b = net_b.simulate(duration_ms=10)

    assert np.array_equal(res_a["spikes"], res_b["spikes"])
    assert np.allclose(res_a["voltages"], res_b["voltages"])
    assert np.allclose(res_a["weights"], res_b["weights"])


@pytest.mark.parametrize("duration_ms", [0, 100])
def test_ca1network_raster_preserves_each_neuron_and_its_spike_times(duration_ms):
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    net = CA1Network(N=5, seed=42)
    result = net.simulate(duration_ms=duration_ms)
    spike_rows, neuron_ids = np.nonzero(result["spikes"])
    if duration_ms:
        assert len(set(neuron_ids)) > 1

    figure = plt.figure()
    try:
        assert net.plot_activity() is plt
        collections = figure.axes[0].collections
        assert len(collections) == 5
        for neuron_id, collection in enumerate(collections):
            assert collection.get_lineoffset() == neuron_id
            rows = spike_rows[neuron_ids == neuron_id]
            np.testing.assert_array_equal(collection.get_positions(), result["time"][rows])
    finally:
        plt.close(figure)
