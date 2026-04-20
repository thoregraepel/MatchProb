// Analytical Markov chain solution for tennis match probabilities.
// Builds transition system, partitions into transient/absorbing, solves (I-Q)^{-1}R.

import { MatchState } from './state.js';
import { nextState, enumerateStates } from './rules.js';
import { solveAbsorbing } from './linalg.js';

/**
 * Build the full transition system and compute win probabilities for every state.
 * @param {number} pServe - P(server wins point) when P1 serves
 * @param {number} pReturn - P(server wins point) when P2 serves
 * @param {number} bestOf - Sets to win (2 or 3)
 * @param {number} server - Initial server (1 or 2)
 * @returns {{ states: MatchState[], winProbs: Float64Array, stateIndex: Map<string,number> }}
 */
export function buildTransitionSystem(pServe, pReturn, bestOf = 2, server = 1) {
  if (pReturn == null) pReturn = 1.0 - pServe;

  const states = enumerateStates(bestOf, server);
  const stateIndex = new Map();
  for (let i = 0; i < states.length; i++) {
    stateIndex.set(states[i].key(), i);
  }
  const n = states.length;

  // Partition into transient and absorbing
  const isTransient = states.map(s => !s.isTerminal());
  const transientIndices = [];
  const absorbingIndices = [];
  for (let i = 0; i < n; i++) {
    if (isTransient[i]) transientIndices.push(i);
    else absorbingIndices.push(i);
  }

  // Map global index -> transient sub-index
  const transientMap = new Map();
  transientIndices.forEach((gi, ti) => transientMap.set(gi, ti));
  const absorbingMap = new Map();
  absorbingIndices.forEach((gi, ai) => absorbingMap.set(gi, ai));

  const nT = transientIndices.length;
  const nA = absorbingIndices.length;

  // Build Q entries (sparse) and R columns
  const qEntries = [];
  // R: for each absorbing state j, store the transient contributions
  const rColumns = new Array(nA);
  for (let j = 0; j < nA; j++) rColumns[j] = new Float64Array(nT);

  for (let ti = 0; ti < nT; ti++) {
    const gi = transientIndices[ti];
    const state = states[gi];

    const pServerWins = state.server === 1 ? pServe : pReturn;

    for (const [pw, prob] of [[state.server, pServerWins], [3 - state.server, 1.0 - pServerWins]]) {
      const ns = nextState(state, pw);
      const ngi = stateIndex.get(ns.key());

      if (isTransient[ngi]) {
        qEntries.push({ row: ti, col: transientMap.get(ngi), val: prob });
      } else {
        const ai = absorbingMap.get(ngi);
        rColumns[ai][ti] += prob;
      }
    }
  }

  // Identify which absorbing states are P1 wins
  const p1WinAbsorbing = absorbingIndices.map(gi => states[gi].matchWinner() === 1);

  // Solve (I-Q) * B[:,j] = R[:,j] for each absorbing state j
  // Then winProb[ti] = sum over j where P1 wins of B[ti,j]
  const winProbTransient = new Float64Array(nT);

  for (let j = 0; j < nA; j++) {
    if (!p1WinAbsorbing[j]) continue; // skip P2-win absorbing states
    const bCol = solveAbsorbing(qEntries, rColumns[j], nT);
    for (let ti = 0; ti < nT; ti++) {
      winProbTransient[ti] += bCol[ti];
    }
  }

  // Build full win probability array
  const winProbs = new Float64Array(n);
  for (let ti = 0; ti < nT; ti++) {
    winProbs[transientIndices[ti]] = winProbTransient[ti];
  }
  for (let ai = 0; ai < nA; ai++) {
    winProbs[absorbingIndices[ai]] = p1WinAbsorbing[ai] ? 1.0 : 0.0;
  }

  return { states, winProbs, stateIndex };
}

/**
 * Get exact P(P1 wins) from a given state.
 */
export function winProbability(pServe, pReturn, startState, bestOf = 2) {
  if (!startState) startState = new MatchState({ bestOf });
  if (pReturn == null) pReturn = pServe; // symmetric model

  const { states, winProbs, stateIndex } = buildTransitionSystem(pServe, pReturn, bestOf, startState.server);

  const idx = stateIndex.get(startState.key());
  if (idx !== undefined) return winProbs[idx];

  // Fallback: find matching state ignoring bestOf differences
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
 * Returns Map<string, number> where key is "g1,g2".
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
