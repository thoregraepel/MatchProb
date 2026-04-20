// Canvas-based win probability timeline chart.

export class TimelineChart {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.probs = [];
    this.setBoundaries = [];   // [{point, label}]
    this.gameBoundaries = [];  // [point]
    this.currentPoint = 0;
    this.showSetLines = true;
    this.showGameLines = true;
    this.player1Name = 'P1';
    this.player2Name = 'P2';
  }

  setData(probs, setBoundaries, gameBoundaries, player1, player2) {
    this.probs = probs;
    this.setBoundaries = setBoundaries;
    this.gameBoundaries = gameBoundaries;
    this.player1Name = player1;
    this.player2Name = player2;
  }

  draw() {
    const { canvas, ctx, probs } = this;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width;
    const H = rect.height;

    const pad = { top: 25, right: 15, bottom: 30, left: 45 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    ctx.clearRect(0, 0, W, H);

    if (probs.length < 2) return;

    const n = probs.length;
    const xScale = (i) => pad.left + (i / (n - 1)) * plotW;
    const yScale = (p) => pad.top + (1 - p) * plotH;

    // Grid lines
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 0.5;
    for (const p of [0, 0.25, 0.5, 0.75, 1.0]) {
      const y = yScale(p);
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(W - pad.right, y);
      ctx.stroke();
    }

    // 50% reference line
    ctx.strokeStyle = '#666';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(pad.left, yScale(0.5));
    ctx.lineTo(W - pad.right, yScale(0.5));
    ctx.stroke();
    ctx.setLineDash([]);

    // Game boundary lines
    if (this.showGameLines) {
      ctx.strokeStyle = 'rgba(100,100,100,0.3)';
      ctx.lineWidth = 0.5;
      for (const pt of this.gameBoundaries) {
        const x = xScale(pt);
        ctx.beginPath();
        ctx.moveTo(x, pad.top);
        ctx.lineTo(x, pad.top + plotH);
        ctx.stroke();
      }
    }

    // Set boundary lines
    if (this.showSetLines) {
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 3]);
      for (const { point, label } of this.setBoundaries) {
        const x = xScale(point);
        ctx.strokeStyle = '#e74c3c';
        ctx.beginPath();
        ctx.moveTo(x, pad.top);
        ctx.lineTo(x, pad.top + plotH);
        ctx.stroke();

        ctx.fillStyle = '#e74c3c';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(label, x, pad.top - 5);
      }
      ctx.setLineDash([]);
    }

    // P1 probability line
    ctx.strokeStyle = '#2ecc71';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const x = xScale(i), y = yScale(probs[i]);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // P2 probability line
    ctx.strokeStyle = '#e74c3c';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const x = xScale(i), y = yScale(1 - probs[i]);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Current point marker
    if (this.currentPoint >= 0 && this.currentPoint < n) {
      const cx = xScale(this.currentPoint);
      const cy = yScale(probs[this.currentPoint]);
      ctx.fillStyle = '#fff';
      ctx.strokeStyle = '#2ecc71';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(cx, cy, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }

    // Y-axis labels
    ctx.fillStyle = '#aaa';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    for (const p of [0, 0.25, 0.5, 0.75, 1.0]) {
      ctx.fillText(p.toFixed(2), pad.left - 5, yScale(p) + 4);
    }

    // X-axis label
    ctx.fillStyle = '#aaa';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Point in match', W / 2, H - 5);

    // Legend
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillStyle = '#2ecc71';
    ctx.fillText(this.player1Name, pad.left + 5, pad.top + 15);
    ctx.fillStyle = '#e74c3c';
    ctx.fillText(this.player2Name, pad.left + 5, pad.top + 30);
  }
}
