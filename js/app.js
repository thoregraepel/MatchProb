// MatchProb — main application logic and UI wiring.

import { MatchState } from './state.js';
import { nextState } from './rules.js';
import { buildTransitionSystem, winProbability, winProbabilityGrid } from './markov.js';
import { SAMPLE_MATCHES, simulatePointSequence } from './pbp.js';
import { TimelineChart } from './chart.js';

// ---- State ----
let mode = 'replay';  // 'replay' or 'manual'
let chart = null;
let cachedSystem = null; // { key, states, winProbs, stateIndex }

// ---- DOM references ----
const $ = (id) => document.getElementById(id);

// ---- Initialization ----
export function init() {
  chart = new TimelineChart($('timeline-canvas'));

  // Mode tabs
  $('tab-replay').addEventListener('click', () => switchMode('replay'));
  $('tab-manual').addEventListener('click', () => switchMode('manual'));
  $('tab-about').addEventListener('click', () => switchMode('about'));

  // Controls
  $('p-serve-slider').addEventListener('input', onParamChange);
  $('decouple-check').addEventListener('change', onDecoupleChange);
  $('p-return-slider').addEventListener('input', onParamChange);
  $('match-select').addEventListener('change', onMatchChange);
  $('point-slider').addEventListener('input', onPointSliderChange);
  $('set-lines-check').addEventListener('change', onChartToggle);
  $('game-lines-check').addEventListener('change', onChartToggle);

  // Manual mode controls
  for (const id of ['m-p1sets', 'm-p2sets', 'm-p1games', 'm-p2games',
                     'm-p1points', 'm-p2points', 'm-server', 'm-bestof']) {
    $(id).addEventListener('change', onManualChange);
  }

  // Populate match selector
  const sel = $('match-select');
  for (const [key, m] of Object.entries(SAMPLE_MATCHES)) {
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = `${m.player1} vs ${m.player2} — ${m.tournament} (${m.score})`;
    sel.appendChild(opt);
  }

  onDecoupleChange();
  switchMode('replay');
  window.addEventListener('resize', () => { if (mode === 'replay') drawChart(); });
}

function switchMode(m) {
  mode = m;
  $('tab-replay').classList.toggle('active', m === 'replay');
  $('tab-manual').classList.toggle('active', m === 'manual');
  $('tab-about').classList.toggle('active', m === 'about');
  $('replay-panel').style.display = m === 'replay' ? '' : 'none';
  $('manual-panel').style.display = m === 'manual' ? '' : 'none';
  $('about-panel').style.display = m === 'about' ? '' : 'none';
  $('controls').style.display = m === 'about' ? 'none' : '';
  if (m === 'replay') onMatchChange();
  else if (m === 'manual') onManualChange();
}

// ---- Parameter helpers ----
function getPServe() { return parseFloat($('p-serve-slider').value); }
function getPReturn() {
  return $('decouple-check').checked
    ? parseFloat($('p-return-slider').value)
    : getPServe();
}

function onDecoupleChange() {
  const decoupled = $('decouple-check').checked;
  $('p-return-row').style.display = decoupled ? '' : 'none';
  onParamChange();
}

function onParamChange() {
  $('p-serve-val').textContent = getPServe().toFixed(2);
  $('p-return-val').textContent = getPReturn().toFixed(2);
  cachedSystem = null;
  if (mode === 'replay') onMatchChange();
  else onManualChange();
}

