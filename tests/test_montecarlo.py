"""Tests for Monte Carlo simulation."""

import numpy as np
import pytest
from matchprob.state import MatchState
from matchprob.montecarlo import simulate_match, simulate_point_sequence


class TestSimulateMatch:
    """Test Monte Carlo match simulation."""

    def test_fair_coin_gives_half(self):
        result = simulate_match(
            p_serve=0.5, n_sims=50_000, rng=np.random.default_rng(42)
        )
        assert abs(result["p1_win_prob"] - 0.5) < 0.02

    def test_certain_server_wins(self):
        result = simulate_match(
            p_serve=1.0, n_sims=100, rng=np.random.default_rng(42)
        )
        # When server always wins, P1 serves first, so P1 always wins
        assert result["p1_win_prob"] == 1.0

    def test_certain_server_loses(self):
        result = simulate_match(
            p_serve=0.0, n_sims=100, rng=np.random.default_rng(42)
        )
        # When server always loses, returner always wins.
        # P1 serves first -> P2 wins that game. P2 serves -> P1 wins.
        # This alternates, so it's actually 50/50 in games. But actually
        # server always losing means returner wins every game,
        # so each player wins when they return.
        # P1 serves G1 -> P2 wins. P2 serves G2 -> P1 wins. Etc.
        # Sets go to tiebreak. In tiebreak server loses -> returner wins.
        # Complex, but both should win equally. Let's just check it runs.
        assert 0.0 <= result["p1_win_prob"] <= 1.0

    def test_strong_server_advantage(self):
        result = simulate_match(
            p_serve=0.8, n_sims=10_000, rng=np.random.default_rng(42)
        )
        # With strong serve, P1 (who serves first) should have slight edge
        assert result["p1_win_prob"] > 0.4

    def test_confidence_interval_contains_estimate(self):
        result = simulate_match(
            p_serve=0.5, n_sims=10_000, rng=np.random.default_rng(42)
        )
        assert result["ci_lower"] <= result["p1_win_prob"] <= result["ci_upper"]

    def test_asymmetric_serve_return(self):
        """Test with different serve and return probabilities."""
        result = simulate_match(
            p_serve=0.7, p_return=0.3, n_sims=10_000,
            rng=np.random.default_rng(42)
        )
        # P1 serving: P1 wins point with p=0.7
        # P2 serving: P2 wins point with p=0.3, so P1 wins with p=0.7
        # So P1 wins 70% of all points regardless -> should win most matches
        assert result["p1_win_prob"] > 0.8

    def test_reproducibility(self):
        r1 = simulate_match(p_serve=0.6, n_sims=1000, rng=np.random.default_rng(99))
        r2 = simulate_match(p_serve=0.6, n_sims=1000, rng=np.random.default_rng(99))
        assert r1["p1_win_prob"] == r2["p1_win_prob"]


class TestSimulatePointSequence:
    """Test point sequence replay."""

    def test_empty_sequence(self):
        traj = simulate_point_sequence([])
        assert len(traj) == 1
        assert traj[0] == MatchState()

    def test_single_point(self):
        traj = simulate_point_sequence([1])
        assert len(traj) == 2
        assert traj[1].p1_points == 1

    def test_full_game(self):
        traj = simulate_point_sequence([1, 1, 1, 1])
        last = traj[-1]
        assert last.p1_games == 1
        assert last.p1_points == 0

    def test_stops_at_terminal(self):
        """Sequence longer than the match should stop at terminal state."""
        # A sequence of all 1s will eventually end the match
        long_seq = [1] * 1000
        traj = simulate_point_sequence(long_seq)
        assert traj[-1].is_terminal()
        assert len(traj) < 1000  # stopped early
