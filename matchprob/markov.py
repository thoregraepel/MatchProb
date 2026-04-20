"""Analytical Markov chain solution for tennis match probabilities."""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

from .state import MatchState
from .rules import next_state, enumerate_states


def build_transition_system(
    p_serve: float = 0.5,
    p_return: Optional[float] = None,
    best_of: int = 2,
    server: int = 1,
) -> tuple[list[MatchState], np.ndarray]:
    """Build the transition matrix and enumerate all states.

    Args:
        p_serve: Probability that the server wins a point when P1 serves.
        p_return: Probability that the server wins a point when P2 serves.
                  Defaults to (1 - p_serve) if None — symmetric model where
                  p_serve is P1's serve advantage.
        best_of: Sets needed to win (2 = best-of-3, 3 = best-of-5).
        server: Initial server (1 or 2).

    Returns:
        (states, win_probs) where win_probs[i] is P(P1 wins | starting in state i).
    """
    if p_return is None:
        p_return = 1.0 - p_serve

    states = enumerate_states(best_of=best_of, server=server)
    state_to_idx = {s: i for i, s in enumerate(states)}
    n = len(states)

    # Identify transient and absorbing states
    transient_mask = [not s.is_terminal() for s in states]
    absorbing_mask = [s.is_terminal() for s in states]

    transient_indices = [i for i, m in enumerate(transient_mask) if m]
    absorbing_indices = [i for i, m in enumerate(absorbing_mask) if m]

    # Map from global index to transient/absorbing sub-index
    transient_map = {gi: ti for ti, gi in enumerate(transient_indices)}
    absorbing_map = {gi: ai for ai, gi in enumerate(absorbing_indices)}

    n_t = len(transient_indices)
    n_a = len(absorbing_indices)

    # Build Q (transient -> transient) and R (transient -> absorbing) as sparse
    q_rows, q_cols, q_vals = [], [], []
    r_rows, r_cols, r_vals = [], [], []

    for ti, gi in enumerate(transient_indices):
        state = states[gi]

        # Probability server wins the point
        if state.server == 1:
            p_server_wins = p_serve
        else:
            p_server_wins = p_return

        # Two possible successors
        for point_winner, prob in [
            (state.server, p_server_wins),
            (3 - state.server, 1.0 - p_server_wins),
        ]:
            ns = next_state(state, point_winner)
            ngi = state_to_idx[ns]

            if transient_mask[ngi]:
                q_rows.append(ti)
                q_cols.append(transient_map[ngi])
                q_vals.append(prob)
            else:
                r_rows.append(ti)
                r_cols.append(absorbing_map[ngi])
                r_vals.append(prob)

    Q = sparse.csr_matrix((q_vals, (q_rows, q_cols)), shape=(n_t, n_t))
    R = sparse.csr_matrix((r_vals, (r_rows, r_cols)), shape=(n_t, n_a))

    # Solve (I - Q) * B = R  =>  B = (I - Q)^{-1} R
    # B[i, j] = probability of being absorbed in absorbing state j starting from transient state i
    I_Q = sparse.eye(n_t, format="csc") - Q.tocsc()

    # Solve for each absorbing state column
    B = np.zeros((n_t, n_a))
    for j in range(n_a):
        rhs = R[:, j].toarray().flatten()
        B[:, j] = spsolve(I_Q, rhs)

    # Identify which absorbing states are P1 wins
    p1_win_absorbing = []
    for ai, gi in enumerate(absorbing_indices):
        p1_win_absorbing.append(states[gi].match_winner() == 1)

    # Win probability for each state
    win_probs = np.zeros(n)
    for ti, gi in enumerate(transient_indices):
        win_probs[gi] = sum(
            B[ti, ai] for ai in range(n_a) if p1_win_absorbing[ai]
        )
    for ai, gi in enumerate(absorbing_indices):
        win_probs[gi] = 1.0 if p1_win_absorbing[ai] else 0.0

    return states, win_probs


def win_probability(
    p_serve: float = 0.5,
    p_return: Optional[float] = None,
    start_state: Optional[MatchState] = None,
    best_of: int = 2,
) -> float:
    """Compute exact P(P1 wins) from a given state.

    Args:
        p_serve: Probability server wins a point when P1 serves.
        p_return: Probability server wins when P2 serves. Defaults to 1 - p_serve.
        start_state: State to query. Defaults to match start.
        best_of: Sets to win (2 or 3).

    Returns:
        Exact win probability for player 1.
    """
    if start_state is None:
        start_state = MatchState(best_of=best_of)

    states, win_probs = build_transition_system(
        p_serve=p_serve,
        p_return=p_return,
        best_of=best_of,
        server=start_state.server,
    )

    state_to_idx = {s: i for i, s in enumerate(states)}

    if start_state in state_to_idx:
        return win_probs[state_to_idx[start_state]]

    # If the exact state isn't found (e.g., different best_of),
    # fall back: try to find a matching state ignoring best_of
    for s, idx in state_to_idx.items():
        if (s.p1_points == start_state.p1_points
                and s.p2_points == start_state.p2_points
                and s.p1_games == start_state.p1_games
                and s.p2_games == start_state.p2_games
                and s.p1_sets == start_state.p1_sets
                and s.p2_sets == start_state.p2_sets
                and s.server == start_state.server
                and s.tiebreak == start_state.tiebreak):
            return win_probs[idx]

    raise ValueError(f"State not found in enumerated states: {start_state}")


def win_probability_grid(
    p_serve: float = 0.5,
    p_return: Optional[float] = None,
    best_of: int = 2,
    p1_sets: int = 0,
    p2_sets: int = 0,
    server: int = 1,
) -> dict[tuple[int, int], float]:
    """Compute win probabilities for all game scores in a set.

    Returns a dict mapping (p1_games, p2_games) -> P(P1 wins match)
    at the start of a new game (0-0 points).
    """
    states, win_probs = build_transition_system(
        p_serve=p_serve,
        p_return=p_return,
        best_of=best_of,
        server=server,
    )

    grid = {}
    state_to_idx = {s: i for i, s in enumerate(states)}

    for s, idx in state_to_idx.items():
        if (s.p1_sets == p1_sets and s.p2_sets == p2_sets
                and s.p1_points == 0 and s.p2_points == 0
                and not s.is_terminal()):
            grid[(s.p1_games, s.p2_games)] = win_probs[idx]

    return grid
