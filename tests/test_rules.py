"""Tests for the tennis scoring rules engine."""

import pytest
from matchprob.state import MatchState
from matchprob.rules import next_state, enumerate_states


class TestPointScoring:
    """Test basic point-level scoring."""

    def test_first_point_server_wins(self):
        state = MatchState()
        ns = next_state(state, 1)  # server (P1) wins
        assert ns.p1_points == 1
        assert ns.p2_points == 0

    def test_first_point_returner_wins(self):
        state = MatchState()
        ns = next_state(state, 2)
        assert ns.p1_points == 0
        assert ns.p2_points == 1

    def test_score_progression_to_40(self):
        state = MatchState()
        for _ in range(3):
            state = next_state(state, 1)
        assert state.p1_points == 3  # 40
        assert state.p2_points == 0

    def test_game_won_at_40_0(self):
        state = MatchState(p1_points=3, p2_points=0)
        ns = next_state(state, 1)
        # Game is won, new game starts
        assert ns.p1_points == 0
        assert ns.p2_points == 0
        assert ns.p1_games == 1
        assert ns.p2_games == 0

    def test_deuce_from_40_40(self):
        state = MatchState(p1_points=3, p2_points=3)
        # This IS deuce (both at 3)
        ns = next_state(state, 1)
        assert ns.p1_points == 4  # advantage P1
        assert ns.p2_points == 3

    def test_advantage_then_deuce(self):
        state = MatchState(p1_points=4, p2_points=3)
        ns = next_state(state, 2)  # P2 wins, back to deuce
        assert ns.p1_points == 3
        assert ns.p2_points == 3

    def test_advantage_then_game(self):
        state = MatchState(p1_points=4, p2_points=3)
        ns = next_state(state, 1)  # P1 wins from advantage
        assert ns.p1_games == 1
        assert ns.p1_points == 0


class TestGameScoring:
    """Test game-level scoring."""

    def test_server_alternates(self):
        state = MatchState(server=1)
        # P1 wins a game at love
        for _ in range(4):
            state = next_state(state, 1)
        assert state.p1_games == 1
        assert state.server == 2  # serve switches

    def test_set_won_at_6_4(self):
        state = MatchState(p1_games=5, p2_games=4, p1_points=3)
        ns = next_state(state, 1)  # wins game -> 6-4, set won
        assert ns.p1_sets == 1
        assert ns.p1_games == 0  # reset for new set
        assert ns.p2_games == 0

    def test_no_set_at_6_5(self):
        state = MatchState(p1_games=5, p2_games=5, p1_points=3)
        ns = next_state(state, 1)  # wins game -> 6-5, no set yet
        assert ns.p1_sets == 0
        assert ns.p1_games == 6
        assert ns.p2_games == 5

    def test_set_won_at_7_5(self):
        state = MatchState(p1_games=6, p2_games=5, p1_points=3)
        ns = next_state(state, 1)  # wins game -> 7-5, set won
        assert ns.p1_sets == 1
        assert ns.p1_games == 0


