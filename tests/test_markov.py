"""Tests for the analytical Markov chain solution."""

import numpy as np
import pytest
from matchprob.state import MatchState
from matchprob.markov import win_probability, build_transition_system, win_probability_grid
from matchprob.montecarlo import simulate_match


class TestWinProbability:
    """Test exact win probability calculations."""

    def test_fair_match_is_half(self):
        p = win_probability(p_serve=0.5, best_of=2)
        assert abs(p - 0.5) < 1e-10

    def test_terminal_p1_wins(self):
        state = MatchState(p1_sets=2, best_of=2)
        p = win_probability(start_state=state, best_of=2)
        assert p == 1.0

    def test_terminal_p2_wins(self):
        state = MatchState(p2_sets=2, best_of=2)
        p = win_probability(start_state=state, best_of=2)
        assert p == 0.0

    def test_strong_server_p1_advantage(self):
        # p_serve=0.7 means whoever serves wins 70% of points
        # P1 serves first, but serve alternates, so advantage is marginal
        p = win_probability(p_serve=0.7, best_of=2)
        assert p > 0.5  # slight edge from serving first

    def test_weak_server_p1_disadvantage(self):
        p = win_probability(p_serve=0.3, best_of=2)
        assert p < 0.5

    def test_probabilities_sum_to_one(self):
        """All transient states should have probabilities in [0, 1]."""
        states, probs = build_transition_system(p_serve=0.65, best_of=2)
        assert all(0.0 - 1e-10 <= p <= 1.0 + 1e-10 for p in probs)

    def test_monotonicity_in_sets(self):
        """Being ahead in sets should give higher win probability."""
        p_ahead = win_probability(
            p_serve=0.6,
            start_state=MatchState(p1_sets=1, p2_sets=0, best_of=2),
            best_of=2,
        )
        p_behind = win_probability(
            p_serve=0.6,
            start_state=MatchState(p1_sets=0, p2_sets=1, best_of=2),
            best_of=2,
        )
        assert p_ahead > p_behind

    def test_symmetry_at_equal_score(self):
        """At 0-0 with p=0.5, win prob should be 0.5."""
        p = win_probability(p_serve=0.5, best_of=2)
        assert abs(p - 0.5) < 1e-10


class TestMCvsAnalytical:
    """Compare Monte Carlo estimates with exact analytical results."""

    @pytest.mark.parametrize("p_serve", [0.5, 0.6, 0.7])
    def test_mc_agrees_with_analytical(self, p_serve):
        exact = win_probability(p_serve=p_serve, best_of=2)
        mc = simulate_match(
            p_serve=p_serve, n_sims=50_000,
            rng=np.random.default_rng(42),
        )
        # MC should be within ~2% of exact
        assert abs(mc["p1_win_prob"] - exact) < 0.02, (
            f"MC={mc['p1_win_prob']:.4f} vs exact={exact:.4f} at p_serve={p_serve}"
        )

    def test_mc_agrees_asymmetric(self):
        exact = win_probability(p_serve=0.65, p_return=0.55, best_of=2)
        mc = simulate_match(
            p_serve=0.65, p_return=0.55, n_sims=50_000,
            rng=np.random.default_rng(42),
        )
        assert abs(mc["p1_win_prob"] - exact) < 0.02


class TestWinProbabilityGrid:
    """Test the grid of win probabilities across game scores."""

    def test_grid_has_entries(self):
        grid = win_probability_grid(p_serve=0.6, best_of=2)
        assert len(grid) > 0
        assert (0, 0) in grid

    def test_grid_values_in_range(self):
        grid = win_probability_grid(p_serve=0.6, best_of=2)
        for key, val in grid.items():
            assert 0.0 <= val <= 1.0, f"Out of range at {key}: {val}"

    def test_grid_monotonicity(self):
        """Being ahead in games should generally give higher win prob."""
        grid = win_probability_grid(p_serve=0.6, best_of=2)
        if (5, 0) in grid and (0, 5) in grid:
            assert grid[(5, 0)] > grid[(0, 5)]
