"""Tennis rules engine — computes the next state after a point is won."""

from .state import MatchState


def _other_player(player: int) -> int:
    return 3 - player  # 1 -> 2, 2 -> 1


def _switch_server(state: MatchState) -> int:
    return _other_player(state.server)


def next_state(state: MatchState, point_winner: int) -> MatchState:
    """Return the new match state after `point_winner` (1 or 2) wins the current point."""
    if state.is_terminal():
        raise ValueError("Match is already over")
    if point_winner not in (1, 2):
        raise ValueError("point_winner must be 1 or 2")

    if state.tiebreak:
        return _next_state_tiebreak(state, point_winner)
    else:
        return _next_state_regular(state, point_winner)


def _next_state_regular(state: MatchState, point_winner: int) -> MatchState:
    """Handle a point in a regular (non-tiebreak) game."""
    p1_pts, p2_pts = state.p1_points, state.p2_points

    # Check if point_winner wins the game
    game_won = False
    if point_winner == 1:
        p1_pts += 1
        # Win at 40 (=3) with opponent < 40, or win advantage
        if p1_pts >= 4 and p2_pts < 3:
            game_won = True
        elif p1_pts >= 4 and p2_pts >= 3:
            if p1_pts - p2_pts >= 2:
                game_won = True
            # If we just got to deuce (both had advantage scenario cancelled),
            # reset to deuce: both at 3
            elif p1_pts == p2_pts:
                # This shouldn't happen in standard scoring flow,
                # but handle deuce reset
                pass
    else:
        p2_pts += 1
        if p2_pts >= 4 and p1_pts < 3:
            game_won = True
        elif p2_pts >= 4 and p1_pts >= 3:
            if p2_pts - p1_pts >= 2:
                game_won = True

    # Deuce handling: if both >= 3 and equal, keep at 3-3
    if not game_won and p1_pts >= 3 and p2_pts >= 3 and p1_pts == p2_pts:
        p1_pts = 3
        p2_pts = 3

    if game_won:
        return _win_game(state, point_winner)
    else:
        return MatchState(
            p1_points=p1_pts,
            p2_points=p2_pts,
            p1_games=state.p1_games,
            p2_games=state.p2_games,
            p1_sets=state.p1_sets,
            p2_sets=state.p2_sets,
            server=state.server,
            tiebreak=False,
            tb_points_played=0,
            best_of=state.best_of,
        )


def _next_state_tiebreak(state: MatchState, point_winner: int) -> MatchState:
    """Handle a point in a tiebreak game.

    To keep the state space finite, we normalize extended tiebreak scores:
    when both players have >=6 points and are tied, we represent it as 6-6;
    when one leads by 1 (like 7-6), we keep that. This works because the
    strategic situation at 8-8 is identical to 6-6 (need 2 ahead to win),
    and we track the server correctly via tb_points_played parity.
    """
    p1_pts = state.p1_points + (1 if point_winner == 1 else 0)
    p2_pts = state.p2_points + (1 if point_winner == 2 else 0)
    tb_played = state.tb_points_played + 1

    # Tiebreak win: first to 7, must lead by 2
    if p1_pts >= 7 and p1_pts - p2_pts >= 2:
        return _win_game(state, 1)
    if p2_pts >= 7 and p2_pts - p1_pts >= 2:
        return _win_game(state, 2)

    # Serve switches: after first point, then every 2 points
    if tb_played == 1 or (tb_played > 1 and (tb_played - 1) % 2 == 0):
        new_server = _switch_server(state)
    else:
        new_server = state.server

    # Normalize extended tiebreak: if both >= 6 and tied, collapse to 6-6
    # If one leads 7-6 (advantage), keep as 7-6. This ensures finite states.
    if p1_pts >= 6 and p2_pts >= 6 and p1_pts == p2_pts:
        p1_pts = 6
        p2_pts = 6
        # tb_points_played is normalized too — at 6-6 the serve pattern
        # for the *next* point depends only on who serves now, which we track.
        tb_played = 12  # canonical "deuce" point count
    elif p1_pts >= 7 and p2_pts >= 6 and p1_pts - p2_pts == 1:
        p1_pts = 7
        p2_pts = 6
        tb_played = 13
    elif p2_pts >= 7 and p1_pts >= 6 and p2_pts - p1_pts == 1:
        p1_pts = 6
        p2_pts = 7
        tb_played = 13

    return MatchState(
        p1_points=p1_pts,
        p2_points=p2_pts,
        p1_games=state.p1_games,
        p2_games=state.p2_games,
        p1_sets=state.p1_sets,
        p2_sets=state.p2_sets,
        server=new_server,
        tiebreak=True,
        tb_points_played=tb_played,
        tb_start_server=state.tb_start_server,
        best_of=state.best_of,
    )


