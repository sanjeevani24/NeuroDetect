export function monotonicNowMs(): number {
  return performance.now();
}

export function monotonicToISOString(monotonicMs: number): string {
  return new Date(performance.timeOrigin + monotonicMs).toISOString();
}

export function latencyMs(startMs: number, endMs: number): number {
  return Math.max(0, endMs - startMs);
}
