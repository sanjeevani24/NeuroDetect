export function monotonicNowMs(): number {
  return performance.now();
}

export function monotonicToISOString(monotonicMs: number): string {
  return new Date(performance.timeOrigin + monotonicMs).toISOString();
}