def _win_game(state: MatchState, game_winner: int) -> MatchState:
    """Handle a game being won — update games, possibly sets."""
    p1_games = state.p1_games + (1 if game_winner == 1 else 0)
    p2_games = state.p2_games + (1 if game_winner == 2 else 0)

    # Determine new server: alternates each game.
    # After a tiebreak, the player who received first in the TB serves
    # first in the next set = switch from tb_start_server.
    if state.tiebreak:
        new_server = _other_player(state.tb_start_server)
    else:
        new_server = _switch_server(state)

    # Check if this game wins a set
    set_won = False
    if not state.tiebreak:
        # Regular game: set won at 6 games with 2 ahead (but not 6-5 → play on)
        if game_winner == 1 and p1_games >= 6 and p1_games - p2_games >= 2:
            set_won = True
        elif game_winner == 2 and p2_games >= 6 and p2_games - p1_games >= 2:
            set_won = True
    else:
        # Tiebreak: winning the TB always wins the set (score becomes 7-6)
        set_won = True

    # Check if we should enter tiebreak (6-6, not already in one)
    entering_tiebreak = (not state.tiebreak and p1_games == 6 and p2_games == 6
                         and not set_won)

    if set_won:
        return _win_set(state, game_winner, p1_games, p2_games, new_server)
    elif entering_tiebreak:
        return MatchState(
            p1_points=0,
            p2_points=0,
            p1_games=p1_games,
            p2_games=p2_games,
            p1_sets=state.p1_sets,
            p2_sets=state.p2_sets,
            server=new_server,
            tiebreak=True,
            tb_points_played=0,
            tb_start_server=new_server,
            best_of=state.best_of,
        )
    else:
        return MatchState(
            p1_points=0,
            p2_points=0,
            p1_games=p1_games,
            p2_games=p2_games,
            p1_sets=state.p1_sets,
            p2_sets=state.p2_sets,
            server=new_server,
            tiebreak=False,
            tb_points_played=0,
            best_of=state.best_of,
        )



def _win_set(
    state: MatchState,
    set_winner: int,
    p1_games: int,
    p2_games: int,
    new_server: int,
) -> MatchState:
    """Handle a set being won — update sets, check for match end."""
    p1_sets = state.p1_sets + (1 if set_winner == 1 else 0)
    p2_sets = state.p2_sets + (1 if set_winner == 2 else 0)

    return MatchState(
        p1_points=0,
        p2_points=0,
        p1_games=0,
        p2_games=0,
        p1_sets=p1_sets,
        p2_sets=p2_sets,
        server=new_server,
        tiebreak=False,
        tb_points_played=0,
        best_of=state.best_of,
    )


def enumerate_states(best_of: int = 2, server: int = 1) -> list[MatchState]:
    """Enumerate all reachable match states via BFS from the initial state."""
    initial = MatchState(server=server, best_of=best_of)
    visited: set[MatchState] = set()
    queue = [initial]
    visited.add(initial)

    while queue:
        current = queue.pop(0)
        if current.is_terminal():
            continue
        for winner in (1, 2):
            ns = next_state(current, winner)
            if ns not in visited:
                visited.add(ns)
                queue.append(ns)

    return sorted(visited, key=lambda s: (
        s.p1_sets, s.p2_sets, s.p1_games, s.p2_games,
        s.tiebreak, s.p1_points, s.p2_points, s.server,
    ))
