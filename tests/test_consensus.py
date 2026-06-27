import numpy as np
from erisml.ethics.governance.consensus import consensus_diagnostics


def test_unimodal_is_consensus():
    rng = np.random.default_rng(0)
    x = rng.normal(0.7, 0.05, 40)
    d = consensus_diagnostics(x)
    assert d["schism"] is False and d["basis"] == "bic"


def test_bimodal_is_schism():
    rng = np.random.default_rng(1)
    x = np.concatenate([rng.normal(0.1, 0.03, 20), rng.normal(0.9, 0.03, 20)])
    d = consensus_diagnostics(x)
    assert d["schism"] is True and d["bimodality_bic"] > 10


def test_vector_bimodal_is_schism():
    rng = np.random.default_rng(2)
    a = rng.normal([0, 0, 0, 0, 0, 0, 0, 0, 0], 0.05, (20, 9))
    b = rng.normal([1, 1, 0, 0, 0, 0, 0, 0, 0], 0.05, (20, 9))
    d = consensus_diagnostics(np.vstack([a, b]))
    assert d["schism"] is True


def test_small_n_degrades_gracefully():
    d = consensus_diagnostics([0.6, 0.62, 0.58])  # n<4
    assert d["basis"] == "insufficient" and d["schism"] is False
    assert d["dispersion"] >= 0.0


def test_weights_accepted():
    d = consensus_diagnostics([0.1, 0.9, 0.5], weights=[2, 1, 1])
    assert "dispersion" in d and d["n"] == 3
