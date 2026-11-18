/**
 * Timing utilities.
 *
 * Spec section 10 requires stimulus_presented_at / response_at to come from
 * a monotonic clock (performance.now()), NOT from React render timing or
 * Date.now() drift. We use performance.now() for all latency math, and
 * convert to wall-clock ISO timestamps (via performance.timeOrigin) only
 * when serializing telemetry events for the backend.
 */

/** Monotonic timestamp in milliseconds, safe for latency subtraction. */
export function monotonicNowMs(): number {
  return performance.now();
}

/** Converts a performance.now() timestamp into an absolute Date for telemetry. */
export function monotonicToDate(monotonicMs: number): Date {
  return new Date(performance.timeOrigin + monotonicMs);
}

/** Converts a performance.now() timestamp into an ISO 8601 string. */
export function monotonicToISOString(monotonicMs: number): string {
  return monotonicToDate(monotonicMs).toISOString();
}

/** Latency in milliseconds between two monotonic timestamps. Never negative. */
export function latencyMs(startMonotonicMs: number, endMonotonicMs: number): number {
  return Math.max(0, endMonotonicMs - startMonotonicMs);
}
