# MatchProb

Tennis match probability calculator using Markov chains.

Given a probability of winning a point on serve (and return), MatchProb computes the exact probability of winning the match from any score state. It provides both Monte Carlo simulation and an analytical solution via absorbing Markov chains.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run tests

```bash
pytest tests/
```

## Run the web app

```bash
streamlit run matchprob/app.py
```

## How it works

Tennis scoring is a finite Markov chain. Each state encodes the full score (points, games, sets) plus who is serving. From any non-terminal state, a point is won by the server with probability `p_serve` or by the returner with probability `1 - p_serve`.

The analytical solution partitions states into transient and absorbing (match-over), then solves for win probabilities using the fundamental matrix of the absorbing chain: `N = (I - Q)^{-1}`, where Q is the transient-to-transient sub-matrix.
