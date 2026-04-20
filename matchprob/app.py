"""MatchProb — Streamlit web app for tennis match probability analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from .markov import build_transition_system, win_probability, win_probability_grid
from .montecarlo import simulate_match
from .state import MatchState

st.set_page_config(page_title="MatchProb", layout="wide")
st.title("MatchProb — Tennis Match Win Probability")
st.markdown(
    "Compute the exact probability of winning a tennis match from any score state, "
    "using a Markov chain model with configurable serve/return point probabilities."
)

# --- Sidebar controls ---
st.sidebar.header("Model Parameters")

p_serve = st.sidebar.slider(
    "P(server wins point) when P1 serves",
    min_value=0.0, max_value=1.0, value=0.65, step=0.01,
    help="Probability that the server wins any given point when Player 1 is serving.",
)

asymmetric = st.sidebar.checkbox("Different probability when P2 serves", value=False)
if asymmetric:
    p_return = st.sidebar.slider(
        "P(server wins point) when P2 serves",
        min_value=0.0, max_value=1.0, value=0.60, step=0.01,
        help="Probability that the server wins a point when Player 2 is serving.",
    )
else:
    p_return = None  # symmetric: uses p_serve for both

best_of_choice = st.sidebar.radio("Match format", ["Best of 3", "Best of 5"])
best_of = 2 if best_of_choice == "Best of 3" else 3

st.sidebar.header("Current Score")
col_s1, col_s2 = st.sidebar.columns(2)
p1_sets = col_s1.number_input("P1 sets", min_value=0, max_value=best_of - 1, value=0)
p2_sets = col_s2.number_input("P2 sets", min_value=0, max_value=best_of - 1, value=0)

col_g1, col_g2 = st.sidebar.columns(2)
p1_games = col_g1.number_input("P1 games", min_value=0, max_value=7, value=0)
p2_games = col_g2.number_input("P2 games", min_value=0, max_value=7, value=0)

is_tiebreak = p1_games == 6 and p2_games == 6
if is_tiebreak:
    st.sidebar.info("Tiebreak!")
    col_p1, col_p2 = st.sidebar.columns(2)
    p1_points = col_p1.number_input("P1 TB points", min_value=0, max_value=7, value=0)
    p2_points = col_p2.number_input("P2 TB points", min_value=0, max_value=7, value=0)
else:
    point_options = {0: "0", 1: "15", 2: "30", 3: "40", 4: "Ad"}
    col_p1, col_p2 = st.sidebar.columns(2)
    p1_points = col_p1.selectbox("P1 points", options=[0, 1, 2, 3, 4], format_func=lambda x: point_options[x])
    p2_points = col_p2.selectbox("P2 points", options=[0, 1, 2, 3, 4], format_func=lambda x: point_options[x])

server = st.sidebar.radio("Who is serving?", [1, 2], format_func=lambda x: f"Player {x}")

# --- Build state and compute ---
start_state = MatchState(
    p1_points=p1_points,
    p2_points=p2_points,
    p1_games=p1_games,
    p2_games=p2_games,
    p1_sets=p1_sets,
    p2_sets=p2_sets,
    server=server,
    tiebreak=is_tiebreak,
    tb_points_played=p1_points + p2_points if is_tiebreak else 0,
    tb_start_server=server if is_tiebreak else 0,
    best_of=best_of,
)

st.subheader("Current Score")
st.code(start_state.score_string())

# --- Win probability ---
if start_state.is_terminal():
    winner = start_state.match_winner()
    st.success(f"Match is over. Player {winner} wins!")
else:
    st.subheader("Win Probability (Analytical — Exact)")
    try:
        exact_p = win_probability(
            p_serve=p_serve, p_return=p_return,
            start_state=start_state, best_of=best_of,
        )
        col1, col2 = st.columns(2)
        col1.metric("P1 Win Probability", f"{exact_p:.4f}")
        col2.metric("P2 Win Probability", f"{1 - exact_p:.4f}")

        # Progress bar
        st.progress(exact_p)
    except Exception as e:
        st.error(f"Could not compute exact probability: {e}")

    # --- Monte Carlo ---
    st.subheader("Monte Carlo Simulation")
    n_sims = st.slider("Number of simulations", 1000, 100_000, 10_000, step=1000)

    if st.button("Run Simulation"):
        with st.spinner("Simulating..."):
            mc = simulate_match(
                p_serve=p_serve, p_return=p_return,
                n_sims=n_sims, start_state=start_state,
            )
        col1, col2, col3 = st.columns(3)
        col1.metric("MC Estimate", f"{mc['p1_win_prob']:.4f}")
        col2.metric("95% CI Lower", f"{mc['ci_lower']:.4f}")
        col3.metric("95% CI Upper", f"{mc['ci_upper']:.4f}")

    # --- Heatmap of game-score probabilities ---
    st.subheader("Win Probability by Game Score (current set)")
    try:
        grid = win_probability_grid(
            p_serve=p_serve, p_return=p_return,
            best_of=best_of, p1_sets=p1_sets, p2_sets=p2_sets,
            server=server,
        )
        if grid:
            max_g1 = max(g1 for g1, _ in grid.keys())
            max_g2 = max(g2 for _, g2 in grid.keys())
            df = pd.DataFrame(
                index=range(max_g1 + 1),
                columns=range(max_g2 + 1),
                dtype=float,
            )
            df.index.name = "P1 Games"
            df.columns.name = "P2 Games"
            for (g1, g2), prob in grid.items():
                df.loc[g1, g2] = prob

            # Style the dataframe as a heatmap
            styled = df.style.format("{:.3f}", na_rep="—").background_gradient(
                cmap="RdYlGn", vmin=0.0, vmax=1.0
            )
            st.dataframe(styled, use_container_width=True)
        else:
            st.info("No game-score grid available for this configuration.")
    except Exception as e:
        st.error(f"Could not compute grid: {e}")
