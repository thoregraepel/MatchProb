// Tennis rules engine — computes the next state after a point.

import { MatchState } from './state.js';

function otherPlayer(p) { return 3 - p; }

export function nextState(state, pointWinner) {
  if (state.isTerminal()) throw new Error('Match is already over');
  if (pointWinner !== 1 && pointWinner !== 2) throw new Error('pointWinner must be 1 or 2');
  return state.tiebreak
    ? nextStateTiebreak(state, pointWinner)
    : nextStateRegular(state, pointWinner);
}

function nextStateRegular(state, pointWinner) {
  let p1 = state.p1Points, p2 = state.p2Points;
  let gameWon = false;

  if (pointWinner === 1) {
    p1++;
    if (p1 >= 4 && p2 < 3) gameWon = true;
    else if (p1 >= 4 && p2 >= 3 && p1 - p2 >= 2) gameWon = true;
  } else {
    p2++;
    if (p2 >= 4 && p1 < 3) gameWon = true;
    else if (p2 >= 4 && p1 >= 3 && p2 - p1 >= 2) gameWon = true;
  }

  // Deuce reset
  if (!gameWon && p1 >= 3 && p2 >= 3 && p1 === p2) {
    p1 = 3; p2 = 3;
  }

  if (gameWon) return winGame(state, pointWinner);

  return new MatchState({
    p1Points: p1, p2Points: p2,
    p1Games: state.p1Games, p2Games: state.p2Games,
    p1Sets: state.p1Sets, p2Sets: state.p2Sets,
    server: state.server, tiebreak: false, tbPointsPlayed: 0,
    tbStartServer: 0, bestOf: state.bestOf,
  });
}

function nextStateTiebreak(state, pointWinner) {
  let p1 = state.p1Points + (pointWinner === 1 ? 1 : 0);
  let p2 = state.p2Points + (pointWinner === 2 ? 1 : 0);
  let tbPlayed = state.tbPointsPlayed + 1;

  // Win check
  if (p1 >= 7 && p1 - p2 >= 2) return winGame(state, 1);
  if (p2 >= 7 && p2 - p1 >= 2) return winGame(state, 2);

  // Serve switch: after 1st point, then every 2 points
  let newServer;
  if (tbPlayed === 1 || (tbPlayed > 1 && (tbPlayed - 1) % 2 === 0)) {
    newServer = otherPlayer(state.server);
  } else {
    newServer = state.server;
  }

  // Normalize extended tiebreak to keep state space finite
  if (p1 >= 6 && p2 >= 6 && p1 === p2) {
    p1 = 6; p2 = 6; tbPlayed = 12;
  } else if (p1 >= 7 && p2 >= 6 && p1 - p2 === 1) {
    p1 = 7; p2 = 6; tbPlayed = 13;
  } else if (p2 >= 7 && p1 >= 6 && p2 - p1 === 1) {
    p1 = 6; p2 = 7; tbPlayed = 13;
  }

  return new MatchState({
    p1Points: p1, p2Points: p2,
    p1Games: state.p1Games, p2Games: state.p2Games,
    p1Sets: state.p1Sets, p2Sets: state.p2Sets,
    server: newServer, tiebreak: true, tbPointsPlayed: tbPlayed,
    tbStartServer: state.tbStartServer, bestOf: state.bestOf,
  });
}

function winGame(state, gameWinner) {
  const p1Games = state.p1Games + (gameWinner === 1 ? 1 : 0);
  const p2Games = state.p2Games + (gameWinner === 2 ? 1 : 0);

  // Determine new server
  let newServer;
  if (state.tiebreak) {
    newServer = otherPlayer(state.tbStartServer);
  } else {
    newServer = otherPlayer(state.server);
  }

  // Check set win
  let setWon = false;
  if (!state.tiebreak) {
    if (gameWinner === 1 && p1Games >= 6 && p1Games - p2Games >= 2) setWon = true;
    if (gameWinner === 2 && p2Games >= 6 && p2Games - p1Games >= 2) setWon = true;
  } else {
    setWon = true; // TB win always wins the set
  }

  // Check tiebreak entry
  const enteringTB = !state.tiebreak && p1Games === 6 && p2Games === 6 && !setWon;

  if (setWon) {
    return winSet(state, gameWinner, p1Games, p2Games, newServer);
  }

  if (enteringTB) {
    return new MatchState({
      p1Points: 0, p2Points: 0, p1Games, p2Games,
      p1Sets: state.p1Sets, p2Sets: state.p2Sets,
      server: newServer, tiebreak: true, tbPointsPlayed: 0,
      tbStartServer: newServer, bestOf: state.bestOf,
    });
  }

  return new MatchState({
    p1Points: 0, p2Points: 0, p1Games, p2Games,
    p1Sets: state.p1Sets, p2Sets: state.p2Sets,
    server: newServer, tiebreak: false, tbPointsPlayed: 0,
    tbStartServer: 0, bestOf: state.bestOf,
  });
}

function winSet(state, setWinner, p1Games, p2Games, newServer) {
  return new MatchState({
    p1Points: 0, p2Points: 0, p1Games: 0, p2Games: 0,
    p1Sets: state.p1Sets + (setWinner === 1 ? 1 : 0),
    p2Sets: state.p2Sets + (setWinner === 2 ? 1 : 0),
    server: newServer, tiebreak: false, tbPointsPlayed: 0,
    tbStartServer: 0, bestOf: state.bestOf,
  });
}

// BFS enumeration of all reachable states
export function enumerateStates(bestOf = 2, server = 1) {
  const initial = new MatchState({ server, bestOf });
  const visited = new Map(); // key -> MatchState
  visited.set(initial.key(), initial);
  const queue = [initial];

  while (queue.length > 0) {
    const current = queue.shift();
    if (current.isTerminal()) continue;
    for (const winner of [1, 2]) {
      const ns = nextState(current, winner);
      const k = ns.key();
      if (!visited.has(k)) {
        visited.set(k, ns);
        queue.push(ns);
      }
    }
  }

  return Array.from(visited.values());
}
