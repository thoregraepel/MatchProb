"""Tests for point-by-point parser."""

from matchprob.pbp import parse_pbp, SAMPLE_MATCHES
from matchprob.montecarlo import simulate_point_sequence
from matchprob.state import MatchState


class TestParsePbp:
    """Test the pbp string parser."""

    def test_simple_game_server_wins(self):
        # Server wins 4 points = 1 game
        points = parse_pbp("SSSS")
        assert points == [1, 1, 1, 1]

    def test_simple_game_returner_wins(self):
        points = parse_pbp("RRRR")
        assert points == [2, 2, 2, 2]

    def test_ace_counts_as_server(self):
        points = parse_pbp("AASS")
        assert points == [1, 1, 1, 1]

    def test_double_fault_counts_as_returner(self):
        points = parse_pbp("DDDD")
        assert points == [2, 2, 2, 2]

    def test_server_alternates_after_game(self):
        # Game 1: P1 serves, wins. Game 2: P2 serves.
        points = parse_pbp("SSSS;SSSS")
        # Game 1: server=1, S means P1 wins -> [1,1,1,1]
        # Game 2: server=2, S means P2 wins -> [2,2,2,2]
        assert points == [1, 1, 1, 1, 2, 2, 2, 2]

    def test_server_alternates_across_sets(self):
        # '.' acts as a game delimiter (like ';') and switches server
        points = parse_pbp("SSSS;SSSS.SSSS")
        # Game 1: P1 serves -> [1,1,1,1]
        # ';' switches to P2
        # Game 2: P2 serves -> [2,2,2,2]
        # '.' switches to P1
        # Game 3: P1 serves -> [1,1,1,1]
        assert points == [1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1]

    def test_tiebreak_serve_changes(self):
        # In tiebreak, '/' marks serve change
        points = parse_pbp("S/R")
        # S with server=1 -> P1 wins
        # / switches to server=2
        # R with server=2 -> P1 wins (returner = P1)
        assert points == [1, 1]

    def test_tiebreak_full(self):
        # P1 serves first point, then P2 serves 2 points, etc.
        points = parse_pbp("S/SS/RR/SS/RR")
        # S: server=1, S -> P1 wins
        # /SS: server=2, SS -> P2 wins twice
        # /RR: server=1, RR -> P2 wins twice
        # /SS: server=2, SS -> P2 wins twice
        # /RR: server=1, RR -> P2 wins twice
        assert points == [1, 2, 2, 2, 2, 2, 2, 2, 2]


class TestSampleMatchesIntegrity:
    """Verify that pre-loaded matches replay correctly."""

    def test_all_matches_have_points(self):
        for name, match in SAMPLE_MATCHES.items():
            assert len(match.point_sequence) > 0, f"{name} has no points"

    def test_all_matches_reach_terminal(self):
        for name, match in SAMPLE_MATCHES.items():
            start = MatchState(best_of=match.best_of)
            trajectory = simulate_point_sequence(match.point_sequence, start_state=start)
            final = trajectory[-1]
            assert final.is_terminal(), (
                f"{name} did not reach terminal state. "
                f"Final: {final.score_string()}, points played: {len(match.point_sequence)}"
            )

    def test_correct_winner(self):
        for name, match in SAMPLE_MATCHES.items():
            start = MatchState(best_of=match.best_of)
            trajectory = simulate_point_sequence(match.point_sequence, start_state=start)
            final = trajectory[-1]
            assert final.match_winner() == match.winner, (
                f"{name}: expected winner P{match.winner}, "
                f"got P{final.match_winner()}. Score: {final.score_string()}"
            )

    def test_us_open_2011_sf_djokovic_wins(self):
        match = SAMPLE_MATCHES["us_open_2011_sf"]
        start = MatchState(best_of=match.best_of)
        trajectory = simulate_point_sequence(match.point_sequence, start_state=start)
        final = trajectory[-1]
        assert final.match_winner() == 2  # Djokovic (P2)
        assert final.p1_sets == 2
        assert final.p2_sets == 3

    def test_australian_open_2017_federer_wins(self):
        match = SAMPLE_MATCHES["australian_open_2017_final"]
        start = MatchState(best_of=match.best_of)
        trajectory = simulate_point_sequence(match.point_sequence, start_state=start)
        final = trajectory[-1]
        assert final.match_winner() == 2  # Federer (player 2)
