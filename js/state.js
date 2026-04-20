// MatchState — complete state of a tennis match.
// Immutable value type: create new objects for each state transition.

export class MatchState {
  constructor({
    p1Points = 0,
    p2Points = 0,
    p1Games = 0,
    p2Games = 0,
    p1Sets = 0,
    p2Sets = 0,
    server = 1,
    tiebreak = false,
    tbPointsPlayed = 0,
    tbStartServer = 0,
    bestOf = 2,       // sets to win: 2 = best-of-3, 3 = best-of-5
  } = {}) {
    this.p1Points = p1Points;
    this.p2Points = p2Points;
    this.p1Games = p1Games;
    this.p2Games = p2Games;
    this.p1Sets = p1Sets;
    this.p2Sets = p2Sets;
    this.server = server;
    this.tiebreak = tiebreak;
    this.tbPointsPlayed = tbPointsPlayed;
    this.tbStartServer = tbStartServer;
    this.bestOf = bestOf;
  }

  isTerminal() {
    return this.p1Sets >= this.bestOf || this.p2Sets >= this.bestOf;
  }

  matchWinner() {
    if (this.p1Sets >= this.bestOf) return 1;
    if (this.p2Sets >= this.bestOf) return 2;
    return null;
  }

  // Unique string key for use in Maps/Sets
  key() {
    return `${this.p1Points},${this.p2Points},${this.p1Games},${this.p2Games},${this.p1Sets},${this.p2Sets},${this.server},${this.tiebreak?1:0},${this.tbPointsPlayed},${this.tbStartServer},${this.bestOf}`;
  }

  scoreString() {
    const pointNames = { 0: '0', 1: '15', 2: '30', 3: '40' };
    const sets = `Sets: ${this.p1Sets}-${this.p2Sets}`;
    const games = `Games: ${this.p1Games}-${this.p2Games}`;

    if (this.isTerminal()) {
      return `${sets} (Match over, P${this.matchWinner()} wins)`;
    }

    let pointStr;
    if (this.tiebreak) {
      pointStr = `Tiebreak: ${this.p1Points}-${this.p2Points}`;
    } else if (this.p1Points >= 3 && this.p2Points >= 3) {
      if (this.p1Points === this.p2Points) {
        pointStr = 'Deuce';
      } else if (this.p1Points > this.p2Points) {
        pointStr = this.server === 1 ? 'Ad-In' : 'Ad-Out';
      } else {
        pointStr = this.server === 1 ? 'Ad-Out' : 'Ad-In';
      }
    } else {
      const p1Name = pointNames[this.p1Points] ?? String(this.p1Points);
      const p2Name = pointNames[this.p2Points] ?? String(this.p2Points);
      pointStr = `Points: ${p1Name}-${p2Name}`;
    }

    return `${sets}, ${games}, ${pointStr}`;
  }
}
