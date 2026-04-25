// Analytical Markov chain solution for tennis match probabilities.
// Uses value iteration on the state graph — no matrix allocation needed.
// For each transient state: v(s) = p * v(s_server_wins) + (1-p) * v(s_returner_wins)
// Terminal states: v = 1 if P1 wins, 0 if P2 wins.
// Converges in ~20 iterations since only deuce/TB-deuce states cycle.

import { MatchState } from './state.js';
import { nextState, enumerateStates } from './rules.js';

/**
 * Build the full transition system and compute win probabilities for every state.
 */
export function buildTransitionSystem(pServe, pReturn, bestOf = 2, server = 1) {
  if (pReturn == null) pReturn = 1.0 - pServe;

  const states = enumerateStates(bestOf, server);
  const stateIndex = new Map();
  for (let i = 0; i < states.length; i++) {
    stateIndex.set(states[i].key(), i);
  }
  const n = states.length;

  // For each transient state, precompute its two successors and probability
  const successors = new Array(n); // successors[i] = { idx1, idx2, p } or null if terminal
  for (let i = 0; i < n; i++) {
    const s = states[i];
    if (s.isTerminal()) { successors[i] = null; continue; }

    const pServerWins = s.server === 1 ? pServe : pReturn;
    const ns1 = nextState(s, s.server);       // server wins
    const ns2 = nextState(s, 3 - s.server);   // returner wins
    successors[i] = {
      idx1: stateIndex.get(ns1.key()),
      idx2: stateIndex.get(ns2.key()),
      p: pServerWins,
    };
  }

  // Value iteration
  const winProbs = new Float64Array(n);

  // Initialize terminal states
  for (let i = 0; i < n; i++) {
    if (states[i].isTerminal()) {
      winProbs[i] = states[i].matchWinner() === 1 ? 1.0 : 0.0;
    } else {
      winProbs[i] = 0.5; // initial guess
    }
  }

  // Iterate until convergence
  const maxIter = 500;
  const tol = 1e-12;
  for (let iter = 0; iter < maxIter; iter++) {
    let maxDiff = 0;
    for (let i = 0; i < n; i++) {
      const succ = successors[i];
      if (!succ) continue; // terminal
      const newVal = succ.p * winProbs[succ.idx1] + (1 - succ.p) * winProbs[succ.idx2];
      const diff = Math.abs(newVal - winProbs[i]);
      if (diff > maxDiff) maxDiff = diff;
      winProbs[i] = newVal;
    }
    if (maxDiff < tol) break;
  }

  return { states, winProbs, stateIndex };
}

/**
 * Get exact P(P1 wins) from a given state.
 */
export function winProbability(pServe, pReturn, startState, bestOf = 2) {
  if (!startState) startState = new MatchState({ bestOf });
  if (pReturn == null) pReturn = pServe;

  const { states, winProbs, stateIndex } = buildTransitionSystem(pServe, pReturn, bestOf, startState.server);

  const idx = stateIndex.get(startState.key());
  if (idx !== undefined) return winProbs[idx];

  // Fallback: find matching state
  for (let i = 0; i < states.length; i++) {
    const s = states[i];
    if (s.p1Points === startState.p1Points && s.p2Points === startState.p2Points &&
        s.p1Games === startState.p1Games && s.p2Games === startState.p2Games &&
        s.p1Sets === startState.p1Sets && s.p2Sets === startState.p2Sets &&
        s.server === startState.server && s.tiebreak === startState.tiebreak) {
      return winProbs[i];
    }
  }

  throw new Error('State not found in enumerated states');
}

/**
 * Compute win probabilities for all game scores in a set (at 0-0 points).
 */
export function winProbabilityGrid(pServe, pReturn, bestOf, p1Sets, p2Sets, server) {
  const { states, winProbs, stateIndex } = buildTransitionSystem(pServe, pReturn, bestOf, server);
  const grid = new Map();

  for (let i = 0; i < states.length; i++) {
    const s = states[i];
    if (s.p1Sets === p1Sets && s.p2Sets === p2Sets &&
        s.p1Points === 0 && s.p2Points === 0 && !s.isTerminal()) {
      grid.set(`${s.p1Games},${s.p2Games}`, winProbs[i]);
    }
  }

  return grid;
}
