"""Score state representation for tennis matches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MatchState:
    """Complete state of a tennis match.

    Attributes:
        p1_points: Points for player 1 in the current game (0-3 for normal, 3=40).
                   At deuce (both 3), 4 = advantage.
        p2_points: Points for player 2 in the current game.
        p1_games: Games won by player 1 in the current set.
        p2_games: Games won by player 2 in the current set.
        p1_sets: Sets won by player 1.
        p2_sets: Sets won by player 2.
        server: Which player is serving (1 or 2).
        tiebreak: Whether the current game is a tiebreak.
        tb_points_played: Total points played in the current tiebreak
                          (used to determine serve switches).
        best_of: Number of sets to win the match (2 for best-of-3, 3 for best-of-5).
    """

    p1_points: int = 0
    p2_points: int = 0
    p1_games: int = 0
    p2_games: int = 0
    p1_sets: int = 0
    p2_sets: int = 0
    server: int = 1
    tiebreak: bool = False
    tb_points_played: int = 0
    tb_start_server: int = 0  # who served first in the tiebreak (0 = not in TB)
    best_of: int = 2  # sets needed to win (2 = best-of-3)

    def is_terminal(self) -> bool:
        """Check if the match is over."""
        return self.p1_sets >= self.best_of or self.p2_sets >= self.best_of

    def match_winner(self) -> Optional[int]:
        """Return the winner (1 or 2) or None if match is ongoing."""
        if self.p1_sets >= self.best_of:
            return 1
        if self.p2_sets >= self.best_of:
            return 2
        return None

    def score_string(self) -> str:
        """Human-readable score string."""
        point_names = {0: "0", 1: "15", 2: "30", 3: "40"}

        sets_str = f"Sets: {self.p1_sets}-{self.p2_sets}"
        games_str = f"Games: {self.p1_games}-{self.p2_games}"

        if self.is_terminal():
            return f"{sets_str} (Match over, P{self.match_winner()} wins)"

        if self.tiebreak:
            point_str = f"Tiebreak: {self.p1_points}-{self.p2_points}"
        elif self.p1_points >= 3 and self.p2_points >= 3:
            if self.p1_points == self.p2_points:
                point_str = "Deuce"
            elif self.p1_points > self.p2_points:
                point_str = "Ad-In" if self.server == 1 else "Ad-Out"
            else:
                point_str = "Ad-Out" if self.server == 1 else "Ad-In"
        else:
            p1_name = point_names.get(self.p1_points, str(self.p1_points))
            p2_name = point_names.get(self.p2_points, str(self.p2_points))
            point_str = f"Points: {p1_name}-{p2_name}"

        return f"{sets_str}, {games_str}, {point_str}"