// ---- Match Replay Mode ----
function onMatchChange() {
  const key = $('match-select').value;
  const match = SAMPLE_MATCHES[key];
  if (!match) return;

  $('match-info').innerHTML =
    `<strong>${match.player1}</strong> (P1) vs <strong>${match.player2}</strong> (P2)<br>` +
    `<em>${match.tournament}, ${match.date}</em> — Final: <strong>${match.score}</strong> ` +
    `(Winner: <strong>${match.winner === 1 ? match.player1 : match.player2}</strong>)`;

  const startState = new MatchState({ bestOf: match.bestOf });
  const trajectory = simulatePointSequence(match.pointSequence, startState);
  const totalPoints = trajectory.length - 1;

  // Get or build transition system
  const sys = getSystem(getPServe(), getPReturn(), match.bestOf, 1);

  // Compute probabilities for each state in trajectory
  const probs = trajectory.map(s => {
    const idx = sys.stateIndex.get(s.key());
    if (idx !== undefined) return sys.winProbs[idx];
    if (s.isTerminal()) return s.matchWinner() === 1 ? 1.0 : 0.0;
    return 0.5;
  });

  // Compute boundaries
  const setBoundaries = [];
  const gameBoundaries = [];
  let prevSets = '0,0', prevGames = '0,0';
  for (let i = 1; i < trajectory.length; i++) {
    const s = trajectory[i];
    const currSets = `${s.p1Sets},${s.p2Sets}`;
    const currGames = `${s.p1Games},${s.p2Games}`;
    if (currSets !== prevSets) {
      const prev = trajectory[i - 1];
      setBoundaries.push({ point: i, label: `${s.p1Sets}-${s.p2Sets} (${prev.p1Games}-${prev.p2Games})` });
      prevSets = currSets;
      prevGames = currGames;
    } else if (currGames !== prevGames) {
      gameBoundaries.push(i);
      prevGames = currGames;
    }
  }

  // Setup slider
  const slider = $('point-slider');
  slider.max = totalPoints;
  slider.value = 0;

  // Store data for slider updates
  chart.setData(probs, setBoundaries, gameBoundaries, match.player1, match.player2);
  chart._trajectory = trajectory;
  chart._match = match;
  chart._probs = probs;

  onPointSliderChange();
}

function onPointSliderChange() {
  const idx = parseInt($('point-slider').value);
  chart.currentPoint = idx;
  drawChart();

  const traj = chart._trajectory;
  const probs = chart._probs;
  const match = chart._match;
  if (!traj || !match) return;

  const state = traj[idx];
  const p1Prob = probs[idx];

  $('replay-score').textContent = state.scoreString();
  $('replay-point-num').textContent = `Point ${idx} of ${traj.length - 1}`;

  $('p1-prob').textContent = p1Prob.toFixed(4);
  $('p2-prob').textContent = (1 - p1Prob).toFixed(4);
  $('p1-name-label').textContent = match.player1;
  $('p2-name-label').textContent = match.player2;
  $('prob-bar').style.width = `${(p1Prob * 100).toFixed(1)}%`;

  if (idx > 0) {
    const pw = match.pointSequence[idx - 1];
    $('last-point').textContent = `Last point: ${pw === 1 ? match.player1 : match.player2}`;
  } else {
    $('last-point').textContent = '';
  }

  // Stats
  const played = match.pointSequence.slice(0, idx);
  const p1Won = played.filter(w => w === 1).length;
  const p2Won = played.filter(w => w === 2).length;
  const total = p1Won + p2Won;
  $('stats-total').textContent = total;
  $('stats-p1').textContent = total > 0 ? `${p1Won} (${(100*p1Won/total).toFixed(1)}%)` : '0';
  $('stats-p2').textContent = total > 0 ? `${p2Won} (${(100*p2Won/total).toFixed(1)}%)` : '0';
}

function onChartToggle() {
  chart.showSetLines = $('set-lines-check').checked;
  chart.showGameLines = $('game-lines-check').checked;
  drawChart();
}

function drawChart() {
  chart.draw();
}