class TestTiebreak:
    """Test tiebreak scoring."""

    def test_tiebreak_starts_at_6_6(self):
        state = MatchState(p1_games=6, p2_games=5, p2_points=3, server=2)
        ns = next_state(state, 2)  # P2 wins to make it 6-6
        assert ns.tiebreak is True
        assert ns.p1_games == 6
        assert ns.p2_games == 6

    def test_tiebreak_win_at_7_0(self):
        state = MatchState(
            p1_games=6, p2_games=6, p1_points=6, p2_points=0,
            tiebreak=True, tb_points_played=6, tb_start_server=1,
        )
        ns = next_state(state, 1)  # 7-0, set won
        assert ns.p1_sets == 1
        assert ns.tiebreak is False

    def test_tiebreak_needs_two_ahead(self):
        state = MatchState(
            p1_games=6, p2_games=6, p1_points=6, p2_points=6,
            tiebreak=True, tb_points_played=12, tb_start_server=1,
        )
        ns = next_state(state, 1)  # 7-6, not won yet
        assert ns.tiebreak is True
        assert ns.p1_points == 7
        assert ns.p1_sets == 0  # not yet

    def test_tiebreak_win_at_8_6(self):
        state = MatchState(
            p1_games=6, p2_games=6, p1_points=7, p2_points=6,
            tiebreak=True, tb_points_played=13, tb_start_server=1,
        )
        ns = next_state(state, 1)  # 8-6, set won
        assert ns.p1_sets == 1

    def test_tiebreak_serve_switch_after_first_point(self):
        state = MatchState(
            p1_games=6, p2_games=6, server=1,
            tiebreak=True, tb_points_played=0, tb_start_server=1,
        )
        ns = next_state(state, 1)  # first point
        assert ns.server == 2  # serve switches after 1st point
        assert ns.tb_points_played == 1

    def test_tiebreak_serve_switch_pattern(self):
        state = MatchState(
            p1_games=6, p2_games=6, server=1,
            tiebreak=True, tb_points_played=0, tb_start_server=1,
        )
        servers = []
        for i in range(7):
            servers.append(state.server)
            state = next_state(state, 1)  # P1 always wins for simplicity
        # Pattern: 1, then switch to 2, 2 stays for 2nd, switch to 1, 1 stays, switch to 2, 2 stays
        # Point 0: server=1
        # Point 1: server=2 (switch after 1st)
        # Point 2: server=2 (no switch)
        # Point 3: server=1 (switch after 2 more)
        # Point 4: server=1 (no switch)
        # Point 5: server=2 (switch)
        # Point 6: server=2 (no switch)
        assert servers == [1, 2, 2, 1, 1, 2, 2]


class TestMatch:
    """Test match-level scoring."""

    def test_match_won_best_of_3(self):
        state = MatchState(p1_sets=1, p1_games=5, p1_points=3, best_of=2)
        ns = next_state(state, 1)  # wins game 6-0, wins set, wins match
        assert ns.is_terminal()
        assert ns.match_winner() == 1
        assert ns.p1_sets == 2

    def test_match_not_over_at_1_0_sets(self):
        state = MatchState(p1_sets=1, best_of=2)
        assert not state.is_terminal()

    def test_terminal_state_raises(self):
        state = MatchState(p1_sets=2, best_of=2)
        with pytest.raises(ValueError, match="already over"):
            next_state(state, 1)

    def test_invalid_point_winner(self):
        state = MatchState()
        with pytest.raises(ValueError, match="must be 1 or 2"):
            next_state(state, 3)


class TestEnumerateStates:
    """Test state enumeration."""

    def test_enumerate_includes_initial(self):
        states = enumerate_states(best_of=2)
        initial = MatchState(best_of=2)
        assert initial in states

    def test_enumerate_includes_terminal(self):
        states = enumerate_states(best_of=2)
        terminals = [s for s in states if s.is_terminal()]
        assert len(terminals) >= 2  # at least P1 wins and P2 wins

    def test_all_successors_in_enumeration(self):
        states = enumerate_states(best_of=2)
        state_set = set(states)
        for s in states:
            if not s.is_terminal():
                for w in (1, 2):
                    ns = next_state(s, w)
                    assert ns in state_set


class TestScoreString:
    """Test human-readable score display."""

    def test_initial_score(self):
        s = MatchState()
        assert "0-0" in s.score_string()

    def test_deuce(self):
        s = MatchState(p1_points=3, p2_points=3)
        assert "Deuce" in s.score_string()

    def test_terminal(self):
        s = MatchState(p1_sets=2, best_of=2)
        assert "P1 wins" in s.score_string()


class TestFullGameReplay:
    """Test by replaying known point sequences."""

    def test_love_game(self):
        """Server wins 4 straight points = 1 game."""
        state = MatchState()
        for _ in range(4):
            state = next_state(state, 1)
        assert state.p1_games == 1
        assert state.p1_points == 0

    def test_love_set(self):
        """Server wins 24 straight points = 6 love games = 1 set."""
        state = MatchState()
        for _ in range(24):
            # Alternate: P1 serves odd games, P2 serves even games
            # But P1 always wins the point
            state = next_state(state, 1)
        assert state.p1_sets == 1
        assert state.p1_games == 0  # reset
