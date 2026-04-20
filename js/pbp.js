// Parser for Jeff Sackmann's point-by-point tennis data format.
// S/A = server won, R/D = returner won, ; = game, . = set, / = TB serve change.

import { MatchState } from './state.js';
import { nextState } from './rules.js';

export function parsePbp(pbpRaw) {
  const points = [];
  let server = 1;

  for (const ch of pbpRaw) {
    if (ch === 'S' || ch === 'A') {
      points.push(server);
    } else if (ch === 'R' || ch === 'D') {
      points.push(3 - server);
    } else if (ch === ';') {
      server = 3 - server;
    } else if (ch === '.') {
      server = 3 - server;
    } else if (ch === '/') {
      server = 3 - server;
    }
  }

  return points;
}

export function simulatePointSequence(pointOutcomes, startState) {
  if (!startState) startState = new MatchState();
  const trajectory = [startState];
  let state = startState;

  for (const winner of pointOutcomes) {
    if (state.isTerminal()) break;
    state = nextState(state, winner);
    trajectory.push(state);
  }

  return trajectory;
}

export const SAMPLE_MATCHES = {
  us_open_2011_sf: {
    player1: 'Roger Federer',
    player2: 'Novak Djokovic',
    date: '10 Sep 2011',
    tournament: 'US Open Semi-Final',
    score: '6-7(7) 4-6 6-3 6-2 7-5',
    winner: 2,
    bestOf: 3,
    pbpRaw: 'SSSS;SSSS;SSSS;SRSSS;SSRRSS;SRSSS;RSSRSS;SSSRS;SSSRRS;SSRSS;RSSSS;RSSSS;S/RS/RS/RR/RS/SS/RS/SR/S.SSSRS;SSSS;RSRRSSRR;SSRRSRSS;RSSSS;RSRSRR;RRRR;SRSRSS;SSRSRS;SSRSS.SSSS;RSSRSRSRSRRSRSRR;SRSSS;RSSSRRSS;SRSSS;SSSS;SSSS;RSSSRS;SRRSSS.RSRRR;SSSS;RSSSS;SSSS;SRRRSR;SSSS;RSRRSSSRSRSS;SSSRRRSS.RSSSS;SRSSS;SSSS;RSRSSS;SRSRSS;SRSSRS;SSSS;RRRR;RSSSRRRSRR;RSSSS;RSRRR;SRSSS',
  },
  french_open_2013_sf: {
    player1: 'Novak Djokovic',
    player2: 'Rafael Nadal',
    date: '7 Jun 2013',
    tournament: 'French Open Semi-Final',
    score: '6-4 3-6 6-1 6-7(3) 9-7',
    winner: 2,
    bestOf: 3,
    pbpRaw: 'SSSS;RSSRSRSRSS;RSSSRS;SRSSRS;SRRSSRSRSS;SSSS;SRSRSRRSRSRR;SSSS;SSRSS;SRSSS.RSSRSS;SRSRSS;SSRRSS;RSSRRSRSRR;RSRRSRSRSRSS;RRRSSSRRSRSS;SRSRSS;SRRRSSSRSRSS;SRSSSRSRSS.SSSS;RRSSSRSS;SSSS;RSSSS;SSSS;SSRSS;RRSSRSS.SSRSRR;RRSSSRSRSS;RRRRSSRR;SRSSSRSRSS;RSSRRSRRSSS;RSSRSRSRSS;SRSSSRSS;RRSSSRSS;RSSRSRSRSRSS;RSRSSS;RSSRSRSRSRSS;SSRSRSRSS;S/RS/SR/RS/RS/RR/SR.RSSRR;RSSSRS;RSRRSSRSS;SSSRS;RSRRSSS;RSRSSSRSRSS;RRRSSRSS;SRSSRS;SRSRSRSRSS;RRSSRSSS;SSRRRRSSS;RSRRSSRSS;SRSSS;SSSS;RRSSRSS;SRSSRS',
  },
  australian_open_2017_final: {
    player1: 'Rafael Nadal',
    player2: 'Roger Federer',
    date: '29 Jan 2017',
    tournament: 'Australian Open Final',
    score: '6-4 3-6 6-1 3-6 6-3',
    winner: 2,
    bestOf: 3,
    pbpRaw: 'SSSS;SRSSRS;RSSDSS;SRSSS;SSSS;SSAS;RSRRR;SSSS;RSASRS;RASSS.RSSSS;DRSSRSRR;SSRRRSSRRSSS;RRRSSR;RRSSHRRRSSSRSS;SSRSS;SRSRSS;RRSSSRSS;RSRSSRSS.SSSS;RRSSSRSS;SRSSRS;RRSSRSS;SSRSS;SRSSS;SSSS.SRSSRS;SRSSRS;RSRSSS;RRRSSSRSRRSSS;SRSSRS;RSRRSSS;SSSRS;RASSRSRSS;SSSRS.SRSSS;RRSSRSRSS;RRSSSRSSS;SSRSS;RRSSSRSSS;SRSSS;RSRSSS;SRSRSRSRSS;SASRS',
  },
  wimbledon_2017_muller_nadal: {
    player1: 'Gilles Muller',
    player2: 'Rafael Nadal',
    date: '10 Jul 2017',
    tournament: 'Wimbledon R16',
    score: '6-3 6-4 3-6 4-6 15-13',
    winner: 1,
    bestOf: 3,
    pbpRaw: 'SADSS;SSSRS;SSSS;SSSA;RRSSRSSA;RSSRRSRR;SSARRS;ARSAS;SSAS.SSSS;RAARSS;SSSS;SRSSRS;SSRSS;ASRAA;SSAS;RRSSRSRSS;RRSRSRSRSS;SASS.RSSSRS;RRSSSRSS;SRRSRSRSRSRSS;SSRSS;SRSSRS;SASS;RSSSS;RRSSRSS;RSSRSRSRSS.SRRSRSRSRSS;SRSSS;RSSRSRSRSS;RRSSRSS;SRSSRS;RSRSSS;SSSS;RRSSSRSS;SSRSS;RSSSS.SSAS;SSRSS;RRSSSRSSS;SSRSS;RSRSSS;ARSSS;SSASS;RSRSSS;SSSA;RSSSS;ARSSRSRSRRSRSS;RSRSSRSS;SSAS;SASS;RSSSS;RSRSSRSRSS;SRSSS;SSRSS;SSASS;RSSSS;RRSSRSS;RRSSSRSSRSSS;SRSSRS;SSARRS;SSSS;RSSRSRSRSRSS;SSAS;SSRSS',
  },
};

// Pre-parse all point sequences
for (const match of Object.values(SAMPLE_MATCHES)) {
  match.pointSequence = parsePbp(match.pbpRaw);
}
