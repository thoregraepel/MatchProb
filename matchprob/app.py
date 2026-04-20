"""MatchProb — Streamlit web app for tennis match probability analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from matchprob.markov import build_transition_system, win_probability, win_probability_grid
from matchprob.montecarlo import simulate_match, simulate_point_sequence
from matchprob.state import MatchState
from matchprob.pbp import SAMPLE_MATCHES

st.set_page_config(page_title="MatchProb", layout="wide")
st.title("MatchProb — Tennis Match Win Probability")

mode = st.radio("Mode", ["Match Replay", "Manual Score"], horizontal=True)

# --- Sidebar controls ---
st.sidebar.header("Model Parameters")

decoupled = st.sidebar.checkbox("Different serve probabilities per player", value=False)

if decoupled:
    p_serve = st.sidebar.slider(
        "P(server wins point) — P1 serving",
        min_value=0.0, max_value=1.0, value=0.65, step=0.01,
    )
    p_return = st.sidebar.slider(
        "P(server wins point) — P2 serving",
        min_value=0.0, max_value=1.0, value=0.65, step=0.01,
    )
else:
    p_serve = st.sidebar.slider(
        "P(server wins point)",
        min_value=0.0, max_value=1.0, value=0.65, step=0.01,
        help="Same probability for both players when serving.",
    )
    p_return = p_serve

# ============================================================
# MODE 1: Manual Score
# ============================================================
if mode == "Manual Score":
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
        p1_points = col_p1.selectbox("P1 points", options=[0, 1, 2, 3, 4],
                                      format_func=lambda x: point_options[x])
        p2_points = col_p2.selectbox("P2 points", options=[0, 1, 2, 3, 4],
                                      format_func=lambda x: point_options[x])

    server = st.sidebar.radio("Who is serving?", [1, 2],
                               format_func=lambda x: f"Player {x}")

    start_state = MatchState(
        p1_points=p1_points, p2_points=p2_points,
        p1_games=p1_games, p2_games=p2_games,
        p1_sets=p1_sets, p2_sets=p2_sets,
        server=server, tiebreak=is_tiebreak,
        tb_points_played=p1_points + p2_points if is_tiebreak else 0,
        tb_start_server=server if is_tiebreak else 0,
        best_of=best_of,
    )

    st.subheader("Current Score")
    st.code(start_state.score_string())

    if start_state.is_terminal():
        st.success(f"Match is over. Player {start_state.match_winner()} wins!")
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
            st.progress(exact_p)
        except Exception as e:
            st.error(f"Could not compute exact probability: {e}")

        # Heatmap of game-score probabilities
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
                    index=range(max_g1 + 1), columns=range(max_g2 + 1), dtype=float,
                )
                df.index.name = "P1 Games"
                df.columns.name = "P2 Games"
                for (g1, g2), prob in grid.items():
                    df.loc[g1, g2] = prob

                def color_cell(val):
                    if pd.isna(val):
                        return ""
                    r = int(255 * (1 - val))
                    g = int(255 * val)
                    return f"background-color: rgb({r},{g},80); color: white"

                styled = df.style.format("{:.3f}", na_rep="—").applymap(color_cell)
                st.dataframe(styled, use_container_width=True)
        except Exception as e:
            st.error(f"Could not compute grid: {e}")

# ============================================================
# MODE 2: Match Replay
# ============================================================
else:
    match_names = {
        "us_open_2011_sf": "Federer vs Djokovic — US Open SF 2011 (6-7 4-6 6-3 6-2 7-5)",
        "french_open_2013_sf": "Djokovic vs Nadal — French Open SF 2013 (6-4 3-6 6-1 6-7 9-7)",
        "australian_open_2017_final": "Nadal vs Federer — Australian Open Final 2017 (6-4 3-6 6-1 3-6 6-3)",
        "wimbledon_2017_muller_nadal": "Muller vs Nadal — Wimbledon R16 2017 (6-3 6-4 3-6 4-6 15-13)",
    }
    selected_key = st.selectbox(
        "Select a match",
        options=list(match_names.keys()),
        format_func=lambda k: match_names[k],
    )
    match = SAMPLE_MATCHES[selected_key]

    st.markdown(f"**{match.player1}** (P1) vs **{match.player2}** (P2)")
    st.markdown(f"*{match.tournament}, {match.date}* — Final score: **{match.score}** "
                f"(Winner: **{match.player1 if match.winner == 1 else match.player2}**)")

    # Build full trajectory
    start = MatchState(best_of=match.best_of)
    trajectory = simulate_point_sequence(match.point_sequence, start_state=start)
    total_points = len(trajectory) - 1  # trajectory includes initial state

    # Compute win probabilities for the full trajectory
    @st.cache_data
    def compute_trajectory_probs(match_key, p_s, p_r):
        m = SAMPLE_MATCHES[match_key]
        s = MatchState(best_of=m.best_of)
        traj = simulate_point_sequence(m.point_sequence, start_state=s)
        best_of = m.best_of

        states_list, win_probs = build_transition_system(
            p_serve=p_s, p_return=p_r, best_of=best_of, server=1,
        )
        state_to_idx = {st: i for i, st in enumerate(states_list)}

        probs = []
        for state in traj:
            if state in state_to_idx:
                probs.append(win_probs[state_to_idx[state]])
            elif state.is_terminal():
                probs.append(1.0 if state.match_winner() == 1 else 0.0)
            else:
                probs.append(0.5)
        return traj, probs

    with st.spinner("Computing win probabilities for all points..."):
        traj, probs = compute_trajectory_probs(selected_key, p_serve, p_return)

    # Timeline slider
    point_idx = st.slider(
        "Point in match",
        min_value=0, max_value=total_points,
        value=0,
        help="Slide to move through the match point by point.",
    )

    state = traj[point_idx]
    p1_prob = probs[point_idx]

    # Current state display
    col_score, col_prob = st.columns([1, 1])
    with col_score:
        st.subheader("Score")
        st.code(state.score_string())
        st.caption(f"Point {point_idx} of {total_points}")
        if point_idx > 0:
            prev_winner = match.point_sequence[point_idx - 1]
            name = match.player1 if prev_winner == 1 else match.player2
            st.caption(f"Last point won by: **{name}**")

    with col_prob:
        st.subheader("Win Probability")
        col1, col2 = st.columns(2)
        col1.metric(match.player1, f"{p1_prob:.3f}")
        col2.metric(match.player2, f"{1 - p1_prob:.3f}")
        st.progress(p1_prob)

    # Compute set and game boundaries
    set_boundary_points = []
    game_boundary_points = []
    prev_sets = (0, 0)
    prev_games = (0, 0)
    for i, s in enumerate(traj):
        curr_sets = (s.p1_sets, s.p2_sets)
        curr_games = (s.p1_games, s.p2_games)
        if curr_sets != prev_sets and i > 0:
            prev_state = traj[i - 1]
            label = f"{curr_sets[0]}-{curr_sets[1]} ({prev_state.p1_games}-{prev_state.p2_games})"
            set_boundary_points.append({"Point": i, "label": label})
            prev_sets = curr_sets
            prev_games = curr_games  # skip game boundary at set boundary
        elif curr_games != prev_games and i > 0:
            game_boundary_points.append({"Point": i})
            prev_games = curr_games

    # Win probability chart with boundary lines
    st.subheader("Win Probability Timeline")

    import altair as alt

    chart_data = pd.DataFrame({
        "Point": range(len(probs)),
        match.player1: probs,
        match.player2: [1 - p for p in probs],
    })
    melted = chart_data.melt("Point", var_name="Player", value_name="Win Probability")

    base = alt.Chart(melted).mark_line().encode(
        x="Point:Q",
        y=alt.Y("Win Probability:Q", scale=alt.Scale(domain=[0, 1])),
        color="Player:N",
    )

    show_set = st.checkbox("Show set boundaries", value=True)
    show_game = st.checkbox("Show game boundaries", value=True)

    layers = [base]

    if show_set and set_boundary_points:
        set_df = pd.DataFrame(set_boundary_points)
        set_rules = alt.Chart(set_df).mark_rule(
            color="red", strokeWidth=2, strokeDash=[4, 2],
        ).encode(x="Point:Q")
        set_labels = alt.Chart(set_df).mark_text(
            align="left", dx=3, dy=-5, fontSize=10, color="red",
        ).encode(x="Point:Q", text="label:N")
        layers += [set_rules, set_labels]

    if show_game and game_boundary_points:
        game_df = pd.DataFrame(game_boundary_points)
        game_rules = alt.Chart(game_df).mark_rule(
            color="gray", strokeWidth=0.5, opacity=0.4,
        ).encode(x="Point:Q")
        layers.append(game_rules)

    combined = alt.layer(*layers).properties(height=400, width="container")
    st.altair_chart(combined, use_container_width=True)

    # Match statistics
    st.subheader("Match Statistics")
    p1_points_won = sum(1 for w in match.point_sequence if w == 1)
    p2_points_won = sum(1 for w in match.point_sequence if w == 2)
    total = p1_points_won + p2_points_won

    col1, col2, col3 = st.columns(3)
    col1.metric("Total points", total)
    col2.metric(f"{match.player1} points", f"{p1_points_won} ({100*p1_points_won/total:.1f}%)")
    col3.metric(f"{match.player2} points", f"{p2_points_won} ({100*p2_points_won/total:.1f}%)")

    # Momentum: biggest probability swings
    if len(probs) > 1:
        swings = [(i, probs[i] - probs[i-1]) for i in range(1, len(probs))]
        swings.sort(key=lambda x: abs(x[1]), reverse=True)
        with st.expander("Biggest momentum swings"):
            for i, (pt, swing) in enumerate(swings[:10]):
                direction = match.player1 if swing > 0 else match.player2
                st.text(f"Point {pt}: {swing:+.4f} toward {direction} "
                        f"({traj[pt].score_string()})")
