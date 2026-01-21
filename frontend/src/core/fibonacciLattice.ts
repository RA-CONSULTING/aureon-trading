// Fibonacci Time Lattice Generator
// Generates time knots based on Fibonacci sequence for QGITA detection

export class FibonacciLattice {
  /**
   * Generate time knots based on Fibonacci sequence.
   * 
   * @param startTime - Starting timestamp (milliseconds)
   * @param baseIntervalMinutes - Base time step (e.g., 5 minutes)
   * @param numPoints - Number of Fibonacci knots to generate
   * @returns Array of timestamp knots
   */
  generateLattice(
    startTime: number,
    baseIntervalMinutes: number,
    numPoints: number
  ): number[] {
    // Generate Fibonacci sequence
    const fib: number[] = [0, 1];
    for (let i = 2; i < numPoints; i++) {
      fib.push(fib[i - 1] + fib[i - 2]);
    }

    // Convert to timestamps
    const baseIntervalMs = baseIntervalMinutes * 60 * 1000;
    const knots = fib.map(f => startTime + baseIntervalMs * f);

    return knots;
  }

  /**
   * Find the closest price data point to each Fibonacci knot.
   * 
   * @param knots - Fibonacci time knots (timestamps)
   * @param priceData - Array of {timestamp, price} objects
   * @returns Array of prices aligned to Fibonacci knots
   */
  alignPricesToKnots(
    knots: number[],
    priceData: Array<{ timestamp: number; price: number }>
  ): Array<{ timestamp: number; price: number }> {
    return knots.map(knot => {
      // Find closest data point to this knot
      let closest = priceData[0];
      let minDiff = Math.abs(priceData[0].timestamp - knot);

      for (const data of priceData) {
        const diff = Math.abs(data.timestamp - knot);
        if (diff < minDiff) {
          minDiff = diff;
          closest = data;
        }
      }

      return closest;
    });
  }

  /**
   * Check if we're currently near a Fibonacci knot.
   * 
   * @param currentTime - Current timestamp
   * @param knots - Fibonacci time knots
   * @param toleranceMinutes - How close we need to be (default 2 minutes)
   * @returns Boolean indicating if we're near a knot
   */
  isNearKnot(
    currentTime: number,
    knots: number[],
    toleranceMinutes: number = 2
  ): boolean {
    const toleranceMs = toleranceMinutes * 60 * 1000;
    
    for (const knot of knots) {
      if (Math.abs(currentTime - knot) <= toleranceMs) {
        return true;
      }
    }
    
    return false;
  }

  /**
   * Get the next Fibonacci knot after current time.
   */
  getNextKnot(currentTime: number, knots: number[]): number | null {
    for (const knot of knots) {
      if (knot > currentTime) {
        return knot;
      }
    }
    return null;
  }

  /**
   * Calculate time until next Fibonacci knot.
   */
  getTimeUntilNextKnot(currentTime: number, knots: number[]): number {
    const nextKnot = this.getNextKnot(currentTime, knots);
    if (nextKnot === null) return Infinity;
    return nextKnot - currentTime;
  }
}

export const fibonacciLattice = new FibonacciLattice();
