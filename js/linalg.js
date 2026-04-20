// Dense linear algebra: solve Ax = b via Gaussian elimination with partial pivoting.
// Used to solve (I - Q)x = r for the absorbing Markov chain.

/**
 * Solve Ax = b in-place. A is n×n (row-major flat array), b is length-n.
 * Returns x (the modified b array). A is destroyed in the process.
 */
export function solve(A, b, n) {
  // Forward elimination with partial pivoting
  for (let col = 0; col < n; col++) {
    // Find pivot
    let maxVal = Math.abs(A[col * n + col]);
    let maxRow = col;
    for (let row = col + 1; row < n; row++) {
      const val = Math.abs(A[row * n + col]);
      if (val > maxVal) { maxVal = val; maxRow = row; }
    }

    // Swap rows
    if (maxRow !== col) {
      for (let j = col; j < n; j++) {
        const tmp = A[col * n + j];
        A[col * n + j] = A[maxRow * n + j];
        A[maxRow * n + j] = tmp;
      }
      const tmp = b[col]; b[col] = b[maxRow]; b[maxRow] = tmp;
    }

    const pivot = A[col * n + col];
    if (Math.abs(pivot) < 1e-15) continue; // singular or near-singular

    // Eliminate below
    for (let row = col + 1; row < n; row++) {
      const factor = A[row * n + col] / pivot;
      A[row * n + col] = 0;
      for (let j = col + 1; j < n; j++) {
        A[row * n + j] -= factor * A[col * n + j];
      }
      b[row] -= factor * b[col];
    }
  }

  // Back substitution
  for (let row = n - 1; row >= 0; row--) {
    let sum = b[row];
    for (let j = row + 1; j < n; j++) {
      sum -= A[row * n + j] * b[j];
    }
    b[row] = sum / A[row * n + row];
  }

  return b;
}

/**
 * Solve (I - Q)x = r where Q is sparse.
 * qRows: array of {row, col, val} entries for Q (transient-to-transient).
 * rVec: right-hand side vector of length nT.
 * nT: number of transient states.
 * Returns solution vector x of length nT.
 *
 * For small systems (nT < 8000), builds dense matrix and uses Gaussian elimination.
 * For larger systems, uses Gauss-Seidel iterative method.
 */
export function solveAbsorbing(qEntries, rVec, nT) {
  if (nT < 8000) {
    return solveDense(qEntries, rVec, nT);
  }
  return solveGaussSeidel(qEntries, rVec, nT);
}

function solveDense(qEntries, rVec, nT) {
  // Build (I - Q) as flat row-major array
  const A = new Float64Array(nT * nT); // initialized to 0
  // Set diagonal to 1 (identity)
  for (let i = 0; i < nT; i++) A[i * nT + i] = 1.0;
  // Subtract Q entries
  for (const { row, col, val } of qEntries) {
    A[row * nT + col] -= val;
  }

  const b = new Float64Array(rVec);
  return solve(A, b, nT);
}

function solveGaussSeidel(qEntries, rVec, nT) {
  // Build sparse row structure for Q
  const qByRow = new Array(nT);
  for (let i = 0; i < nT; i++) qByRow[i] = [];
  for (const { row, col, val } of qEntries) {
    qByRow[row].push({ col, val });
  }

  const x = new Float64Array(rVec); // initial guess
  const maxIter = 10000;
  const tol = 1e-12;

  for (let iter = 0; iter < maxIter; iter++) {
    let maxDiff = 0;
    for (let i = 0; i < nT; i++) {
      let sum = rVec[i];
      for (const { col, val } of qByRow[i]) {
        sum += val * x[col]; // (I-Q)x = r  =>  x_i = r_i + sum(Q_ij * x_j)
      }
      const diff = Math.abs(sum - x[i]);
      if (diff > maxDiff) maxDiff = diff;
      x[i] = sum;
    }
    if (maxDiff < tol) break;
  }

  return x;
}
