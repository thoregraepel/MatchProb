"""Parser for Jeff Sackmann's point-by-point tennis data format.

Format reference: https://github.com/JeffSackmann/tennis_pointbypoint

Notation:
    S = Server won the point
    R = Returner won the point
    A = Ace (server won)
    D = Double fault (returner won)
    ; = Game boundary
    . = Set boundary
    / = Serve change within tiebreak
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MatchInfo:
    """Metadata and point-by-point data for a match."""

    player1: str  # server1 in the data (served first)
    player2: str
    date: str
    tournament: str
    score: str
    winner: int  # 1 or 2
    pbp_raw: str  # raw pbp string
    point_sequence: List[int]  # parsed: list of 1s and 2s (who won each point)
    best_of: int = 2  # sets to win: 2 = best-of-3, 3 = best-of-5

    @property
    def description(self) -> str:
        return f"{self.player1} vs {self.player2} — {self.tournament} ({self.date})"


def parse_pbp(pbp_raw: str) -> List[int]:
    """Parse a pbp string into a sequence of point winners (1 or 2).

    Player 1 is 'server1' (the player who served first in the match).
    The server alternates each game. In tiebreaks, '/' marks serve changes.

    Returns:
        List of 1 or 2 indicating who won each point.
    """
    points = []
    server = 1  # server1 starts serving
    in_tiebreak = False
    game_count_in_set = 0

    i = 0
    while i < len(pbp_raw):
        ch = pbp_raw[i]

        if ch in ('S', 'A'):
            # Server won the point (S = generic, A = ace)
            points.append(server)
        elif ch in ('R', 'D'):
            # Returner won the point (R = generic, D = double fault)
            points.append(3 - server)
        elif ch == ';':
            # Game boundary — server switches
            game_count_in_set += 1
            if not in_tiebreak:
                server = 3 - server
        elif ch == '.':
            # Set boundary — also acts as a game delimiter (replaces ';').
            # Server alternates, same as at a game boundary.
            game_count_in_set = 0
            in_tiebreak = False
            server = 3 - server
        elif ch == '/':
            # Tiebreak serve change
            in_tiebreak = True
            server = 3 - server
        # Ignore any other characters

        i += 1

    return points


# --- Pre-loaded iconic matches ---

SAMPLE_MATCHES = {
    "us_open_2011_sf": MatchInfo(
        player1="Roger Federer",
        player2="Novak Djokovic",
        date="10 Sep 2011",
        tournament="US Open Semi-Final",
        score="6-7(7) 4-6 6-3 6-2 7-5",
        winner=2,
        best_of=3,
        pbp_raw="SSSS;SSSS;SSSS;SRSSS;SSRRSS;SRSSS;RSSRSS;SSSRS;SSSRRS;SSRSS;RSSSS;RSSSS;S/RS/RS/RR/RS/SS/RS/SR/S.SSSRS;SSSS;RSRRSSRR;SSRRSRSS;RSSSS;RSRSRR;RRRR;SRSRSS;SSRSRS;SSRSS.SSSS;RSSRSRSRSRRSRSRR;SRSSS;RSSSRRSS;SRSSS;SSSS;SSSS;RSSSRS;SRRSSS.RSRRR;SSSS;RSSSS;SSSS;SRRRSR;SSSS;RSRRSSSRSRSS;SSSRRRSS.RSSSS;SRSSS;SSSS;RSRSSS;SRSRSS;SRSSRS;SSSS;RRRR;RSSSRRRSRR;RSSSS;RSRRR;SRSSS",
        point_sequence=[],
    ),
    "french_open_2013_sf": MatchInfo(
        player1="Novak Djokovic",
        player2="Rafael Nadal",
        date="7 Jun 2013",
        tournament="French Open Semi-Final",
        score="6-4 3-6 6-1 6-7(3) 9-7",
        winner=2,
        best_of=3,
        pbp_raw="SSSS;RSSRSRSRSS;RSSSRS;SRSSRS;SRRSSRSRSS;SSSS;SRSRSRRSRSRR;SSSS;SSRSS;SRSSS.RSSRSS;SRSRSS;SSRRSS;RSSRRSRSRR;RSRRSRSRSRSS;RRRSSSRRSRSS;SRSRSS;SRRRSSSRSRSS;SRSSSRSRSS.SSSS;RRSSSRSS;SSSS;RSSSS;SSSS;SSRSS;RRSSRSS.SSRSRR;RRSSSRSRSS;RRRRSSRR;SRSSSRSRSS;RSSRRSRRSSS;RSSRSRSRSS;SRSSSRSS;RRSSSRSS;RSSRSRSRSRSS;RSRSSS;RSSRSRSRSRSS;SSRSRSRSS;S/RS/SR/RS/RS/RR/SR.RSSRR;RSSSRS;RSRRSSRSS;SSSRS;RSRRSSS;RSRSSSRSRSS;RRRSSRSS;SRSSRS;SRSRSRSRSS;RRSSRSSS;SSRRRRSSS;RSRRSSRSS;SRSSS;SSSS;RRSSRSS;SRSSRS",
        point_sequence=[],
    ),
    "australian_open_2017_final": MatchInfo(
        player1="Rafael Nadal",
        player2="Roger Federer",
        date="29 Jan 2017",
        tournament="Australian Open Final",
        score="6-4 3-6 6-1 3-6 6-3",
        winner=2,
        best_of=3,
        pbp_raw="SSSS;SRSSRS;RSSDSS;SRSSS;SSSS;SSAS;RSRRR;SSSS;RSASRS;RASSS.RSSSS;DRSSRSRR;SSRRRSSRRSSS;RRRSSR;RRSSHRRRSSSRSS;SSRSS;SRSRSS;RRSSSRSS;RSRSSRSS.SSSS;RRSSSRSS;SRSSRS;RRSSRSS;SSRSS;SRSSS;SSSS.SRSSRS;SRSSRS;RSRSSS;RRRSSSRSRRSSS;SRSSRS;RSRRSSS;SSSRS;RASSRSRSS;SSSRS.SRSSS;RRSSRSRSS;RRSSSRSSS;SSRSS;RRSSSRSSS;SRSSS;RSRSSS;SRSRSRSRSS;SASRS",
        point_sequence=[],
    ),
    "wimbledon_2017_muller_nadal": MatchInfo(
        player1="Gilles Muller",
        player2="Rafael Nadal",
        date="10 Jul 2017",
        tournament="Wimbledon R16",
        score="6-3 6-4 3-6 4-6 15-13",
        winner=1,
        best_of=3,
        pbp_raw="SADSS;SSSRS;SSSS;SSSA;RRSSRSSA;RSSRRSRR;SSARRS;ARSAS;SSAS.SSSS;RAARSS;SSSS;SRSSRS;SSRSS;ASRAA;SSAS;RRSSRSRSS;RRSRSRSRSS;SASS.RSSSRS;RRSSSRSS;SRRSRSRSRSRSS;SSRSS;SRSSRS;SASS;RSSSS;RRSSRSS;RSSRSRSRSS.SRRSRSRSRSS;SRSSS;RSSRSRSRSS;RRSSRSS;SRSSRS;RSRSSS;SSSS;RRSSSRSS;SSRSS;RSSSS.SSAS;SSRSS;RRSSSRSSS;SSRSS;RSRSSS;ARSSS;SSASS;RSRSSS;SSSA;RSSSS;ARSSRSRSRRSRSS;RSRSSRSS;SSAS;SASS;RSSSS;RSRSSRSRSS;SRSSS;SSRSS;SSASS;RSSSS;RRSSRSS;RRSSSRSSRSSS;SRSSRS;SSARRS;SSSS;RSSRSRSRSRSS;SSAS;SSRSS",
        point_sequence=[],
    ),
}

# Parse all point sequences on module load
for match in SAMPLE_MATCHES.values():
    match.point_sequence = parse_pbp(match.pbp_raw)