// ---- Manual Score Mode ----
function onManualChange() {
  const bestOf = parseInt($('m-bestof').value);
  const p1Sets = parseInt($('m-p1sets').value);
  const p2Sets = parseInt($('m-p2sets').value);
  const p1Games = parseInt($('m-p1games').value);
  const p2Games = parseInt($('m-p2games').value);
  const p1Points = parseInt($('m-p1points').value);
  const p2Points = parseInt($('m-p2points').value);
  const server = parseInt($('m-server').value);
  const isTB = p1Games === 6 && p2Games === 6;

  const state = new MatchState({
    p1Points, p2Points, p1Games, p2Games, p1Sets, p2Sets,
    server, tiebreak: isTB,
    tbPointsPlayed: isTB ? p1Points + p2Points : 0,
    tbStartServer: isTB ? server : 0,
    bestOf,
  });

  $('manual-score').textContent = state.scoreString();

  if (state.isTerminal()) {
    $('manual-prob').innerHTML = `<strong>Match over. Player ${state.matchWinner()} wins!</strong>`;
    $('manual-grid').innerHTML = '';
    return;
  }

  // Compute probability (runs in main thread — may take a moment for best-of-5)
  $('manual-prob').innerHTML = 'Computing...';

  // Use setTimeout to allow UI to update
  setTimeout(() => {
    try {
      const pServe = getPServe();
      const pReturn = getPReturn();
      const sys = getSystem(pServe, pReturn, bestOf, server);
      const idx = sys.stateIndex.get(state.key());
      let prob;
      if (idx !== undefined) {
        prob = sys.winProbs[idx];
      } else {
        prob = winProbability(pServe, pReturn, state, bestOf);
      }

      $('manual-prob').innerHTML =
        `<div class="prob-display">` +
        `<span class="p1">P1: ${prob.toFixed(4)}</span>` +
        `<span class="p2">P2: ${(1-prob).toFixed(4)}</span>` +
        `</div>` +
        `<div class="prob-bar-container"><div class="prob-bar" style="width:${(prob*100).toFixed(1)}%"></div></div>`;

      // Game score grid
      buildGrid(pServe, pReturn, bestOf, p1Sets, p2Sets, server);
    } catch (e) {
      $('manual-prob').innerHTML = `Error: ${e.message}`;
    }
  }, 10);
}

function buildGrid(pServe, pReturn, bestOf, p1Sets, p2Sets, server) {
  const grid = winProbabilityGrid(pServe, pReturn, bestOf, p1Sets, p2Sets, server);
  if (grid.size === 0) { $('manual-grid').innerHTML = ''; return; }

  let maxG1 = 0, maxG2 = 0;
  for (const k of grid.keys()) {
    const [g1, g2] = k.split(',').map(Number);
    if (g1 > maxG1) maxG1 = g1;
    if (g2 > maxG2) maxG2 = g2;
  }

  let html = '<table class="grid-table"><tr><th>P1\\P2</th>';
  for (let g2 = 0; g2 <= maxG2; g2++) html += `<th>${g2}</th>`;
  html += '</tr>';

  for (let g1 = 0; g1 <= maxG1; g1++) {
    html += `<tr><th>${g1}</th>`;
    for (let g2 = 0; g2 <= maxG2; g2++) {
      const val = grid.get(`${g1},${g2}`);
      if (val !== undefined) {
        const r = Math.round(255 * (1 - val));
        const g = Math.round(255 * val);
        html += `<td style="background:rgb(${r},${g},80);color:#fff">${val.toFixed(3)}</td>`;
      } else {
        html += '<td class="na">—</td>';
      }
    }
    html += '</tr>';
  }
  html += '</table>';
  $('manual-grid').innerHTML = '<h3>Win Probability by Game Score</h3>' + html;
}

// ---- Transition system cache ----
function getSystem(pServe, pReturn, bestOf, server) {
  const key = `${pServe},${pReturn},${bestOf},${server}`;
  if (cachedSystem && cachedSystem.key === key) return cachedSystem;
  const sys = buildTransitionSystem(pServe, pReturn, bestOf, server);
  cachedSystem = { key, ...sys };
  return cachedSystem;
}
