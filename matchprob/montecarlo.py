"""Monte Carlo simulation of tennis matches."""

from __future__ import annotations

from typing import Optional

import numpy as np

from .state import MatchState
from .rules import next_state


def simulate_match(
    p_serve: float = 0.5,
    p_return: Optional[float] = None,
    n_sims: int = 10_000,
    start_state: Optional[MatchState] = None,
    rng: Optional[np.random.Generator] = None,
) -> dict:
    """Simulate many matches and estimate P(player 1 wins).

    Args:
        p_serve: Probability that the server wins any given point.
        p_return: Probability that the returner wins any given point.
                  If None, defaults to (1 - p_serve), i.e. a single
                  parameter model where serving advantage is captured by p_serve.
        n_sims: Number of matches to simulate.
        start_state: Starting score state. Defaults to match start with P1 serving.
        rng: NumPy random generator for reproducibility.

    Returns:
        Dictionary with keys:
            'p1_win_prob': estimated probability P1 wins
            'ci_lower': lower bound of 95% confidence interval
            'ci_upper': upper bound of 95% confidence interval
            'n_sims': number of simulations run
    """
    if p_return is None:
        p_return = 1.0 - p_serve
    if start_state is None:
        start_state = MatchState()
    if rng is None:
        rng = np.random.default_rng()

    p1_wins = 0

    for _ in range(n_sims):
        state = start_state
        while not state.is_terminal():
            # Probability that server wins this point
            if state.server == 1:
                p_server_wins = p_serve
            else:
                p_server_wins = p_return

            if rng.random() < p_server_wins:
                point_winner = state.server
            else:
                point_winner = 3 - state.server

            state = next_state(state, point_winner)

        if state.match_winner() == 1:
            p1_wins += 1

    p_hat = p1_wins / n_sims
    # Wilson score interval for 95% CI
    z = 1.96
    denominator = 1 + z**2 / n_sims
    centre = (p_hat + z**2 / (2 * n_sims)) / denominator
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n_sims)) / n_sims) / denominator

    return {
        "p1_win_prob": p_hat,
        "ci_lower": max(0.0, centre - margin),
        "ci_upper": min(1.0, centre + margin),
        "n_sims": n_sims,
    }


def simulate_point_sequence(
    point_outcomes: list,
    start_state: Optional[MatchState] = None,
) -> list:
    """Replay a sequence of point outcomes and return the state trajectory.

    Args:
        point_outcomes: List of 1s and 2s indicating who won each point.
        start_state: Starting state. Defaults to match start.

    Returns:
        List of states (length = len(point_outcomes) + 1), starting with start_state.
    """
    if start_state is None:
        start_state = MatchState()

    trajectory = [start_state]
    state = start_state

    for winner in point_outcomes:
        if state.is_terminal():
            break
        state = next_state(state, winner)
        trajectory.append(state)

    return trajectory
